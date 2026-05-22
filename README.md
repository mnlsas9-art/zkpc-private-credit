# Continuous Risk Pricing of Tokenized Private Credit — Reproducibility Package

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![DOI](https://img.shields.io/badge/DOI-pending-orange.svg)](#)

This repository contains the complete reproducibility package for the paper:

> **Continuous Risk Pricing of Tokenized Private Credit Using Zero-Knowledge Attested Factor Reporting: A Mortgage-Architecture Analog**
> Naga Lalitha Kumar Mudiganti
> *Financial Innovation* (Springer / SWUFE), submitted 2026

## What this is

A controlled laboratory study of how cryptographic predicate attestation would
change the cadence of price discovery in tokenized private credit markets,
implemented as a calibrated Monte Carlo simulation. The simulation evaluates a
zero-knowledge attested reporting regime (monthly cadence) against a
conventional opaque reporting regime (quarterly cadence) across four scenarios
(base, single-factor deterioration, correlated stress, recovery), with
parameters calibrated to real benchmark data from the Cliffwater Direct Lending
Index and the VanEck BDC Income ETF.

The headline finding: under correlated stress, the zero-knowledge attested
regime produces a 33.1% reduction in the maximum monthly price drop and a
28.7% reduction in the standard deviation of monthly price changes, relative
to the opaque baseline — while preserving identical peak conditional value at
risk, identical terminal valuations, and identical default intensities at
reporting boundaries.

## Quick reproduction

```bash
git clone https://github.com/mnlsas9-art/zkpc-private-credit.git
cd zkpc-private-credit
pip install -r requirements.txt
python reproduce.py
```

That single command runs the full simulation, generates all figures, runs the
sensitivity analysis, and writes a results report. Total runtime: approximately
3 minutes on a 2023-vintage laptop with 16 GB RAM. No GPU required.

Expected outputs (all written to `output/`):

- `summary.json` — headline metrics for each of the four scenarios
- `sensitivity.json` — sensitivity sweep across five parameters
- `series.npz` — raw path-level time series (large file)
- `params.json` — frozen parameter set used in this run
- `report.txt` — human-readable summary

Expected figures (all written to `figures/`):

- `fig1_adjusted_price_stress.png` — Figure 1 in the paper
- `fig2_cvar_stress.png` — Figure 2 in the paper
- `fig3_ltv_stress.png` — Figure 3 in the paper
- `fig_supp_scenario_grid.png` — Supplementary figure (all four scenarios)

## Verifying bit-exact reproducibility

The simulation uses a fixed master random seed (`seed = 42`) and is
deterministic across re-runs on the same NumPy / Python version. To verify
bit-exact reproduction:

```bash
python -m pytest tests/test_reproducibility.py
```

The test compares the headline metrics from a fresh run against the values
saved in `tests/expected_outputs.json`, requiring exact equality (no tolerance
for floating-point drift). On the reference environment (Python 3.10, NumPy
1.26.x, SciPy 1.11.x), bit-exact reproducibility has been verified.

If the test fails, the most likely cause is a NumPy minor version mismatch
affecting RNG internals. Standard error bands reported in the paper (typically
~0.0001 on mean adjusted price) are well-calibrated to absorb such drift; the
qualitative findings hold across any reasonable Python scientific stack.

## What is in this package

```
zkpc-private-credit/
├── README.md              ← this file
├── LICENSE                ← Apache 2.0
├── CITATION.cff           ← machine-readable citation metadata
├── CHANGELOG.md           ← version history
├── requirements.txt       ← pinned dependencies
├── pyproject.toml         ← package metadata
├── reproduce.py           ← one-command full reproduction
├── .gitignore
├── src/
│   └── zkpc/
│       ├── __init__.py
│       ├── simulation.py  ← core simulation engine
│       ├── figures.py     ← figure generation
│       └── sensitivity.py ← sensitivity sweep
├── data/
│   ├── README.md          ← data provenance notes
│   └── cdli_quarterly_returns_2023Q1-2025Q4.csv
├── figures/               ← generated figures land here
├── output/                ← generated simulation outputs land here
├── tests/
│   ├── test_invariants.py        ← framework invariants
│   ├── test_reproducibility.py   ← bit-exact reproduction
│   └── expected_outputs.json     ← reference values
└── docs/
    ├── parameter_reference.md    ← Table 3 in extended form
    └── predicate_taxonomy.md     ← Table 2 in extended form
```

## Computational requirements

- Python 3.10 or later
- NumPy ≥ 1.24
- SciPy ≥ 1.10
- Matplotlib ≥ 3.7
- pytest (for tests only)
- Approximately 16 GB RAM (10,000-path simulation across four scenarios)
- Approximately 3 minutes total runtime on commodity hardware

Bit-exact reproducibility (matching `tests/expected_outputs.json` to 10 decimal places) was verified on Python 3.10 with NumPy 1.26.x and SciPy 1.11.x. Newer versions of NumPy and SciPy produce qualitatively identical findings — the headline 33% / 29% cliff and standard-deviation reductions are robust to NumPy minor-version RNG drift, as confirmed by the sensitivity analysis in Section 7.3 of the paper.

## Citation

If you use this code or its outputs in your own work, please cite both the
paper and the archived release:

```
@article{Mudiganti2026ContinuousRiskPricing,
  title   = {Continuous Risk Pricing of Tokenized Private Credit Using
             Zero-Knowledge Attested Factor Reporting: A Mortgage-Architecture
             Analog},
  author  = {Mudiganti, Naga Lalitha Kumar},
  journal = {Financial Innovation},
  year    = {2026},
  note    = {Submitted}
}
```

A machine-readable citation is provided in `CITATION.cff`.

## License

Apache License 2.0. See `LICENSE` for full terms.

You are free to use, modify, and distribute this code for any purpose,
including commercial use, with attribution. The patent grant clause of
Apache 2.0 explicitly permits use of any patentable subject matter contained
herein.

## Contact

Naga Lalitha Kumar Mudiganti
ORCID: 0009-0000-5907-3704

For questions, bug reports, or contributions, please open an issue on the
GitHub repository.

## Acknowledgments

The Cliffwater Direct Lending Index quarterly return data used for calibration
was assembled from Cliffwater LLC's publicly distributed press releases. BIZD
ETF reference statistics were sourced from Seeking Alpha and PortfoliosLab as
cited in Section 5 of the paper. ICE BofA US High Yield OAS reference data is
available from the Federal Reserve Economic Data system. RWA.xyz tokenized
credit market statistics were sourced from the RWA.xyz public dashboard. The
author acknowledges these public data sources with thanks.
