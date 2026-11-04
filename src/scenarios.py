
from pathlib import Path
import argparse
import pandas as pd


DATA_DIR = Path("data/raw")
OUTPUT_DIR = Path("data/processed")

SCENARIOS = {
    "pessimistic": {
        "probability_multiplier": 0.75,
        "slippage_factor": 0.85,
    },
    "baseline": {
        "probability_multiplier": 1.00,
        "slippage_factor": 1.00,
    },
    "optimistic": {
        "probability_multiplier": 1.20,
        "slippage_factor": 1.00,
    },
}


def build_scenarios(data_dir=DATA_DIR, output_dir=OUTPUT_DIR):
    """Generate scenario-based forecasts from historical snapshots."""

    data_dir = Path(data_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    snapshots = pd.read_csv(data_dir / "forecast_snapshots.csv")

    scenario_frames = []

    for scenario_name, assumptions in SCENARIOS.items():
        scenario = snapshots.copy()

        scenario["scenario"] = scenario_name

        scenario["adjusted_probability"] = (
            scenario["win_probability"]
            * assumptions["probability_multiplier"]
        ).clip(lower=0.0, upper=1.0)

        scenario["scenario_forecast_amount"] = (
            scenario["opportunity_amount"]
            * scenario["adjusted_probability"]
            * assumptions["slippage_factor"]
        ).round(2)

        scenario_frames.append(scenario)

    detail = pd.concat(scenario_frames, ignore_index=True)

    summary = (
        detail.groupby(
            ["snapshot_date", "quarter", "scenario"],
            as_index=False,
        )
        .agg(
            opportunity_count=("opportunity_id", "count"),
            pipeline_amount=("opportunity_amount", "sum"),
            scenario_forecast_amount=("scenario_forecast_amount", "sum"),
        )
    )

    summary["pipeline_amount"] = summary["pipeline_amount"].round(2)
    summary["scenario_forecast_amount"] = (
        summary["scenario_forecast_amount"].round(2)
    )

    detail_path = output_dir / "scenario_detail.csv"
    summary_path = output_dir / "scenario_summary.csv"

    detail.to_csv(detail_path, index=False)
    summary.to_csv(summary_path, index=False)

    print("Scenario forecasting completed.")
    print(f"Original forecast records: {len(snapshots):,}")
    print(f"Scenario records: {len(detail):,}")
    print(f"Scenario summary records: {len(summary):,}")
    print(f"Detail output: {detail_path}")
    print(f"Summary output: {summary_path}")

    return detail, summary


def main():
    parser = argparse.ArgumentParser(
        description="Generate pessimistic, baseline, and optimistic forecasts."
    )
    parser.add_argument(
        "--data-dir",
        default=str(DATA_DIR),
    )
    parser.add_argument(
        "--output-dir",
        default=str(OUTPUT_DIR),
    )

    args = parser.parse_args()

    build_scenarios(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()
