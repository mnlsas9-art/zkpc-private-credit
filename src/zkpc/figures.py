"""
Figure generation for the reproducibility package.

Reads simulation outputs from `output/series.npz` (produced by
simulation.run_all) and writes the four figures referenced in Sections 7.1
and 7.2 of the manuscript:

  * fig1_adjusted_price_stress.png — Figure 1 in the paper
  * fig2_cvar_stress.png           — Figure 2 in the paper
  * fig3_ltv_stress.png            — Figure 3 in the paper
  * fig_supp_scenario_grid.png     — Supplementary figure

All figures are 300 DPI suitable for publication.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict

import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

# ---- Style ----
_STYLE = {
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.labelsize": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "grid.linewidth": 0.5,
    "legend.frameon": False,
    "lines.linewidth": 1.6,
    "figure.dpi": 110,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
}

COLOR_ZK = "#1f4e8c"
COLOR_OP = "#c0392b"


def _apply_style():
    mpl.rcParams.update(_STYLE)


def _load(simdir: Path) -> Dict[str, np.ndarray]:
    """Load the simulation series .npz into a dict of arrays."""
    return dict(np.load(simdir / "series.npz"))


def plot_adjusted_price(data: Dict[str, np.ndarray], outdir: Path) -> Path:
    """Figure 1: mean adjusted price under correlated stress, both regimes."""
    fig, ax = plt.subplots(figsize=(6.5, 3.8))
    sc = "correlated_stress"
    months = np.arange(len(data[f"{sc}_zk_price_adj_mean"]))

    zk_mean = data[f"{sc}_zk_price_adj_mean"]
    zk_se = data[f"{sc}_zk_price_adj_se"]
    op_mean = data[f"{sc}_opaque_price_adj_mean"]
    op_se = data[f"{sc}_opaque_price_adj_se"]

    ax.plot(months, zk_mean, color=COLOR_ZK, label="ZK-attested (monthly)")
    ax.fill_between(months, zk_mean - 1.96 * zk_se, zk_mean + 1.96 * zk_se,
                    color=COLOR_ZK, alpha=0.15, linewidth=0)
    ax.plot(months, op_mean, color=COLOR_OP, linestyle="--",
            label="Opaque (quarterly)")
    ax.fill_between(months, op_mean - 1.96 * op_se, op_mean + 1.96 * op_se,
                    color=COLOR_OP, alpha=0.15, linewidth=0)
    ax.axvspan(13, months[-1], alpha=0.06, color="grey", label="Stress window")

    ax.set_xlabel("Month")
    ax.set_ylabel("Mean adjusted price")
    ax.set_xlim(0, months[-1])
    ax.legend(loc="upper right")

    outpath = outdir / "fig1_adjusted_price_stress.png"
    fig.savefig(outpath)
    plt.close(fig)
    return outpath


def plot_cvar(data: Dict[str, np.ndarray], outdir: Path) -> Path:
    """Figure 2: cross-sectional CVaR_95 under correlated stress, both regimes."""
    fig, ax = plt.subplots(figsize=(6.5, 3.8))
    sc = "correlated_stress"
    months = np.arange(len(data[f"{sc}_zk_cvar"]))

    ax.plot(months, data[f"{sc}_zk_cvar"], color=COLOR_ZK,
            label="ZK-attested (monthly)")
    ax.plot(months, data[f"{sc}_opaque_cvar"], color=COLOR_OP, linestyle="--",
            label="Opaque (quarterly)")
    ax.axvspan(13, months[-1], alpha=0.06, color="grey", label="Stress window")
    ax.axhline(0.05, color="black", linewidth=0.5, linestyle=":")

    ax.set_xlabel("Month")
    ax.set_ylabel("CVaR$_{95}$")
    ax.set_xlim(0, months[-1])
    ax.legend(loc="upper left")

    outpath = outdir / "fig2_cvar_stress.png"
    fig.savefig(outpath)
    plt.close(fig)
    return outpath


def plot_ltv(data: Dict[str, np.ndarray], outdir: Path) -> Path:
    """Figure 3: mean dynamic LTV under correlated stress, both regimes."""
    fig, ax = plt.subplots(figsize=(6.5, 3.8))
    sc = "correlated_stress"
    months = np.arange(len(data[f"{sc}_zk_ltv_mean"]))

    zk_mean = data[f"{sc}_zk_ltv_mean"]
    zk_se = data[f"{sc}_zk_ltv_se"]
    op_mean = data[f"{sc}_opaque_ltv_mean"]
    op_se = data[f"{sc}_opaque_ltv_se"]

    ax.plot(months, zk_mean, color=COLOR_ZK, label="ZK-attested (monthly)")
    ax.fill_between(months, zk_mean - 1.96 * zk_se, zk_mean + 1.96 * zk_se,
                    color=COLOR_ZK, alpha=0.15, linewidth=0)
    ax.plot(months, op_mean, color=COLOR_OP, linestyle="--",
            label="Opaque (quarterly)")
    ax.fill_between(months, op_mean - 1.96 * op_se, op_mean + 1.96 * op_se,
                    color=COLOR_OP, alpha=0.15, linewidth=0)
    ax.axvspan(13, months[-1], alpha=0.06, color="grey", label="Stress window")

    ax.set_xlabel("Month")
    ax.set_ylabel("Mean dynamic LTV")
    ax.set_xlim(0, months[-1])
    ax.legend(loc="upper right")

    outpath = outdir / "fig3_ltv_stress.png"
    fig.savefig(outpath)
    plt.close(fig)
    return outpath


def plot_scenario_grid(data: Dict[str, np.ndarray], outdir: Path) -> Path:
    """Supplementary figure: mean adjusted price across all four scenarios."""
    fig, axes = plt.subplots(2, 2, figsize=(9.0, 5.5), sharex=True)
    scenarios = [
        ("base", "Base"),
        ("single_factor", "Single-factor deterioration"),
        ("correlated_stress", "Correlated stress"),
        ("recovery", "Recovery"),
    ]
    for ax, (key, title) in zip(axes.flat, scenarios):
        months = np.arange(len(data[f"{key}_zk_price_adj_mean"]))
        ax.plot(months, data[f"{key}_zk_price_adj_mean"], color=COLOR_ZK,
                label="ZK-attested")
        ax.plot(months, data[f"{key}_opaque_price_adj_mean"], color=COLOR_OP,
                linestyle="--", label="Opaque")
        ax.set_title(title)
        ax.set_xlim(0, months[-1])
    axes[1, 0].set_xlabel("Month")
    axes[1, 1].set_xlabel("Month")
    axes[0, 0].set_ylabel("Mean adjusted price")
    axes[1, 0].set_ylabel("Mean adjusted price")
    axes[0, 0].legend(loc="lower left")
    fig.tight_layout()

    outpath = outdir / "fig_supp_scenario_grid.png"
    fig.savefig(outpath)
    plt.close(fig)
    return outpath


def make_all(simdir: str | Path = "output", outdir: str | Path = "figures"):
    """
    Generate all four figures. Reads from `simdir/series.npz` and writes
    PNGs to `outdir/`.
    """
    _apply_style()
    simdir = Path(simdir)
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    data = _load(simdir)
    paths = [
        plot_adjusted_price(data, outdir),
        plot_cvar(data, outdir),
        plot_ltv(data, outdir),
        plot_scenario_grid(data, outdir),
    ]
    for path in paths:
        print(f"  wrote {path}")
    return paths


if __name__ == "__main__":
    make_all()
