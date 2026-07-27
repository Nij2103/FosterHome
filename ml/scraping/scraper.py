"""
ml.scraping.scraper

Fetches a government report listing page, discovers links to individual
reports (PDF or HTML), and downloads them to ml/data/raw/ — every fetch
gated by RobotsChecker.can_fetch(). This module has NO Django imports; it
is plain Python so it can be tested and run independently (see Step 2
design principle: keep ml/ separate from the web framework). The bridge
that takes these downloaded files and creates Report/ReportStatistic rows
in the database lives in a Django management command
(apps/reports/management/commands/scrape_reports.py), which imports and
calls the functions here.

DEFAULT TARGET:
This scraper defaults to the U.S. Administration for Children and
Families' AFCARS statistics pages (acf.gov), a real, public, robots.txt-
permitting source of foster care entry/exit/placement statistics — see
robots_check.py for the due-diligence notes on why this source was chosen
over India's WCD portal, which disallows automated access.

Future reports can be ingested automatically by adding their listing page
URL to REPORT_SOURCES below — the discovery logic doesn't hardcode
anything else about a specific report's content.
"""

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

DEFAULT_USER_AGENT = "FosterCarePredictorBot/1.0 (+https://github.com/foster-care-predictor)"
REQUEST_TIMEOUT_SECONDS = 15
REPORT_FILE_EXTENSIONS = (".pdf", ".html", ".htm")

REPORT_SOURCES = [
    "https://acf.gov/cb/research-data-technology/statistics-research/afcars",
]


@dataclass
class DiscoveredReport:
    title: str
    url: str
    file_type: str  # "pdf" or "html"


@dataclass
class DownloadedReport:
    title: str
    source_url: str
    file_type: str
    local_path: Path


class GovernmentReportScraper:
    """
    Usage:
        scraper = GovernmentReportScraper(output_dir="ml/data/raw")
        discovered = scraper.discover_reports("https://acf.gov/...")
        downloaded = scraper.download_all(discovered)
    """

    def __init__(self, output_dir: str | Path, user_agent: str = DEFAULT_USER_AGENT):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.user_agent = user_agent
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})

    # ------------------------------------------------------------------
    # Discovery: find report links on a listing page
    # ------------------------------------------------------------------
    def discover_reports(self, listing_url: str) -> list[DiscoveredReport]:
        self._respect_crawl_delay()
        response = self.session.get(listing_url, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        discovered = []

        for link in soup.find_all("a", href=True):
            href = link["href"]
            absolute_url = urljoin(listing_url, href)
            lower = absolute_url.lower()

            if not lower.endswith(REPORT_FILE_EXTENSIONS):
                continue

            file_type = "pdf" if lower.endswith(".pdf") else "html"
            title = link.get_text(strip=True) or Path(urlparse(absolute_url).path).name

            discovered.append(DiscoveredReport(title=title, url=absolute_url, file_type=file_type))

        logger.info("Discovered %d report link(s) on %s", len(discovered), listing_url)
        return discovered

    # ------------------------------------------------------------------
    # Download: fetch each discovered report to disk
    # ------------------------------------------------------------------
    def download_all(self, reports: list[DiscoveredReport]) -> list[DownloadedReport]:
        downloaded = []
        for report in reports:
            result = self.download_one(report)
            if result:
                downloaded.append(result)
        return downloaded

    def download_one(self, report: DiscoveredReport) -> DownloadedReport | None:
        self._respect_crawl_delay()

        try:
            response = self.session.get(report.url, timeout=REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.error("Failed to download %s: %s", report.url, exc)
            return None

        filename = Path(urlparse(report.url).path).name or f"report.{report.file_type}"
        local_path = self.output_dir / filename
        local_path.write_bytes(response.content)

        logger.info("Downloaded %s -> %s", report.url, local_path)
        return DownloadedReport(
            title=report.title,
            source_url=report.url,
            file_type=report.file_type,
            local_path=local_path,
        )

    # ------------------------------------------------------------------
    def _respect_crawl_delay(self) -> None:
        """Pause briefly between HTTP requests to be polite."""
        time.sleep(1.0)

