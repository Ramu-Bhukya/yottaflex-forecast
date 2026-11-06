
from pathlib import Path
import pandas as pd

DATA_DIR = Path("data/raw")
OUTPUT_DIR = Path("data/processed")
SIMULATION_END = pd.Timestamp("2026-11-04")


def compare_forecasts():
    forecasts = pd.read_csv(
        OUTPUT_DIR / "improved_forecast_detail.csv"
    )
    bookings = pd.read_csv(
        DATA_DIR / "historical_bookings.csv"
    )

    forecasts["snapshot_date"] = pd.to_datetime(
        forecasts["snapshot_date"]
    )
    bookings["booking_date"] = pd.to_datetime(
        bookings["booking_date"]
    )

    # Exclude quarters that have not fully ended.
    forecasts["quarter_end"] = (
        forecasts["snapshot_date"]
        .dt.to_period("Q")
        .dt.end_time
        .dt.normalize()
    )

    forecasts = forecasts[
        forecasts["quarter_end"] <= SIMULATION_END
    ].copy()

    # Every forecast record must be unique.
    if forecasts["forecast_id"].duplicated().any():
        raise ValueError("Duplicate forecast IDs found")

    # Match each forecast to its opportunity bookings.
    matched = forecasts[
        [
            "forecast_id",
            "opportunity_id",
            "snapshot_date",
            "quarter_end",
        ]
    ].merge(
        bookings[
            [
                "opportunity_id",
                "booking_date",
                "booking_amount",
            ]
        ],
        on="opportunity_id",
        how="left",
    )

    # Count only bookings inside the forecast horizon.
    valid_booking = (
        (matched["booking_date"] > matched["snapshot_date"])
        & (matched["booking_date"] <= matched["quarter_end"])
    )

    matched["eligible_booking_amount"] = (
        matched["booking_amount"]
        .where(valid_booking, 0)
        .fillna(0)
    )

    actuals = (
        matched.groupby("forecast_id", as_index=False)
        .agg(
            actual_bookings=(
                "eligible_booking_amount", "sum"
            )
        )
    )

    detail = forecasts.merge(
        actuals,
        on="forecast_id",
        how="left",
        validate="one_to_one",
    )

    detail["actual_bookings"] = (
        detail["actual_bookings"].fillna(0)
    )

    rows = []

    for quarter, group in detail.groupby("quarter"):
        actual = group["actual_bookings"].sum()

        for method, column in [
            ("Baseline", "baseline_forecast_amount"),
            ("Improved", "improved_forecast_amount"),
        ]:
            predicted = group[column].sum()
            error = predicted - actual

            opportunity_absolute_error = (
                group[column] - group["actual_bookings"]
            ).abs().sum()

            rows.append({
                "quarter": quarter,
                "method": method,
                "opportunities": len(group),
                "forecast_amount": round(predicted, 2),
                "actual_bookings": round(actual, 2),
                "error": round(error, 2),
                "absolute_error": round(abs(error), 2),
                "bias_pct": (
                    round(error / actual * 100, 2)
                    if actual > 0 else float("nan")
                ),
                "wape_pct": (
                    round(
                        opportunity_absolute_error
                        / actual * 100, 2
                    )
                    if actual > 0 else float("nan")
                ),
            })

    results = pd.DataFrame(rows)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    results.to_csv(
        OUTPUT_DIR / "forecast_model_comparison.csv",
        index=False,
    )

    detail.to_csv(
        OUTPUT_DIR / "forecast_comparison_detail.csv",
        index=False,
    )

    print("Forecast comparison completed!")
    print()
    print(results.to_string(index=False))
    print()
    print("Excluded incomplete quarters: 2026Q4")
    print()
    print("Note: WAPE is based on opportunity-level errors.")
    print("High WAPE can occur when actual bookings are low.")

    return results


if __name__ == "__main__":
    compare_forecasts()
