
from pathlib import Path

import pandas as pd
import pytest


DATA_DIR = Path("data/raw")


@pytest.fixture(scope="module")
def tables():
    return {
        path.stem: pd.read_csv(path)
        for path in DATA_DIR.glob("*.csv")
    }


def test_all_ten_tables_exist(tables):
    expected = {
        "territories",
        "sales_reps",
        "accounts",
        "stages",
        "opportunities",
        "stage_history",
        "activities",
        "quotas",
        "historical_bookings",
        "forecast_snapshots",
    }

    assert set(tables) == expected


def test_full_scale_record_counts(tables):
    assert len(tables["sales_reps"]) == 2000
    assert len(tables["accounts"]) == 2000
    assert len(tables["opportunities"]) == 20000
    assert len(tables["territories"]) == 4
    assert len(tables["stages"]) == 6
    assert len(tables["quotas"]) == 16000


def test_primary_key_uniqueness(tables):
    primary_keys = {
        "territories": "territory_id",
        "sales_reps": "rep_id",
        "accounts": "account_id",
        "stages": "stage_id",
        "opportunities": "opportunity_id",
        "stage_history": "stage_history_id",
        "activities": "activity_id",
        "quotas": "quota_id",
        "historical_bookings": "booking_id",
        "forecast_snapshots": "forecast_id",
    }

    for table_name, primary_key in primary_keys.items():
        frame = tables[table_name]

        assert frame[primary_key].notna().all(), table_name
        assert frame[primary_key].is_unique, table_name


def test_expected_close_dates(tables):
    opportunities = tables["opportunities"]

    created = pd.to_datetime(opportunities["created_date"])
    expected = pd.to_datetime(opportunities["expected_close_date"])

    assert (expected >= created).all()


def test_forecast_snapshot_uniqueness(tables):
    snapshots = tables["forecast_snapshots"]

    duplicates = snapshots.duplicated(
        subset=["snapshot_date", "opportunity_id"]
    )

    assert not duplicates.any()


def test_quarterly_quota_uniqueness(tables):
    quotas = tables["quotas"]

    duplicates = quotas.duplicated(
        subset=["rep_id", "quarter"]
    )

    assert not duplicates.any()


def test_clean_currency_consistency(tables):
    for table_name, frame in tables.items():
        if "currency" in frame.columns:
            assert set(frame["currency"].dropna()) == {"USD"}, table_name



def test_manifest_matches_csv_counts(tables):
    import hashlib
    import json

    manifest_path = Path("data/manifest.json")
    assert manifest_path.exists(), "Manifest file is missing"

    with manifest_path.open(encoding="utf-8") as file:
        manifest = json.load(file)

    assert manifest["seed"] == 20261022

    manifest_files = manifest["files"]
    assert len(manifest_files) == 10

    recorded_names = [entry["file"] for entry in manifest_files]

    assert len(recorded_names) == len(set(recorded_names))

    expected_names = {f"{name}.csv" for name in tables}
    assert set(recorded_names) == expected_names

    for entry in manifest_files:
        filename = entry["file"]
        csv_path = DATA_DIR / filename
        table_name = csv_path.stem

        assert csv_path.exists(), f"Missing file: {filename}"
        assert entry["rows"] == len(tables[table_name]), (
            f"Incorrect row count: {filename}"
        )

        sha256 = hashlib.sha256()

        with csv_path.open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                sha256.update(chunk)

        assert entry["sha256"] == sha256.hexdigest(), (
            f"SHA-256 mismatch: {filename}"
        )

