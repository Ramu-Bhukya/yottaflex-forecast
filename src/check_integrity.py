from pathlib import Path
import pandas as pd


DATA_DIR = Path("data/raw")

PRIMARY_KEYS = {
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

FOREIGN_KEYS = [
    ("sales_reps", "territory_id", "territories", "territory_id"),
    ("accounts", "territory_id", "territories", "territory_id"),
    ("opportunities", "account_id", "accounts", "account_id"),
    ("opportunities", "rep_id", "sales_reps", "rep_id"),
    ("opportunities", "stage_id", "stages", "stage_id"),
    ("stage_history", "opportunity_id", "opportunities", "opportunity_id"),
    ("stage_history", "stage_id", "stages", "stage_id"),
    ("activities", "opportunity_id", "opportunities", "opportunity_id"),
    ("activities", "rep_id", "sales_reps", "rep_id"),
    ("quotas", "rep_id", "sales_reps", "rep_id"),
    ("historical_bookings", "opportunity_id", "opportunities", "opportunity_id"),
    ("historical_bookings", "rep_id", "sales_reps", "rep_id"),
    ("forecast_snapshots", "opportunity_id", "opportunities", "opportunity_id"),
    ("forecast_snapshots", "rep_id", "sales_reps", "rep_id"),
    ("forecast_snapshots", "stage_id", "stages", "stage_id"),
]


def check_integrity():
    tables = {
        name: pd.read_csv(DATA_DIR / f"{name}.csv")
        for name in PRIMARY_KEYS
    }

    errors = []

    print("Checking primary keys...")

    for name, key in PRIMARY_KEYS.items():
        df = tables[name]

        if key not in df.columns:
            errors.append(f"{name}: missing primary key column {key}")
            continue

        missing = int(df[key].isna().sum())
        duplicates = int(df[key].duplicated().sum())

        if missing:
            errors.append(f"{name}: {missing} missing primary keys")

        if duplicates:
            errors.append(f"{name}: {duplicates} duplicate primary keys")

    print("Checking foreign keys...")

    for child, child_key, parent, parent_key in FOREIGN_KEYS:
        child_df = tables[child]
        parent_df = tables[parent]

        if child_key not in child_df.columns:
            errors.append(f"{child}: missing column {child_key}")
            continue

        if parent_key not in parent_df.columns:
            errors.append(f"{parent}: missing column {parent_key}")
            continue

        invalid = (
            child_df[child_key].notna()
            & ~child_df[child_key].isin(parent_df[parent_key])
        )

        count = int(invalid.sum())

        if count:
            errors.append(
                f"{child}.{child_key}: {count} invalid references "
                f"to {parent}.{parent_key}"
            )

    print()
    if errors:
        print(f"FAIL: {len(errors)} integrity issues found")
        for error in errors:
            print("-", error)
        raise SystemExit(1)

    print("PASS: All primary-key and foreign-key checks passed.")
    print(f"Tables checked: {len(tables)}")
    print(f"Foreign-key relationships checked: {len(FOREIGN_KEYS)}")


if __name__ == "__main__":
    check_integrity()