
from pathlib import Path
import argparse
import pandas as pd


DATA_DIR = Path("data/raw")
OUTPUT_DIR = Path("data/processed")


def build_forecast(data_dir=DATA_DIR, output_dir=OUTPUT_DIR):
    """Build opportunity-level and segmented stage-weighted forecasts."""

    data_dir = Path(data_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    snapshots = pd.read_csv(data_dir / "forecast_snapshots.csv")
    opportunities = pd.read_csv(data_dir / "opportunities.csv")
    reps = pd.read_csv(data_dir / "sales_reps.csv")
    territories = pd.read_csv(data_dir / "territories.csv")

    # Add product and account information without using future outcomes.
    forecast = snapshots.merge(
        opportunities[["opportunity_id", "product", "account_id"]],
        on="opportunity_id",
        how="left",
        validate="many_to_one",
    )

    # Associate each opportunity with its representative and territory.
    forecast = forecast.merge(
        reps[["rep_id", "territory_id"]],
        on="rep_id",
        how="left",
        validate="many_to_one",
    )

    forecast = forecast.merge(
        territories[["territory_id", "territory_name"]],
        on="territory_id",
        how="left",
        validate="many_to_one",
    )

    # Recalculate the baseline forecast explicitly.
    forecast["calculated_forecast_amount"] = (
        forecast["opportunity_amount"] * forecast["win_probability"]
    ).round(2)

    forecast["forecast_difference"] = (
        forecast["forecast_amount"]
        - forecast["calculated_forecast_amount"]
    ).round(2)

    # A snapshot is an independent observation of the pipeline.
    # Never sum different snapshot dates as though they were new revenue.
    group_columns = [
        "snapshot_date",
        "quarter",
        "territory_name",
        "rep_id",
        "product",
    ]

    summary = (
        forecast.groupby(group_columns, dropna=False)
        .agg(
            opportunity_count=("opportunity_id", "count"),
            pipeline_amount=("opportunity_amount", "sum"),
            forecast_amount=("calculated_forecast_amount", "sum"),
        )
        .reset_index()
    )

    summary["pipeline_amount"] = summary["pipeline_amount"].round(2)
    summary["forecast_amount"] = summary["forecast_amount"].round(2)

    detail_path = output_dir / "forecast_detail.csv"
    summary_path = output_dir / "forecast_summary.csv"

    forecast.to_csv(detail_path, index=False)
    summary.to_csv(summary_path, index=False)

    print("Forecast generation completed.")
    print(f"Opportunity-level records: {len(forecast):,}")
    print(f"Segmented summary records: {len(summary):,}")
    print(f"Detail output: {detail_path}")
    print(f"Summary output: {summary_path}")

    return forecast, summary


def main():
    parser = argparse.ArgumentParser(
        description="Generate stage-weighted revenue forecasts."
    )
    parser.add_argument(
        "--data-dir",
        default=str(DATA_DIR),
        help="Directory containing input CSV files.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(OUTPUT_DIR),
        help="Directory for forecast outputs.",
    )

    args = parser.parse_args()

    build_forecast(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()
