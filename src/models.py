"""Plain data structures shared by the reader, parser and writer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import NamedTuple

CellValue = str | float | None
Row = tuple[CellValue, ...]


@dataclass(frozen=True)
class SheetData:
    """A source sheet with all of its cells.

    Attributes:
        title: Sheet title as stored in the workbook.
        rows: All rows; the tuple index equals the sheet row number minus one.
    """

    title: str
    rows: tuple[Row, ...]


@dataclass(frozen=True)
class TableLayout:
    """Location of the product table on a sheet (all indexes are zero-based).

    Attributes:
        header_row: Row holding the "Найменування продуктів" and "РАЗОМ" headings.
        name_column: Column with product names.
        total_column: Column with the "РАЗОМ" quantities.
    """

    header_row: int
    name_column: int
    total_column: int


class MenuDate(NamedTuple):
    """Date taken from the menu heading, e.g. 28 вересня 2026."""

    day: str
    month: str
    year: str

    def label(self) -> str:
        """Return the date as printed on the document: `на «28» вересня 2026 р.`."""
        return f"на «{self.day}» {self.month} {self.year} р."


@dataclass(frozen=True)
class Product:
    """A product together with its total quantity."""

    name: str
    quantity: float


@dataclass(frozen=True)
class Requisition:
    """Content of one requisition document (one source sheet -> one document).

    Attributes:
        title: Title of the source sheet.
        date: Date found above the table, if any.
        products: Products sorted by name.
    """

    title: str
    date: MenuDate | None
    products: tuple[Product, ...]

    @property
    def is_empty(self) -> bool:
        """Whether the sheet contained no products."""
        return not self.products
