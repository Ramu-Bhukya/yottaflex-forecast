
from pathlib import Path
import pandas as pd

RAW = Path("data/raw")
PROCESSED = Path("data/processed")


def generate_segment_accuracy():
    detail = pd.read_csv(
        PROCESSED / "forecast_comparison_detail.csv"
    )

    opportunities = pd.read_csv(
        RAW / "opportunities.csv",
        usecols=["opportunity_id", "product"],
    )

    reps = pd.read_csv(
        RAW / "sales_reps.csv",
        usecols=["rep_id", "territory_id"],
    )

    territories = pd.read_csv(
        RAW / "territories.csv",
        usecols=["territory_id", "territory_name"],
    )

    # Add product and territory information.
    detail = detail.merge(
        opportunities,
        on="opportunity_id",
        how="left",
        validate="many_to_one",
    )

    detail = detail.merge(
        reps,
        on="rep_id",
        how="left",
        validate="many_to_one",
    )

    detail = detail.merge(
        territories,
        on="territory_id",
        how="left",
        validate="many_to_one",
    )

    # Calculate how many days remain in the quarter.
    detail["snapshot_date"] = pd.to_datetime(
        detail["snapshot_date"]
    )
    detail["quarter_end"] = pd.to_datetime(
        detail["quarter_end"]
    )

    detail["horizon_days"] = (
        detail["quarter_end"] - detail["snapshot_date"]
    ).dt.days

    # Create readable horizon groups.
    detail["horizon_group"] = pd.cut(
        detail["horizon_days"],
        bins=[-1, 30, 60, 90, float("inf")],
        labels=["0-30", "31-60", "61-90", "91+"],
    )

    rows = []

    for method, forecast_column in [
        ("Baseline", "baseline_forecast_amount"),
        ("Improved", "improved_forecast_amount"),
    ]:
        current = detail.copy()

        current["predicted"] = current[forecast_column]
        current["absolute_opportunity_error"] = (
            current["predicted"]
            - current["actual_bookings"]
        ).abs()

        # Report each segment type separately.
        for segment_type, column in [
            ("Territory", "territory_name"),
            ("Product", "product"),
            ("Horizon", "horizon_group"),
        ]:
            grouped = current.groupby(
                [column],
                observed=True,
                dropna=False,
            )

            for segment_value, group in grouped:
                actual = group["actual_bookings"].sum()
                predicted = group["predicted"].sum()
                error = predicted - actual

                rows.append({
                    "method": method,
                    "segment_type": segment_type,
                    "segment": str(segment_value),
                    "opportunities": len(group),
                    "forecast_amount": round(predicted, 2),
                    "actual_bookings": round(actual, 2),
                    "error": round(error, 2),
                    "bias_pct": (
                        round(error / actual * 100, 2)
                        if actual > 0
                        else float("nan")
                    ),
                    "wape_pct": (
                        round(
                            group[
                                "absolute_opportunity_error"
                            ].sum() / actual * 100,
                            2,
                        )
                        if actual > 0
                        else float("nan")
                    ),
                })

    results = pd.DataFrame(rows)

    PROCESSED.mkdir(parents=True, exist_ok=True)

    output_path = (
        PROCESSED / "forecast_accuracy_by_segment.csv"
    )
    results.to_csv(output_path, index=False)

    print("Segment accuracy report completed!")
    print()
    print(results.to_string(index=False))
    print()
    print(f"Saved to: {output_path}")

    return results


if __name__ == "__main__":
    generate_segment_accuracy()
