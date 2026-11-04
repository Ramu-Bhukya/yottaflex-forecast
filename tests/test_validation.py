import pandas as pd

from src.validate import validate_dataset


EXPECTED_ANOMALIES = {
    "close_before_creation",
    "mixed_currency",
    "stage_probability_mismatch",
    "duplicate_opportunity_counted",
    "future_leakage",
}


def test_clean_data_has_no_violations():
    issues = validate_dataset("data/raw")

    assert issues.empty, (
        "Clean dataset unexpectedly contains violations"
    )


def test_injected_anomalies_are_detected():
    issues = validate_dataset("data/anomalies")

    detected = set(issues["anomaly_type"])

    assert detected == EXPECTED_ANOMALIES, (
        f"Expected {EXPECTED_ANOMALIES}, "
        f"but detected {detected}"
    )


def test_all_five_anomalies_are_detected():
    issues = validate_dataset("data/anomalies")

    assert len(issues) == 5


def test_detected_records_match_ground_truth():
    issues = validate_dataset("data/anomalies")

    ground_truth = pd.read_csv(
        "data/ground_truth.csv"
    )

    expected = set(
        zip(
            ground_truth["anomaly_type"],
            ground_truth["record_id"],
        )
    )

    actual = set(
        zip(
            issues["anomaly_type"],
            issues["record_id"],
        )
    )

    assert actual == expected, (
        "Detected anomaly records do not match "
        "ground truth labels"
    )



    ##python -m pytest tests/test_validation.py -v