"""Application service that turns a menu workbook into requisition workbooks."""

from __future__ import annotations

import io
import re
import zipfile
from collections.abc import Sequence
from dataclasses import dataclass

from .models import Requisition
from .parser import SheetParser
from .reader import SourceReader
from .writer import RequisitionWriter


@dataclass(frozen=True)
class GeneratedFile:
    """An output workbook together with the data it was created from."""

    filename: str
    content: bytes
    requisition: Requisition


class RequisitionService:
    """Coordinates reading, parsing and writing; one source sheet gives one file."""

    def __init__(
        self,
        parser: SheetParser | None = None,
        writer: RequisitionWriter | None = None,
    ) -> None:
        """Create the service.

        Args:
            parser: Sheet parser; the default one uses the configured settings.
            writer: Document writer; the default one uses the configured texts.
        """
        self._parser = parser or SheetParser()
        self._writer = writer or RequisitionWriter()

    def generate(self, source: bytes, suffix: str) -> list[GeneratedFile]:
        """Generate one requisition workbook for each worksheet of the source file.

        Args:
            source: Content of the menu workbook.
            suffix: File extension of the workbook: ".xls" or ".xlsx".

        Raises:
            SourceFileError: If the file is unsupported or cannot be read.
        """
        sheets = SourceReader.for_suffix(suffix).read(source)
        generated: list[GeneratedFile] = []
        for number, sheet in enumerate(sheets, start=1):
            requisition = self._parser.parse(sheet)
            generated.append(
                GeneratedFile(
                    filename=self.make_filename(number, sheet.title),
                    content=self._writer.render(requisition),
                    requisition=requisition,
                )
            )
        return generated

    @staticmethod
    def make_filename(number: int, sheet_title: str) -> str:
        """Create a filesystem-safe output filename, e.g. 'Вимога_2_Дієта - обід.xlsx'."""
        safe_title = re.sub(r'[\\/:*?"<>|]', "", sheet_title)
        safe_title = re.sub(r"\s+", " ", safe_title).strip()
        return f"Вимога_{number}_{safe_title}.xlsx"

    @staticmethod
    def pack_zip(files: Sequence[GeneratedFile]) -> bytes:
        """Bundle the generated workbooks into an in-memory ZIP archive."""
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
            for generated_file in files:
                archive.writestr(generated_file.filename, generated_file.content)
        return buffer.getvalue()
