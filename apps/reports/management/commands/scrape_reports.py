"""
Management command: scrape_reports

Bridges the framework-independent ml/scraping package (plain Python, no
Django imports — see Step 2 design) into the database. This command is
the ONLY place ml/scraping and Django models are wired together, which
keeps ml/ genuinely reusable/testable outside the web framework.

Run with:
    python manage.py scrape_reports
    python manage.py scrape_reports --source https://acf.gov/some-other-listing-page
    python manage.py scrape_reports --local-dir /path/to/fixtures  (see --help)

Safe to re-run: reports are matched on source_url and updated, not duplicated.
"""

from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from apps.reports.models import Report, ReportStatistic
from ml.scraping.afcars_table_parser import parse_numbers_at_a_glance
from ml.scraping.pdf_parser import clean_text, extract_tables, extract_text
from ml.scraping.scraper import REPORT_SOURCES, GovernmentReportScraper


class Command(BaseCommand):
    help = "Scrape government foster-care report PDFs/HTML pages and ingest them into the database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            action="append",
            help="Listing page URL to scrape. Can be passed multiple times. "
                 "Defaults to ml.scraping.scraper.REPORT_SOURCES if omitted.",
        )
        parser.add_argument(
            "--local-dir",
            help="Skip live discovery/download entirely and ingest PDF/HTML files "
                 "already present in this local directory instead. Useful for "
                 "offline testing or re-ingesting previously downloaded reports.",
        )

    def handle(self, *args, **options):
        raw_dir = Path(settings.BASE_DIR) / "ml" / "data" / "raw"

        if options["local_dir"]:
            downloaded = self._collect_local_files(Path(options["local_dir"]))
        else:
            sources = options["source"] or REPORT_SOURCES
            downloaded = []
            scraper = GovernmentReportScraper(output_dir=raw_dir)
            for listing_url in sources:
                self.stdout.write(f"Discovering reports at {listing_url} ...")
                discovered = scraper.discover_reports(listing_url)
                self.stdout.write(f"  found {len(discovered)} candidate link(s)")
                downloaded += scraper.download_all(discovered)

        if not downloaded:
            self.stdout.write(self.style.WARNING("No reports downloaded/found — nothing to ingest."))
            return

        for item in downloaded:
            self._ingest(item)

        self.stdout.write(self.style.SUCCESS(f"Ingested {len(downloaded)} report(s)."))

    # ------------------------------------------------------------------
    def _collect_local_files(self, directory: Path):
        """Wraps local files into the same shape download_all() would return."""
        from ml.scraping.scraper import DownloadedReport

        items = []
        for path in directory.glob("*"):
            if path.suffix.lower() not in (".pdf", ".html", ".htm"):
                continue
            file_type = "pdf" if path.suffix.lower() == ".pdf" else "html"
            items.append(DownloadedReport(
                title=path.stem.replace("-", " ").replace("_", " ").title(),
                source_url=f"file://{path}",
                file_type=file_type,
                local_path=path,
            ))
        return items

    # ------------------------------------------------------------------
    def _ingest(self, downloaded):
        report, created = Report.objects.update_or_create(
            source_url=downloaded.source_url,
            defaults={
                "title": downloaded.title,
                "file_type": downloaded.file_type,
            },
        )

        with open(downloaded.local_path, "rb") as fh:
            report.raw_file.save(downloaded.local_path.name, File(fh), save=False)

        if downloaded.file_type == "pdf":
            raw_text = extract_text(downloaded.local_path)
            report.parsed_text = clean_text(raw_text)
            report.save()

            tables = extract_tables(downloaded.local_path)
            stats_created = 0
            for table in tables:
                rows = table["rows"]
                # Heuristic: this is the "Numbers at a Glance" table if its
                # header row contains "Fiscal Year" — the only table shape
                # this project currently knows how to interpret (see
                # afcars_table_parser.py docstring for why that's by design,
                # not a limitation to hide).
                header_text = " ".join(cell or "" for cell in rows[0]).lower() if rows else ""
                if "fiscal year" not in header_text:
                    continue

                parsed_stats = parse_numbers_at_a_glance(rows)
                for stat in parsed_stats:
                    ReportStatistic.objects.update_or_create(
                        report=report,
                        state=stat["state"],
                        year=stat["year"],
                        metric_name=stat["metric_name"],
                        defaults={"value": stat["value"]},
                    )
                    stats_created += 1

            self.stdout.write(f"  {report.title}: {stats_created} statistic(s) ingested")
        else:
            report.save()
            self.stdout.write(f"  {report.title}: saved (HTML report, no table parsing yet)")

        verb = "Created" if created else "Updated"
        self.stdout.write(f"{verb} Report: {report.title}")
