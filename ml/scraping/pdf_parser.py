"""
ml.scraping.pdf_parser

Extracts plain text (for search/keyword matching, stored in
Report.parsed_text) and tables (for structured ReportStatistic rows) from
downloaded government report PDFs, using pdfplumber.

WHY PDFPLUMBER OVER PyPDF2/pypdf:
pypdf and PyPDF2 are good for merging/splitting/encrypting PDFs (that's
why the separate 'pdf' skill in this environment uses them for document
manipulation), but they are weak at table extraction from PDFs — layout
tables are just visually-positioned text to them. pdfplumber inspects
character positions and line geometry to reconstruct actual table
structure, which is exactly what we need since government reports are
essentially tables wrapped in prose.
"""

import logging
from pathlib import Path

import pdfplumber

logger = logging.getLogger(__name__)


def extract_text(pdf_path: str | Path) -> str:
    """
    Extracts and concatenates plain text from every page of a PDF.
    Used to populate Report.parsed_text for keyword search.
    """
    text_chunks = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text_chunks.append(page_text)
    return "\n\n".join(text_chunks).strip()


def extract_tables(pdf_path: str | Path) -> list[dict]:
    """
    Extracts every table found in the PDF.

    Returns a list of dicts: [{"page": int, "table_index": int, "rows": [[...], ...]}, ...]
    Kept as raw rows (not yet mapped to ReportStatistic) because table
    *shape* varies by report — the caller (see
    ml/features/feature_engineering.py or the ingest management command)
    is responsible for interpreting a specific table's columns, since that
    mapping is inherently report-specific domain knowledge, not something
    a generic extractor can infer safely.
    """
    tables_found = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            page_tables = page.extract_tables()
            for table_index, table in enumerate(page_tables):
                # Skip empty/noise tables sometimes returned for decorative lines
                if not table or all(cell is None for row in table for cell in row):
                    continue
                tables_found.append({
                    "page": page_num,
                    "table_index": table_index,
                    "rows": table,
                })
    logger.info("Extracted %d table(s) from %s", len(tables_found), pdf_path)
    return tables_found


def clean_text(raw_text: str) -> str:
    """
    Basic cleaning applied to extracted text before storage: collapses
    repeated whitespace/newlines left behind by PDF layout artifacts.
    Deliberately conservative — we don't want to accidentally strip
    meaningful content, just normalize whitespace noise.
    """
    lines = [line.strip() for line in raw_text.splitlines()]
    non_empty = [line for line in lines if line]
    return "\n".join(non_empty)
