# Synthetic Data Assumptions and Modeling Limitations

## Purpose

This document describes the assumptions, design decisions, and known limitations of the YottaFlex synthetic revenue forecasting platform.

The objective is to generate realistic, reproducible sales data suitable for testing forecasting workflows, data validation, and anomaly detection.

The dataset is entirely synthetic and does not represent actual YottaFlex business information.

## 1. Reproducibility

All random data generation uses the fixed seed `20261022`.

The generator supports two scales:

| Parameter | Starter | Full |
|---|---:|---:|
| Sales representatives | 20 | 2,000 |
| Accounts | 20 | 2,000 |
| Opportunities | 200 | 20,000 |

Four territories and six pipeline stages are used in both configurations.

The generator writes CSV files to `data/raw/`. Re-running the generator overwrites those files.

A SHA-256 manifest is used to verify reproducibility. The full-scale dataset was regenerated and all ten CSV checksums matched.

## 2. Time Horizon

The simulation covers opportunities created during 2025 and 2026.

Quarterly quotas cover eight quarters, from 2025 Q1 through 2026 Q4.

Forecast snapshots are generated at selected quarter-end dates.

The simulation observation cutoff is November 4, 2026. Opportunities whose realized close dates fall after this cutoff remain open in the generated data.

As a result, the final quarter of 2026 is incomplete and should not be treated as a finalized accuracy evaluation period.

## 3. Sales Organization

The model contains four sales territories:

- North
- South
- East
- West

Sales representatives and accounts are assigned to territories.

Each opportunity is associated with one account and one owning representative.

The current implementation does not include an effective-dated history of territory or representative ownership changes. Territory reassignment cannot therefore be reconstructed historically.

## 4. Opportunity Generation

Opportunity values are sampled from a lognormal distribution to produce a right-skewed distribution of deal sizes.

Opportunities are assigned creation dates, products, owners, accounts, and initial pipeline stages.

Expected close dates are generated approximately 30 to 180 days after opportunity creation.

All monetary values in the clean dataset use USD.

Opportunity identifiers incorporate the creation year and a deterministic sequence number.

## 5. Pipeline Stages

The six pipeline stages and their baseline probabilities are:

| Stage | Win probability |
|---|---:|
| Prospecting | 10% |
| Qualification | 25% |
| Proposal | 50% |
| Negotiation | 80% |
| Closed Won | 100% |
| Closed Lost | 0% |

These probabilities are illustrative assumptions, not probabilities calibrated from historical business data.

Stage transitions are recorded in `stage_history` with effective timestamps.

Terminal won and lost stages are recorded when opportunities close.

## 6. Sales Outcomes and Bookings

Sales outcomes are simulated using probabilities influenced by the initially assigned opportunity stage.

Realized close dates may be delayed relative to expected close dates by up to 45 days.

A won opportunity generates a historical booking.

Lost opportunities do not generate bookings.

Booking dates match actual close dates in the current implementation.

The generator creates at most one booking per won opportunity.

The model does not currently simulate partial bookings, refunds, cancellations, or multiple revenue-recognition events per opportunity.

## 7. Activities

Each opportunity receives synthetic sales activity records.

Activities include a type, date, duration, representative, and status.

Historical forecast snapshots count activities known at the snapshot date.

Activity count is currently a descriptive feature rather than an input that adjusts forecast probabilities.

The generator does not model detailed causal relationships between specific activity types and eventual sales outcomes.

## 8. Quotas and Seasonality

Each sales representative receives a quota for every quarter in the modeled eight-quarter period.

Quarterly quotas incorporate illustrative seasonal factors:

| Quarter | Factor |
|---|---:|
| Q1 | 0.90 |
| Q2 | 1.00 |
| Q3 | 0.95 |
| Q4 | 1.15 |

These factors represent a simplified assumption that fourth-quarter sales targets are higher.

They are not inferred from historical YottaFlex performance.

The quota seasonality assumptions should not be interpreted as proof that realized bookings follow the same seasonal pattern.

## 9. Historical Forecast Snapshots

Forecast snapshots are generated at historical observation dates.

An opportunity is eligible for a snapshot when it:

- Already exists at the snapshot date
- Has not closed by that date
- Has an expected close date within the relevant reporting-quarter boundary

The snapshot captures the opportunity amount, representative, stage as of the snapshot, deal age, activity count, and stage-based forecast value.

Only stage changes and activities known by the snapshot date are eligible for historical features.

This prevents future events from being used in ordinary snapshot construction.

The intentionally corrupted anomaly dataset contains a separate future-stage leakage example for validation testing.

## 10. Baseline Forecasting Method

The baseline forecast is calculated as:

`forecast_amount = opportunity_amount × win_probability`

The win probability is determined by the opportunity's stage at the snapshot date.

Forecast amounts are rounded to two decimal places.

This approach provides a simple, interpretable benchmark.

However, it is not a fully trained or statistically calibrated predictive model.

Deal age, activity volume, representative performance, product differences, and territory effects are not yet used to adjust the probability.

## 11. Forecast Evaluation

Forecast evaluation compares historical opportunity-level forecast values with subsequent realized bookings.

Bookings are attributed to the appropriate opportunity and evaluated within the relevant forecast horizon.

The evaluator excludes incomplete reporting periods from finalized accuracy calculations.

Reported metrics include forecast bias and weighted absolute percentage error.

**Important limitation:** The evaluation covers the cohort of opportunities represented in each historical snapshot. It does not measure total company bookings, because new opportunities created after the snapshot may contribute additional revenue.

Forecast performance should be interpreted with that scope in mind.

## 12. Data Quality and Anomaly Injection

The project deliberately injects five labeled anomalies into a copy of the clean dataset:

1. An expected close date before the opportunity creation date
2. A non-USD currency in the USD baseline
3. A stage probability that does not match the stage reference table
4. A duplicated opportunity within a forecast snapshot
5. A future stage incorrectly used in a historical snapshot

The original clean CSV files are preserved.

The separate ground-truth file identifies injected anomalies for validation testing.

The validation system detected all five injected anomalies in the verified full-scale run.

## 13. Integrity and Business Rules

The project includes automated checks for:

- Unique, non-null primary keys
- Valid foreign-key references
- Positive booking amounts
- Valid opportunity close dates
- Booking status consistency
- Booking-date consistency
- Terminal pipeline stage consistency
- Forecast arithmetic
- Snapshot uniqueness
- Stage probability consistency
- Historical stage leakage
- Currency consistency

These checks help identify structural and business-rule violations but do not establish that every synthetic distribution is statistically realistic.

## 14. Known Limitations

The current implementation has several limitations:

- No effective-dated territory assignment history
- No historical versioning of expected close dates
- No explicit modeling of opportunity ownership transfers
- No partial or recurring bookings
- No trained probability calibration
- No causal activity-to-outcome model
- Limited treatment of product, account, and representative heterogeneity
- No external economic or market indicators
- Incomplete 2026 Q4 observation period
- Forecast accuracy limited to snapshot opportunity cohorts

These are deliberate scope boundaries and potential areas for future improvement.

## 15. Potential Extensions

Future development could add:

- Effective-dated territory and ownership changes
- Historical expected-close revisions and slippage tracking
- Calibrated probabilities using historical outcomes
- Deal-age and activity-based probability adjustments
- Rep-level and territory-level forecasting
- Scenario-based uncertainty ranges
- Rolling forecast horizons
- More comprehensive accuracy evaluation by segment
- SQL database exports and downstream analytics integrations

## Conclusion

The synthetic data platform provides a reproducible foundation for historical sales forecasting, anomaly detection, and relational data validation.

Its primary strengths are deterministic generation, explicit temporal records, traceable forecast calculations, and separately labeled data-quality anomalies.

The documented limitations distinguish the implemented baseline from more advanced production forecasting capabilities.