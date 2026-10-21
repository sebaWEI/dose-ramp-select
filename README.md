# dose-ramp-select

**CSV → two figures + a metrics table** to justify which transfection / assay dose to keep.

Built for luciferase (FLUC) dose ramps, but any positive scalar readout works.

| Output | What it answers |
| --- | --- |
| `fig_fold_profiles.png` | Relative activity (fold vs control) across constructs — is the dynamic range usable? |
| `fig_variance_eta2.png` | **Left:** within-sequence replicate noise (lower better). **Right:** η² = fraction of log-readout variance explained by construct identity (higher better). |
| `metrics.csv` | Numbers behind the figures |

Default selection rule: **highest η²**, ties broken by **lowest within-sequence variance**. Override with `--selected`.

---

## Install

```bash
git clone https://github.com/sebaWEI/dose-ramp-select.git
cd dose-ramp-select
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
```

## Quick start

```bash
dose-ramp-select run examples/example_tidy_rlu.csv -o out --selected 20
```

Or without installing:

```bash
python -m dose_ramp_select run examples/example_tidy_rlu.csv -o out
```

Open `out/fig_fold_profiles.png` and `out/fig_variance_eta2.png`.

---

## Input format

One **tidy** table (CSV or TSV). Required fields (aliases accepted):

| Field | Aliases | Meaning |
| --- | --- | --- |
| `dose` | `dose_ng`, `concentration`, `conc`, `ng` | Dose level (numeric) |
| `replicate` | `rep`, `well`, `repeat` | Biological / technical replicate id |
| `construct` | `sample`, `sequence`, `variant`, `name` | Sequence / condition label |
| `value` | `rlu`, `fluc`, `signal`, `luminescence`, `readout` | Positive scalar readout |

Example:

```csv
dose_ng,replicate,construct,rlu
5,1,3l-1,1866
5,1,3l-2,1340
5,1,control,99
…
20,1,3l-1,33779
20,1,control,2225
```

**Rules the tool enforces**

- ≥2 replicates per dose  
- Control present at every dose (name configurable, default `control`)  
- Only constructs shared across **all** doses are compared  
- Values ≥ 0; control must be > 0 for fold normalization  

---

## Method (short)

1. **Fold profile** — each replicate ÷ same-plate control; plot mean ± SD per construct.  
2. **Within variance** — mean of per-construct variances on \(\mathrm{log}_{10}(\mathrm{value})\) for non-control sequences (default also excludes `5s`).  
3. **η²** — one-way ANOVA style decomposition on \(\mathrm{log}_{10}(\mathrm{value})\) across all shared constructs:  
   \(\eta^2 = SS_{\mathrm{between}} / SS_{\mathrm{total}}\).

Interpretation for dose choice:

- Want **low** left bar (tight replicates)  
- Want **high** right bar (sequence drives most variance)  
- Fold profile should still show a clear high–low span  

Dose is **not** assumed monotonic with noise — pick the measurement sweet spot.

---

## CLI options

```text
dose-ramp-select run DATA.csv [options]

  -o, --out DIR           Output directory (default: dose_ramp_out)
  --control NAME          Control construct (default: control)
  --exclude A,B           Extra constructs excluded from within-var / fold-span
                          (default: 5s). Still drawn on the fold profile.
  --selected DOSE         Highlight this dose (default: auto)
  --construct-order A,B   Optional x-axis order for the fold figure
```

---

## Python API

```python
from pathlib import Path
from dose_ramp_select.io import load_tidy, shared_constructs, resolve_control, sequence_constructs
from dose_ramp_select.metrics import compute_all, auto_select, metrics_table
from dose_ramp_select.plot import plot_fold_profiles, plot_variance

df = load_tidy("examples/example_tidy_rlu.csv")
shared = shared_constructs(df)
control = resolve_control(shared, "control")
sequence = sequence_constructs(shared, control, exclude=["5s"])
metrics = compute_all(df, shared, control, sequence)
selected = auto_select(metrics)

out = Path("out")
metrics_table(metrics).to_csv(out / "metrics.csv", index=False)
plot_fold_profiles(metrics, selected, out / "fig_fold_profiles.png")
plot_variance(metrics, selected, out / "fig_variance_eta2.png")
```

---

## Develop

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT. Example data from iGEM PekingHSC 2026 LETM1 FLUC dose-ramp experiments.
