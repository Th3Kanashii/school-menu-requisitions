# school-menu-requisitions

A Streamlit app that reads menu sheets from an Excel file and creates a separate
"Requisition" (*Вимога*) workbook for each sheet. Both `.xlsx` and the legacy `.xls`
format are supported.

## How it works

1. `app.py`: the web interface. The `RequisitionApp` class handles uploading the source
   file and downloading the results.
2. `src/reader.py`: `SourceReader` and its subclasses `XlsxReader` and `XlsReader` read
   Excel files into neutral data structures. `SourceReader.for_suffix` picks the right
   reader.
3. `src/parser.py`: `SheetParser` finds the table header, the date and the products, and
   sums up repeated products. `NameNormalizer` cleans and unifies product names using
   the glossary.
4. `src/writer.py`: `RequisitionWriter` builds the output workbook and its print layout.
5. `src/service.py`: `RequisitionService` coordinates reading, parsing, writing the
   files and packing them into a ZIP.
6. `src/models.py` and `src/config.py`: data models (`dataclass`) and settings.

To support a new file format, add a `SourceReader` subclass with a `suffix` attribute
and a `_read_sheets` method. The components (`SheetParser`, `RequisitionWriter`,
`NameNormalizer`) can be replaced through constructor arguments.

## Running

Python 3.12 is required.

```bash
uv sync
make run
```

## Input data

- The table is located by its header: the row that contains both the headings
  `Найменування продуктів` ("Product name") and `РАЗОМ` ("TOTAL"). Columns are taken
  from this header rather than from fixed letters, so different layouts work
  (Monday: F and Q; Sunday: G and R).
- Every row below the header that has a name and a number in the `РАЗОМ` column ends up
  in the Requisition. Quantities of identical products within a sheet are summed.
- The date is read from the cell above the table, in the form «на 06 вересня 2026 р.»
  ("as of 6 September 2026").
- One sheet of the file = one Requisition. (The "Sunday" file has a single sheet, so it
  produces a single Requisition for the whole day.)
- Product-name mappings are configured in `src/config.py`.

Note: for formulas in `.xlsx` files, the results cached by Excel are used
(`data_only=True`). If a workbook has no cached formula results, those values may come
out empty. Open and save the workbook in Excel before importing it.

## Tests

```bash
uv run -m unittest discover -s tests -t .
```
