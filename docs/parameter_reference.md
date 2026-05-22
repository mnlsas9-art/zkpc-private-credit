# Parameter Reference

This document is the extended companion to Table 3 of the manuscript. It
specifies each parameter's role in the model, its baseline value, its
calibration source, and its behavior under sensitivity analysis.

## Quick reference

| Symbol | Description | Baseline | Source |
|---|---|---|---|
| `c` | Loan coupon (annualized) | 10.0% | CDLI income yield |
| `r` | Risk-free rate | 4.5% | 5-year US Treasury, mid-2025 |
| `lambda0` | Baseline default intensity | 3.5% | CDLI realized loss + non-accrual |
| `R` | Recovery rate | 65% | Standard middle-market senior secured |
| `F` | Number of credit factors | 6 | Design choice |
| `sigma` | Per-factor annualized volatility | 13.0% | BIZD 21% w/ sentiment-overlay adjustment |
| `beta` | Factor sensitivity vector | (0.5, 0.5, 0.5, 0.3, 0.3, 0.2) | Design choice (declining importance) |
| `corr_normal` | Factor correlation, normal regime | 0.25 | Pre-COVID cross-asset correlations |
| `corr_stress` | Factor correlation, stress regime | 0.65 | COVID 2020 cross-asset correlation peaks |
| `N` (`n_predicates`) | Number of predicates | 16 | Refined taxonomy, Section 4.1 |
| `gamma` | Trust sensitivity in hazard | 1.1 | Design choice |
| `delta` | CVaR sensitivity in adjusted price | 1.5 | Design choice |
| `base_ltv` | Base loan-to-value cap | 70% | Standard middle-market origination |
| `eta` | Trust exponent in LTV | 0.5 | Design choice |
| `kappa` | CVaR sensitivity in LTV | 0.9 | Design choice |
| `maturity` | Loan maturity | 5 years | Standard middle-market direct lending |
| `dt` | Simulation time step | 1 month (1/12) | ZK regime cadence |
| `n_paths` | Monte Carlo paths | 10,000 | SE target ≤ 0.01% |
| `seed` | Master random seed | 42 | Reproducibility |

## Parameter detail

### Empirically anchored parameters

**`c` — Loan coupon.** Set to 10% per annum. The Cliffwater Direct Lending
Index reports an income yield of 11.10% per annum stable across all 12
quarters of the 2023Q1–2025Q4 sample. 10% is set conservatively below this
to allow for adverse changes during the simulation horizon.

**`r` — Risk-free rate.** Set to 4.5% per annum based on the 5-year US
Treasury yield around mid-2025. The framework's findings are not sensitive
to this parameter within reasonable ranges.

**`lambda0` — Baseline default intensity.** Set to 3.5% per annum. Calibrated
against CDLI realized loss rate (1.01% per annum long-run average) and
non-accrual rate (2.13% long-run average), with the higher level reflecting
the broader risk distribution being modeled.

**`R` — Recovery rate.** Set to 65%. Standard assumption for middle-market
senior secured direct lending; consistent with industry data on private credit
recovery experience and with the Lando (2004) survey.

**`sigma` — Per-factor annualized volatility.** Set to 13.0%. Calibrated to
target a balance between the smoothed CDLI vol (0.79% annualized) at the
opaque regime and the equity-overlay BIZD vol (21.01% annualized) at the
ZK regime. The 13% level reflects the "fundamental" factor volatility after
stripping out equity-market sentiment that drives BIZD's higher observed vol.

**`corr_stress` — Stress-period factor correlation.** Set to 0.65. Calibrated
to the COVID-period cross-asset correlation pattern, when leveraged loan
indices, BDC equity prices, high-yield credit spreads, and broader equity
indices all moved approximately together at correlations in the 0.65 to 0.75
range. Sensitivity analysis (Table 6) shows the headline finding is robust
across the 0.40 to 0.85 range.

### Framework-design parameters

**`F` — Number of credit factors.** Set to 6. Provides sufficient
dimensionality for a meaningful factor structure while keeping simulation
runtime tractable.

**`beta` — Factor sensitivity vector.** Declining magnitudes (0.5, 0.5, 0.5,
0.3, 0.3, 0.2) reflect three high-impact factors and three lower-impact
factors. The factor structure is symmetric enough not to require strong prior
beliefs about which specific factors dominate.

**`N` — Number of predicates.** Set to 16. Reflects the refined predicate
taxonomy specified in Section 4.1 of the manuscript, including PIK-aware
predicates (4, 5, 6, 8, 9) and concealment-aware predicates (12, 13, 14, 15).
This is the parameter with the strongest impact on cliff reduction: at N=6,
the cliff reduction falls to 23.0%; at N=24, it rises to 37.9% (Table 6).

**`gamma` — Trust sensitivity in hazard.** Set to 1.1. Controls how strongly
verified compliance reduces the hazard rate. Higher values produce stronger
coupling between trust and pricing; the framework's qualitative findings are
robust across the 0.5 to 2.0 range (Table 6).

**`delta` — CVaR sensitivity in adjusted price.** Set to 1.5. Controls the
exponential discount applied to the mark-to-market price as a function of
the cross-sectional CVaR. The headline cliff reduction peaks at `delta=1.5`
and decreases at higher values (where both regimes get larger absolute drops
but the ratio compresses).

**`base_ltv`, `eta`, `kappa` — LTV functional parameters.** Set to 70%, 0.5,
and 0.9 respectively. The base LTV reflects standard middle-market origination
levels; the exponents control the relative weight of trust and CVaR in the
dynamic haircut.

### Simulation parameters

**`n_paths` — Monte Carlo paths.** Set to 10,000. Produces Monte Carlo standard
errors of order 0.0001 on mean adjusted price, well below the magnitude of the
regime effects under investigation.

**`seed` — Master random seed.** Set to 42. Ensures bit-exact reproducibility
across re-runs on the reference environment (Python 3.10, NumPy 1.26.x).

## Modifying parameters

To run the simulation with non-baseline parameters, edit a copy of `Params()`:

```python
from zkpc import Params, run_all

# Override factor volatility
p = Params(sigma=0.10, n_predicates=10)
summaries = run_all(p=p, outdir="custom_output")
```

The sensitivity sweep in `zkpc.sensitivity.run_sensitivity()` exercises this
pattern across the five principal levers identified in Table 6.
