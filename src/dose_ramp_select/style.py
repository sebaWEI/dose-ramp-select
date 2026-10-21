"""Wiki-aligned matplotlib style (PekingHSC wiki-plot-spec)."""

from __future__ import annotations

from matplotlib import pyplot as plt

WIKI = {
    "blue": "#169bb7",
    "green": "#059669",
    "ink": "#1a3348",
    "muted": "#7a8896",
    "line": "#dfe7ed",
    "paper": "#f6f9fa",
    "white": "#ffffff",
}


def apply_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Inter", "Arial", "Helvetica", "DejaVu Sans"],
            "font.size": 10,
            "axes.titlesize": 13,
            "axes.titleweight": "semibold",
            "axes.titlelocation": "left",
            "axes.labelsize": 11,
            "axes.labelcolor": WIKI["ink"],
            "axes.edgecolor": WIKI["line"],
            "axes.linewidth": 0.8,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.facecolor": WIKI["white"],
            "figure.facecolor": WIKI["white"],
            "xtick.color": WIKI["ink"],
            "ytick.color": WIKI["ink"],
            "xtick.labelsize": 9.5,
            "ytick.labelsize": 9.5,
            "text.color": WIKI["ink"],
            "grid.color": WIKI["line"],
            "grid.linewidth": 0.7,
            "legend.frameon": False,
            "legend.fontsize": 9,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
            "savefig.dpi": 300,
            "savefig.bbox": "tight",
            "savefig.facecolor": WIKI["white"],
        }
    )
