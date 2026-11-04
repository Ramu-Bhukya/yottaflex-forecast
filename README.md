<!-- # YottaFlex Revenue Forecasting Data Platform

A reproducible synthetic sales data platform for revenue forecasting, historical pipeline analysis, data-quality validation, and forecast evaluation.

Built as an AI Forward Deployed Engineer take-home project.

## Project Overview

This project generates a relational sales dataset with opportunities, accounts, representatives, stage transitions, activities, quotas, bookings, and historical forecast snapshots.

The platform supports:

- Deterministic synthetic data generation
- Starter and full-scale datasets
- Historical, as-of forecast snapshots
- Stage-weighted pipeline forecasting
- Forecast accuracy evaluation
- Five deliberately injected data-quality anomalies
- Automated anomaly detection and integrity checks
- SHA-256 checksums for reproducibility

## Dataset Scale

| Entity | Starter Scale | Full Scale |
|---|---:|---:|
| Sales representatives | 20 | 2,000 |
| Accounts | 20 | 2,000 |
| Opportunities | 200 | 20,000 |
| Territories | 4 | 4 |
| Stages | 6 | 6 |
| Quotas | 160 | 16,000 |

The full-scale generation also produced:

- 66,101 stage-history records
- 100,125 activity records
- 6,782 historical bookings
- 16,254 forecast snapshot records

These counts are specific to the current generator implementation and seed.

## Technology

- Python 3.12
- pandas
- NumPy
- pytest
- CSV and JSON

## Setup

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Generate Data

Generate the starter dataset:

```bash
python -m src.generate_data --scale starter
```

Generate the full dataset:

```bash
python -m src.generate_data --scale full
```

The generator uses the fixed random seed `20261022`.

Generated CSV files are written to `data/raw/`.

**Note:** Running either command overwrites the existing CSV files in `data/raw/`.

## Forecasting Method

The baseline forecast uses stage-weighted pipeline values:

**Forecast amount = Opportunity amount × Stage win probability**

Stage probabilities:

| Stage | Probability |
|---|---:|
| Prospecting | 10% |
| Qualification | 25% |
| Proposal | 50% |
| Negotiation | 80% |
| Closed Won | 100% |
| Closed Lost | 0% |

Historical snapshots use the latest stage recorded as of each snapshot date. They also record deal age and completed activity counts.

The current baseline uses stage probabilities directly. Deal age and activity counts are available as features but are not yet incorporated into the probability formula.

## Forecast Evaluation

Run:

```bash
python -m src.evaluate
```

The evaluator matches each forecast opportunity to its actual booking outcome within the relevant forecast horizon.

Outputs:

- `data/processed/forecast_accuracy.csv`
- `data/processed/forecast_evaluation_detail.csv`

Metrics include forecast error, percentage error, bias, and opportunity-level weighted absolute percentage error (WAPE).

Incomplete quarters are excluded from finalized accuracy calculations.

The evaluation measures accuracy for opportunities included in each snapshot. It should not be interpreted as total company revenue forecast accuracy.

## Data-Quality Anomalies

Five anomalies are deliberately injected:

1. Expected close date before opportunity creation
2. Mixed currency in the USD baseline
3. Stage probability mismatch
4. Duplicate opportunity in a forecast snapshot
5. Future-stage information leakage

Inject anomalies:

```bash
python -m src.inject_anomalies
```

This creates corrupted copies in `data/anomalies/`.

Expected labels are stored separately in `data/ground_truth.csv`.

The clean dataset in `data/raw/` is not modified by anomaly injection.

## Validation

Validate the clean dataset:

```bash
python -m src.validate --data-dir data/raw
```

Validate the corrupted dataset:

```bash
python -m src.validate --data-dir data/anomalies
```

Check primary and foreign keys:

```bash
python -m src.check_integrity
```

Check booking arithmetic and lifecycle rules:

```bash
python -m src.check_business_rules
```

Run automated validation tests:

```bash
python -m pytest tests/test_validation.py -v
```

In the verified full-scale run:

- Clean dataset: 0 targeted anomaly-rule violations
- Corrupted dataset: all 5 injected anomalies detected
- Primary and foreign-key checks: passed
- Six business-rule checks: passed
- Automated validation tests: 4 passed

## Reproducibility

Create the SHA-256 manifest:

```bash
python -m src.manifest
```

The manifest is written to `data/manifest.json` and contains the row count and SHA-256 checksum for each clean CSV.

Regenerating the full dataset with the same seed produced identical SHA-256 checksums for all 10 CSV files.

## Documentation

- `docs/schema.md` — entity relationships and schema structure
- `docs/data_dictionary.md` — table and field definitions
- `docs/assumptions.md` — generation assumptions and modeling limitations

## Known Limitations

- The baseline forecast is stage-weighted rather than a fully calibrated predictive model.
- Opportunity age and activity counts are recorded but not yet used to adjust win probabilities.
- Snapshot evaluation measures a defined opportunity cohort, not all company bookings.
- The current generator simulates actual close-date delays but does not maintain historical revisions to expected close dates.
- The data is synthetic and is not intended to represent actual YottaFlex customers or business performance.

## License and Use

This repository is a technical demonstration using synthetic data. It is not affiliated with or endorsed by YottaFlex.



wc -l README.md  -->


# YottaFlex Sales Forecasting POC

## 1. What Is This Project?

This project is a **Proof of Concept (POC)** for a sales forecasting system.

A POC is a small working version of a bigger idea. It helps show whether the idea can work before a company invests in building a complete product.

The main goal of this project is to show how YottaFlex could use sales data to:

- Understand how much revenue might come in.
- See which sales opportunities are likely to close.
- Compare expected sales with actual sales.
- Explore what happens when sales performance is better or worse than expected.
- Find mistakes in sales data before those mistakes affect business decisions.

Because we do not have access to YottaFlex's real sales information, this project creates **realistic-looking fake data** to demonstrate the system.

All customer names, sales opportunities, and revenue figures are synthetic.

## 2. What Business Problem Are We Solving?

Imagine a company has thousands of sales opportunities.

Some customers are just starting conversations with the sales team. Others are close to signing contracts. Some deals will succeed, and others will fail.

Sales leaders need answers to questions such as:

- How much revenue can we expect this quarter?
- Which sales teams are performing well?
- What happens if some important deals are delayed?
- How accurate were our previous forecasts?
- Can we trust the sales data used in the forecast?

Without a consistent forecasting process, teams may rely on spreadsheets, manual estimates, or incomplete information.

This POC demonstrates a simple, repeatable way to answer those questions using data and Python.

## 3. What Did We Build?

We built a Python-based system that performs six main jobs.

### Job 1: Create sample sales data

The system generates fake but connected sales records, including customers, salespeople, opportunities, sales activities, targets, and completed sales.

This allows us to test the system without using confidential company information.

### Job 2: Estimate future revenue

The system looks at each sales opportunity and its current sales stage.

It then estimates how much revenue that opportunity could contribute.

For example, a $10,000 opportunity with a 50% chance of closing contributes $5,000 to the forecast.

### Job 3: Compare different outcomes

The system produces three possible views of the forecast:

- **Pessimistic:** Sales performance is weaker than expected.
- **Baseline:** Sales follow the normal assumptions.
- **Optimistic:** Sales performance is stronger than expected.

These scenarios help explain how changes in deal success rates could affect expected revenue.

### Job 4: Check previous forecasts

The system compares past forecasts with sales that actually closed.

This helps us understand whether the forecasting method tends to overestimate or underestimate revenue.

### Job 5: Find bad data

The system deliberately introduces five mistakes into a separate copy of the data.

It then checks whether those mistakes can be detected.

### Job 6: Save data in useful formats

The system exports data as:

- **CSV:** Easy to open in Excel.
- **JSON:** Useful for software applications.
- **SQLite:** Useful for storing related tables and running SQL queries.

## 4. How Much Data Did We Create?

We created a full-size test dataset covering eight quarters, from 2025 Q1 through 2026 Q4.

| Type of data | Number of records |
|---|---:|
| Sales territories | 4 |
| Sales representatives | 2,000 |
| Customer accounts | 2,000 |
| Sales stages | 6 |
| Sales opportunities | 20,000 |
| Sales stage changes | 66,101 |
| Sales activities | 100,125 |
| Quarterly sales targets | 16,000 |
| Completed sales bookings | 6,782 |
| Historical forecast records | 16,254 |
| **Total records** | **229,272** |

We also support a smaller starter dataset with 20 sales representatives, 20 customer accounts, and 200 opportunities.

## 5. How Does Sales Forecasting Work?

Each opportunity moves through different stages of the sales process.

We assign a simple chance of success to each stage.

| Sales stage | Chance of winning |
|---|---:|
| Prospecting | 10% |
| Qualification | 25% |
| Proposal | 50% |
| Negotiation | 80% |
| Closed Won | 100% |
| Closed Lost | 0% |

The forecast uses this calculation:

**Expected Revenue = Deal Amount × Chance of Winning**

For example:

| Opportunity | Deal amount | Chance of winning | Expected revenue |
|---|---:|---:|---:|
| Deal A | $10,000 | 50% | $5,000 |
| Deal B | $20,000 | 80% | $16,000 |
| Deal C | $5,000 | 10% | $500 |
| **Total** | **$35,000** | | **$21,500** |

In this example, the sales pipeline contains $35,000 in possible deals, but the weighted revenue forecast is $21,500.

This is a simple and explainable starting point. It is not a machine-learning prediction model.

## 6. How Do the Three Forecast Scenarios Work?

The baseline forecast uses the normal sales-stage probabilities.

The pessimistic scenario reduces those probabilities and applies an additional reduction to represent possible delays or weaker sales performance.

The optimistic scenario increases the probabilities, with a maximum of 100%.

For example, if the normal chance of winning a deal is 50%:

| Scenario | Adjusted chance |
|---|---:|
| Pessimistic | 37.5% |
| Baseline | 50% |
| Optimistic | 60% |

The pessimistic calculation also applies an additional 0.85 factor to expected revenue.

These scenarios help explore possible outcomes. They are not guaranteed future results or statistical confidence intervals.

## 7. How Do We Check Forecast Accuracy?

Making a forecast is only part of the job.

We also want to know whether earlier forecasts were close to what actually happened.

Our system:

1. Looks at a historical forecast.
2. Finds completed sales related to the opportunities in that forecast.
3. Compares expected revenue with actual booked revenue.
4. Calculates forecast error and bias.

This can help a sales team understand whether its forecasting assumptions are too optimistic or too conservative.

The current evaluation focuses on opportunities that were already present in a historical snapshot. It does not measure every possible source of company revenue.

## 8. What Data Problems Can the System Detect?

Real sales data is not always clean.

For example, a salesperson might enter the wrong close date, duplicate an opportunity, or use an incorrect currency.

To demonstrate data-quality checks, we created five intentional errors.

| Problem | Simple explanation |
|---|---|
| Wrong close date | A deal is expected to close before it was created |
| Wrong currency | One record uses EUR instead of the expected USD |
| Wrong probability | The chance of winning does not match the sales stage |
| Duplicate opportunity | The same deal appears twice in one forecast snapshot |
| Future information | An old forecast uses a sales stage that was not known at that time |

The original data stays clean.

The corrupted copy is saved separately so the validation system can be tested safely.

All five intentional errors were detected in our validation tests.

## 9. How Is the Project Organized?

```text
yottaflex-forecast/
│
├── src/                  Python code that runs the system
│   ├── generate_data.py  Creates sample sales data
│   ├── forecast.py       Calculates expected revenue
│   ├── scenarios.py      Creates three forecast scenarios
│   ├── evaluate.py       Checks forecast accuracy
│   ├── inject_anomalies.py
│   │                     Adds intentional data mistakes
│   ├── validate.py       Finds data problems
│   ├── database.py       Creates the SQLite database
│   ├── export_json.py    Exports JSON files
│   ├── manifest.py       Records file checksums
│   ├── check_integrity.py
│   │                     Checks table relationships
│   └── check_business_rules.py
│                         Checks sales-data rules
│
├── tests/                Automated tests
├── docs/                 Technical documentation
├── data/
│   ├── raw/              Original generated data
│   ├── anomalies/        Data containing intentional errors
│   └── processed/        Forecast results and exports
│
├── requirements.txt      Python dependencies
└── README.md             This guide
```

## 10. How to Run the Project

You need Python installed on your computer.

Open a terminal inside the project folder.

### Step 1: Create a Python environment

On macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 2: Install the required packages

```bash
python -m pip install -r requirements.txt
```

### Step 3: Generate the full dataset

```bash
python -m src.generate_data --scale full
```

This creates the sample sales data.

**Note:** Generating data again replaces the CSV files in `data/raw/`.

### Step 4: Create the data manifest

```bash
python -m src.manifest
```

This records the names, sizes, and checksums of the generated CSV files.

### Step 5: Calculate the revenue forecast

```bash
python -m src.forecast
```

Results are saved in:

- `data/processed/forecast_detail.csv`
- `data/processed/forecast_summary.csv`

### Step 6: Generate the three scenarios

```bash
python -m src.scenarios
```

Results are saved in:

- `data/processed/scenario_detail.csv`
- `data/processed/scenario_summary.csv`

### Step 7: Check forecast accuracy

```bash
python -m src.evaluate
```

Results are saved in:

- `data/processed/forecast_accuracy.csv`
- `data/processed/forecast_evaluation_detail.csv`

### Step 8: Check the data

```bash
python -m src.check_integrity
python -m src.check_business_rules
python -m src.validate --data-dir data/raw
```

These commands check whether the data follows the expected rules.

### Step 9: Create and test bad data

```bash
python -m src.inject_anomalies
python -m src.validate --data-dir data/anomalies
```

The second command is expected to identify five intentional errors.

### Step 10: Export the database and JSON files

```bash
python -m src.database
python -m src.export_json
```

The SQLite database is saved at:

`data/processed/yottaflex.db`

The JSON files are saved in:

`data/processed/json/`

### Step 11: Run the automated tests

```bash
python -m pytest tests/ -v
```

This checks that the major parts of the project are working as expected.

## 11. What Results Did We Verify?

The following results were verified during development:

| Check | Result |
|---|---|
| Full-scale data generation | Completed |
| Ten related data tables | Created |
| Total generated records | 229,272 |
| Repeatable data generation | Verified |
| Primary-key checks | 10 passed |
| Foreign-key checks | 15 passed |
| Business-rule checks | 6 passed |
| Intentional errors detected | 5 out of 5 |
| Baseline forecast records | 16,254 |
| Three-scenario forecast records | 48,762 |
| SQLite export | Verified |
| JSON export | 10 files verified |
| Automated tests | 18 passed |

The project uses a fixed random seed, `20261022`, so the same full-scale data can be generated again.

The system also checks SHA-256 file hashes to confirm that regenerated CSV files match the expected results.

## 12. What Has Not Been Built Yet?

This is a working POC, not a finished enterprise product.

The following features are not yet implemented:

- A working web dashboard or user interface
- A REST API
- A machine-learning forecasting model
- Automatically learned win probabilities
- Statistical confidence intervals
- Full historical tracking of territory and salesperson changes
- Historical tracking of every expected close-date revision
- Detailed forecast accuracy reporting across every segment and time horizon

These would be reasonable next steps for a production system.

## 13. What Would We Improve Next?

If this POC were expanded, the next improvements would be:

1. **Build a dashboard** so sales leaders can view forecasts without running Python commands.
2. **Improve forecast accuracy** by learning from historical sales outcomes.
3. **Use more sales signals**, such as deal age, recent activities, and customer history.
4. **Track changing deal dates** to understand which opportunities are slipping.
5. **Add more detailed reporting** by sales team, territory, product, and forecast horizon.
6. **Add automated monitoring** to alert users when data quality becomes poor.

## 14. Why This POC Matters

This project shows that a company can build a structured process for working with sales forecasts.

Instead of manually calculating forecasts from disconnected spreadsheets, the system can:

- Organize sales information.
- Calculate expected revenue consistently.
- Compare different business scenarios.
- Check whether previous forecasts were accurate.
- Detect data errors.
- Produce results in formats that other systems can use.

The POC provides a foundation for a more advanced forecasting application.

## 15. Additional Documentation

More detailed technical information is available in:

- `docs/schema.md` — How the data tables are connected.
- `docs/data_dictionary.md` — What each field means.
- `docs/assumptions.md` — Assumptions and limitations used to generate the data.

---

**Important:** All data in this project is synthetic. This POC is a demonstration and does not use real YottaFlex customer, pipeline, or revenue information.