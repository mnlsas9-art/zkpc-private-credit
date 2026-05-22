"""
Bit-exact reproducibility test.

Runs the simulation fresh and compares the headline metrics against
reference values in expected_outputs.json. The test requires exact equality
(no floating-point tolerance) on the reference environment.

If the test fails, the most likely cause is a NumPy minor-version RNG
internals change. The qualitative findings hold across any reasonable
Python scientific stack; the Monte Carlo standard errors reported in
the paper (~0.0001 on mean adjusted price) absorb such drift.
"""

import json
import sys
from pathlib import Path

import pytest

# Insert local src/ on path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from zkpc import Params, run_all  # noqa: E402


METRICS_TO_CHECK = [
    "price_adj_m36_mean_zk",
    "price_adj_m36_mean_opaque",
    "peak_cvar_zk",
    "peak_cvar_opaque",
    "max_monthly_drop_mean_zk",
    "max_monthly_drop_mean_opaque",
    "price_change_std_mean_zk",
    "price_change_std_mean_opaque",
    "ltv_m36_mean_zk",
    "ltv_m36_mean_opaque",
]


@pytest.fixture(scope="module")
def expected():
    """Load the reference expected outputs."""
    path = Path(__file__).parent / "expected_outputs.json"
    return json.loads(path.read_text())


@pytest.fixture(scope="module")
def fresh(tmp_path_factory):
    """Run the simulation fresh and return the summary list."""
    outdir = tmp_path_factory.mktemp("simout")
    summaries = run_all(p=Params(), outdir=outdir)
    return summaries


@pytest.mark.parametrize("scenario_idx", [0, 1, 2, 3])
def test_bit_exact_reproducibility(expected, fresh, scenario_idx):
    """Fresh run must match saved reference values bit-for-bit."""
    exp = expected[scenario_idx]
    new = fresh[scenario_idx]
    assert exp["scenario"] == new["scenario"], (
        f"Scenario name mismatch at index {scenario_idx}"
    )
    for metric in METRICS_TO_CHECK:
        assert exp[metric] == new[metric], (
            f"Bit-exact failure in {new['scenario']}.{metric}: "
            f"expected={exp[metric]:.10f}, got={new[metric]:.10f}, "
            f"diff={abs(exp[metric] - new[metric]):.2e}"
        )


def test_headline_finding(fresh):
    """The headline cliff-reduction finding from the manuscript."""
    stress = next(s for s in fresh if s["scenario"] == "correlated_stress")
    max_zk = stress["max_monthly_drop_mean_zk"]
    max_op = stress["max_monthly_drop_mean_opaque"]
    reduction_pct = (1 - max_zk / max_op) * 100

    # Manuscript reports approximately 33 percent.
    assert 32.0 < reduction_pct < 34.0, (
        f"Headline cliff reduction is {reduction_pct:.2f}%; "
        f"manuscript reports approximately 33 percent"
    )


def test_std_reduction(fresh):
    """The secondary headline: standard deviation reduction."""
    stress = next(s for s in fresh if s["scenario"] == "correlated_stress")
    std_zk = stress["price_change_std_mean_zk"]
    std_op = stress["price_change_std_mean_opaque"]
    reduction_pct = (1 - std_zk / std_op) * 100

    # Manuscript reports approximately 29 percent.
    assert 27.5 < reduction_pct < 30.0, (
        f"Std reduction is {reduction_pct:.2f}%; "
        f"manuscript reports approximately 29 percent"
    )
