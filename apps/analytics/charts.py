"""
apps.analytics.charts

Matplotlib in-memory SVG chart generators.
Renders all charts directly into BytesIO buffers and returns pure SVG strings.
No temporary files or images are written to disk.
"""

import matplotlib.pyplot as plt
import numpy as np
from apps.analytics.utils import THEME_COLORS, render_fig_to_svg


def _apply_figure_styles(fig, ax, title_text):
    """Applies clean consistent styling parameters to Matplotlib axes."""
    fig.patch.set_facecolor("none")
    ax.set_facecolor("#ffffff")
    ax.set_title(title_text, fontsize=12, fontweight="bold", pad=14, color="#212121")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#E5E5E5")
    ax.spines["bottom"].set_color("#E5E5E5")
    ax.tick_params(colors="#6B7280", labelsize=9)


# ==============================================================================
# 1. Child Analytics Charts
# ==============================================================================

def generate_child_age_distribution_chart(data: dict) -> str:
    """Generates a Bar Chart of Child Age Distribution in SVG."""
    fig, ax = plt.subplots(figsize=(6, 3.8), dpi=100)
    _apply_figure_styles(fig, ax, "Child Age Distribution")

    categories = list(data.keys())
    counts = list(data.values())

    BAR_PALETTE = ["#2E7D32", "#1565C0", "#E65100", "#6A1B9A", "#00838F", "#AD1457", "#558B2F", "#4527A0"]
    bar_colors = [BAR_PALETTE[i % len(BAR_PALETTE)] for i in range(len(categories))]
    bars = ax.bar(categories, counts, color=bar_colors, width=0.55, edgecolor="none", zorder=3)
    ax.set_ylabel("Number of Children", fontsize=9.5, fontweight="bold", color="#475569")
    ax.grid(axis="y", linestyle="--", alpha=0.5, color="#cbd5e1", zorder=0)

    for bar in bars:
        height = bar.get_height()
        ax.annotate(
            f"{int(height)}",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8.5,
            fontweight="bold",
            color="#1e293b",
        )

    plt.tight_layout()
    return render_fig_to_svg(fig)


def generate_child_language_distribution_chart(data: dict) -> str:
    """Generates a Pie Chart of Primary Language Spoken in SVG."""
    fig, ax = plt.subplots(figsize=(6, 3.8), dpi=100)
    fig.patch.set_facecolor("none")
    ax.set_title("Primary Language Spoken", fontsize=12, fontweight="bold", pad=14, color="#1e293b")

    labels = list(data.keys())
    counts = list(data.values())
    colors = THEME_COLORS["pie_colors"][: len(labels)]

    wedges, texts, autotexts = ax.pie(
        counts,
        labels=labels,
        autopct="%1.1f%%",
        startangle=140,
        colors=colors,
        textprops={"fontsize": 8.5, "color": "#1e293b"},
        wedgeprops={"edgecolor": "#ffffff", "linewidth": 1.5},
    )
    for autotext in autotexts:
        autotext.set_color("#ffffff")
        autotext.set_weight("bold")

    plt.tight_layout()
    return render_fig_to_svg(fig)


# ==============================================================================
# 2. Foster Family Analytics Charts
# ==============================================================================

def generate_family_capacity_distribution_chart(data: dict) -> str:
    """Generates a Bar Chart of Foster Family Capacity Distribution in SVG."""
    fig, ax = plt.subplots(figsize=(6, 3.8), dpi=100)
    _apply_figure_styles(fig, ax, "Family Capacity Distribution")

    categories = list(data.keys())
    counts = list(data.values())

    BAR_PALETTE = ["#4CAF50", "#1565C0", "#F59E0B", "#E53935", "#8E24AA", "#00ACC1", "#FB8C00", "#43A047"]
    bar_colors = [BAR_PALETTE[i % len(BAR_PALETTE)] for i in range(len(categories))]
    bars = ax.bar(categories, counts, color=bar_colors, width=0.55, edgecolor="none", zorder=3)
    ax.set_ylabel("Number of Families", fontsize=9.5, fontweight="bold", color="#475569")
    ax.grid(axis="y", linestyle="--", alpha=0.5, color="#cbd5e1", zorder=0)

    for bar in bars:
        height = bar.get_height()
        ax.annotate(
            f"{int(height)}",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8.5,
            fontweight="bold",
            color="#1e293b",
        )

    plt.tight_layout()
    return render_fig_to_svg(fig)


def generate_family_housing_stability_chart(data: dict) -> str:
    """Generates a Pie Chart of Housing Stability in SVG."""
    fig, ax = plt.subplots(figsize=(6, 3.8), dpi=100)
    fig.patch.set_facecolor("none")
    ax.set_title("Housing Stability Tier", fontsize=12, fontweight="bold", pad=14, color="#1e293b")

    labels = list(data.keys())
    counts = list(data.values())
    colors = [THEME_COLORS["success"], THEME_COLORS["warning"], THEME_COLORS["danger"]]
    colors = colors[: len(labels)]

    wedges, texts, autotexts = ax.pie(
        counts,
        labels=labels,
        autopct="%1.1f%%",
        startangle=140,
        colors=colors,
        textprops={"fontsize": 8.5, "color": "#1e293b"},
        wedgeprops={"edgecolor": "#ffffff", "linewidth": 1.5},
    )
    for autotext in autotexts:
        autotext.set_color("#ffffff")
        autotext.set_weight("bold")

    plt.tight_layout()
    return render_fig_to_svg(fig)


# ==============================================================================
# 3. Prediction Analytics Charts
# ==============================================================================

def generate_compatibility_score_distribution_chart(data: dict) -> str:
    """Generates a Bar Chart of Compatibility Score Distribution in SVG."""
    fig, ax = plt.subplots(figsize=(6, 3.8), dpi=100)
    _apply_figure_styles(fig, ax, "Compatibility Score Range Distribution")

    categories = list(data.keys())
    counts = list(data.values())

    BAR_PALETTE = ["#C62828", "#E65100", "#F59E0B", "#2E7D32", "#1565C0"]
    bar_colors = [BAR_PALETTE[i % len(BAR_PALETTE)] for i in range(len(categories))]
    bars = ax.bar(categories, counts, color=bar_colors, width=0.55, edgecolor="none", zorder=3)
    ax.set_ylabel("Prediction Runs", fontsize=9.5, fontweight="bold", color="#475569")
    ax.grid(axis="y", linestyle="--", alpha=0.5, color="#cbd5e1", zorder=0)

    for bar in bars:
        height = bar.get_height()
        ax.annotate(
            f"{int(height)}",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8.5,
            fontweight="bold",
            color="#1e293b",
        )

    plt.tight_layout()
    return render_fig_to_svg(fig)


def generate_risk_level_distribution_chart(data: dict) -> str:
    """Generates a Pie Chart of Prediction Risk Level Distribution in SVG."""
    fig, ax = plt.subplots(figsize=(6, 3.8), dpi=100)
    fig.patch.set_facecolor("none")
    ax.set_title("Prediction Risk Level Breakdown", fontsize=12, fontweight="bold", pad=14, color="#1e293b")

    labels = list(data.keys())
    counts = list(data.values())
    colors = [THEME_COLORS["success"], THEME_COLORS["warning"], THEME_COLORS["danger"]]
    colors = colors[: len(labels)]

    wedges, texts, autotexts = ax.pie(
        counts,
        labels=labels,
        autopct="%1.1f%%",
        startangle=140,
        colors=colors,
        textprops={"fontsize": 8.5, "color": "#1e293b"},
        wedgeprops={"edgecolor": "#ffffff", "linewidth": 1.5},
    )
    for autotext in autotexts:
        autotext.set_color("#ffffff")
        autotext.set_weight("bold")

    plt.tight_layout()
    return render_fig_to_svg(fig)


# ==============================================================================
# 4. Placement Analytics Charts
# ==============================================================================

def generate_placement_status_distribution_chart(data: dict) -> str:
    """Generates a Pie Chart of Placement Status Distribution in SVG."""
    fig, ax = plt.subplots(figsize=(6, 3.8), dpi=100)
    fig.patch.set_facecolor("none")
    ax.set_title("Placement Status Breakdown", fontsize=12, fontweight="bold", pad=14, color="#1e293b")

    labels = list(data.keys())
    counts = list(data.values())
    colors = [THEME_COLORS["success"], "#1565C0", THEME_COLORS["danger"], THEME_COLORS["warning"]]
    colors = colors[: len(labels)]

    wedges, texts, autotexts = ax.pie(
        counts,
        labels=labels,
        autopct="%1.1f%%",
        startangle=140,
        colors=colors,
        textprops={"fontsize": 8.5, "color": "#1e293b"},
        wedgeprops={"edgecolor": "#ffffff", "linewidth": 1.5},
    )
    for autotext in autotexts:
        autotext.set_color("#ffffff")
        autotext.set_weight("bold")

    plt.tight_layout()
    return render_fig_to_svg(fig)


def generate_monthly_placement_trend_chart(data: dict) -> str:
    """Generates a Line Chart of Monthly Placement Trends in SVG."""
    fig, ax = plt.subplots(figsize=(6, 3.8), dpi=100)
    _apply_figure_styles(fig, ax, "Monthly Placement Volume Trend")

    categories = list(data.keys())
    counts = list(data.values())

    ax.plot(
        categories,
        counts,
        color=THEME_COLORS["primary"],
        marker="o",
        linewidth=2.5,
        markersize=6,
        markerfacecolor=THEME_COLORS["accent"],
        markeredgecolor="#ffffff",
        markeredgewidth=1.5,
        zorder=3,
    )
    ax.set_ylabel("Placements Created", fontsize=9.5, fontweight="bold", color="#475569")
    ax.grid(True, linestyle="--", alpha=0.5, color="#cbd5e1", zorder=0)

    for i, count in enumerate(counts):
        ax.annotate(
            f"{int(count)}",
            xy=(categories[i], count),
            xytext=(0, 6),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8.5,
            fontweight="bold",
            color="#1e293b",
        )

    plt.tight_layout()
    return render_fig_to_svg(fig)
