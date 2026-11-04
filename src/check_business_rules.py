from pathlib import Path

import pandas as pd


DATA_DIR = Path("data/raw")
TOLERANCE = 0.02


def check_business_rules():
    opportunities = pd.read_csv(
        DATA_DIR / "opportunities.csv"
    )
    bookings = pd.read_csv(
        DATA_DIR / "historical_bookings.csv"
    )
    snapshots = pd.read_csv(
        DATA_DIR / "forecast_snapshots.csv"
    )
    history = pd.read_csv(
        DATA_DIR / "stage_history.csv"
    )

    errors = []

    # 1. Booking amounts must be positive.
    invalid_amounts = bookings[
        bookings["booking_amount"] <= 0
    ]

    if not invalid_amounts.empty:
        errors.append(
            f"{len(invalid_amounts)} nonpositive booking amounts"
        )

    # 2. Forecast arithmetic must be consistent.
    expected_forecast = (
        snapshots["opportunity_amount"]
        * snapshots["win_probability"]
    )

    invalid_forecasts = (
        snapshots["forecast_amount"]
        - expected_forecast
    ).abs() > TOLERANCE

    if invalid_forecasts.any():
        errors.append(
            f"{int(invalid_forecasts.sum())} "
            "incorrect forecast calculations"
        )

    # 3. Actual close dates cannot precede creation.
    opportunities["created_date"] = pd.to_datetime(
        opportunities["created_date"]
    )
    opportunities["actual_close_date"] = pd.to_datetime(
        opportunities["actual_close_date"],
        errors="coerce",
    )

    invalid_close_dates = opportunities[
        opportunities["actual_close_date"].notna()
        &
        (
            opportunities["actual_close_date"]
            < opportunities["created_date"]
        )
    ]

    if not invalid_close_dates.empty:
        errors.append(
            f"{len(invalid_close_dates)} "
            "actual close dates before creation"
        )

    # 4. Bookings must belong to won opportunities.
    joined = bookings.merge(
        opportunities[
            ["opportunity_id", "status", "actual_close_date"]
        ],
        on="opportunity_id",
        how="left",
        validate="many_to_one",
    )

    invalid_status = joined[
        joined["status"] != "won"
    ]

    if not invalid_status.empty:
        errors.append(
            f"{len(invalid_status)} "
            "bookings on non-won opportunities"
        )

    # 5. Booking date must match actual close date.
    joined["booking_date"] = pd.to_datetime(
        joined["booking_date"]
    )

    invalid_booking_dates = joined[
        joined["booking_date"]
        != joined["actual_close_date"]
    ]

    if not invalid_booking_dates.empty:
        errors.append(
            f"{len(invalid_booking_dates)} "
            "booking dates do not match close dates"
        )

    # 6. Closed opportunities must have terminal stages.
    terminal_stages = {
        "won": "STAGE-005",
        "lost": "STAGE-006",
    }

    history["changed_at"] = pd.to_datetime(
        history["changed_at"]
    )

    latest = (
        history.sort_values("changed_at")
        .groupby("opportunity_id")
        .tail(1)
        .set_index("opportunity_id")["stage_id"]
    )

    closed = opportunities[
        opportunities["status"].isin(["won", "lost"])
    ].copy()

    closed["final_stage"] = (
        closed["opportunity_id"].map(latest)
    )

    closed["expected_stage"] = (
        closed["status"].map(terminal_stages)
    )

    invalid_terminal = closed[
        closed["final_stage"]
        != closed["expected_stage"]
    ]

    if not invalid_terminal.empty:
        errors.append(
            f"{len(invalid_terminal)} "
            "closed opportunities with incorrect final stages"
        )

    print("Business rule validation")
    print("------------------------")
    print(f"Opportunities: {len(opportunities):,}")
    print(f"Bookings: {len(bookings):,}")
    print(f"Forecast records: {len(snapshots):,}")
    print()

    if errors:
        print(f"FAIL: {len(errors)} business rule failures")
        for error in errors:
            print("-", error)
        raise SystemExit(1)

    print("PASS: All six business rules passed.")


if __name__ == "__main__":
    check_business_rules()