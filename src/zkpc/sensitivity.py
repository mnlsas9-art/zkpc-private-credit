"""
Sensitivity analysis across the five principal parameter levers (Section 7.3).

For each parameter, vary across a range while holding others at the baseline
value (Table 3), and report the ZK-vs-opaque effect on the headline metric
(maximum monthly price drop reduction).

Only the correlated-stress scenario is exercised — the headline scenario the
framework is designed to address.

Reference: Mudiganti (2026), Table 6.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Dict, List

import numpy as np

from .simulation import Params, build_scenarios, run_scenario, summarise


def _reduction_pct(zk: float, op: float) -> float:
    """Percentage reduction of zk relative to opaque (positive = ZK is smaller)."""
    if op == 0:
        return 0.0
    return (1.0 - zk / op) * 100.0


def _run_one(p: Params) -> Dict[str, float]:
    """Run only the correlated stress scenario with parameter set p."""
    scenarios = build_scenarios(p)
    stress = next(s for s in scenarios if s.name == "correlated_stress")
    master_rng = np.random.default_rng(p.seed)
    # Discard the first three scenarios' RNG draws to keep the stress scenario
    # using the same RNG state as in the main simulation.
    for _ in range(3):
        _ = master_rng.integers(0, 2**31)
        _ = master_rng.integers(0, 2**31)
    res = run_scenario(p, stress, master_rng)
    s = summarise(p, res, "correlated_stress")
    return {
        "max_drop_zk": s["max_monthly_drop_mean_zk"],
        "max_drop_op": s["max_monthly_drop_mean_opaque"],
        "max_drop_reduction_pct": _reduction_pct(
            s["max_monthly_drop_mean_zk"], s["max_monthly_drop_mean_opaque"]
        ),
        "std_changes_zk": s["price_change_std_mean_zk"],
        "std_changes_op": s["price_change_std_mean_opaque"],
        "std_changes_reduction_pct": _reduction_pct(
            s["price_change_std_mean_zk"], s["price_change_std_mean_opaque"]
        ),
        "peak_cvar_zk": s["peak_cvar_zk"],
        "peak_cvar_op": s["peak_cvar_opaque"],
    }


# Sensitivity sweeps from Table 6 of the manuscript.
SWEEPS = [
    ("sigma", [0.08, 0.10, 0.13, 0.16, 0.20], "Factor volatility"),
    ("gamma", [0.5, 0.8, 1.1, 1.5, 2.0], "Trust sensitivity"),
    ("n_predicates", [6, 10, 16, 20, 24], "Number of predicates"),
    ("corr_stress", [0.40, 0.55, 0.65, 0.75, 0.85], "Stress correlation"),
    ("delta", [0.5, 1.0, 1.5, 2.5, 4.0], "CVaR sensitivity"),
]


def run_sensitivity(outdir: str | Path = "output") -> List[Dict]:
    """
    Run the full sensitivity sweep and write results to outdir/sensitivity.json.

    Returns the list of result dicts (5 parameters x 5 values = 25 rows).
    """
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    baseline = Params()
    results: List[Dict] = []

    header = (f"{'Parameter':<20s} {'Value':<10s} {'MaxDrop ZK':<12s} "
              f"{'MaxDrop Op':<12s} {'Reduction%':<12s} "
              f"{'StdChg Reduc%':<14s} {'Peak CVaR ZK':<13s}")
    print(header)
    print("-" * 100)

    for param_name, values, label in SWEEPS:
        for v in values:
            p = deepcopy(baseline)
            setattr(p, param_name, v)
            r = _run_one(p)
            row = {"parameter": param_name, "label": label, "value": v, **r}
            results.append(row)
            print(
                f"{label:<20s} {v!s:<10s} "
                f"{r['max_drop_zk']:<12.4f} {r['max_drop_op']:<12.4f} "
                f"{r['max_drop_reduction_pct']:<12.2f} "
                f"{r['std_changes_reduction_pct']:<14.2f} "
                f"{r['peak_cvar_zk']:<13.4f}"
            )
        print()

    outpath = outdir / "sensitivity.json"
    outpath.write_text(json.dumps(results, indent=2))
    print(f"\nWrote {outpath}")
    return results


if __name__ == "__main__":
    run_sensitivity()
