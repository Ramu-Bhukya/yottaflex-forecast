
import pandas as pd

RAW = "data/raw/"

snapshots = pd.read_csv(
    RAW + "forecast_snapshots.csv",
    parse_dates=["snapshot_date"],
)

history = pd.read_csv(
    RAW + "stage_history.csv",
    parse_dates=["changed_at"],
)

activities = pd.read_csv(
    RAW + "activities.csv",
    parse_dates=["activity_date"],
)

opportunities = pd.read_csv(
    RAW + "opportunities.csv",
    parse_dates=["created_date"],
)

print("Checking historical point-in-time correctness...")
print()

# 1. Verify that opportunities existed at snapshot time.
created = snapshots.merge(
    opportunities[["opportunity_id", "created_date"]],
    on="opportunity_id",
    how="left",
    validate="many_to_one",
)

future_opportunities = (
    created["created_date"].isna()
    | (created["created_date"] > created["snapshot_date"])
).sum()

# 2. Reconstruct each opportunity's stage as of the snapshot.
stage_events = history.merge(
    snapshots[
        ["forecast_id", "opportunity_id", "snapshot_date"]
    ],
    on="opportunity_id",
    how="inner",
)

stage_events = stage_events[
    stage_events["changed_at"]
    <= stage_events["snapshot_date"]
]

stage_events = stage_events.sort_values(
    ["forecast_id", "changed_at", "stage_history_id"]
)

latest_stages = stage_events.drop_duplicates(
    "forecast_id",
    keep="last",
)[["forecast_id", "stage_id"]]

latest_stages = latest_stages.rename(
    columns={"stage_id": "expected_stage_id"}
)

stage_check = snapshots.merge(
    latest_stages,
    on="forecast_id",
    how="left",
    validate="one_to_one",
)

missing_stage_history = (
    stage_check["expected_stage_id"].isna()
).sum()

stage_mismatches = (
    stage_check["expected_stage_id"].notna()
    & (
        stage_check["stage_id"]
        != stage_check["expected_stage_id"]
    )
).sum()

# 3. Recalculate activity counts using only past activities.
activity_events = activities.merge(
    snapshots[
        ["forecast_id", "opportunity_id", "snapshot_date"]
    ],
    on="opportunity_id",
    how="inner",
)

past_activities = activity_events[
    activity_events["activity_date"]
    <= activity_events["snapshot_date"]
]

activity_counts = (
    past_activities.groupby("forecast_id")
    .size()
    .rename("expected_activity_count")
    .reset_index()
)

activity_check = snapshots.merge(
    activity_counts,
    on="forecast_id",
    how="left",
    validate="one_to_one",
)

activity_check["expected_activity_count"] = (
    activity_check["expected_activity_count"]
    .fillna(0)
    .astype(int)
)

activity_mismatches = (
    activity_check["activity_count"]
    != activity_check["expected_activity_count"]
).sum()

# 4. Recalculate deal age.
age_check = created.copy()

age_check["expected_age"] = (
    age_check["snapshot_date"]
    - age_check["created_date"]
).dt.days

age_mismatches = (
    age_check["deal_age_days"]
    != age_check["expected_age"]
).sum()

print("Total snapshots:", len(snapshots))
print("Opportunities created after snapshot:", future_opportunities)
print("Snapshots missing historical stage:", missing_stage_history)
print("Stage mismatches:", stage_mismatches)
print("Activity count mismatches:", activity_mismatches)
print("Deal age mismatches:", age_mismatches)
print()

results = [
    future_opportunities,
    missing_stage_history,
    stage_mismatches,
    activity_mismatches,
    age_mismatches,
]

if all(value == 0 for value in results):
    print("PASS: All historical snapshot checks passed.")
else:
    print("REVIEW: Historical snapshot inconsistencies found.")
    print("These may reflect data-generation rules or leakage.")
