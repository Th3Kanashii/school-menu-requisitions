"""Builds the requisition .xlsx document from scratch."""

from __future__ import annotations

import io
from collections.abc import Sequence
from datetime import datetime

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, Side
from openpyxl.worksheet.worksheet import Worksheet

from .config import DOCUMENT_TITLE, SCHOOL_NAME
from .models import Product, Requisition


class RequisitionWriter:
    """Renders a `Requisition` as an Excel workbook ready for printing."""

    SHEET_TITLE = "Вимога"
    BLANK_DATE_LINE = "на «_______»__________________ 2026 р."
    TABLE_HEADERS = ("№п/п", "Найменування продуктів", "К - сть")
    SIGNATURES = (
        "Дієтсестра          ___________________",
        "Завскладом       ____________________",
        "ЗМІНА ПРИЙНЯЛА __________________",
        "Кухар ___________________",
    )

    FONT_NAME = "Times New Roman"
    COLUMN_WIDTHS = {"A": 8, "B": 32, "C": 14.3}
    TITLE_ROW_HEIGHTS = (17.5, 18.75, 30)
    HEADER_ROW = 4
    HEADER_ROW_HEIGHT = 32.25
    PRODUCT_ROW_HEIGHT = 21
    SIGNATURE_ROW_HEIGHT = 22

    _MEDIUM = Side(style="medium")
    BOX = Border(left=_MEDIUM, right=_MEDIUM, top=_MEDIUM, bottom=_MEDIUM)
    CENTERED = Alignment(horizontal="center", vertical="center", wrap_text=True)
    LEFT_ALIGNED = Alignment(horizontal="left", vertical="center", wrap_text=True)

    def __init__(
        self,
        school_name: str = SCHOOL_NAME,
        document_title: str = DOCUMENT_TITLE,
    ) -> None:
        """Create a writer.

        Args:
            school_name: First line of the document.
            document_title: Second line of the document.
        """
        self._school_name = school_name
        self._document_title = document_title

    def render(self, requisition: Requisition) -> bytes:
        """Return the content of the .xlsx file for `requisition`."""
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = self.SHEET_TITLE

        self._set_column_widths(sheet)
        self._write_title(sheet, requisition)
        self._write_table_header(sheet)
        last_row = self._write_products(sheet, requisition.products)
        self._write_signatures(sheet, first_row=last_row + 2)
        self._configure_printing(sheet)

        buffer = io.BytesIO()
        workbook.save(buffer)
        return buffer.getvalue()

    def _font(self, size: int, *, bold: bool = True) -> Font:
        return Font(name=self.FONT_NAME, size=size, bold=bold)

    def _set_column_widths(self, sheet: Worksheet) -> None:
        for column, width in self.COLUMN_WIDTHS.items():
            sheet.column_dimensions[column].width = width

    def _write_title(self, sheet: Worksheet, requisition: Requisition) -> None:
        date_line = requisition.date.label() if requisition.date else self.BLANK_DATE_LINE
        lines = (self._school_name, self._document_title, date_line)
        for row, (text, height) in enumerate(
            zip(lines, self.TITLE_ROW_HEIGHTS, strict=True), start=1
        ):
            sheet.cell(row, 1, text).font = self._font(14)
            sheet.row_dimensions[row].height = height

    def _write_table_header(self, sheet: Worksheet) -> None:
        for column, text in enumerate(self.TABLE_HEADERS, start=1):
            cell = sheet.cell(self.HEADER_ROW, column, text)
            cell.font, cell.alignment, cell.border = self._font(12), self.CENTERED, self.BOX
        sheet.row_dimensions[self.HEADER_ROW].height = self.HEADER_ROW_HEIGHT

    def _write_products(self, sheet: Worksheet, products: Sequence[Product]) -> int:
        """Write one row per product and return the number of the last written row."""
        row = self.HEADER_ROW
        for number, product in enumerate(products, start=1):
            row += 1
            cells = (
                (number, self.CENTERED, self._font(14)),
                (product.name, self.LEFT_ALIGNED, self._font(14)),
                (product.quantity, self.CENTERED, self._font(14, bold=False)),
            )
            for column, (value, alignment, font) in enumerate(cells, start=1):
                cell = sheet.cell(row, column, value)
                cell.font, cell.alignment, cell.border = font, alignment, self.BOX
            sheet.row_dimensions[row].height = self.PRODUCT_ROW_HEIGHT
        return row

    def _write_signatures(self, sheet: Worksheet, first_row: int) -> None:
        for row, text in enumerate(self.SIGNATURES, start=first_row):
            sheet.cell(row, 1, text).font = self._font(14)
            sheet.row_dimensions[row].height = self.SIGNATURE_ROW_HEIGHT

        generated_at = datetime.now().strftime("%d.%m.%Y о %H:%M")
        footer = (
            "Документ сформовано автоматично",
            f"Дата формування: {generated_at}",
        )

        for row, text in enumerate(footer, start=first_row + len(self.SIGNATURES) + 1):
            sheet.cell(row, 1, text).font = self._font(10, bold=False)
            sheet.row_dimensions[row].height = self.SIGNATURE_ROW_HEIGHT

    @staticmethod
    def _configure_printing(sheet: Worksheet) -> None:
        sheet.page_setup.orientation = "portrait"
        sheet.page_setup.paperSize = sheet.PAPERSIZE_A4
        sheet.page_setup.fitToWidth = 1
        sheet.page_setup.fitToHeight = 0
        sheet.sheet_properties.pageSetUpPr.fitToPage = True
