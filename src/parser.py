"""Turns a source sheet (`SheetData`) into a requisition (`Requisition`)."""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Mapping, Sequence

from .config import NAME_HEADER, PRODUCT_ALIASES, QUANTITY_DECIMALS, TOTAL_HEADER
from .models import CellValue, MenuDate, Product, Requisition, Row, SheetData, TableLayout


class NameNormalizer:
    """Cleans text and maps menu spellings of products onto requisition names."""

    def __init__(self, aliases: Mapping[str, str] = PRODUCT_ALIASES) -> None:
        """Create a normalizer.

        Args:
            aliases: Glossary "spelling in the menu" -> "name in the requisition".
        """
        self._canonical_names = {self.key(source): target for source, target in aliases.items()}

    @staticmethod
    def clean(text: str) -> str:
        """Collapse whitespace: '  Олія  ' -> 'Олія'."""
        return re.sub(r"\s+", " ", text).strip()

    @classmethod
    def key(cls, text: str) -> str:
        """Return a comparison key that ignores letter case and extra spaces."""
        return cls.clean(text).casefold()

    def canonical_name(self, raw_name: str) -> str:
        """Return the glossary name of a product, or its cleaned original name."""
        cleaned = self.clean(raw_name)
        return self._canonical_names.get(self.key(cleaned), cleaned)


class SheetParser:
    """Extracts the date and the products with their totals from a sheet."""

    # "на 28 вересня 2026 р." -> ("28", "вересня", "2026")
    _DATE_PATTERN = re.compile(r"на\s+(\d{1,2})\s+([^\W\d_]+)\s+(\d{4})")

    def __init__(self, normalizer: NameNormalizer | None = None) -> None:
        """Create a parser.

        Args:
            normalizer: Name normalizer; the default one uses the configured glossary.
        """
        self._normalizer = normalizer or NameNormalizer()

    def parse(self, sheet: SheetData) -> Requisition:
        """Build a requisition from one sheet.

        A sheet without a recognizable table header yields an empty requisition.
        """
        title = sheet.title.strip()
        layout = self.find_layout(sheet.rows)
        if layout is None:
            return Requisition(title=title, date=None, products=())
        return Requisition(
            title=title,
            date=self._find_date(sheet.rows[: layout.header_row]),
            products=self._collect_products(sheet.rows[layout.header_row + 1 :], layout),
        )

    def find_layout(self, rows: Sequence[Row]) -> TableLayout | None:
        """Locate the product table by its header instead of fixed column letters.

        The header is the first row that contains both the "Найменування продуктів"
        and the "РАЗОМ" headings. This lets one logic serve sheets whose table is
        shifted (Monday: F and Q, Sunday: G and R). A stray "Разом" elsewhere, such as
        a row label in column A below the header, is ignored because that row has no
        product-name heading.
        """
        for index, row in enumerate(rows):
            name_column = self._find_column(row, NAME_HEADER)
            total_column = self._find_column(row, TOTAL_HEADER)
            if name_column is not None and total_column is not None:
                return TableLayout(index, name_column, total_column)
        return None

    def _find_column(self, row: Row, header: str) -> int | None:
        """Return the index of the first cell equal to `header`, ignoring letter case."""
        target = self._normalizer.key(header)
        for index, value in enumerate(row):
            if isinstance(value, str) and self._normalizer.key(value) == target:
                return index
        return None

    @staticmethod
    def _cell(row: Row, index: int) -> CellValue:
        """Return the cell value, or None when the row is shorter than `index`."""
        return row[index] if index < len(row) else None

    def _find_date(self, rows_above_table: Sequence[Row]) -> MenuDate | None:
        """Find a date like "на 28 вересня 2026 р." in any cell above the table."""
        for row in rows_above_table:
            for value in row:
                if isinstance(value, str) and (match := self._DATE_PATTERN.search(value)):
                    return MenuDate(*match.groups())
        return None

    def _collect_products(self, rows: Sequence[Row], layout: TableLayout) -> tuple[Product, ...]:
        """Sum quantities of identical products and return them sorted by name."""
        totals: defaultdict[str, float] = defaultdict(float)
        names: dict[str, str] = {}

        for row in rows:
            raw_name = self._cell(row, layout.name_column)
            total = self._cell(row, layout.total_column)
            if not (isinstance(raw_name, str) and raw_name.strip() and isinstance(total, float)):
                continue  # not a product row: subtotals, signatures, blank lines
            name = self._normalizer.canonical_name(raw_name)
            key = self._normalizer.key(name)
            names.setdefault(key, name)
            totals[key] += total

        products = (
            Product(names[key], round(total, QUANTITY_DECIMALS)) for key, total in totals.items()
        )
        return tuple(sorted(products, key=lambda product: product.name.casefold()))
