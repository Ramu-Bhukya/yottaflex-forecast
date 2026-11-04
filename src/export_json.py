
from pathlib import Path
import argparse
import json

import pandas as pd


DATA_DIR = Path("data/raw")
OUTPUT_DIR = Path("data/processed/json")

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


def export_json(data_dir=DATA_DIR, output_dir=OUTPUT_DIR):
    data_dir = Path(data_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for table in TABLES:
        csv_path = data_dir / f"{table}.csv"
        json_path = output_dir / f"{table}.json"

        frame = pd.read_csv(csv_path)

        # Convert missing CSV values into JSON null values.
        records = json.loads(
            frame.to_json(orient="records", date_format="iso")
        )

        with json_path.open("w", encoding="utf-8") as file:
            json.dump(records, file, indent=2, ensure_ascii=False)

        print(f"Exported {table}: {len(records):,} records")

    print()
    print("PASS: JSON export completed.")
    print(f"Output directory: {output_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="Export all ten sales tables as JSON."
    )
    parser.add_argument("--data-dir", default=str(DATA_DIR))
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))

    args = parser.parse_args()

    export_json(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()
