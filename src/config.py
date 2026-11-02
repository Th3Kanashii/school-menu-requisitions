"""Settings: table header texts, document texts and the product-name glossary."""

from __future__ import annotations

# --- table header in the source sheets ---------------------------------------
# Columns are NOT hard-coded by letter: the table is shifted on different weekdays
# (Monday: name in F, total in Q; Sunday: name in G, total in R).
# The header row is the first row that contains both headings below.
NAME_HEADER = "Найменування продуктів"  # heading of the product-name column
TOTAL_HEADER = "РАЗОМ"  # heading of the quantity column

# --- generated document ------------------------------------------------------
SCHOOL_NAME = "ВИГОДСЬКА СШ"
DOCUMENT_TITLE = "Меню вимога на видачу продуктів"
QUANTITY_DECIMALS = 3  # number of decimals quantities are rounded to

# --- product-name glossary ---------------------------------------------------
# "Spelling in the menu" -> "name used in the requisition".
# It merges different spellings of one product and lets the document use warehouse
# names. Lookups ignore letter case and extra spaces.
PRODUCT_ALIASES: dict[str, str] = {
    "Гречка": "Крупа гречана",
    "Мука": "Борошно пшеничне",
    "Свинина": "М'ясо",
    "Томатна паста": "Томат",
    "Масло": "Масло вершкове",
    "Огірки солені": "Огірки",
    "Рис оброблений": "Рис",
    "Часник сухий": "Часник",
    "Перець мелен.": "Перець чорний мел.",
    "Перець чор. мелен.": "Перець чорний мел.",
    "Сік 0,200": "Сік",
    "Хліб цільноз.": "Хліб цільнозерновий",
    "Хліб цільнозерн.": "Хліб цільнозерновий",
    "Хліб цільнозернов.": "Хліб цільнозерновий",
    "Хліб цільнозер.": "Хліб цільнозерновий",
    "Хліб цільн.": "Хліб цільнозерновий",
    "Рис проп.": "Рис",
    "Сік (200 гр.)": "Сік",
    "Капуста свіж.": "Капуста",
    "Сухарі паніров.": "Сухарі",
    "Горошок свіжоз": "Горошок свіжозамор.",
}
