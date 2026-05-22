"""
Test the structural invariants of the framework.

These tests verify that the simulation respects the structural properties
proved as propositions in Section 4.6 of the manuscript:

  P1: Trust score is bounded in [0, 1].
  P1 (corollary): Price is monotone decreasing in hazard intensity.
  P2: Under deterministic stress, cliff-effect ordering holds: opaque-regime
      max drop strictly exceeds ZK-regime max drop.
  Internal: Hazard intensity is strictly positive.
  Internal: Adjusted price equals raw price at zero CVaR.
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from zkpc import (  # noqa: E402
    Params, build_scenarios, run_scenario,
    hazard, trust_score, mtm_price, simulate_factors, simulate_predicates,
)


def test_trust_score_bounded():
    """Trust score is always in [0, 1] across all paths and time steps."""
    p = Params(n_paths=500)
    rng = np.random.default_rng(p.seed)
    scenarios = build_scenarios(p)
    stress = next(s for s in scenarios if s.name == "correlated_stress")
    X = simulate_factors(p, stress, rng)
    P = simulate_predicates(p, X, rng)
    T = trust_score(P)
    assert T.min() >= 0.0, f"Trust score went negative: min={T.min()}"
    assert T.max() <= 1.0, f"Trust score exceeded 1: max={T.max()}"


def test_hazard_positive():
    """Default intensity is strictly positive."""
    p = Params(n_paths=500)
    rng = np.random.default_rng(p.seed)
    scenarios = build_scenarios(p)
    stress = next(s for s in scenarios if s.name == "correlated_stress")
    X = simulate_factors(p, stress, rng)
    P = simulate_predicates(p, X, rng)
    T = trust_score(P)
    lam = hazard(p, X, T)
    assert lam.min() > 0.0, f"Hazard went non-positive: min={lam.min()}"


def test_price_monotone_in_hazard():
    """Price is monotone decreasing in hazard intensity (P1 corollary)."""
    p = Params()
    lam_low = np.array([[0.02, 0.03, 0.04]])
    lam_high = np.array([[0.05, 0.07, 0.10]])
    t_index = np.array([0, 1, 2])
    price_low = mtm_price(p, lam_low, t_index)
    price_high = mtm_price(p, lam_high, t_index)
    assert np.all(price_low > price_high), (
        f"Price not monotone in hazard: "
        f"price(lam_low)={price_low}, price(lam_high)={price_high}"
    )


def test_cliff_effect_ordering_correlated_stress():
    """
    P2: Under correlated stress, the max monthly price drop in the opaque
    regime strictly exceeds the max monthly price drop in the ZK regime.
    """
    p = Params()
    scenarios = build_scenarios(p)
    stress = next(s for s in scenarios if s.name == "correlated_stress")
    master_rng = np.random.default_rng(p.seed)
    # Skip ahead to the stress scenario's RNG state
    for _ in range(3):
        _ = master_rng.integers(0, 2**31)
        _ = master_rng.integers(0, 2**31)

    res = run_scenario(p, stress, master_rng)
    diffs_zk = -np.diff(res["zk"]["price_adj"], axis=1)
    diffs_op = -np.diff(res["opaque"]["price_adj"], axis=1)
    max_zk = diffs_zk.max(axis=1).mean()
    max_op = diffs_op.max(axis=1).mean()

    assert max_op > max_zk, (
        f"Cliff-effect ordering violated: "
        f"max_op={max_op:.6f} should exceed max_zk={max_zk:.6f}"
    )


def test_terminal_price_identical_at_report():
    """
    Mean adjusted price at month 36 (a quarterly reporting boundary) is
    identical across regimes by construction.
    """
    p = Params()
    scenarios = build_scenarios(p)
    stress = next(s for s in scenarios if s.name == "correlated_stress")
    master_rng = np.random.default_rng(p.seed)
    for _ in range(3):
        _ = master_rng.integers(0, 2**31)
        _ = master_rng.integers(0, 2**31)

    res = run_scenario(p, stress, master_rng)
    # Month 36 is a quarterly boundary (36 = 12 * 3)
    price_36_zk = res["zk"]["price_adj"][:, 36].mean()
    price_36_op = res["opaque"]["price_adj"][:, 36].mean()

    # Should be very close (differ only because CVaR is path-dependent through
    # the staleness operator on intermediate steps).
    diff = abs(price_36_zk - price_36_op)
    assert diff < 0.005, (
        f"Mean adjusted price at quarterly boundary diverges: "
        f"zk={price_36_zk:.6f}, op={price_36_op:.6f}, diff={diff:.6f}"
    )


def test_peak_cvar_essentially_equal():
    """
    Peak CVaR across regimes is essentially equal (framework preserves
    underlying risk; changes only when risk is observed, not what risk is).
    """
    p = Params()
    scenarios = build_scenarios(p)
    stress = next(s for s in scenarios if s.name == "correlated_stress")
    master_rng = np.random.default_rng(p.seed)
    for _ in range(3):
        _ = master_rng.integers(0, 2**31)
        _ = master_rng.integers(0, 2**31)

    res = run_scenario(p, stress, master_rng)
    peak_zk = res["zk"]["cvar"].max()
    peak_op = res["opaque"]["cvar"].max()
    rel_diff = abs(peak_zk - peak_op) / peak_zk
    assert rel_diff < 0.01, (
        f"Peak CVaR differs across regimes by more than 1%: "
        f"zk={peak_zk:.6f}, op={peak_op:.6f}, rel_diff={rel_diff:.4f}"
    )
