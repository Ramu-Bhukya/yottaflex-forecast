
from pathlib import Path
import pandas as pd

DATA_DIR = Path("data/raw")
OUTPUT_DIR = Path("data/processed")


def build_improved_forecast(
    data_dir=DATA_DIR,
    output_dir=OUTPUT_DIR,
):
    data_dir = Path(data_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    snapshots = pd.read_csv(
        data_dir / "forecast_snapshots.csv"
    )
    opportunities = pd.read_csv(
        data_dir / "opportunities.csv"
    )

    snapshots["snapshot_date"] = pd.to_datetime(
        snapshots["snapshot_date"]
    )
    opportunities["actual_close_date"] = pd.to_datetime(
        opportunities["actual_close_date"],
        errors="coerce",
    )

    # Keep outcome information separate from the
    # information available for each forecast.
    outcomes = opportunities[
        ["opportunity_id", "status", "actual_close_date"]
    ].copy()

    # Historical observations that may become training
    # examples once their actual outcomes are known.
    history = snapshots[
        ["opportunity_id", "snapshot_date", "stage_id"]
    ].merge(
        outcomes,
        on="opportunity_id",
        how="left",
        validate="many_to_one",
    )

    # A historical observation must predate its outcome.
    history = history[
        history["actual_close_date"].notna()
        & history["status"].isin(["won", "lost"])
        & (
            history["snapshot_date"]
            < history["actual_close_date"]
        )
    ].copy()

    # Avoid counting repeated observations of the same
    # opportunity at the same stage multiple times.
    history = (
        history.sort_values("snapshot_date")
        .drop_duplicates(
            ["opportunity_id", "stage_id"],
            keep="last",
        )
    )

    history["is_won"] = (
        history["status"] == "won"
    ).astype(int)

    results = []

    for snapshot_date, current in snapshots.groupby(
        "snapshot_date", sort=True
    ):
        current = current.copy()

        # Only outcomes already known on this date.
        past = history[
            history["actual_close_date"] <= snapshot_date
        ]

        conversion = (
            past.groupby("stage_id")
            .agg(
                historical_wins=("is_won", "sum"),
                historical_deals=("is_won", "count"),
            )
            .reset_index()
        )

        current = current.merge(
            conversion,
            on="stage_id",
            how="left",
            validate="many_to_one",
        )

        current["historical_wins"] = (
            current["historical_wins"]
            .fillna(0)
            .astype(int)
        )
        current["historical_deals"] = (
            current["historical_deals"]
            .fillna(0)
            .astype(int)
        )

        # Original baseline forecast.
        current["baseline_forecast_amount"] = (
            current["opportunity_amount"]
            * current["win_probability"]
        ).round(2)

        # Smooth historical conversion rates toward
        # the baseline when historical evidence is scarce.
        prior_strength = 20

        current["historical_probability"] = (
            (
                current["historical_wins"]
                + prior_strength
                * current["win_probability"]
            )
            / (
                current["historical_deals"]
                + prior_strength
            )
        )

        # Small, documented heuristic adjustments.
        # These are assumptions, not learned coefficients.
        age_adjustment = (
            (current["deal_age_days"] - 120)
            .clip(lower=0)
            / 120
            * 0.05
        ).clip(upper=0.10)

        activity_adjustment = (
            current["activity_count"]
            .clip(lower=0, upper=10)
            / 10
            * 0.05
        )

        current["improved_probability"] = (
            current["historical_probability"]
            - age_adjustment
            + activity_adjustment
        ).clip(lower=0, upper=1)

        # Preserve the meaning of terminal stages.
        current.loc[
            current["win_probability"] == 0,
            "improved_probability",
        ] = 0

        current.loc[
            current["win_probability"] == 1,
            "improved_probability",
        ] = 1

        current["improved_forecast_amount"] = (
            current["opportunity_amount"]
            * current["improved_probability"]
        ).round(2)

        results.append(current)

    detail = pd.concat(
        results, ignore_index=True
    )

    summary = (
        detail.groupby(
            ["snapshot_date", "quarter"],
            as_index=False,
        )
        .agg(
            opportunity_count=("opportunity_id", "count"),
            baseline_forecast=(
                "baseline_forecast_amount", "sum"
            ),
            improved_forecast=(
                "improved_forecast_amount", "sum"
            ),
        )
    )

    detail.to_csv(
        output_dir / "improved_forecast_detail.csv",
        index=False,
    )
    summary.to_csv(
        output_dir / "improved_forecast_summary.csv",
        index=False,
    )

    print("Improved forecast completed.")
    print(f"Opportunity records: {len(detail):,}")
    print(f"Snapshot summaries: {len(summary):,}")
    print(summary.to_string(index=False))

    return detail, summary


if __name__ == "__main__":
    build_improved_forecast()
