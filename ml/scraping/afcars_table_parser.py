"""
ml.scraping.afcars_table_parser

WHY A REPORT-SPECIFIC PARSER FILE:
pdf_parser.extract_tables() deliberately returns raw, uninterpreted rows —
table *shape* differs from report to report, so a generic extractor can't
safely guess which row is a header, which column is a year, etc. This
module encodes the specific, real shape of the AFCARS "Numbers at a
Glance" table (year columns, metric-name rows), which is the table this
project's scraper actually targets. If a future report has a different
shape, it gets its own small parser function here rather than trying to
force one "universal" parser to handle every possible table layout — that
kind of over-generalization usually breaks silently on edge cases.

REAL TABLE SHAPE (from the actual AFCARS Report #29, a public U.S.
government document):

    Fiscal Year                                          | 2017 | 2018 | ...
    Number in foster care on September 30 of the FY       | 436,556 | ...
    Number entered foster care during the FY               | 270,197 | ...
    Number exited foster care during the FY                 | 248,882 | ...

This is a "wide" table (years as columns). We transpose it into the long/
tidy (state, year, metric_name, value) shape that ReportStatistic uses —
this transposition is exactly what "designed with EDA in mind" (Step 3
notes) pays off: no further reshaping is needed before Pandas/Seaborn use it.
"""

import logging
import re

logger = logging.getLogger(__name__)

# The reports this parser targets are national aggregates, not broken out
# by state — AFCARS state-level breakdowns exist in a different table.
# Using the literal string "National" (rather than leaving state blank)
# keeps ReportStatistic.state non-null and makes national vs. state-level
# rows trivially filterable later in EDA: df[df.state == "National"].
NATIONAL_LABEL = "National"


def _looks_like_year(value: str) -> bool:
    return bool(re.fullmatch(r"(19|20)\d{2}", value.strip()))


def _parse_number(value: str) -> float | None:
    """Turns '436,556' or '436556' into 436556.0; returns None if not numeric."""
    if value is None:
        return None
    cleaned = value.replace(",", "").replace("%", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_numbers_at_a_glance(rows: list[list[str]]) -> list[dict]:
    """
    Input: raw table rows as returned by pdf_parser.extract_tables()
           (a list of lists of cell strings/None).
    Output: a list of dicts, each ready to become one ReportStatistic row:
           {"state": "National", "year": 2021, "metric_name": "...", "value": 391098.0}
    """
    if not rows:
        return []

    header = [cell.strip() if cell else "" for cell in rows[0]]
    year_columns = {idx: cell for idx, cell in enumerate(header) if _looks_like_year(cell)}

    if not year_columns:
        logger.warning("No year columns detected in table header %r — skipping.", header)
        return []

    statistics = []
    for row in rows[1:]:
        if not row or row[0] is None:
            continue
        metric_name = row[0].strip()
        if not metric_name:
            continue

        for col_idx, year_str in year_columns.items():
            if col_idx >= len(row):
                continue
            value = _parse_number(row[col_idx])
            if value is None:
                continue
            statistics.append({
                "state": NATIONAL_LABEL,
                "year": int(year_str),
                "metric_name": _normalize_metric_name(metric_name),
                "value": value,
            })

    logger.info("Parsed %d statistic(s) from 'Numbers at a Glance' table.", len(statistics))
    return statistics


def _normalize_metric_name(raw_name: str) -> str:
    """
    Turns a prose column label like 'Number in foster care on September 30
    of the FY' into a short, consistent snake_case metric key like
    'children_in_care_sep30' — easier to filter/group on in Pandas than
    matching on slightly-varying prose strings across report editions.
    """
    mapping = {
        "number in foster care on september 30 of the fy": "children_in_care_sep30",
        "number entered foster care during the fy": "entered_foster_care",
        "number exited foster care during the fy": "exited_foster_care",
        "number served by the foster care system during the fy": "total_served",
        "number waiting to be adopted on september 30 of the fy": "waiting_to_be_adopted",
    }
    key = raw_name.strip().lower()
    return mapping.get(key, re.sub(r"[^a-z0-9]+", "_", key).strip("_"))
