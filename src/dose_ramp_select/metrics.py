"""Dose-level metrics: fold profiles, within variance, η²."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .io import DoseRampError


@dataclass(frozen=True)
class DoseMetrics:
    dose: float
    n_reps: int
    within_var: float
    eta2: float
    fold_span: float
    median_cv: float
    constructs: list[str]
    fold_mean: np.ndarray
    fold_sd: np.ndarray


def _matrix(
    df: pd.DataFrame,
    dose: float,
    constructs: list[str],
) -> np.ndarray:
    g = df[np.isclose(df["dose"], dose) | (df["dose"] == dose)]
    if g.empty:
        # exact match fallback for ints
        g = df[df["dose"] == dose]
    piv = g.pivot_table(index="replicate", columns="construct", values="value", aggfunc="mean")
    missing = [c for c in constructs if c not in piv.columns]
    if missing:
        raise DoseRampError(f"Dose {dose}: missing constructs {missing}")
    X = piv[constructs].to_numpy(dtype=float)
    if X.shape[0] < 2:
        raise DoseRampError(f"Dose {dose}: need ≥2 replicates, got {X.shape[0]}")
    if np.any(~np.isfinite(X)):
        raise DoseRampError(f"Dose {dose}: non-finite values after pivoting")
    return X


def dose_metrics(
    df: pd.DataFrame,
    dose: float,
    constructs: list[str],
    control: str,
    sequence: list[str],
) -> DoseMetrics:
    X = _matrix(df, dose, constructs)
    c_idx = constructs.index(control)
    ctrl = X[:, [c_idx]]
    if np.any(ctrl <= 0):
        raise DoseRampError(
            f"Dose {dose}: control readout must be > 0 for fold normalization"
        )
    folds = X / ctrl
    fold_mean = folds.mean(0)
    fold_sd = folds.std(0, ddof=1)

    seq_idx = [constructs.index(c) for c in sequence]
    means = X.mean(0)
    sds = X.std(0, ddof=1)
    cvs = sds / np.clip(means, 1e-12, None)
    f_seq = fold_mean[seq_idx]
    fold_span = float(f_seq.max() - f_seq.min())
    median_cv = float(np.median(cvs[seq_idx]))

    logX = np.log10(np.clip(X, 1.0, None))
    # η² over all shared constructs (including control)
    grand = logX.mean()
    ss_b = sum(
        logX.shape[0] * (logX[:, k].mean() - grand) ** 2
        for k in range(logX.shape[1])
    )
    ss_w = sum(
        ((logX[:, k] - logX[:, k].mean()) ** 2).sum()
        for k in range(logX.shape[1])
    )
    eta2 = float(ss_b / (ss_b + ss_w)) if (ss_b + ss_w) > 0 else float("nan")

    # within-sequence variance: mean of per-construct replicate variances (log)
    within_var = float(np.mean([logX[:, k].var(ddof=1) for k in seq_idx]))

    return DoseMetrics(
        dose=float(dose),
        n_reps=int(X.shape[0]),
        within_var=within_var,
        eta2=eta2,
        fold_span=fold_span,
        median_cv=median_cv,
        constructs=list(constructs),
        fold_mean=fold_mean,
        fold_sd=fold_sd,
    )


def compute_all(
    df: pd.DataFrame,
    constructs: list[str],
    control: str,
    sequence: list[str],
) -> list[DoseMetrics]:
    doses = sorted(df["dose"].unique())
    return [dose_metrics(df, d, constructs, control, sequence) for d in doses]


def auto_select(metrics: list[DoseMetrics]) -> float:
    """Pick dose with highest η²; ties → lowest within variance."""
    if not metrics:
        raise DoseRampError("No dose metrics to select from")
    ranked = sorted(metrics, key=lambda m: (-m.eta2, m.within_var, m.dose))
    return ranked[0].dose


def metrics_table(metrics: list[DoseMetrics]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "dose": m.dose,
                "n_reps": m.n_reps,
                "within_var": m.within_var,
                "eta2": m.eta2,
                "fold_span": m.fold_span,
                "median_cv": m.median_cv,
            }
            for m in metrics
        ]
    )
