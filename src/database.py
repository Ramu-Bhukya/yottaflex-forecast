
from pathlib import Path
import argparse
import sqlite3

import pandas as pd


DATA_DIR = Path("data/raw")
DATABASE_PATH = Path("data/processed/yottaflex.db")

TABLES = [
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
]

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

FOREIGN_KEYS = {
    "sales_reps": [("territory_id", "territories", "territory_id")],
    "accounts": [("territory_id", "territories", "territory_id")],
    "opportunities": [
        ("account_id", "accounts", "account_id"),
        ("rep_id", "sales_reps", "rep_id"),
        ("stage_id", "stages", "stage_id"),
    ],
    "stage_history": [
        ("opportunity_id", "opportunities", "opportunity_id"),
        ("stage_id", "stages", "stage_id"),
    ],
    "activities": [
        ("opportunity_id", "opportunities", "opportunity_id"),
        ("rep_id", "sales_reps", "rep_id"),
    ],
    "quotas": [("rep_id", "sales_reps", "rep_id")],
    "historical_bookings": [
        ("opportunity_id", "opportunities", "opportunity_id"),
        ("rep_id", "sales_reps", "rep_id"),
    ],
    "forecast_snapshots": [
        ("opportunity_id", "opportunities", "opportunity_id"),
        ("rep_id", "sales_reps", "rep_id"),
        ("stage_id", "stages", "stage_id"),
    ],
}


def sqlite_type(series):
    if pd.api.types.is_integer_dtype(series):
        return "INTEGER"
    if pd.api.types.is_float_dtype(series):
        return "REAL"
    return "TEXT"


def export_database(data_dir=DATA_DIR, database_path=DATABASE_PATH):
    data_dir = Path(data_dir)
    database_path = Path(database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)

    # Use a temporary file so an unsuccessful export does not replace
    # an existing database.
    temporary_path = database_path.with_suffix(".tmp.db")
    temporary_path.unlink(missing_ok=True)

    connection = sqlite3.connect(temporary_path)

    try:
        connection.execute("PRAGMA foreign_keys = ON")

        for table in TABLES:
            frame = pd.read_csv(data_dir / f"{table}.csv")
            primary_key = PRIMARY_KEYS[table]

            columns = []

            for column in frame.columns:
                data_type = sqlite_type(frame[column])
                definition = f'"{column}" {data_type}'

                if column == primary_key:
                    definition += " PRIMARY KEY NOT NULL"

                columns.append(definition)

            for column, parent_table, parent_column in FOREIGN_KEYS.get(
                table, []
            ):
                columns.append(
                    f'FOREIGN KEY ("{column}") '
                    f'REFERENCES "{parent_table}" ("{parent_column}")'
                )

            if table == "forecast_snapshots":
                columns.append(
                    'UNIQUE ("snapshot_date", "opportunity_id")'
                )

            if table == "quotas":
                columns.append('UNIQUE ("rep_id", "quarter")')

            statement = (
                f'CREATE TABLE "{table}" (\n    '
                + ",\n    ".join(columns)
                + "\n)"
            )

            connection.execute(statement)

            placeholders = ", ".join("?" for _ in frame.columns)
            quoted_columns = ", ".join(
                f'"{column}"' for column in frame.columns
            )

            insert_statement = (
                f'INSERT INTO "{table}" ({quoted_columns}) '
                f"VALUES ({placeholders})"
            )

            rows = (
                tuple(
                    None if pd.isna(value) else value
                    for value in row
                )
                for row in frame.itertuples(index=False, name=None)
            )

            connection.executemany(insert_statement, rows)

            print(f"Imported {table}: {len(frame):,} records")

        connection.commit()

        violations = connection.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

        if violations:
            raise ValueError(
                f"Foreign-key violations detected: {violations[:5]}"
            )

        integrity = connection.execute(
            "PRAGMA integrity_check"
        ).fetchone()[0]

        if integrity != "ok":
            raise ValueError(f"SQLite integrity check failed: {integrity}")

    except Exception:
        connection.close()
        temporary_path.unlink(missing_ok=True)
        raise

    connection.close()
    temporary_path.replace(database_path)

    print()
    print("PASS: SQLite export completed.")
    print(f"Database: {database_path}")
    print("Foreign-key and integrity checks passed.")


def main():
    parser = argparse.ArgumentParser(
        description="Export the clean sales dataset to SQLite."
    )
    parser.add_argument("--data-dir", default=str(DATA_DIR))
    parser.add_argument("--database", default=str(DATABASE_PATH))

    args = parser.parse_args()

    export_database(
        data_dir=args.data_dir,
        database_path=args.database,
    )


if __name__ == "__main__":
    main()
