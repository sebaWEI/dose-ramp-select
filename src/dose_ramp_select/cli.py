"""Command-line interface: CSV → metrics + two figures."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .io import (
    DoseRampError,
    load_tidy,
    resolve_control,
    sequence_constructs,
    shared_constructs,
)
from .metrics import auto_select, compute_all, metrics_table
from .plot import plot_fold_profiles, plot_variance


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="dose-ramp-select",
        description=(
            "Select an assay / transfection dose from a tidy dose-ramp table. "
            "Writes a metrics CSV plus two figures: fold profiles and "
            "within-variance + η²."
        ),
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    sub = p.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="Analyze a tidy CSV and write figures")
    run.add_argument(
        "csv",
        type=Path,
        help="Tidy CSV/TSV with columns dose, replicate, construct, value "
        "(aliases like dose_ng / rlu accepted)",
    )
    run.add_argument(
        "-o",
        "--out",
        type=Path,
        default=Path("dose_ramp_out"),
        help="Output directory (default: ./dose_ramp_out)",
    )
    run.add_argument(
        "--control",
        default="control",
        help="Control construct name for fold normalization (default: control)",
    )
    run.add_argument(
        "--exclude",
        default="5s",
        help="Comma-separated constructs to exclude from within-variance "
        "and fold-span (still shown on fold profile). Default: 5s",
    )
    run.add_argument(
        "--selected",
        type=float,
        default=None,
        help="Highlight this dose. Default: auto (max η², then min within-var)",
    )
    run.add_argument(
        "--construct-order",
        default=None,
        help="Optional comma-separated construct order for the fold-profile x-axis. "
        "Constructs not listed are appended alphabetically; missing names ignored.",
    )
    return p


def _order_constructs(shared: list[str], order: str | None, control: str) -> list[str]:
    if not order:
        # control last; others alphabetical
        others = sorted(c for c in shared if c != control)
        return others + [control]
    wanted = [x.strip() for x in order.split(",") if x.strip()]
    seen: list[str] = []
    for w in wanted:
        matches = [c for c in shared if c.lower() == w.lower()]
        if matches and matches[0] not in seen:
            seen.append(matches[0])
    for c in shared:
        if c not in seen:
            seen.append(c)
    # ensure control last if present
    if control in seen:
        seen = [c for c in seen if c != control] + [control]
    return seen


def cmd_run(args: argparse.Namespace) -> int:
    df = load_tidy(args.csv)
    shared = shared_constructs(df)
    control = resolve_control(shared, args.control)
    exclude = [x.strip() for x in str(args.exclude).split(",") if x.strip()]
    sequence = sequence_constructs(shared, control, exclude=exclude)
    constructs = _order_constructs(shared, args.construct_order, control)

    metrics = compute_all(df, constructs, control, sequence)
    selected = (
        float(args.selected) if args.selected is not None else auto_select(metrics)
    )
    if not any(abs(m.dose - selected) < 1e-9 for m in metrics):
        raise DoseRampError(
            f"--selected {selected} not in doses {[m.dose for m in metrics]}"
        )

    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)

    table = metrics_table(metrics)
    table["selected"] = table["dose"].apply(lambda d: abs(d - selected) < 1e-9)
    table_path = out / "metrics.csv"
    table.to_csv(table_path, index=False)

    fold_path = plot_fold_profiles(metrics, selected, out / "fig_fold_profiles.png")
    var_path = plot_variance(metrics, selected, out / "fig_variance_eta2.png")

    print(f"doses: {', '.join(str(m.dose) for m in metrics)}")
    print(f"constructs ({len(constructs)}): {', '.join(constructs)}")
    print(f"sequence set ({len(sequence)}): {', '.join(sequence)}")
    print(f"selected dose: {selected}")
    print(table.to_string(index=False, float_format=lambda x: f"{x:.4g}"))
    print(f"wrote {table_path}")
    print(f"wrote {fold_path} (+ .svg)")
    print(f"wrote {var_path} (+ .svg)")
    return 0


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.cmd == "run":
            code = cmd_run(args)
        else:
            parser.error(f"unknown command {args.cmd}")
            return
    except DoseRampError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(2)
    sys.exit(code)


if __name__ == "__main__":
    main()
