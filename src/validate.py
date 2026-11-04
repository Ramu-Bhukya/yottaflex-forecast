from pathlib import Path
import argparse

import pandas as pd


STAGE_PROBABILITIES = {
    "STAGE-001": 0.10,
    "STAGE-002": 0.25,
    "STAGE-003": 0.50,
    "STAGE-004": 0.80,
    "STAGE-005": 1.00,
    "STAGE-006": 0.00,
}


def validate_dataset(data_dir):
    data_dir = Path(data_dir)

    opportunities = pd.read_csv(
        data_dir / "opportunities.csv"
    )
    snapshots = pd.read_csv(
        data_dir / "forecast_snapshots.csv"
    )
    history = pd.read_csv(
        data_dir / "stage_history.csv"
    )

    issues = []

    def report(rule, table, record_id, description):
        issues.append({
            "anomaly_type": rule,
            "table": table,
            "record_id": str(record_id),
            "description": description,
        })

    # RULE 1: Expected close cannot precede creation.
    opportunities["created_date"] = pd.to_datetime(
        opportunities["created_date"]
    )
    opportunities["expected_close_date"] = pd.to_datetime(
        opportunities["expected_close_date"]
    )

    invalid_dates = opportunities[
        opportunities["expected_close_date"]
        < opportunities["created_date"]
    ]

    for row in invalid_dates.itertuples(index=False):
        report(
            "close_before_creation",
            "opportunities",
            row.opportunity_id,
            "Expected close date is before creation date",
        )

    # RULE 2: Currency must match USD baseline.
    invalid_currency = opportunities[
        opportunities["currency"] != "USD"
    ]

    for row in invalid_currency.itertuples(index=False):
        report(
            "mixed_currency",
            "opportunities",
            row.opportunity_id,
            "Unexpected currency",
        )

    # RULE 3: Probability must match the stage.
    snapshots["expected_probability"] = (
        snapshots["stage_id"].map(STAGE_PROBABILITIES)
    )

    invalid_probabilities = snapshots[
        snapshots["expected_probability"].isna()
        |
        (
            (
                snapshots["win_probability"]
                - snapshots["expected_probability"]
            ).abs() > 0.000001
        )
    ]

    for row in invalid_probabilities.itertuples(index=False):
        report(
            "stage_probability_mismatch",
            "forecast_snapshots",
            row.forecast_id,
            "Probability does not match stage",
        )

    # RULE 4: An opportunity may appear only once
    # per snapshot date.
    duplicates = snapshots[
        snapshots.duplicated(
            subset=["snapshot_date", "opportunity_id"],
            keep="first",
        )
    ]

    for row in duplicates.itertuples(index=False):
        report(
            "duplicate_opportunity_counted",
            "forecast_snapshots",
            row.forecast_id,
            "Duplicate opportunity within snapshot",
        )

    # RULE 5: Snapshot stage must equal the latest
    # stage known as of the snapshot date.
    history["changed_at"] = pd.to_datetime(
        history["changed_at"]
    )

    snapshots["snapshot_date"] = pd.to_datetime(
        snapshots["snapshot_date"]
    )

    # Snapshot dates represent end-of-day cutoffs.
    # This avoids accidentally excluding same-day
    # stage changes due to timestamp precision.
    history["changed_date"] = (
        history["changed_at"].dt.normalize()
    )

    history_by_opp = {
        opp_id: group.sort_values(
            ["changed_at", "stage_history_id"]
        )
        for opp_id, group in history.groupby(
            "opportunity_id"
        )
    }

    for row in snapshots.itertuples(index=False):
        opp_history = history_by_opp.get(
            row.opportunity_id
        )

        if opp_history is None:
            continue

        known_history = opp_history[
            opp_history["changed_date"]
            <= row.snapshot_date
        ]

        if known_history.empty:
            continue

        expected_stage = (
            known_history.iloc[-1]["stage_id"]
        )

        if row.stage_id != expected_stage:
            report(
                "future_leakage",
                "forecast_snapshots",
                row.forecast_id,
                (
                    f"Snapshot stage {row.stage_id} "
                    f"differs from as-of stage "
                    f"{expected_stage}"
                ),
            )

    results = pd.DataFrame(
        issues,
        columns=[
            "anomaly_type",
            "table",
            "record_id",
            "description",
        ],
    )

    print(f"\nDataset: {data_dir}")
    print(f"Opportunities: {len(opportunities)}")
    print(f"Forecast records: {len(snapshots)}")
    print(f"Validation issues: {len(results)}")

    if results.empty:
        print("PASS: No issues detected.")
    else:
        print()
        print(results.to_string(index=False))

    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data-dir",
        default="data/raw",
        help="Directory containing CSV files",
    )

    args = parser.parse_args()
    validate_dataset(args.data_dir)


if __name__ == "__main__":
    main()
    