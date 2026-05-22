# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] — 2026-05-22

### Added

- Initial release accompanying paper submission to *Financial Innovation*.
- Core simulation engine (`src/zkpc/simulation.py`).
- Figure generation (`src/zkpc/figures.py`).
- Sensitivity analysis (`src/zkpc/sensitivity.py`).
- One-command reproduction script (`reproduce.py`).
- Test suite covering framework invariants and bit-exact reproducibility.
- CDLI quarterly returns calibration data (2023Q1–2025Q4).
- Parameter reference documentation.
- Predicate taxonomy documentation.
- Apache 2.0 license.

### Verified

- Bit-exact reproducibility across re-runs with `seed=42` on the reference
  environment (Python 3.10, NumPy 1.26.x, SciPy 1.11.x).
- Framework invariants: trust score bounded in [0,1]; price monotone in trust
  score; cliff-effect ordering between regimes under deterministic stress.

### Reference values (seed=42, correlated stress scenario)

- Maximum monthly price drop, ZK regime: 0.028888
- Maximum monthly price drop, opaque regime: 0.043220
- Cliff reduction: 33.16%
- Standard deviation reduction: 28.62%
- Peak CVaR_95: 0.227418 (ZK) vs 0.226753 (opaque)
