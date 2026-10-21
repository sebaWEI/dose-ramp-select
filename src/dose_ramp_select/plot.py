"""Two-panel dose-selection figures."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.patches import Patch

from .metrics import DoseMetrics
from .style import WIKI, apply_style

OTHER_MARKERS = [
    dict(ls="-", marker="o", ms=4.0),
    dict(ls="--", marker="s", ms=3.8),
    dict(ls=":", marker="^", ms=4.2),
    dict(ls="-.", marker="D", ms=3.6),
]


def _fmt_dose(d: float) -> str:
    if float(d).is_integer():
        return str(int(d))
    return f"{d:g}"


def plot_fold_profiles(
    metrics: list[DoseMetrics],
    selected: float,
    out: Path,
    title: str = "Relative activity across doses",
) -> Path:
    apply_style()
    constructs = metrics[0].constructs
    x = np.arange(len(constructs))

    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    ax.grid(axis="y", which="major")
    ax.grid(axis="x", visible=False)
    ax.axhline(1.0, color=WIKI["muted"], lw=0.9, ls=(0, (3, 2.5)), zorder=1)

    others = [m for m in metrics if not np.isclose(m.dose, selected)]
    selected_m = next(m for m in metrics if np.isclose(m.dose, selected))

    for i, m in enumerate(others):
        st = OTHER_MARKERS[i % len(OTHER_MARKERS)]
        ax.plot(
            x,
            m.fold_mean,
            color=WIKI["muted"],
            lw=1.35,
            alpha=0.85,
            zorder=2,
            label=f"{_fmt_dose(m.dose)}",
            ls=st["ls"],
            marker=st["marker"],
            markersize=st["ms"],
            markerfacecolor=WIKI["white"],
            markeredgecolor=WIKI["muted"],
            markeredgewidth=0.9,
        )

    ax.fill_between(
        x,
        selected_m.fold_mean - selected_m.fold_sd,
        selected_m.fold_mean + selected_m.fold_sd,
        color=WIKI["blue"],
        alpha=0.14,
        linewidth=0,
        zorder=3,
    )
    ax.plot(
        x,
        selected_m.fold_mean,
        color=WIKI["blue"],
        lw=2.2,
        marker="o",
        markersize=5.5,
        markerfacecolor=WIKI["blue"],
        markeredgecolor=WIKI["ink"],
        markeredgewidth=0.5,
        zorder=4,
        label=f"{_fmt_dose(selected)} (selected)",
    )

    ax.set_xticks(x)
    ax.set_xticklabels(constructs, rotation=40, ha="right")
    ax.set_ylabel("Fold vs control")
    ax.set_xlabel("Construct")
    ax.set_title(title)
    ax.set_xlim(-0.3, len(constructs) - 0.7)
    ax.set_ylim(bottom=0)

    handles, labels = ax.get_legend_handles_labels()
    # selected last in plot → move to front of legend
    if handles:
        handles = [handles[-1]] + handles[:-1]
        labels = [labels[-1]] + labels[:-1]
    ax.legend(handles, labels, loc="upper right", handlelength=2.2)

    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out)
    fig.savefig(out.with_suffix(".svg"))
    plt.close(fig)
    return out


def plot_variance(
    metrics: list[DoseMetrics],
    selected: float,
    out: Path,
    title: str = "Low replicate noise and high sequence-explained variance",
) -> Path:
    apply_style()
    doses = [m.dose for m in metrics]
    within = np.array([m.within_var for m in metrics])
    eta = np.array([m.eta2 for m in metrics])
    x = np.arange(len(doses))

    fig, (ax, ax2) = plt.subplots(
        1, 2, figsize=(7.6, 4.0), gridspec_kw={"wspace": 0.35}
    )
    for a in (ax, ax2):
        a.grid(axis="y", which="major")
        a.grid(axis="x", visible=False)

    for i, dose in enumerate(doses):
        is_sel = np.isclose(dose, selected)
        fill = WIKI["blue"] if is_sel else WIKI["muted"]
        alpha = 1.0 if is_sel else 0.85
        ax.bar(
            i,
            within[i],
            width=0.62,
            color=fill,
            alpha=alpha,
            edgecolor=WIKI["ink"],
            linewidth=0.6,
            zorder=3,
        )
        ax.text(
            i,
            within[i] * 1.06,
            f"{within[i]:.3f}",
            ha="center",
            va="bottom",
            fontsize=8.5,
            color=WIKI["blue"] if is_sel else WIKI["muted"],
            fontweight="semibold" if is_sel else "normal",
        )

    ax.set_xticks(x)
    ax.set_xticklabels([_fmt_dose(d) for d in doses])
    ax.set_ylabel(r"Within-sequence variance of $\mathrm{log}_{10}$(value)")
    ax.set_title("Replicate noise (lower is better)")
    ax.set_ylim(0, max(within) * 1.28 if len(within) else 1.0)

    for i, dose in enumerate(doses):
        is_sel = np.isclose(dose, selected)
        fill = WIKI["blue"] if is_sel else WIKI["muted"]
        ax2.bar(
            i,
            eta[i],
            width=0.62,
            color=fill,
            alpha=1.0 if is_sel else 0.85,
            edgecolor=WIKI["ink"],
            linewidth=0.6,
            zorder=3,
        )
        ax2.bar(
            i,
            1 - eta[i],
            width=0.62,
            bottom=eta[i],
            color=WIKI["paper"],
            edgecolor=WIKI["ink"],
            linewidth=0.6,
            zorder=2,
        )
        ax2.text(
            i,
            eta[i] / 2,
            f"{eta[i]:.0%}",
            ha="center",
            va="center",
            fontsize=9,
            color=WIKI["white"],
            fontweight="semibold",
        )

    ax2.set_xticks(x)
    ax2.set_xticklabels([_fmt_dose(d) for d in doses])
    ax2.set_ylim(0, 1.05)
    ax2.set_ylabel("Fraction of total variance")
    ax2.set_title("η² = sequence / total (higher is better)")

    fig.legend(
        handles=[
            Patch(
                facecolor=WIKI["blue"],
                edgecolor=WIKI["ink"],
                linewidth=0.6,
                label=f"{_fmt_dose(selected)} (selected)",
            ),
            Patch(
                facecolor=WIKI["muted"],
                alpha=0.85,
                edgecolor=WIKI["ink"],
                linewidth=0.6,
                label="Other doses",
            ),
            Patch(
                facecolor=WIKI["paper"],
                edgecolor=WIKI["ink"],
                linewidth=0.6,
                label="Residual noise (right)",
            ),
        ],
        loc="upper center",
        bbox_to_anchor=(0.5, 0.02),
        ncol=3,
        fontsize=8.5,
    )
    fig.suptitle(
        title,
        x=0.01,
        ha="left",
        fontsize=13,
        fontweight="semibold",
        color=WIKI["ink"],
        y=0.98,
    )
    fig.subplots_adjust(left=0.09, right=0.98, top=0.86, bottom=0.18, wspace=0.35)

    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out)
    fig.savefig(out.with_suffix(".svg"))
    plt.close(fig)
    return out
