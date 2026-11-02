"""Readers that turn Excel workbooks into format-independent sheet data."""

from __future__ import annotations

import io
import zipfile
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar

import openpyxl
from openpyxl.utils.exceptions import InvalidFileException

from .models import CellValue, SheetData

if TYPE_CHECKING:
    from xlrd.sheet import Sheet

# Cell type codes of xlrd (xlrd.XL_CELL_TEXT and xlrd.XL_CELL_NUMBER). They are kept
# here so the optional xlrd dependency is imported only when an .xls file is read.
_XLS_CELL_TEXT = 1
_XLS_CELL_NUMBER = 2


class SourceFileError(ValueError):
    """Raised when the source file cannot be read or uses an unsupported format."""


class SourceReader(ABC):
    """Base class of the format-specific workbook readers.

    A subclass declares the file `suffix` it handles and implements `_read_sheets`.
    Use `SourceReader.for_suffix` to get the reader that matches a file name.
    """

    suffix: ClassVar[str]

    @classmethod
    def for_suffix(cls, suffix: str) -> SourceReader:
        """Create the reader that handles `suffix` (for example ".xls").

        Raises:
            SourceFileError: If no reader supports the suffix.
        """
        for reader_class in cls.__subclasses__():
            if reader_class.suffix == suffix.lower():
                return reader_class()
        raise SourceFileError(f"Непідтримуваний формат «{suffix}». Потрібен .xls або .xlsx.")

    def read(self, content: bytes) -> list[SheetData]:
        """Read every worksheet of the workbook stored in `content`.

        Raises:
            SourceFileError: If the content is not a readable Excel workbook.
        """
        try:
            return self._read_sheets(content)
        except (OSError, zipfile.BadZipFile, InvalidFileException) as error:
            raise SourceFileError("Файл пошкоджений або не є таблицею Excel.") from error

    @abstractmethod
    def _read_sheets(self, content: bytes) -> list[SheetData]:
        """Format-specific reading; may raise the errors handled in `read`."""


class XlsxReader(SourceReader):
    """Reader for the modern .xlsx format (backed by openpyxl)."""

    suffix = ".xlsx"

    def _read_sheets(self, content: bytes) -> list[SheetData]:
        # data_only=True returns the cached results of formulas instead of the formulas.
        workbook = openpyxl.load_workbook(io.BytesIO(content), data_only=True, read_only=True)
        try:
            return [
                SheetData(
                    title=worksheet.title,
                    rows=tuple(
                        tuple(self._to_cell(value) for value in row)
                        for row in worksheet.iter_rows(values_only=True)
                    ),
                )
                for worksheet in workbook.worksheets
            ]
        finally:
            workbook.close()

    @staticmethod
    def _to_cell(value: object) -> CellValue:
        """Keep only text and numbers; numbers are always normalized to float."""
        if isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            return value
        return None


class XlsReader(SourceReader):
    """Reader for the legacy .xls format (backed by xlrd)."""

    suffix = ".xls"

    def _read_sheets(self, content: bytes) -> list[SheetData]:
        import xlrd  # imported lazily: the dependency is needed only for this format

        try:
            workbook = xlrd.open_workbook(file_contents=content)
        except xlrd.XLRDError as error:
            raise SourceFileError("Файл пошкоджений або не є таблицею Excel.") from error

        return [
            SheetData(
                title=sheet.name,
                rows=tuple(
                    tuple(self._read_cell(sheet, row, column) for column in range(sheet.ncols))
                    for row in range(sheet.nrows)
                ),
            )
            for sheet in workbook.sheets()
        ]

    @staticmethod
    def _read_cell(sheet: Sheet, row: int, column: int) -> CellValue:
        """Return the cell as str or float; empty, error, date and boolean cells give None."""
        cell = sheet.cell(row, column)
        if cell.ctype == _XLS_CELL_TEXT:
            return str(cell.value)
        if cell.ctype == _XLS_CELL_NUMBER:
            return float(cell.value)
        return None
