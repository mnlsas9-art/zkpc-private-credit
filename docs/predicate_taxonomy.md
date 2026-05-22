# Predicate Taxonomy

This document is the extended companion to Table 2 of the manuscript. It
specifies each of the 16 predicates in the refined taxonomy, the concealment
vector it addresses (if any), the threshold convention used in the simulation,
and the policy literature documenting the underlying concealment mechanism.

## Quick reference

| # | Category | Predicate | Concealment vector |
|---|---|---|---|
| 1 | Balance sheet | leverage ratio ≤ threshold | Direct leverage stress |
| 2 | Balance sheet | cash-to-debt ratio ≥ threshold | Liquidity reserves |
| 3 | Balance sheet | net working capital ≥ threshold | Operating liquidity |
| 4 | Balance sheet | cumulative PIK capitalization ≤ cap | PIK-driven principal inflation |
| 5 | Income statement | DSCR (cash interest only) ≥ threshold | PIK-masked coverage |
| 6 | Income statement | interest coverage excluding PIK ≥ threshold | PIK concealment |
| 7 | Income statement | EBITDA margin ≥ floor | Margin compression |
| 8 | Payment behavior | cash interest paid ≥ threshold | Cash-vs-PIK substitution |
| 9 | Payment behavior | no PIK election (or PIK below cap) | PIK election as stress signal |
| 10 | Payment behavior | principal amortization on schedule | Amortization deferral |
| 11 | Adverse event | no covenant breach declared | Direct covenant failure |
| 12 | Adverse event | no covenant waiver this period | Covenant waiver concealment |
| 13 | Adverse event | no amend-and-extend executed | Maturity-stress concealment |
| 14 | Adverse event | no dividend recap under stress | Sponsor extraction |
| 15 | Adverse event | no fund-level NAV loan > threshold | Layered leverage |
| 16 | Adverse event | no cross-default triggered | Cross-default propagation |

## Predicate detail

### Balance sheet predicates (1–4)

**Predicate 1 — Leverage ratio cap.** Detects direct leverage stress. The
standard middle-market direct lending instrument carries a maximum leverage
covenant in the range of 5.0x to 7.0x EBITDA. The simulation uses 6.0x as
the cap.

**Predicate 2 — Cash-to-debt ratio floor.** Detects liquidity stress. Standard
middle-market loans require minimum liquidity reserves. The simulation uses
5% of total debt as the floor.

**Predicate 3 — Net working capital floor.** Detects operating liquidity
stress. Working capital below 10% of revenue is treated as a stress signal.

**Predicate 4 — PIK capitalization cap.** Detects cumulative PIK-driven
principal inflation. PIK interest is capitalized into principal rather than
paid in cash; cumulative PIK above 25% of original principal indicates that
the loan's economic exposure has materially expanded beyond original
underwriting. *Concealment vector documented in IMF GFSR 2024 Ch. 2,
Moody's Analytics 2025.*

### Income statement predicates (5–7)

**Predicate 5 — DSCR on cash interest only.** Detects PIK-masked coverage
deterioration. Conventional DSCR predicates include PIK interest as if it
were paid; this masks economic distress when borrowers substitute PIK for
cash interest. Measuring DSCR on cash interest only reveals the true
coverage. Floor: 1.10x.

**Predicate 6 — Interest coverage excluding PIK.** Companion to Predicate 5;
measures interest coverage ratio with PIK income excluded. Floor: 2.0x.
Together with Predicate 5, this provides robustness against PIK-driven
concealment.

**Predicate 7 — EBITDA margin floor.** Detects margin compression. Floor: 10%.

### Payment behavior predicates (8–10)

**Predicate 8 — Cash interest payment threshold.** Detects cash-vs-PIK
substitution. Even when contractual interest is "paid" via PIK election,
the cash interest actually transferred should remain above a threshold of
contractual amount. Threshold: 75% of contractual interest paid in cash.

**Predicate 9 — PIK election cap.** Detects PIK election as a stress signal.
A borrower electing to substitute PIK for cash interest in a given period
is signaling cash-flow stress; the predicate fires when PIK exceeds 20% of
total interest paid in the current period.

**Predicate 10 — Principal amortization on schedule.** Detects amortization
deferral. For amortizing loans, principal payments deferred or missed
indicate stress.

### Adverse event predicates (11–16)

**Predicate 11 — No declared covenant breach.** The direct covenant compliance
predicate. Fires on any declared covenant breach.

**Predicate 12 — No covenant waiver executed.** Detects covenant waiver
concealment. Sponsors and lenders may negotiate waivers in lieu of declaring
formal breaches; the waiver itself is the distress signal that the borrower
would have otherwise been in technical default. *Concealment vector
documented in IMF 2024, Moody's Analytics 2025.*

**Predicate 13 — No amend-and-extend executed.** Detects maturity-stress
concealment. Borrowers facing maturity that cannot be refinanced at original
terms execute amend-and-extend transactions to push maturity out, typically
at higher coupons. This is a distress signal masked as a "successful
refinancing." *Concealment vector documented in IMF 2024.*

**Predicate 14 — No dividend recap under stress.** Detects sponsor extraction
during distress. When private equity sponsors execute dividend recaps from
portfolio companies that are themselves under stress, this indicates rent
extraction at lender expense. The predicate fires conditionally on the
borrower's trust score (extraction during low trust is the signal of concern).

**Predicate 15 — No fund-level NAV loan above threshold.** Detects layered
leverage at the fund level. NAV-based loans collateralized by the entire
fund portfolio expand the fund's leverage and create cascading risks not
visible in loan-level disclosures. Threshold: 15% of fund NAV. *Concealment
vector documented in Levin and Malfroy-Camine 2025, IMF 2024.*

**Predicate 16 — No cross-default triggered.** Detects cross-default
propagation. Cross-defaults between related entities or across borrower
relationships indicate systemic linkage and trigger broader credit
implications.

## Predicate design philosophy

The taxonomy is *concealment-aware*: six of the sixteen predicates (4, 5,
6, 8, 9, 12, 13, 14, 15) explicitly target documented concealment vectors
rather than the conventional balance-sheet, income-statement, payment, and
adverse-event check-box approach that constitutes most existing covenant
sets. The choice to incorporate these is not cosmetic; the sensitivity
analysis in Section 7.3 of the manuscript shows that expanding from a
conventional 6-predicate set to the refined 16-predicate set increases the
headline cliff reduction from 23.0% to 34.4%.

The taxonomy is also *modular*: each predicate is independent of the others
in its cryptographic attestation, so production deployments can adopt
subsets of the taxonomy depending on the specific loan agreement and the
operational priorities of the parties involved.

The framework operates equivalently on any predicate set satisfying the
two structural properties required: (1) each predicate must be expressible
as a Boolean function over the borrower's confidential financial state, and
(2) the predicate set must be fixed at origination and published as part of
the loan's terms.

## Implementation note

In the simulation, predicates are represented as a noisy linear function of
factors 1 and 2 plus iid noise, with the predicate value set to 1 when the
indicator falls below a threshold. This is a stylized representation: each
production predicate would be implemented as a specific arithmetic circuit
operating on the borrower's actual financial state. See Section 8.4 of the
manuscript for discussion of the engineering work involved in translating
predicate definitions into production-grade ZK circuits.
