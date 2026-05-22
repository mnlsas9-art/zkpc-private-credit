"""
zkpc — Zero-Knowledge Private Credit framework simulation.

Reference implementation for the manuscript:

    Mudiganti, N. L. K. (2026). Continuous Risk Pricing of Tokenized Private
    Credit Using Zero-Knowledge Attested Factor Reporting:
    A Mortgage-Architecture Analog. Financial Innovation (submitted).

License: Apache 2.0
"""

from .simulation import (
    Params,
    Scenario,
    build_scenarios,
    simulate_factors,
    simulate_predicates,
    trust_score,
    hazard,
    stale_state,
    mtm_price,
    cvar_cross_sectional,
    compute_metrics,
    run_scenario,
    summarise,
    run_all,
)

from . import figures
from . import sensitivity

__version__ = "1.0.0"
__author__ = "Naga Lalitha Kumar Mudiganti"
__all__ = [
    "Params",
    "Scenario",
    "build_scenarios",
    "simulate_factors",
    "simulate_predicates",
    "trust_score",
    "hazard",
    "stale_state",
    "mtm_price",
    "cvar_cross_sectional",
    "compute_metrics",
    "run_scenario",
    "summarise",
    "run_all",
    "figures",
    "sensitivity",
]
