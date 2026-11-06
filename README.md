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

## 8. Experimental Historical Forecast and Results

In addition to the baseline, `src/improved_forecast.py` implements an **experimental heuristic**, not a trained machine-learning model. It uses stage-specific historical win/loss outcomes, deal age, and activity count to adjust the stage probabilities. Historical outcomes are included only once their close dates are known at the forecast snapshot date; final opportunity stages are not used as snapshot-time features. Historical observations are drawn from earlier stage snapshots of completed opportunities, so the resulting conversion estimates may be affected by selection bias.

`src/compare_forecasts.py` evaluates both methods on the same snapshot opportunities, counting actual bookings strictly after each snapshot and no later than the end of that quarter. Incomplete 2026 Q4 is excluded. WAPE is computed from opportunity-level absolute errors divided by total actual bookings; bias compares total predicted and actual bookings.

**Observed results on the synthetic full-scale dataset:**

| Quarter | Baseline WAPE | Experimental WAPE | Baseline bias | Experimental bias |
|---|---:|---:|---:|---:|
| 2025 Q1 | 130.94% | 133.22% | -7.99% | -3.66% |
| 2025 Q2 | 114.00% | 147.44% | 7.59% | 69.94% |
| 2025 Q3 | 106.01% | 127.42% | 8.48% | 48.87% |
| 2025 Q4 | 104.11% | 120.84% | 4.56% | 39.06% |
| 2026 Q1 | 118.77% | 138.40% | 17.23% | 55.75% |
| 2026 Q2 | 105.66% | 123.26% | 11.63% | 46.10% |
| 2026 Q3 | 100.67% | 115.93% | 0.30% | 32.68% |

The **baseline has lower WAPE in all seven completed quarters**. The experimental model tends to overpredict, so it is retained for transparency and further research, **not recommended as the better-performing model**. These are retrospective results on synthetic data, not an independent holdout evaluation. Neither model has been demonstrated to be accurate on real customer data. The evaluation covers only opportunities present in each snapshot and their within-quarter bookings, not total company revenue.

Two focused tests in `tests/test_improved_forecast.py` passed independently: one verifies that changing a future outcome does not alter an earlier forecast in a minimal example; the other checks forecast arithmetic and probability bounds. These tests do not prove comprehensive point-in-time correctness. The original suite of 18 tests also passed; run `python -m pytest -q` to confirm the combined suite in your own environment.

## 9. What Data Problems Can the System Detect?

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

## 10. How Is the Project Organized?

```text
yottaflex-forecast/
│
├── src/                  Python code that runs the system
│   ├── generate_data.py  Creates sample sales data
│   ├── forecast.py       Calculates expected revenue
│   ├── scenarios.py      Creates three forecast scenarios
│   ├── evaluate.py       Checks forecast accuracy
│   ├── improved_forecast.py  Experimental historical forecast
│   ├── compare_forecasts.py  Compares baseline and experiment
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
├── tests/                Automated tests (including test_improved_forecast.py)
├── docs/                 Technical documentation
├── data/
│   ├── raw/              Original generated data
│   ├── anomalies/        Data containing intentional errors
│   └── processed/        Forecast results and exports
│
├── requirements.txt      Python dependencies
└── README.md             This guide
```

## 11. How to Run the Project

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

### Optional: Run the experimental forecasting comparison

```bash
python -m src.improved_forecast
python -m src.compare_forecasts
```

These commands create `data/processed/improved_forecast_detail.csv`, `improved_forecast_summary.csv`, `forecast_model_comparison.csv`, and `forecast_comparison_detail.csv`. Run the full-scale data generation first. The experimental model does **not** replace the baseline.

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

## 12. What Results Did We Verify?

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
| Existing automated tests | 18 passed |
| Additional experimental forecast tests | 2 passed separately |

The project uses a fixed random seed, `20261022`, so the same full-scale data can be generated again.

The system also checks SHA-256 file hashes to confirm that regenerated CSV files match the expected results.

## 13. What Has Not Been Built Yet?

This is a working POC, not a finished enterprise product.

The following features are not yet implemented:

- A working web dashboard or user interface
- A REST API
- A trained machine-learning forecasting model
- Validated and calibrated learned win probabilities (an experimental historical-rate heuristic is included)
- Statistical confidence intervals
- Full historical tracking of territory and salesperson changes
- Historical tracking of every expected close-date revision
- Detailed forecast accuracy reporting across every segment and time horizon

These would be reasonable next steps for a production system.

## 14. What Would We Improve Next?

If this POC were expanded, the next improvements would be:

1. **Build a dashboard** so sales leaders can view forecasts without running Python commands.
2. **Improve forecast accuracy** by learning from historical sales outcomes.
3. **Validate more sales signals**, including deal age, recent activities, and customer history, before using them in production forecasts.
4. **Track changing deal dates** to understand which opportunities are slipping.
5. **Add more detailed reporting** by sales team, territory, product, and forecast horizon.
6. **Add automated monitoring** to alert users when data quality becomes poor.

## 15. Why This POC Matters

This project shows that a company can build a structured process for working with sales forecasts.

Instead of manually calculating forecasts from disconnected spreadsheets, the system can:

- Organize sales information.
- Calculate expected revenue consistently.
- Compare different business scenarios.
- Check whether previous forecasts were accurate.
- Detect data errors.
- Produce results in formats that other systems can use.

The POC provides a foundation for a more advanced forecasting application.

## 16. Additional Documentation

More detailed technical information is available in:

- `docs/schema.md` — How the data tables are connected.
- `docs/data_dictionary.md` — What each field means.
- `docs/assumptions.md` — Assumptions and limitations used to generate the data.

---

**Important:** All data in this project is synthetic. This POC is a demonstration and does not use real YottaFlex customer, pipeline, or revenue information.

## Forecast Accuracy by Segment and Horizon

Run:

```bash
python -m src.segment_accuracy
```

This generates `data/processed/forecast_accuracy_by_segment.csv`.

The report compares baseline and experimental forecasts across:

- **Territory:** East, North, South, West
- **Product:** AI Platform, Analytics Suite, Data Integration, Enterprise Support
- **Forecast horizon:** Days remaining until quarter end

The report includes predicted bookings, actual bookings, forecast error, percentage bias, and opportunity-level WAPE.

The baseline model achieved lower WAPE than the experimental model across every reported territory, product, and horizon group.

**Limitation:** Territory segmentation uses the representative's current territory assignment rather than a historically effective-dated assignment.

## Historical Point-in-Time Validation

Run:

```bash
python -m src.check_point_in_time
```

This verifies historical snapshot consistency for:

- Opportunity creation dates
- Historical opportunity stages
- Activity counts as of the snapshot date
- Deal age calculations

**Verified results:** All five checks passed across 16,254 forecast snapshots, with zero inconsistencies.

The experimental forecasting code also filters historical training outcomes by `actual_close_date <= snapshot_date`. Snapshot consistency checks and the existing unit tests provide evidence against future-data leakage, but do not constitute an exhaustive leakage audit.

## Automated Test Results

Run:

```bash
python -m pytest -q
```

Latest verified result:

```text
20 passed in 94.35s
```

All 20 automated tests passed on November 5, 2026.