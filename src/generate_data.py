import argparse
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 20261022
OUTPUT_DIR = Path("data/raw")


def generate_territories():
    return pd.DataFrame([
        {"territory_id": "TER-001", "territory_name": "North"},
        {"territory_id": "TER-002", "territory_name": "South"},
        {"territory_id": "TER-003", "territory_name": "East"},
        {"territory_id": "TER-004", "territory_name": "West"},
    ])


def generate_sales_reps(count, territories, rng):
    territory_ids = territories["territory_id"].tolist()

    return pd.DataFrame([
        {
            "rep_id": f"REP-{i:06d}",
            "rep_name": f"Sales Rep {i}",
            "territory_id": str(rng.choice(territory_ids)),
            "status": "active",
        }
        for i in range(1, count + 1)
    ])


def generate_accounts(count, territories, rng):
    territory_ids = territories["territory_id"].tolist()

    return pd.DataFrame([
        {
            "account_id": f"ACC-{i:06d}",
            "account_name": f"Customer Company {i}",
            "territory_id": str(rng.choice(territory_ids)),
            "industry": str(rng.choice([
                "Technology", "Healthcare",
                "Finance", "Retail", "Manufacturing"
            ])),
        }
        for i in range(1, count + 1)
    ])


def generate_stages():
    return pd.DataFrame([
        {"stage_id": "STAGE-001", "stage_name": "Prospecting", "probability": 0.10},
        {"stage_id": "STAGE-002", "stage_name": "Qualification", "probability": 0.25},
        {"stage_id": "STAGE-003", "stage_name": "Proposal", "probability": 0.50},
        {"stage_id": "STAGE-004", "stage_name": "Negotiation", "probability": 0.80},
        {"stage_id": "STAGE-005", "stage_name": "Closed Won", "probability": 1.00},
        {"stage_id": "STAGE-006", "stage_name": "Closed Lost", "probability": 0.00},
    ])





def generate_opportunities(count, reps, accounts, stages, rng):
    rep_ids = reps["rep_id"].tolist()
    account_ids = accounts["account_id"].tolist()

    # Only use open sales stages
    open_stages = stages[
        ~stages["stage_name"].isin(["Closed Won", "Closed Lost"])
    ]
    stage_ids = open_stages["stage_id"].tolist()

    opportunities = []

    for i in range(1, count + 1):

        # STEP 1: Generate opportunity creation date
        created_date = pd.Timestamp("2025-01-01") + pd.Timedelta(
            days=int(rng.integers(0, 670))
        )

        # STEP 2: Generate unique opportunity ID
        opportunity_id = f"OPP-{created_date.year}-{i:06d}"

        # STEP 3: Generate expected close date
        sales_cycle_days = int(rng.integers(30, 181))
        close_date = created_date + pd.Timedelta(
            days=sales_cycle_days
        )

        # STEP 4: Generate deal amount
        amount = round(
            float(rng.lognormal(mean=10, sigma=0.9)),
            2
        )

        # STEP 5: Create opportunity record
        opportunities.append({
            "opportunity_id": opportunity_id,
            "account_id": str(rng.choice(account_ids)),
            "rep_id": str(rng.choice(rep_ids)),
            "stage_id": str(rng.choice(stage_ids)),
            "amount": amount,
            "currency": "USD",
            "product": str(rng.choice([
                "AI Platform",
                "Analytics Suite",
                "Enterprise Support",
                "Data Integration"
            ])),
            "created_date": created_date.date().isoformat(),
            "expected_close_date": close_date.date().isoformat(),
            "status": "open",
        })

    return pd.DataFrame(opportunities)
def generate_stage_history(opportunities, rng):
    records = []

    for opp in opportunities.itertuples(index=False):
        created = pd.Timestamp(opp.created_date)
        final_stage_number = int(opp.stage_id.split("-")[-1])

        # The current stage is reached through sequential transitions.
        # The initial stage is always Prospecting.
        elapsed_days = max(
            0,
            (pd.Timestamp(opp.expected_close_date) - created).days
        )

        # Keep stage events within the known opportunity timeline.
        # This is starter logic; actual close-date changes come later.
        max_history_days = max(0, elapsed_days - 1)

        transition_count = final_stage_number - 1

        if transition_count > 0:
            transition_offsets = sorted(
                rng.choice(
                    np.arange(1, max_history_days + 1),
                    size=transition_count,
                    replace=False
                ).tolist()
            )
        else:
            transition_offsets = []

        stage_events = [(0, 1)] + [
            (offset, stage_number)
            for stage_number, offset in enumerate(
                transition_offsets, start=2
            )
        ]

        for sequence, (offset, stage_number) in enumerate(
            stage_events, start=1
        ):
            records.append({
                "stage_history_id": (
                    f"STG-{opp.opportunity_id}-{sequence:03d}"
                ),
                "opportunity_id": opp.opportunity_id,
                "stage_id": f"STAGE-{stage_number:03d}",
                "changed_at": (
                    created + pd.Timedelta(days=offset)
                ).isoformat(),
            })

    return pd.DataFrame(records)
def generate_activities(opportunities, rng):
    records = []
    activity_types = ["call", "email", "meeting", "follow_up"]

    activity_counter = 1

    for opp in opportunities.itertuples(index=False):
        created = pd.Timestamp(opp.created_date)
        expected_close = pd.Timestamp(opp.expected_close_date)

        duration_days = max(
            1, (expected_close - created).days
        )

        activity_count = int(rng.integers(2, 9))

        for _ in range(activity_count):
            offset = int(rng.integers(0, duration_days + 1))
            activity_date = created + pd.Timedelta(days=offset)

            records.append({
                "activity_id": f"ACT-{activity_counter:08d}",
                "opportunity_id": opp.opportunity_id,
                "rep_id": opp.rep_id,
                "activity_type": str(rng.choice(activity_types)),
                "activity_date": activity_date.isoformat(),
                "duration_minutes": int(rng.integers(5, 91)),
                "status": "completed",
            })

            activity_counter += 1

    return pd.DataFrame(records)

def generate_quotas(reps, rng):
    records = []

    # Eight quarters: 2025 Q1 through 2026 Q4
    quarters = [
        (year, quarter)
        for year in [2025, 2026]
        for quarter in [1, 2, 3, 4]
    ]

    for rep in reps.itertuples(index=False):
        # Each representative has a consistent base quota
        base_quota = float(
            rng.uniform(250000, 750000)
        )

        for year, quarter in quarters:
            quarter_label = f"{year}Q{quarter}"

            # Slight seasonal adjustment
            seasonal_factor = {
                1: 0.90,
                2: 1.00,
                3: 0.95,
                4: 1.15,
            }[quarter]

            quota_amount = round(
                base_quota * seasonal_factor,
                2
            )

            records.append({
                "quota_id": (
                    f"QUOTA-{rep.rep_id}-{quarter_label}"
                ),
                "rep_id": rep.rep_id,
                "quarter": quarter_label,
                "quota_amount": quota_amount,
                "currency": "USD",
            })

    return pd.DataFrame(records)
def generate_sales_outcomes(opportunities, rng):
    records = []
    updated_opportunities = opportunities.copy()

    # Simulation cutoff date
    simulation_end = pd.Timestamp("2026-11-04")

    # Conversion probabilities based on sales stage
    stage_probabilities = {
        "STAGE-001": 0.10,
        "STAGE-002": 0.25,
        "STAGE-003": 0.50,
        "STAGE-004": 0.80,
    }

    # Initialize actual close date
    updated_opportunities["actual_close_date"] = None

    for idx, opp in updated_opportunities.iterrows():

        expected_close = pd.Timestamp(
            opp["expected_close_date"]
        )

        # STEP 1: Keep future opportunities open
        if expected_close > simulation_end:
            continue

        # STEP 2: Determine win probability
        probability = stage_probabilities[
            opp["stage_id"]
        ]

        won = bool(rng.random() < probability)

        # STEP 3: Simulate close-date slippage
        # 0–45 days late; no early closes in this starter model
        delay_days = int(rng.integers(0, 46))

        actual_close = expected_close + pd.Timedelta(
            days=delay_days
        )

        # STEP 4: Keep deals open if their actual close
        # occurs after the simulation cutoff
        if actual_close > simulation_end:
            continue

        # STEP 5: Ensure actual close is after creation
        created = pd.Timestamp(opp["created_date"])

        actual_close = max(
            actual_close,
            created
        )

        # STEP 6: Update opportunity status
        if won:
            updated_opportunities.at[idx, "status"] = "won"

            updated_opportunities.at[
                idx, "actual_close_date"
            ] = actual_close.date().isoformat()

            # Create booking for won opportunities only
            records.append({
                "booking_id": f"BOOK-{len(records) + 1:08d}",
                "opportunity_id": opp["opportunity_id"],
                "rep_id": opp["rep_id"],
                "booking_date": actual_close.date().isoformat(),
                "booking_amount": opp["amount"],
                "currency": opp["currency"],
            })

        else:
            updated_opportunities.at[idx, "status"] = "lost"

            updated_opportunities.at[
                idx, "actual_close_date"
            ] = actual_close.date().isoformat()

    # STEP 7: Return updated opportunities and bookings
    historical_bookings = pd.DataFrame(
        records,
        columns=[
            "booking_id",
            "opportunity_id",
            "rep_id",
            "booking_date",
            "booking_amount",
            "currency",
        ]
    )

    return updated_opportunities, historical_bookings
def finalize_stage_history(opportunities, stage_history):
    records = []

    for opp in opportunities.itertuples(index=False):
        if opp.status not in ("won", "lost"):
            continue

        final_stage_id = (
            "STAGE-005" if opp.status == "won"
            else "STAGE-006"
        )

        opp_history = stage_history[
            stage_history["opportunity_id"] == opp.opportunity_id
        ]

        sequence = len(opp_history) + 1

        records.append({
            "stage_history_id": (
                f"STG-{opp.opportunity_id}-{sequence:03d}"
            ),
            "opportunity_id": opp.opportunity_id,
            "stage_id": final_stage_id,
            "changed_at": pd.Timestamp(
                opp.actual_close_date
            ).isoformat(),
        })

    if not records:
        return stage_history

    final_events = pd.DataFrame(records)

    result = pd.concat(
        [stage_history, final_events],
        ignore_index=True
    )

    return result.sort_values(
        ["opportunity_id", "changed_at", "stage_history_id"]
    ).reset_index(drop=True)
def generate_forecast_snapshots(
    opportunities,
    stage_history,
    activities
):
    records = []

    # One snapshot per quarter, for eight quarters
    snapshot_dates = [
        "2025-01-31",
        "2025-04-30",
        "2025-07-31",
        "2025-10-31",
        "2026-01-31",
        "2026-04-30",
        "2026-07-31",
        "2026-10-31",
    ]

    stage_probabilities = {
        "STAGE-001": 0.10,
        "STAGE-002": 0.25,
        "STAGE-003": 0.50,
        "STAGE-004": 0.80,
        "STAGE-005": 1.00,
        "STAGE-006": 0.00,
    }

    history = stage_history.copy()
    history["changed_at"] = pd.to_datetime(
        history["changed_at"]
    )

    activity_data = activities.copy()
    activity_data["activity_date"] = pd.to_datetime(
        activity_data["activity_date"]
    )

    opps = opportunities.copy()
    opps["created_date"] = pd.to_datetime(
        opps["created_date"]
    )
    opps["expected_close_date"] = pd.to_datetime(
        opps["expected_close_date"]
    )
    opps["actual_close_date"] = pd.to_datetime(
        opps["actual_close_date"]
    )

    for snapshot_str in snapshot_dates:
        snapshot_date = pd.Timestamp(snapshot_str)

        quarter = (
            f"{snapshot_date.year}Q"
            f"{snapshot_date.quarter}"
        )

        quarter_end = (
            snapshot_date.to_period("Q").end_time.normalize()
        )

        # Only opportunities created by the snapshot date
        # and not yet closed on that date
        eligible = opps[
            (opps["created_date"] <= snapshot_date)
            &
            (
                opps["actual_close_date"].isna()
                |
                (opps["actual_close_date"] > snapshot_date)
            )
        ]

        # Stage events known by the snapshot date
        known_history = history[
            history["changed_at"] <= snapshot_date
        ]

        latest_stages = (
            known_history.sort_values(
                ["changed_at", "stage_history_id"]
            )
            .drop_duplicates(
                "opportunity_id",
                keep="last"
            )
            .set_index("opportunity_id")["stage_id"]
        )

        # Only activities completed by the snapshot date
        known_activities = activity_data[
            activity_data["activity_date"] <= snapshot_date
        ]

        activity_counts = (
            known_activities.groupby("opportunity_id")
            .size()
        )

        snapshot_counter = 1
        for opp in eligible.itertuples(index=False):

            # Include overdue open opportunities
            # and deals expected to close by quarter end
            if opp.expected_close_date > quarter_end:
                continue

            stage_id = latest_stages.get(
                opp.opportunity_id,
                "STAGE-001"
            )

            probability = stage_probabilities[stage_id]

            activity_count = int(
                activity_counts.get(opp.opportunity_id, 0)
            )

            deal_age_days = (
                snapshot_date - opp.created_date
            ).days

            # Starter weighted-pipeline forecast
            forecast_amount = round(
                float(opp.amount) * probability,
                2
            )
            records.append({
                "forecast_id": (
                    f"FCST-{snapshot_date:%Y-%m-%d}-"
                    f"{snapshot_counter:03d}"
                ),
                "snapshot_date": snapshot_str,
                "quarter": quarter,
                "opportunity_id": opp.opportunity_id,
                "rep_id": opp.rep_id,
                "stage_id": stage_id,
                "deal_age_days": deal_age_days,
                "activity_count": activity_count,
                "opportunity_amount": opp.amount,
                "win_probability": probability,
                "forecast_amount": forecast_amount,
                "currency": opp.currency,
            })

            snapshot_counter += 1

    return pd.DataFrame(
        records,
        columns=[
            "forecast_id",
            "snapshot_date",
            "quarter",
            "opportunity_id",
            "rep_id",
            "stage_id",
            "deal_age_days",
            "activity_count",
            "opportunity_amount",
            "win_probability",
            "forecast_amount",
            "currency",
        ]
    )

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scale",
        choices=["starter", "full"],
        default="starter"
    )
    args = parser.parse_args()

    # Fixed seed for reproducibility
    rng = np.random.default_rng(SEED)

    # Dataset sizes
    rep_count = 20 if args.scale == "starter" else 2000
    account_count = 20 if args.scale == "starter" else 2000
    opportunity_count = 200 if args.scale == "starter" else 20000

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # STEP 1: Generate master data
    territories = generate_territories()

    reps = generate_sales_reps(
        rep_count,
        territories,
        rng
    )

    accounts = generate_accounts(
        account_count,
        territories,
        rng
    )

    stages = generate_stages()

    # STEP 2: Generate opportunities
    opportunities = generate_opportunities(
        opportunity_count,
        reps,
        accounts,
        stages,
        rng
    )

    # STEP 3: Generate stage history
    stage_history = generate_stage_history(
        opportunities,
        rng
    )

    # STEP 4: Generate sales activities
    activities = generate_activities(
        opportunities,
        rng
    )

    # STEP 5: Generate quarterly quotas
    quotas = generate_quotas(
        reps,
        rng
    )

    # STEP 6: Generate sales outcomes and historical bookings
    opportunities, historical_bookings = generate_sales_outcomes(
        opportunities,
        rng
    )
    stage_history = finalize_stage_history(
    opportunities,
    stage_history
)   
    forecast_snapshots = generate_forecast_snapshots(
    opportunities,
    stage_history,
    activities
)

    # STEP 7: Prepare tables for export
    tables = {
        "territories": territories,
        "sales_reps": reps,
        "accounts": accounts,
        "stages": stages,
        "opportunities": opportunities,
        "stage_history": stage_history,
        "activities": activities,
        "quotas": quotas,
        "historical_bookings": historical_bookings,
        "forecast_snapshots": forecast_snapshots,
    }

    # STEP 8: Export CSV files
    for name, df in tables.items():
        path = OUTPUT_DIR / f"{name}.csv"
        df.to_csv(path, index=False)

        print(
            f"Generated {path}: {len(df)} records"
        )

    # STEP 9: Display summary
    print("--------------------------------")
    print("Data generation completed successfully!")
    print(f"Scale: {args.scale}")
    print(f"Total sales reps: {len(reps)}")
    print(f"Total accounts: {len(accounts)}")
    print(f"Total opportunities: {len(opportunities)}")
    print(f"Total stage history: {len(stage_history)}")
    print(f"Total activities: {len(activities)}")
    print(f"Total quotas: {len(quotas)}")
    print(f"Total historical bookings: {len(historical_bookings)}")
    print(f"Total forecast snapshots: {len(forecast_snapshots)}")
    print("--------------------------------")




if __name__ == "__main__":
    main()