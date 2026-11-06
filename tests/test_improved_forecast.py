
import pandas as pd

from src.improved_forecast import build_improved_forecast


def test_future_outcomes_do_not_leak(tmp_path):
    """
    Changing an outcome that occurs in the future
    must not change an earlier forecast.
    """

    data_dir = tmp_path / "raw"
    output_dir = tmp_path / "processed"
    data_dir.mkdir()

    snapshots = pd.DataFrame([
        {
            "forecast_id": "F1",
            "snapshot_date": "2025-01-31",
            "quarter": "2025Q1",
            "opportunity_id": "OPP1",
            "rep_id": "REP1",
            "stage_id": "STAGE-002",
            "deal_age_days": 30,
            "activity_count": 2,
            "opportunity_amount": 10000,
            "win_probability": 0.25,
            "forecast_amount": 2500,
            "currency": "USD",
        }
    ])

    opportunities = pd.DataFrame([
        {
            "opportunity_id": "OPP1",
            "status": "won",
            "actual_close_date": "2025-07-15",
        }
    ])

    snapshots.to_csv(
        data_dir / "forecast_snapshots.csv",
        index=False,
    )
    opportunities.to_csv(
        data_dir / "opportunities.csv",
        index=False,
    )

    first, _ = build_improved_forecast(
        data_dir=data_dir,
        output_dir=output_dir,
    )

    # Change a future outcome from won to lost.
    opportunities["status"] = "lost"
    opportunities.to_csv(
        data_dir / "opportunities.csv",
        index=False,
    )

    second, _ = build_improved_forecast(
        data_dir=data_dir,
        output_dir=output_dir,
    )

    assert (
        first["improved_probability"].iloc[0]
        == second["improved_probability"].iloc[0]
    )

    assert first["historical_deals"].iloc[0] == 0
    assert second["historical_deals"].iloc[0] == 0


def test_forecast_amount_matches_probability(tmp_path):
    """
    The improved forecast amount must equal
    opportunity amount multiplied by probability.
    """

    data_dir = tmp_path / "raw"
    output_dir = tmp_path / "processed"
    data_dir.mkdir()

    snapshots = pd.DataFrame([
        {
            "forecast_id": "F1",
            "snapshot_date": "2025-01-31",
            "quarter": "2025Q1",
            "opportunity_id": "OPP1",
            "rep_id": "REP1",
            "stage_id": "STAGE-002",
            "deal_age_days": 30,
            "activity_count": 2,
            "opportunity_amount": 10000,
            "win_probability": 0.25,
            "forecast_amount": 2500,
            "currency": "USD",
        }
    ])

    opportunities = pd.DataFrame([
        {
            "opportunity_id": "OPP1",
            "status": "open",
            "actual_close_date": None,
        }
    ])

    snapshots.to_csv(
        data_dir / "forecast_snapshots.csv",
        index=False,
    )
    opportunities.to_csv(
        data_dir / "opportunities.csv",
        index=False,
    )

    detail, _ = build_improved_forecast(
        data_dir=data_dir,
        output_dir=output_dir,
    )

    row = detail.iloc[0]

    expected = round(
        row["opportunity_amount"]
        * row["improved_probability"],
        2,
    )

    assert row["improved_forecast_amount"] == expected
    assert 0 <= row["improved_probability"] <= 1
