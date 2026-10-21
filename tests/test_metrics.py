from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from dose_ramp_select.io import (
    DoseRampError,
    load_tidy,
    resolve_control,
    sequence_constructs,
    shared_constructs,
)
from dose_ramp_select.metrics import auto_select, compute_all, metrics_table

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "example_tidy_rlu.csv"


def test_example_loads_and_selects_20():
    df = load_tidy(EXAMPLE)
    shared = shared_constructs(df)
    control = resolve_control(shared, "control")
    sequence = sequence_constructs(shared, control, exclude=["5s"])
    # use intersection order with control last
    constructs = sorted(c for c in shared if c != control) + [control]
    metrics = compute_all(df, constructs, control, sequence)
    assert auto_select(metrics) == 20.0
    table = metrics_table(metrics)
    row20 = table.loc[table["dose"] == 20].iloc[0]
    assert row20["eta2"] > 0.9
    assert row20["within_var"] == table["within_var"].min()


def test_missing_control_errors():
    df = load_tidy(EXAMPLE)
    df = df[df["construct"] != "control"]
    shared = shared_constructs(df)
    with pytest.raises(DoseRampError, match="Control"):
        resolve_control(shared, "control")


def test_aliases():
    raw = pd.DataFrame(
        {
            "concentration": [1, 1, 1, 1, 2, 2, 2, 2],
            "rep": [1, 1, 2, 2, 1, 1, 2, 2],
            "sample": ["A", "ctrl", "A", "ctrl", "A", "ctrl", "A", "ctrl"],
            "signal": [10, 5, 12, 6, 40, 8, 36, 9],
        }
    )
    path = Path("/tmp/dose_ramp_alias.csv")
    raw.to_csv(path, index=False)
    df = load_tidy(path)
    assert list(df.columns[:4]) == ["dose", "replicate", "construct", "value"]
