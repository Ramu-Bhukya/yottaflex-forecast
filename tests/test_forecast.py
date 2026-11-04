
import pandas as pd
import pytest

from src.forecast import build_forecast
from src.scenarios import build_scenarios


@pytest.fixture(scope="module")
def forecast_results(tmp_path_factory):
    output_dir = tmp_path_factory.mktemp("forecast_outputs")
    return build_forecast(output_dir=output_dir)


@pytest.fixture(scope="module")
def scenario_results(tmp_path_factory):
    output_dir = tmp_path_factory.mktemp("scenario_outputs")
    return build_scenarios(output_dir=output_dir)


def test_forecast_record_count(forecast_results):
    detail, summary = forecast_results
    snapshots = pd.read_csv("data/raw/forecast_snapshots.csv")

    assert len(detail) == len(snapshots)
    assert not summary.empty


def test_forecast_arithmetic(forecast_results):
    detail, _ = forecast_results

    expected = (
        detail["opportunity_amount"] * detail["win_probability"]
    ).round(2)

    pd.testing.assert_series_equal(
        detail["calculated_forecast_amount"].reset_index(drop=True),
        expected.reset_index(drop=True),
        check_names=False,
    )


def test_forecast_no_missing_segments(forecast_results):
    detail, _ = forecast_results

    assert detail["territory_name"].notna().all()
    assert detail["product"].notna().all()
    assert detail["rep_id"].notna().all()


def test_scenario_record_count(scenario_results):
    detail, summary = scenario_results
    snapshots = pd.read_csv("data/raw/forecast_snapshots.csv")

    assert len(detail) == len(snapshots) * 3
    assert len(summary) == snapshots["snapshot_date"].nunique() * 3


def test_scenario_ordering(scenario_results):
    _, summary = scenario_results

    pivot = summary.pivot(
        index="snapshot_date",
        columns="scenario",
        values="scenario_forecast_amount",
    )

    assert (pivot["pessimistic"] <= pivot["baseline"]).all()
    assert (pivot["baseline"] <= pivot["optimistic"]).all()


def test_baseline_scenario_arithmetic(scenario_results):
    detail, _ = scenario_results

    baseline = detail[detail["scenario"] == "baseline"]

    expected = (
        baseline["opportunity_amount"] * baseline["win_probability"]
    ).round(2)

    pd.testing.assert_series_equal(
        baseline["scenario_forecast_amount"].reset_index(drop=True),
        expected.reset_index(drop=True),
        check_names=False,
    )
