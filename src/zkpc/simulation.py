"""
Continuous Risk Pricing of Tokenized Private Credit
using Zero-Knowledge Attested Factor Reporting

Core simulation engine implementing the framework specified in Section 4 of
the manuscript and exercising it across the four scenarios specified in
Section 6.1.

The simulation compares two information regimes operating on the same
underlying credit paths:

  * The zero-knowledge attested regime updates observed factors and trust
    score at monthly cadence, replicating cryptographic predicate attestation.
  * The opaque baseline regime updates observed factors and trust score
    only at quarterly cadence, replicating conventional private credit
    reporting.

Both regimes operate on identical underlying paths, so any difference in
outcomes is attributable to the cadence of reporting alone.

Reference: Mudiganti, N. L. K. (2026). Continuous Risk Pricing of Tokenized
Private Credit Using Zero-Knowledge Attested Factor Reporting:
A Mortgage-Architecture Analog. Financial Innovation (submitted).

Author: N. L. K. Mudiganti
License: Apache 2.0
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Callable, Dict, List

import numpy as np


# ============================================================================
# Parameters
# ============================================================================

@dataclass
class Params:
    """
    Baseline parameter set for the laboratory validation simulation.

    Values match Table 3 of the manuscript. Calibration sources are
    documented in Section 5; sensitivity analysis across the principal
    parameters is reported in Section 7.3.
    """

    # --- Loan and market parameters ---
    coupon: float = 0.10               # c, loan coupon (annualized).
                                       # Calibrated to CDLI income yield.
    risk_free: float = 0.045           # r, risk-free rate.
                                       # 5-year US Treasury, mid-2025.
    lambda0: float = 0.035             # baseline default intensity.
                                       # Brackets CDLI realized loss + non-accrual.
    recovery: float = 0.65             # R, recovery rate.
                                       # Standard middle-market senior secured.
    maturity: float = 5.0              # T_m, loan maturity (years).
    dt: float = 1.0 / 12.0             # simulation time step (monthly).

    # --- Factor process parameters ---
    n_factors: int = 6                 # F, number of credit factors.
    sigma: float = 0.13                # per-factor annualised volatility.
                                       # Calibrated so opaque-regime simulated
                                       # vol approximates CDLI's observed 0.79%
                                       # annualized vol (2023Q1-2025Q4) and
                                       # stress regime approaches BIZD-like
                                       # magnitudes (BIZD 21% annualized vol).
    beta: tuple = (0.5, 0.5, 0.5, 0.3, 0.3, 0.2)  # factor sensitivities
    corr_normal: float = 0.25          # factor correlation, normal regime
    corr_stress: float = 0.65          # factor correlation, stress regime

    # --- Predicate and trust score parameters ---
    n_predicates: int = 16             # N, number of predicates.
                                       # Refined taxonomy from Section 4.1,
                                       # Table 2; PIK-aware and concealment-aware.
    gamma: float = 1.1                 # trust sensitivity in hazard intensity
    pred_noise: float = 0.30           # noise on predicate indicator
    pred_threshold: float = 0.30       # predicate passes when indicator < threshold
                                       # (factors interpreted as risk indicators:
                                       # higher value = greater stress)

    # --- Pricing and collateral parameters ---
    delta: float = 1.5                 # CVaR sensitivity in adjusted price
    base_ltv: float = 0.70             # theta, base loan-to-value cap
    eta: float = 0.5                   # trust exponent in LTV
    kappa: float = 0.9                 # CVaR sensitivity in LTV

    # --- Simulation parameters ---
    n_paths: int = 10_000              # Monte Carlo paths
    seed: int = 42                     # master random seed (reproducibility)

    @property
    def n_steps(self) -> int:
        """Total number of monthly time steps."""
        return int(round(self.maturity / self.dt))


# ============================================================================
# Scenarios
# ============================================================================

@dataclass
class Scenario:
    """
    A scenario specifies the trajectory of factor drift and correlation
    over the simulation horizon.
    """
    name: str
    drift_fn: Callable[[int], np.ndarray]
    corr_fn: Callable[[int], np.ndarray]


def build_scenarios(p: Params) -> List[Scenario]:
    """
    Build the four scenarios specified in Section 6.1 of the manuscript:

      1. base — no directional stress.
      2. single_factor — factor 1 drift +30%/yr starting month 13.
      3. correlated_stress — all factors drift +20%/yr from month 13,
         correlation jumps to stress level (0.65).
      4. recovery — correlated stress from month 13 to 24, then mild
         reversal from month 25 onward, correlation returns to normal.
    """
    F = p.n_factors

    def corr_matrix(rho: float) -> np.ndarray:
        C = np.full((F, F), rho)
        np.fill_diagonal(C, 1.0)
        return C

    C_normal = corr_matrix(p.corr_normal)
    C_stress = corr_matrix(p.corr_stress)

    # --- Base: stationary, normal correlation ---
    base = Scenario(
        name="base",
        drift_fn=lambda t: np.zeros(F),
        corr_fn=lambda t: C_normal,
    )

    # --- Single-factor deterioration ---
    def single_drift(t: int) -> np.ndarray:
        d = np.zeros(F)
        if t >= 13:
            d[0] = 0.30
        return d

    single_factor = Scenario(
        name="single_factor",
        drift_fn=single_drift,
        corr_fn=lambda t: C_normal,
    )

    # --- Correlated stress ---
    def stress_drift(t: int) -> np.ndarray:
        return np.full(F, 0.20) if t >= 13 else np.zeros(F)

    def stress_corr(t: int) -> np.ndarray:
        return C_stress if t >= 13 else C_normal

    correlated_stress = Scenario(
        name="correlated_stress",
        drift_fn=stress_drift,
        corr_fn=stress_corr,
    )

    # --- Recovery: stress months 13-24, then recovery from month 25 ---
    def recovery_drift(t: int) -> np.ndarray:
        if 13 <= t < 25:
            return np.full(F, 0.20)
        elif t >= 25:
            return np.full(F, -0.10)
        return np.zeros(F)

    def recovery_corr(t: int) -> np.ndarray:
        if 12 <= t < 24:
            return C_stress
        return C_normal

    recovery = Scenario(
        name="recovery",
        drift_fn=recovery_drift,
        corr_fn=recovery_corr,
    )

    return [base, single_factor, correlated_stress, recovery]


# ============================================================================
# Path generation
# ============================================================================

def simulate_factors(p: Params, scenario: Scenario, rng: np.random.Generator) -> np.ndarray:
    """
    Generate Monte Carlo paths of the latent credit state.

    Each factor follows correlated geometric Brownian motion under the
    physical measure (Section 4.2):

        dX_t = mu(t) dt + sigma * L(t) dW_t

    where L(t)L(t)^T = correlation matrix.

    Returns
    -------
    X : ndarray, shape (n_paths, n_steps+1, n_factors)
        Latent factor paths starting at X(0) = 0.
    """
    N, T, F = p.n_paths, p.n_steps, p.n_factors
    X = np.zeros((N, T + 1, F))
    sqrt_dt = np.sqrt(p.dt)

    for t in range(T):
        mu = scenario.drift_fn(t)
        C = scenario.corr_fn(t)
        L = np.linalg.cholesky(C)
        Z = rng.standard_normal((N, F))
        dW = Z @ L.T
        X[:, t + 1, :] = X[:, t, :] + mu * p.dt + p.sigma * sqrt_dt * dW

    return X


def simulate_predicates(p: Params, X: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """
    Generate predicate compliance outcomes given the latent factor paths.

    Each predicate i tracks a noisy linear combination of factors 1 and 2:

        Y_i(t) = alpha_i1 * X_1(t) + alpha_i2 * X_2(t) + eps_i(t)
        P_i(t) = 1{Y_i(t) < threshold}

    Random per-predicate weights generate diverse but correlated failures.
    The binary P_i is what gets cryptographically attested under the framework
    (Section 4.1); the underlying Y_i never leaves the borrower's information
    set.

    Returns
    -------
    P : ndarray, shape (n_paths, n_steps+1, n_predicates)
        Predicate compliance, values in {0, 1}.
    """
    N, Tp1, _ = X.shape
    K = p.n_predicates

    # Random predicate weights on factors 1 and 2 (fixed across paths).
    weights_rng = np.random.default_rng(p.seed + 999)
    alpha1 = weights_rng.uniform(0.5, 1.5, size=K)
    alpha2 = weights_rng.uniform(0.3, 1.0, size=K)

    X1 = X[:, :, 0:1]
    X2 = X[:, :, 1:2]
    Y = (X1 * alpha1[None, None, :]) + (X2 * alpha2[None, None, :])

    eps = rng.standard_normal((N, Tp1, K)) * p.pred_noise
    Y = Y + eps

    P = (Y < p.pred_threshold).astype(np.float64)
    return P


def trust_score(P: np.ndarray) -> np.ndarray:
    """
    Composite trust score: T(t) = mean over predicates.

    Section 4.3 of the manuscript.

    Returns
    -------
    T : ndarray, shape (n_paths, n_steps+1)
        Trust score in [0, 1].
    """
    return P.mean(axis=2)


def hazard(p: Params, X: np.ndarray, T_score: np.ndarray) -> np.ndarray:
    """
    Default intensity functional (Section 4.3):

        lambda(t) = lambda0 * exp(beta . X(t) - gamma * T(t))

    Returns
    -------
    lam : ndarray, shape (n_paths, n_steps+1)
    """
    beta = np.asarray(p.beta)
    betaX = X @ beta
    return p.lambda0 * np.exp(betaX - p.gamma * T_score)


# ============================================================================
# Information regimes
# ============================================================================

def stale_state(arr: np.ndarray, step_interval: int) -> np.ndarray:
    """
    Apply the staleness operator: hold values constant between reporting
    boundaries.

    Used to construct the opaque baseline regime (Section 6.2). The
    zero-knowledge regime uses the unfiltered array directly.

    Parameters
    ----------
    arr : ndarray
        Time-indexed array with time on axis 1.
    step_interval : int
        Number of time steps between reporting boundaries (3 for quarterly
        opaque regime under monthly time stepping).
    """
    out = arr.copy()
    Tp1 = arr.shape[1]
    last_report = 0
    for t in range(Tp1):
        if t % step_interval == 0:
            last_report = t
        else:
            out[:, t, ...] = arr[:, last_report, ...]
    return out


# ============================================================================
# Reduced-form mark-to-market pricing
# ============================================================================

def mtm_price(p: Params, lam_t: np.ndarray, t_index: np.ndarray) -> np.ndarray:
    """
    Mark-to-market price under reduced-form credit risk with intensity
    frozen at the current observed value (Section 4.4):

        Lambda = r + lam(t)
        Price = (c + R * lam) * (1 - exp(-Lambda * tau)) / Lambda
                + exp(-Lambda * tau)

    where tau = T_m - t is remaining time to maturity.

    Closed-form mark-to-market price under piecewise-constant intensity;
    see Lando (2004, Ch. 5).
    """
    tau = p.maturity - t_index * p.dt
    Lam = p.risk_free + lam_t
    e = np.exp(-Lam * tau)
    coup_pv = (p.coupon + p.recovery * lam_t) * (1.0 - e) / Lam
    return coup_pv + e


def cvar_cross_sectional(losses: np.ndarray, alpha: float = 0.95) -> np.ndarray:
    """
    Conditional value at risk at level alpha, computed cross-sectionally
    across paths at each time step (Section 4.4):

        CVaR_alpha(t) = E[L(t) | L(t) >= VaR_alpha(t)]

    Parameters
    ----------
    losses : ndarray, shape (n_paths, n_steps+1)
        Fractional loss per path per time step.
    alpha : float
        Confidence level (default 0.95).
    """
    Tp1 = losses.shape[1]
    out = np.empty(Tp1)
    for t in range(Tp1):
        L = losses[:, t]
        var = np.quantile(L, alpha)
        tail = L[L >= var]
        out[t] = tail.mean() if tail.size else var
    return out


def compute_metrics(p: Params, X_rep: np.ndarray, T_rep: np.ndarray) -> Dict[str, np.ndarray]:
    """
    Compute the framework outputs from reported factors and trust score.

    Computes: default intensity, mark-to-market price, cross-sectional CVaR,
    adjusted price (CVaR-discounted), and dynamic loan-to-value ratio.

    Section 4.3 - 4.5 of the manuscript.
    """
    lam = hazard(p, X_rep, T_rep)
    t_index = np.arange(p.n_steps + 1)
    price = mtm_price(p, lam, t_index)

    price0 = price[:, 0:1]
    loss = np.clip(1.0 - price / price0, 0.0, None)
    cvar = cvar_cross_sectional(loss, alpha=0.95)

    cvar_b = cvar[None, :]
    price_adj = price * np.exp(-p.delta * cvar_b)
    ltv = p.base_ltv * (price_adj / price0) * (T_rep ** p.eta) * np.exp(-p.kappa * cvar_b)

    return {
        "price": price,
        "price_adj": price_adj,
        "cvar": cvar,
        "ltv": ltv,
        "lam": lam,
    }


# ============================================================================
# Per-scenario execution
# ============================================================================

def run_scenario(p: Params, scenario: Scenario, master_rng: np.random.Generator) -> Dict:
    """
    Run a full scenario and compute outputs under both information regimes.

    Both regimes operate on the same underlying credit paths; the only
    difference is the staleness operator applied to the opaque regime
    (Section 6.2 design property: within-path comparison).
    """
    # Use independent streams for factors and predicate noise.
    rng_f = np.random.default_rng(master_rng.integers(0, 2**31))
    rng_p = np.random.default_rng(master_rng.integers(0, 2**31))

    X = simulate_factors(p, scenario, rng_f)
    P = simulate_predicates(p, X, rng_p)
    T = trust_score(P)

    # Reported state under each regime.
    X_zk, T_zk = X, T
    X_op = stale_state(X, step_interval=3)
    T_op = stale_state(T[..., None], step_interval=3)[..., 0]

    return {
        "true_X": X,
        "true_T": T,
        "zk": compute_metrics(p, X_zk, T_zk),
        "opaque": compute_metrics(p, X_op, T_op),
    }


# ============================================================================
# Summary statistics
# ============================================================================

def path_mean_se(arr: np.ndarray):
    """Mean and standard error of the mean across paths."""
    m = arr.mean(axis=0)
    se = arr.std(axis=0, ddof=1) / np.sqrt(arr.shape[0])
    return m, se


def summarise(p: Params, results: Dict, scenario_name: str) -> Dict:
    """
    Build the comparison table used in Section 7.1 of the manuscript.

    Computes scenario-level summary statistics for both regimes:
      - Adjusted price at month 36 (mean, SE)
      - Peak CVaR_95 over horizon
      - LTV at month 36 (mean, SE)
      - Maximum monthly price drop (per path then averaged, with SE)
      - Default intensity at month 36 (mean, SE)
      - Std of monthly price changes (per path then averaged, with SE)
      - First month CVaR exceeds 5%
      - Average CVaR over the stress window (months 12-36)
    """
    zk = results["zk"]
    op = results["opaque"]
    summary: Dict = {}
    month36 = 36

    for label, r in (("zk", zk), ("opaque", op)):
        m, se = path_mean_se(r["price_adj"][:, month36])
        summary[f"price_adj_m36_mean_{label}"] = float(m)
        summary[f"price_adj_m36_se_{label}"] = float(se)

    summary["peak_cvar_zk"] = float(zk["cvar"].max())
    summary["peak_cvar_opaque"] = float(op["cvar"].max())

    for label, r in (("zk", zk), ("opaque", op)):
        m, se = path_mean_se(r["ltv"][:, month36])
        summary[f"ltv_m36_mean_{label}"] = float(m)
        summary[f"ltv_m36_se_{label}"] = float(se)

    for label, r in (("zk", zk), ("opaque", op)):
        diffs = -np.diff(r["price_adj"], axis=1)
        per_path_max = diffs.max(axis=1)
        m, se = path_mean_se(per_path_max)
        summary[f"max_monthly_drop_mean_{label}"] = float(m)
        summary[f"max_monthly_drop_se_{label}"] = float(se)

    for label, r in (("zk", zk), ("opaque", op)):
        m, se = path_mean_se(r["lam"][:, month36])
        summary[f"lambda_m36_mean_{label}"] = float(m)
        summary[f"lambda_m36_se_{label}"] = float(se)

    for label, r in (("zk", zk), ("opaque", op)):
        diffs = np.diff(r["price_adj"], axis=1)
        per_path_std = diffs.std(axis=1, ddof=1)
        m, se = path_mean_se(per_path_std)
        summary[f"price_change_std_mean_{label}"] = float(m)
        summary[f"price_change_std_se_{label}"] = float(se)

    threshold = 0.05
    for label, r in (("zk", zk), ("opaque", op)):
        cvar_series = r["cvar"]
        idx = int(np.argmax(cvar_series > threshold))
        if cvar_series[idx] > threshold:
            summary[f"first_month_cvar_above_5pct_{label}"] = idx
        else:
            summary[f"first_month_cvar_above_5pct_{label}"] = None

    for label, r in (("zk", zk), ("opaque", op)):
        summary[f"avg_cvar_stress_window_{label}"] = float(r["cvar"][12:37].mean())

    summary["scenario"] = scenario_name
    return summary


# ============================================================================
# Top-level driver
# ============================================================================

def run_all(p: Params | None = None, outdir: str | Path = "output") -> List[Dict]:
    """
    Run the full simulation: four scenarios under two information regimes,
    write results to outdir, and return the summary list.
    """
    if p is None:
        p = Params()
    outpath = Path(outdir)
    outpath.mkdir(parents=True, exist_ok=True)

    scenarios = build_scenarios(p)
    master_rng = np.random.default_rng(p.seed)

    all_results: Dict[str, Dict] = {}
    all_summaries: List[Dict] = []

    for sc in scenarios:
        res = run_scenario(p, sc, master_rng)
        all_results[sc.name] = res
        all_summaries.append(summarise(p, res, sc.name))
        print(f"  ran scenario: {sc.name}")

    with open(outpath / "params.json", "w") as f:
        json.dump(asdict(p), f, indent=2, default=str)

    with open(outpath / "summary.json", "w") as f:
        json.dump(all_summaries, f, indent=2)

    # Save mean time series for plotting
    npz_payload = {}
    for sc_name, res in all_results.items():
        for regime in ("zk", "opaque"):
            r = res[regime]
            npz_payload[f"{sc_name}_{regime}_price_adj_mean"] = r["price_adj"].mean(axis=0)
            npz_payload[f"{sc_name}_{regime}_price_adj_se"] = (
                r["price_adj"].std(axis=0, ddof=1) / np.sqrt(p.n_paths)
            )
            npz_payload[f"{sc_name}_{regime}_cvar"] = r["cvar"]
            npz_payload[f"{sc_name}_{regime}_ltv_mean"] = r["ltv"].mean(axis=0)
            npz_payload[f"{sc_name}_{regime}_ltv_se"] = (
                r["ltv"].std(axis=0, ddof=1) / np.sqrt(p.n_paths)
            )
            npz_payload[f"{sc_name}_{regime}_lambda_mean"] = r["lam"].mean(axis=0)
    np.savez(outpath / "series.npz", **npz_payload)

    print(f"\nWrote {outpath/'params.json'}")
    print(f"Wrote {outpath/'summary.json'}")
    print(f"Wrote {outpath/'series.npz'}")
    return all_summaries


if __name__ == "__main__":
    run_all()
