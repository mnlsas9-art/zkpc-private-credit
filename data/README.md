# Calibration data

## `cdli_quarterly_returns_2023Q1-2025Q4.csv`

Quarterly total return decomposition for the Cliffwater Direct Lending Index
(CDLI) for the period 2023Q1 through 2025Q4 (twelve quarterly observations).

### Schema

| Column | Description |
|---|---|
| `quarter_end_date` | Quarter-end date (e.g., "Dec 31, 2025"). |
| `total_return_pct` | Total quarterly return, in percent. |
| `income_pct` | Income return component (interest), in percent. |
| `realized_gain_loss_pct` | Realized gains and losses, in percent. |
| `unrealized_gain_loss_pct` | Unrealized P&L component, in percent. |

Components sum to total return up to rounding.

### Source

Cliffwater LLC's quarterly press releases distributing CDLI results. Each
quarter's release reports the headline total return alongside the
decomposition. Compiled by the author from publicly distributed press
releases on PRNewswire, Yahoo Finance, Morningstar, and similar
syndication channels.

### Use in the manuscript

Section 5.2 of the manuscript reports the following statistics computed from
this CSV:

- Mean total return: 10.57 % per annum
- Mean income return: 11.10 % per annum (stable across all 12 quarters)
- Mean realized loss: −0.75 % per annum
- Annualized total return volatility: 0.79 %
- Lag-1 autocorrelation of total return: 0.70

These statistics calibrate the simulation's `coupon`, `lambda0`, and `sigma`
parameters as documented in Section 5 of the manuscript.

### Reproducing the statistics from this CSV

```python
import numpy as np
import csv

with open("cdli_quarterly_returns_2023Q1-2025Q4.csv") as f:
    rows = list(csv.reader(f))[2:]  # skip header + column row

total = np.array([float(r[1].replace("%", "")) for r in rows if r[0]])
total = total[::-1]  # chronological order

print(f"Mean total: {total.mean():.3f}%/Q  ({total.mean()*4:.2f}%/yr)")
print(f"Std (annualized): {total.std(ddof=1) * np.sqrt(4):.2f}%")
print(f"Lag-1 autocorrelation: {np.corrcoef(total[:-1], total[1:])[0, 1]:.3f}")
```

### Disclaimer

This data file was assembled from publicly distributed Cliffwater press
releases. The Cliffwater Direct Lending Index is owned exclusively by
Cliffwater LLC. Use of these statistics in this reproducibility package is
for academic research purposes consistent with Cliffwater's public
distribution of CDLI summary results.
