"""Load and validate tidy dose-ramp tables."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

REQUIRED = ("dose", "replicate", "construct", "value")

# Accept common aliases so users need not rename columns.
ALIASES: dict[str, tuple[str, ...]] = {
    "dose": ("dose", "dose_ng", "dose_ug", "concentration", "conc", "ng"),
    "replicate": ("replicate", "rep", "well", "n", "repeat"),
    "construct": ("construct", "sample", "sequence", "variant", "name", "condition"),
    "value": ("value", "rlu", "fluc", "signal", "luminescence", "readout"),
}


class DoseRampError(ValueError):
    """User-facing validation error."""


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    lower = {c: str(c).strip().lower() for c in df.columns}
    df = df.rename(columns=lower)
    mapping: dict[str, str] = {}
    for canonical, aliases in ALIASES.items():
        found = [a for a in aliases if a in df.columns]
        if not found:
            raise DoseRampError(
                f"Missing column for '{canonical}'. "
                f"Accepted names: {', '.join(aliases)}. "
                f"Got: {list(df.columns)}"
            )
        mapping[found[0]] = canonical
    out = df.rename(columns=mapping)
    # keep first hit only for each canonical
    cols = list(REQUIRED)
    extra = [c for c in out.columns if c not in cols]
    return out[cols + extra]


def load_tidy(path: str | Path) -> pd.DataFrame:
    """Load a tidy CSV/TSV with dose × replicate × construct × value."""
    path = Path(path)
    if not path.is_file():
        raise DoseRampError(f"File not found: {path}")

    sep = "\t" if path.suffix.lower() in {".tsv", ".txt"} else ","
    try:
        raw = pd.read_csv(path, sep=sep)
    except Exception as exc:  # noqa: BLE001
        raise DoseRampError(f"Could not read {path}: {exc}") from exc

    if raw.empty:
        raise DoseRampError(f"{path} is empty")

    df = _normalize_columns(raw)
    df["construct"] = df["construct"].astype(str).str.strip()
    df["replicate"] = pd.to_numeric(df["replicate"], errors="coerce")
    df["dose"] = pd.to_numeric(df["dose"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    if df["dose"].isna().any():
        raise DoseRampError("Non-numeric dose values found")
    if df["replicate"].isna().any():
        raise DoseRampError("Non-numeric replicate values found")
    if df["value"].isna().any():
        raise DoseRampError("Non-numeric / missing readout values found")
    if (df["value"] < 0).any():
        raise DoseRampError("Negative readout values are not allowed")

    # drop exact duplicate keys (keep first)
    df = df.drop_duplicates(subset=["dose", "replicate", "construct"], keep="first")
    df = df.sort_values(["dose", "replicate", "construct"]).reset_index(drop=True)
    return df


def shared_constructs(df: pd.DataFrame) -> list[str]:
    """Constructs present at every dose (intersection)."""
    sets = [set(g["construct"].unique()) for _, g in df.groupby("dose")]
    if not sets:
        raise DoseRampError("No doses found")
    shared = set.intersection(*sets)
    if not shared:
        raise DoseRampError("No constructs shared across all doses")
    return sorted(shared)


def resolve_control(constructs: list[str], control: str) -> str:
    """Match control name case-insensitively."""
    wanted = control.strip().lower()
    for c in constructs:
        if c.lower() == wanted:
            return c
    raise DoseRampError(
        f"Control '{control}' not found among constructs: {constructs}"
    )


def sequence_constructs(
    constructs: list[str],
    control: str,
    exclude: list[str] | None = None,
) -> list[str]:
    """Constructs used for within-variance (exclude control + optional refs)."""
    ban = {control.lower()}
    if exclude:
        ban.update(x.strip().lower() for x in exclude if x.strip())
    seq = [c for c in constructs if c.lower() not in ban]
    if len(seq) < 2:
        raise DoseRampError(
            "Need ≥2 non-control constructs for sequence variance metrics"
        )
    return seq
