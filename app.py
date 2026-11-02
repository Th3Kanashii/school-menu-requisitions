"""Streamlit interface: upload a menu workbook, download a requisition for each sheet."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import streamlit as st

from src.reader import SourceFileError
from src.service import RequisitionService

if TYPE_CHECKING:
    from src.service import GeneratedFile

AUTHOR = "Kishibe"
XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@st.cache_data(show_spinner="Формую Вимоги…")
def generate_files(source: bytes, suffix: str) -> list[GeneratedFile]:
    """Generate the requisition files; cached so reruns do not repeat the work."""
    return RequisitionService().generate(source, suffix)


class RequisitionApp:
    """The single page of the application."""

    def run(self) -> None:
        """Render the whole page: header, upload and results, footer."""
        st.set_page_config(
            page_title="Формування Вимог",
            page_icon="📋",
            menu_items={"About": f"**Формування Вимог**  \nАвтор: {AUTHOR}"},
        )
        st.title("📋 Формування Вимог")
        st.caption("З кожного листа беремо колонку «РАЗОМ» і формуємо окремий файл Вимоги.")
        self._handle_upload()
        self._show_footer()

    def _handle_upload(self) -> None:
        """Ask for the menu file and show the generated requisitions."""
        source = st.file_uploader("Файл з меню-вимогами", type=["xls", "xlsx"])
        if source is None:
            return

        try:
            files = generate_files(source.getvalue(), Path(source.name).suffix)
        except SourceFileError as error:
            st.error(str(error))
            return

        self._show_results(files)

    @staticmethod
    def _show_footer() -> None:
        """Show the author line at the bottom of the page."""
        st.divider()
        st.caption(f"Автор: {AUTHOR}")

    def _show_results(self, files: list[GeneratedFile]) -> None:
        """Show the download-all button and one row per generated file."""
        st.success(f"Готово: сформовано файлів — {len(files)}")
        st.download_button(
            "⬇️ Завантажити все одним архівом (.zip)",
            data=RequisitionService.pack_zip(files),
            file_name="Вимоги.zip",
            mime="application/zip",
            type="primary",
        )
        st.divider()
        for number, file in enumerate(files, start=1):
            self._show_file(file, number)

    @staticmethod
    def _show_file(file: GeneratedFile, number: int) -> None:
        """Show information about one generated file and its download button."""
        requisition = file.requisition
        info, button = st.columns([3, 1])
        with info:
            st.markdown(
                f"**{number}. {requisition.title}**  \nпродуктів: {len(requisition.products)}"
            )
            if requisition.is_empty:
                st.warning(
                    "Не знайдено шапку таблиці («Найменування продуктів» і «РАЗОМ») — "
                    "файл порожній."
                )
        with button:
            st.download_button(
                "Завантажити",
                data=file.content,
                file_name=file.filename,
                mime=XLSX_MIME,
                key=f"download_{number}",
            )


if __name__ == "__main__":
    RequisitionApp().run()
