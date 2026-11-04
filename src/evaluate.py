from pathlib import Path
import pandas as pd

DATA_DIR = Path("data/raw")
OUTPUT_DIR = Path("data/processed")

# Last date for which simulated outcomes are available.
SIMULATION_END = pd.Timestamp("2026-11-04")


def evaluate_forecasts():
    snapshots = pd.read_csv(
        DATA_DIR / "forecast_snapshots.csv"
    )
    bookings = pd.read_csv(
        DATA_DIR / "historical_bookings.csv"
    )

    snapshots["snapshot_date"] = pd.to_datetime(
        snapshots["snapshot_date"]
    )
    bookings["booking_date"] = pd.to_datetime(
        bookings["booking_date"]
    )

    # A forecast must be made before its outcome.
    # Evaluate bookings strictly after the snapshot date.
    snapshots["quarter_end"] = (
        snapshots["snapshot_date"]
        .dt.to_period("Q")
        .dt.end_time
        .dt.normalize()
    )

    # Join actual bookings to the exact opportunities
    # that appeared in each historical snapshot.
    booking_lookup = (
        bookings.groupby("opportunity_id", as_index=False)
        ["booking_amount"]
        .sum()
    )

    booking_dates = (
        bookings.groupby("opportunity_id", as_index=False)
        ["booking_date"]
        .min()
    )

    booking_lookup = booking_lookup.merge(
        booking_dates,
        on="opportunity_id",
        how="left"
    )

    evaluation = snapshots.merge(
        booking_lookup,
        on="opportunity_id",
        how="left",
        validate="many_to_one"
    )

    # A booking counts only when it occurs
    # after the snapshot and by quarter end.
    within_horizon = (
        (evaluation["booking_date"] >
         evaluation["snapshot_date"])
        &
        (evaluation["booking_date"] <=
         evaluation["quarter_end"])
    )

    evaluation["actual_bookings"] = (
        evaluation["booking_amount"]
        .where(within_horizon, 0)
        .fillna(0)
    )

    # Avoid treating incomplete quarters as final.
    evaluation["is_complete"] = (
        evaluation["quarter_end"] <= SIMULATION_END
    )

    completed = evaluation[
        evaluation["is_complete"]
    ].copy()

    results = completed.groupby(
        "quarter", as_index=False
    ).agg(
        opportunities=("opportunity_id", "count"),
        forecast_amount=("forecast_amount", "sum"),
        actual_bookings=("actual_bookings", "sum")
    )

    results["error"] = (
        results["forecast_amount"]
        - results["actual_bookings"]
    )

    results["absolute_error"] = (
        results["error"].abs()
    )

    results["absolute_percentage_error"] = (
        results["absolute_error"]
        / results["actual_bookings"].replace(0, float("nan"))
        * 100
    )

    results["bias_pct"] = (
        results["error"]
        / results["actual_bookings"].replace(0, float("nan"))
        * 100
    )

    # WAPE at the opportunity level, rather than
    # absolute percentage error on aggregate totals.
    completed["absolute_opportunity_error"] = (
        completed["forecast_amount"]
        - completed["actual_bookings"]
    ).abs()

    wape = completed.groupby("quarter").agg(
        total_absolute_error=(
            "absolute_opportunity_error", "sum"
        ),
        total_actual=("actual_bookings", "sum")
    ).reset_index()

    wape["wape_pct"] = (
        wape["total_absolute_error"]
        / wape["total_actual"].replace(0, float("nan"))
        * 100
    )

    results = results.merge(
        wape[["quarter", "wape_pct"]],
        on="quarter",
        how="left"
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    results.to_csv(
        OUTPUT_DIR / "forecast_accuracy.csv",
        index=False
    )

    evaluation.to_csv(
        OUTPUT_DIR / "forecast_evaluation_detail.csv",
        index=False
    )

    print("Cohort-based forecast evaluation completed!")
    print()
    print(results.round(2).to_string(index=False))
    print()
    print(
        "Excluded incomplete quarters:",
        sorted(
            evaluation.loc[
                ~evaluation["is_complete"], "quarter"
            ].unique().tolist()
        )
    )

    return results


if __name__ == "__main__":
    evaluate_forecasts()