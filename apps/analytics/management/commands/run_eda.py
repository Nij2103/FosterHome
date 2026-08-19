"""
Management command: run_eda

Bridges ml/eda and ml/visualization (both pure pandas/seaborn, no Django
imports) into the database — same bridge pattern as scrape_reports (Step
6) and generate_synthetic_data (Step 7). Loads Child/FosterFamily/
Placement/ReportStatistic into DataFrames, runs the EDA functions, writes
a markdown summary, and generates every chart as a PNG under
media/analytics/charts/ so the Django dashboard (Step 10) can serve them
directly.

Run with: python manage.py run_eda
"""

from pathlib import Path

import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand

from apps.children.models import Child
from apps.families.models import FosterFamily
from apps.placements.models import Placement
from ml.eda.eda_report import (
    correlation_matrix,
    distribution_stats,
    duplicate_rows_summary,
    missing_values_summary,
    outlier_summary,
)
from ml.visualization import charts


class Command(BaseCommand):
    help = "Run full EDA (missing values, duplicates, outliers, correlation) and generate all charts."

    def handle(self, *args, **options):
        charts_dir = Path(settings.MEDIA_ROOT) / "analytics" / "charts"
        summary_path = Path(settings.BASE_DIR) / "docs" / "eda_summary.md"

        children_df = pd.DataFrame(list(Child.objects.values()))
        families_df = pd.DataFrame(list(FosterFamily.objects.values()))

        if children_df.empty or families_df.empty:
            self.stdout.write(self.style.ERROR(
                "No data found. Run `python manage.py generate_synthetic_data` first."
            ))
            return

        # The surrogate primary key is meaningless for statistical
        # analysis (it's an arbitrary row identifier, not a measured
        # quantity) — excluded from the numeric-analysis copy so it
        # doesn't pollute distribution/correlation/outlier tables with
        # noise. The full children_df (with id) is still used for chart
        # functions that need it for joins.
        children_numeric_df = children_df.drop(columns=["id"])

        # Build placements_df with the child/family attributes the charts
        # need (experience_years, disruption status) via a proper join.
        placement_rows = []
        for p in Placement.objects.select_related("child", "family").all():
            placement_rows.append({
                "status": p.status,
                "child_state": p.child.state,
                "family_state": p.family.state,
                "experience_years": p.family.experience_years,
            })
        placements_df = pd.DataFrame(placement_rows)

        stats_df = pd.DataFrame()

        self.stdout.write("Running EDA...")
        report_lines = ["# Exploratory Data Analysis Summary", ""]
        report_lines.append(f"Generated from {len(children_df)} children, "
                             f"{len(families_df)} foster families, "
                             f"{len(placements_df)} placements.\n")

        # --- Missing values ---
        missing_df = missing_values_summary(children_numeric_df)
        report_lines.append("## Missing Values (Children)")
        report_lines.append(missing_df.to_markdown(index=False) if not missing_df.empty else "None found.")
        report_lines.append("")

        # --- Duplicates ---
        dup = duplicate_rows_summary(children_df, subset=["first_name", "age", "state", "created_at"])
        report_lines.append("## Duplicate Rows (Children)")
        report_lines.append(f"Duplicate count: {dup['duplicate_count']} ({dup['duplicate_pct']}%)\n")

        # --- Distribution stats ---
        stats_table = distribution_stats(children_numeric_df)
        report_lines.append("## Distribution Statistics (Children, numeric columns)")
        report_lines.append(stats_table.to_markdown())
        report_lines.append("")

        # --- Outliers ---
        outliers = outlier_summary(children_numeric_df, columns=["age", "behavioral_notes_score", "time_in_care_months"])
        report_lines.append("## Outlier Summary (IQR method)")
        report_lines.append(outliers.to_markdown(index=False))
        report_lines.append("")

        # --- Correlation ---
        corr = correlation_matrix(children_numeric_df)
        report_lines.append("## Correlation Matrix (Children, numeric columns)")
        report_lines.append(corr.to_markdown())
        report_lines.append("")

        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text("\n".join(str(line) for line in report_lines))
        self.stdout.write(self.style.SUCCESS(f"EDA summary written to {summary_path}"))

        # --- Charts ---
        self.stdout.write("Generating charts...")
        generated = []
        generated.append(charts.plot_missing_values(missing_df, charts_dir / "missing_values.png"))
        generated.append(charts.plot_age_distribution(children_df, charts_dir / "age_distribution.png"))
        generated.append(charts.plot_gender_distribution(children_df, charts_dir / "gender_distribution.png"))
        generated.append(charts.plot_state_wise_children(children_df, charts_dir / "state_wise_children.png"))
        generated.append(charts.plot_special_needs_by_placement(children_df, charts_dir / "special_needs_by_placement.png"))
        generated.append(charts.plot_correlation_heatmap(corr, charts_dir / "correlation_heatmap.png"))
        generated.append(charts.plot_outlier_boxplot(children_df, "time_in_care_months", charts_dir / "outlier_boxplot_time_in_care.png"))
        generated.append(charts.plot_violin_behavioral_score(children_df, charts_dir / "violin_behavioral_score.png"))
        generated.append(charts.plot_pairplot(
            children_df, ["age", "behavioral_notes_score", "time_in_care_months"],
            charts_dir / "pairplot_numeric_features.png",
        ))
        generated.append(charts.plot_family_capacity_distribution(families_df, charts_dir / "family_capacity_distribution.png"))
        generated.append(charts.plot_home_type_distribution(families_df, charts_dir / "home_type_distribution.png"))

        if not placements_df.empty:
            generated.append(charts.plot_placement_status_counts(placements_df, charts_dir / "placement_status_counts.png"))
            generated.append(charts.plot_experience_vs_disruption(placements_df, charts_dir / "experience_vs_disruption.png"))

        if not stats_df.empty:
            for metric in stats_df["metric_name"].unique():
                safe_name = metric.replace("/", "_")
                generated.append(charts.plot_year_wise_trend(
                    stats_df, metric, charts_dir / f"trend_{safe_name}.png",
                ))

        for path in generated:
            self.stdout.write(f"  saved {path}")

        self.stdout.write(self.style.SUCCESS(f"Generated {len(generated)} chart(s) in {charts_dir}"))
