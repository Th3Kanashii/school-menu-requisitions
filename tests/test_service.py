"""Reading, file naming and packing of the generated requisitions."""

import io
import unittest
import zipfile

import openpyxl

from src.reader import SourceFileError, SourceReader
from src.service import RequisitionService


def make_source() -> bytes:
    """Build a one-sheet workbook shaped like a Sunday menu (name in G, total in R)."""
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Неділя 1 тиждень "
    sheet["G3"] = "на видачу продуктів харчування на 06  вересня 2026 р."
    sheet["G9"], sheet["R9"] = "Найменування продуктів", "РАЗОМ"
    for row, (name, total) in enumerate([("Масло ", 0.01), ("Гречка", 0.29), ("Масло", 0.02)], 15):
        sheet.cell(row, 7, name)
        sheet.cell(row, 18, total)
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


class ServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.files = RequisitionService().generate(make_source(), ".xlsx")

    def test_one_file_per_sheet_with_safe_name(self) -> None:
        self.assertEqual([f.filename for f in self.files], ["Вимога_1_Неділя 1 тиждень.xlsx"])

    def test_document_content(self) -> None:
        sheet = openpyxl.load_workbook(io.BytesIO(self.files[0].content)).active
        self.assertEqual(sheet["A3"].value, "на «06» вересня 2026 р.")
        self.assertEqual([sheet.cell(5, c).value for c in (1, 2, 3)], [1, "Крупа гречана", 0.29])
        self.assertEqual([sheet.cell(6, c).value for c in (1, 2, 3)], [2, "Масло вершкове", 0.03])

    def test_zip_contains_every_file(self) -> None:
        with zipfile.ZipFile(io.BytesIO(RequisitionService.pack_zip(self.files))) as archive:
            self.assertEqual(archive.namelist(), [f.filename for f in self.files])

    def test_filename_removes_forbidden_characters(self) -> None:
        filename = RequisitionService.make_filename(1, 'a/b:c*d?"e<f>g|h ')
        self.assertEqual(filename, "Вимога_1_abcdefgh.xlsx")


class ReaderTests(unittest.TestCase):
    def test_unsupported_suffix(self) -> None:
        with self.assertRaises(SourceFileError):
            SourceReader.for_suffix(".csv")

    def test_corrupted_xlsx(self) -> None:
        with self.assertRaises(SourceFileError):
            SourceReader.for_suffix(".xlsx").read(b"not a workbook")


if __name__ == "__main__":
    unittest.main()
