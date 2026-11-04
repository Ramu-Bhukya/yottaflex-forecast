from pathlib import Path
import shutil

import pandas as pd


RAW_DIR = Path("data/raw")
ANOMALY_DIR = Path("data/anomalies")
GROUND_TRUTH_PATH = Path("data/ground_truth.csv")


def inject_anomalies():
    ANOMALY_DIR.mkdir(parents=True, exist_ok=True)

    # Copy clean CSVs without modifying the originals.
    for source in RAW_DIR.glob("*.csv"):
        shutil.copy2(source, ANOMALY_DIR / source.name)

    opportunities_path = ANOMALY_DIR / "opportunities.csv"
    snapshots_path = ANOMALY_DIR / "forecast_snapshots.csv"

    opportunities = pd.read_csv(opportunities_path)
    snapshots = pd.read_csv(snapshots_path)

    ground_truth = []

    # 1. Close date before creation date
    row = opportunities.index[0]
    opp_id = opportunities.loc[row, "opportunity_id"]

    created = pd.to_datetime(
        opportunities.loc[row, "created_date"]
    )

    opportunities.loc[row, "expected_close_date"] = (
        created - pd.Timedelta(days=10)
    ).strftime("%Y-%m-%d")

    ground_truth.append({
        "anomaly_type": "close_before_creation",
        "table": "opportunities",
        "record_id": opp_id,
        "description": "Expected close date precedes creation date",
    })

    # 2. Mixed currency in a USD dataset
    row = opportunities.index[1]
    opp_id = opportunities.loc[row, "opportunity_id"]

    opportunities.loc[row, "currency"] = "EUR"

    ground_truth.append({
        "anomaly_type": "mixed_currency",
        "table": "opportunities",
        "record_id": opp_id,
        "description": "EUR opportunity in USD-only baseline",
    })

    # 3. Stage probability mismatch
    row = snapshots.index[0]
    forecast_id = snapshots.loc[row, "forecast_id"]

    snapshots.loc[row, "win_probability"] = 0.99

    ground_truth.append({
        "anomaly_type": "stage_probability_mismatch",
        "table": "forecast_snapshots",
        "record_id": forecast_id,
        "description": "Win probability does not match stage",
    })

    # 4. Duplicate opportunity in one forecast snapshot.
    # Give the duplicate a new forecast ID so that the
    # duplicate is detected by the business key:
    # (snapshot_date, opportunity_id).
    row = snapshots.index[1]
    duplicate = snapshots.loc[row].copy()

    duplicate["forecast_id"] = "FCST-DUPLICATE-001"

    snapshots = pd.concat(
        [snapshots, duplicate.to_frame().T],
        ignore_index=True,
    )

    ground_truth.append({
        "anomaly_type": "duplicate_opportunity_counted",
        "table": "forecast_snapshots",
        "record_id": duplicate["forecast_id"],
        "description": "Opportunity appears twice in one snapshot",
    })

    # 5. Future leakage: use a stage that was not yet
    # known at the snapshot date.
    history = pd.read_csv(
        RAW_DIR / "stage_history.csv"
    )

    history["changed_at"] = pd.to_datetime(
        history["changed_at"]
    )
    snapshots["snapshot_date"] = pd.to_datetime(
        snapshots["snapshot_date"]
    )

    leakage_found = False

    # for idx, snapshot in snapshots.iterrows():
    reserved_forecast_ids = {
        forecast_id,
        duplicate["forecast_id"],
        snapshots.loc[1, "forecast_id"],
    }

    for idx, snapshot in snapshots.iterrows():

        # Use a different forecast record for leakage.
        if snapshot["forecast_id"] in reserved_forecast_ids:
            continue
        future = history[
            (history["opportunity_id"] ==
             snapshot["opportunity_id"])
            &
            (history["changed_at"] >
             snapshot["snapshot_date"])
            &
            (history["stage_id"] !=
             snapshot["stage_id"])
        ].sort_values("changed_at")

        if future.empty:
            continue

        future_stage = future.iloc[0]["stage_id"]

        # snapshots.loc[idx, "stage_id"] = future_stage
        snapshots.loc[idx, "stage_id"] = future_stage

        # Keep probability consistent with the leaked
        # stage so this is a pure future-leakage anomaly.
        stage_probabilities = {
            "STAGE-001": 0.10,
            "STAGE-002": 0.25,
            "STAGE-003": 0.50,
            "STAGE-004": 0.80,
            "STAGE-005": 1.00,
            "STAGE-006": 0.00,
        }

        leaked_probability = stage_probabilities[future_stage]

        snapshots.loc[idx, "win_probability"] = (
            leaked_probability
        )

        snapshots.loc[idx, "forecast_amount"] = round(
            float(snapshot["opportunity_amount"])
            * leaked_probability,
            2,
        )

        ground_truth.append({
            "anomaly_type": "future_leakage",
            "table": "forecast_snapshots",
            "record_id": snapshot["forecast_id"],
            "description": (
                "Snapshot uses a stage recorded after "
                "its snapshot date"
            ),
        })

        leakage_found = True
        break

    if not leakage_found:
        raise RuntimeError(
            "No suitable future stage transition found"
        )

    # Save corrupted copies.
    opportunities.to_csv(
        opportunities_path,
        index=False,
    )

    snapshots["snapshot_date"] = (
        snapshots["snapshot_date"]
        .dt.strftime("%Y-%m-%d")
    )

    snapshots.to_csv(
        snapshots_path,
        index=False,
    )

    # Ground truth stays outside the feature dataset.
    truth = pd.DataFrame(ground_truth)
    truth.to_csv(
        GROUND_TRUTH_PATH,
        index=False,
    )

    print("Anomaly injection completed!")
    print(f"Injected anomalies: {len(truth)}")
    print()
    print(truth.to_string(index=False))
    print()
    print("Clean data:", RAW_DIR)
    print("Corrupted data:", ANOMALY_DIR)
    print("Labels:", GROUND_TRUTH_PATH)


if __name__ == "__main__":
    inject_anomalies()