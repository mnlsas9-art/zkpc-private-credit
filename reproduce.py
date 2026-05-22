"""
One-command full reproduction of the manuscript results.

Runs the simulation across the four scenarios, generates all four figures,
runs the sensitivity sweep, and writes a human-readable report summarising
the headline findings.

Usage:
    python reproduce.py

Total runtime: approximately 3 minutes on commodity hardware.

Outputs written:
    output/params.json         — frozen parameter set
    output/summary.json        — per-scenario summary metrics
    output/sensitivity.json    — sensitivity sweep results (Table 6)
    output/series.npz          — raw mean time series across paths
    output/report.txt          — human-readable summary
    figures/fig1_adjusted_price_stress.png
    figures/fig2_cvar_stress.png
    figures/fig3_ltv_stress.png
    figures/fig_supp_scenario_grid.png

Random seed 42 is used throughout. On the reference environment
(Python 3.10, NumPy 1.26.x), bit-exact reproducibility has been verified.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

# Insert local src/ on path so we can run without installing.
sys.path.insert(0, str(Path(__file__).parent / "src"))

from zkpc import run_all, figures, sensitivity  # noqa: E402


def write_report(summary_list, sensitivity_results, outpath: Path) -> None:
    """Write a human-readable summary of the headline findings."""
    lines = []
    lines.append("=" * 78)
    lines.append("REPRODUCTION REPORT")
    lines.append("Continuous Risk Pricing of Tokenized Private Credit")
    lines.append("Using Zero-Knowledge Attested Factor Reporting")
    lines.append("=" * 78)
    lines.append("")
    lines.append("Reference: Mudiganti (2026), Financial Innovation, submitted.")
    lines.append("Random seed: 42")
    lines.append("Path count: 10,000")
    lines.append("Horizon: 5 years, monthly time stepping")
    lines.append("")
    lines.append("-" * 78)
    lines.append("HEADLINE NUMBERS — CORRELATED STRESS SCENARIO (Table 4)")
    lines.append("-" * 78)
    lines.append("")

    stress = next(s for s in summary_list if s["scenario"] == "correlated_stress")
    max_zk = stress["max_monthly_drop_mean_zk"]
    max_op = stress["max_monthly_drop_mean_opaque"]
    cliff_red = (1 - max_zk / max_op) * 100
    std_zk = stress["price_change_std_mean_zk"]
    std_op = stress["price_change_std_mean_opaque"]
    std_red = (1 - std_zk / std_op) * 100

    lines.append(f"  Max monthly price drop, ZK:        {max_zk:.6f}")
    lines.append(f"  Max monthly price drop, opaque:    {max_op:.6f}")
    lines.append(f"  Cliff reduction:                   {cliff_red:.2f}%")
    lines.append("")
    lines.append(f"  Std of monthly changes, ZK:        {std_zk:.6f}")
    lines.append(f"  Std of monthly changes, opaque:    {std_op:.6f}")
    lines.append(f"  Standard deviation reduction:      {std_red:.2f}%")
    lines.append("")
    lines.append(f"  Peak CVaR_95, ZK:                  {stress['peak_cvar_zk']:.6f}")
    lines.append(f"  Peak CVaR_95, opaque:              {stress['peak_cvar_opaque']:.6f}")
    lines.append(f"  (Essentially identical: framework preserves underlying risk)")
    lines.append("")
    lines.append(f"  Mean adjusted price at month 36, ZK:     {stress['price_adj_m36_mean_zk']:.6f}")
    lines.append(f"  Mean adjusted price at month 36, opaque: {stress['price_adj_m36_mean_opaque']:.6f}")
    lines.append(f"  (Identical at quarterly reporting boundaries)")
    lines.append("")

    lines.append("-" * 78)
    lines.append("CROSS-SCENARIO COMPARISON (Table 5)")
    lines.append("-" * 78)
    lines.append("")
    lines.append(f"  {'Scenario':<32s} {'Max drop reduction':<20s} {'Std reduction':<15s}")
    for s in summary_list:
        max_red = (1 - s["max_monthly_drop_mean_zk"] / s["max_monthly_drop_mean_opaque"]) * 100
        sd_red = (1 - s["price_change_std_mean_zk"] / s["price_change_std_mean_opaque"]) * 100
        lines.append(f"  {s['scenario']:<32s} {max_red:>15.2f}%    {sd_red:>10.2f}%")
    lines.append("")

    lines.append("-" * 78)
    lines.append("SENSITIVITY ANALYSIS (Table 6)")
    lines.append("-" * 78)
    lines.append("")
    lines.append(f"  {'Parameter':<25s} {'Value':<10s} {'Cliff reduction':<15s}")
    last_param = None
    for r in sensitivity_results:
        if r["parameter"] != last_param:
            if last_param is not None:
                lines.append("")
            last_param = r["parameter"]
        lines.append(f"  {r['label']:<25s} {r['value']!s:<10s} {r['max_drop_reduction_pct']:>10.2f}%")
    lines.append("")

    lines.append("-" * 78)
    lines.append("EXPECTED REFERENCE VALUES")
    lines.append("-" * 78)
    lines.append("")
    lines.append("Bit-exact match on the reference environment (Python 3.10, NumPy 1.26):")
    lines.append("  Max monthly drop, ZK:        0.028888")
    lines.append("  Max monthly drop, opaque:    0.043220")
    lines.append("  Cliff reduction:             33.16%")
    lines.append("  Std reduction:               28.62%")
    lines.append("  Peak CVaR, ZK:               0.227418")
    lines.append("  Peak CVaR, opaque:           0.226753")
    lines.append("")
    lines.append("If your numbers differ in the 4th decimal place or later, this is")
    lines.append("usually a NumPy minor-version RNG drift. Qualitative findings hold.")
    lines.append("")
    lines.append("=" * 78)

    outpath.write_text("\n".join(lines))


def main():
    """Top-level reproduction driver."""
    pkg_root = Path(__file__).parent.resolve()
    outdir = pkg_root / "output"
    figdir = pkg_root / "figures"
    outdir.mkdir(exist_ok=True)
    figdir.mkdir(exist_ok=True)

    print()
    print("=" * 78)
    print("STEP 1 of 3: Running simulation (4 scenarios x 10,000 paths)")
    print("=" * 78)
    t0 = time.time()
    summaries = run_all(outdir=outdir)
    t1 = time.time()
    print(f"  Elapsed: {t1 - t0:.1f}s")
    print()

    print("=" * 78)
    print("STEP 2 of 3: Generating figures")
    print("=" * 78)
    t0 = time.time()
    figures.make_all(simdir=outdir, outdir=figdir)
    t1 = time.time()
    print(f"  Elapsed: {t1 - t0:.1f}s")
    print()

    print("=" * 78)
    print("STEP 3 of 3: Running sensitivity sweep (5 params x 5 values = 25 runs)")
    print("=" * 78)
    t0 = time.time()
    sens_results = sensitivity.run_sensitivity(outdir=outdir)
    t1 = time.time()
    print(f"  Elapsed: {t1 - t0:.1f}s")
    print()

    # Write human-readable report
    report_path = outdir / "report.txt"
    write_report(summaries, sens_results, report_path)
    print(f"Wrote {report_path}")
    print()
    print("=" * 78)
    print("REPRODUCTION COMPLETE.")
    print("Read output/report.txt for the headline numbers and comparison tables.")
    print("=" * 78)


if __name__ == "__main__":
    main()
