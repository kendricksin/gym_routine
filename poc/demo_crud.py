"""
Lark Base CRUD Demo — walks through a realistic gym tracker scenario.

Creates a Base with two tables (ExerciseCatalog + WorkoutLog), seeds data,
then demonstrates search, update, and batch operations.

The Base is kept alive so you can view it in Lark afterward.
Run with --cleanup to delete it.

Usage:
    uv run --with requests --with python-dotenv python demo_crud.py
    uv run --with requests --with python-dotenv python demo_crud.py --cleanup <app_token>
"""

import os
import sys
import time

import requests
from dotenv import load_dotenv

load_dotenv()

APP_ID = os.environ["LARK_APP_ID"]
APP_SECRET = os.environ["LARK_APP_SECRET"]
API = "https://open.larksuite.com/open-apis"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def auth() -> str:
    r = requests.post(f"{API}/auth/v3/tenant_access_token/internal",
                      json={"app_id": APP_ID, "app_secret": APP_SECRET}).json()
    return r["tenant_access_token"]


def h(token: str) -> dict:
    return {"Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8"}


def call(method, url, token, json=None, label=""):
    resp = getattr(requests, method)(url, headers=h(token), json=json)
    data = resp.json()
    if data["code"] != 0:
        print(f"  FAIL [{label}] code={data['code']} msg={data['msg']}")
        sys.exit(1)
    return data


def text_value(field_val):
    """Lark returns text fields as [{'text': 'x', 'type': 'text'}] from search.
    This normalises to a plain string."""
    if isinstance(field_val, list) and field_val and "text" in field_val[0]:
        return field_val[0]["text"]
    return field_val


def print_records(items):
    for item in items:
        fields = {k: text_value(v) for k, v in item["fields"].items()}
        print(f"    {item['record_id']}  {fields}")


# ---------------------------------------------------------------------------
# Cleanup mode
# ---------------------------------------------------------------------------
if len(sys.argv) >= 3 and sys.argv[1] == "--cleanup":
    token = auth()
    app_token = sys.argv[2]
    r = requests.delete(f"{API}/drive/v1/files/{app_token}?type=bitable",
                        headers=h(token)).json()
    print(f"Delete result: code={r['code']} msg={r['msg']}")
    sys.exit(0)


# ===========================================================================
# DEMO START
# ===========================================================================
print("=" * 60)
print("LARK BASE CRUD DEMO")
print("=" * 60)

token = auth()
now_ms = int(time.time() * 1000)
today_ms = int(time.mktime(time.strptime(time.strftime("%Y-%m-%d"), "%Y-%m-%d")) * 1000)


# ---------------------------------------------------------------------------
# 1. CREATE BASE — app owns it, full write access
# ---------------------------------------------------------------------------
print("\n1. CREATE BASE")
print("-" * 40)
data = call("post", f"{API}/bitable/v1/apps", token,
            json={"name": "Gym Tracker Demo"}, label="create base")
app_token = data["data"]["app"]["app_token"]
base_url = data["data"]["app"].get("url", "")
print(f"  app_token:  {app_token}")
print(f"  open in Lark: {base_url}")


# ---------------------------------------------------------------------------
# 2. CREATE TABLES — with typed fields
# ---------------------------------------------------------------------------
print("\n2. CREATE TABLES")
print("-" * 40)

# ExerciseCatalog
data = call("post", f"{API}/bitable/v1/apps/{app_token}/tables", token, json={
    "table": {
        "name": "ExerciseCatalog",
        "default_view_name": "All Exercises",
        "fields": [
            {"field_name": "name",         "type": 1},   # Text
            {"field_name": "category",     "type": 1},   # Text
            {"field_name": "muscle_group", "type": 1},   # Text
            {"field_name": "equipment",    "type": 1},   # Text
            {"field_name": "big_small",    "type": 1},   # Text
        ],
    }
}, label="create ExerciseCatalog")
catalog_id = data["data"]["table_id"]
print(f"  ExerciseCatalog: {catalog_id}")

# WorkoutLog
data = call("post", f"{API}/bitable/v1/apps/{app_token}/tables", token, json={
    "table": {
        "name": "WorkoutLog",
        "default_view_name": "All Sets",
        "fields": [
            {"field_name": "date",          "type": 5},   # Date
            {"field_name": "session_type",  "type": 1},   # Text
            {"field_name": "exercise_name", "type": 1},   # Text
            {"field_name": "set_number",    "type": 2},   # Number
            {"field_name": "weight_kg",     "type": 2},   # Number
            {"field_name": "reps",          "type": 2},   # Number
            {"field_name": "RPE",           "type": 2},   # Number
            {"field_name": "notes",         "type": 1},   # Text
        ],
    }
}, label="create WorkoutLog")
log_id = data["data"]["table_id"]
print(f"  WorkoutLog:      {log_id}")


# ---------------------------------------------------------------------------
# 3. SEED — batch insert exercises into ExerciseCatalog
# ---------------------------------------------------------------------------
print("\n3. SEED EXERCISE CATALOG (batch create)")
print("-" * 40)

exercises = [
    {"name": "Bench Press",      "category": "push", "muscle_group": "chest",      "equipment": "barbell",    "big_small": "BIG"},
    {"name": "Overhead Press",   "category": "push", "muscle_group": "shoulders",  "equipment": "barbell",    "big_small": "BIG"},
    {"name": "Lateral Raises",   "category": "push", "muscle_group": "shoulders",  "equipment": "dumbbell",   "big_small": "SMALL"},
    {"name": "Cable Fly",        "category": "push", "muscle_group": "chest",      "equipment": "cable",      "big_small": "SMALL"},
    {"name": "Tricep Pushdown",  "category": "push", "muscle_group": "triceps",    "equipment": "cable",      "big_small": "SMALL"},
    {"name": "Pull-ups",         "category": "pull", "muscle_group": "back",       "equipment": "bodyweight", "big_small": "BIG"},
    {"name": "Leg Press",        "category": "legs", "muscle_group": "quads",      "equipment": "machine",    "big_small": "BIG"},
    {"name": "Romanian Deadlift","category": "legs", "muscle_group": "hamstrings", "equipment": "barbell",    "big_small": "BIG"},
]

data = call("post",
    f"{API}/bitable/v1/apps/{app_token}/tables/{catalog_id}/records/batch_create",
    token,
    json={"records": [{"fields": ex} for ex in exercises]},
    label="seed catalog")
print(f"  inserted {len(data['data']['records'])} exercises")


# ---------------------------------------------------------------------------
# 4. LOG A WORKOUT — simulate "Bench 60kg 8, 65kg 8, 65kg 7"
# ---------------------------------------------------------------------------
print("\n4. LOG A WORKOUT (batch create sets)")
print("-" * 40)

bench_sets = [
    {"date": today_ms, "session_type": "push", "exercise_name": "Bench Press", "set_number": 1, "weight_kg": 60,   "reps": 8},
    {"date": today_ms, "session_type": "push", "exercise_name": "Bench Press", "set_number": 2, "weight_kg": 65,   "reps": 8},
    {"date": today_ms, "session_type": "push", "exercise_name": "Bench Press", "set_number": 3, "weight_kg": 65,   "reps": 7},
]
ohp_sets = [
    {"date": today_ms, "session_type": "push", "exercise_name": "Overhead Press", "set_number": 1, "weight_kg": 40, "reps": 10},
    {"date": today_ms, "session_type": "push", "exercise_name": "Overhead Press", "set_number": 2, "weight_kg": 40, "reps": 10},
    {"date": today_ms, "session_type": "push", "exercise_name": "Overhead Press", "set_number": 3, "weight_kg": 40, "reps": 9},
]

all_sets = bench_sets + ohp_sets
data = call("post",
    f"{API}/bitable/v1/apps/{app_token}/tables/{log_id}/records/batch_create",
    token,
    json={"records": [{"fields": s} for s in all_sets]},
    label="log sets")
set_ids = [r["record_id"] for r in data["data"]["records"]]
print(f"  logged {len(set_ids)} sets across 2 exercises")


# ---------------------------------------------------------------------------
# 5. SEARCH — find all Bench Press sets
# ---------------------------------------------------------------------------
print("\n5. SEARCH — Bench Press sets only")
print("-" * 40)

data = call("post",
    f"{API}/bitable/v1/apps/{app_token}/tables/{log_id}/records/search",
    token,
    json={
        "filter": {
            "conjunction": "and",
            "conditions": [
                {"field_name": "exercise_name", "operator": "is", "value": ["Bench Press"]}
            ],
        },
        "sort": [{"field_name": "set_number", "desc": False}],
    },
    label="search bench")
items = data["data"]["items"]
print(f"  found {len(items)} sets:")
print_records(items)

# Calculate volume (what the agent does)
total_volume = 0
top_weight = 0
for item in items:
    w = item["fields"]["weight_kg"]
    r = item["fields"]["reps"]
    total_volume += w * r
    top_weight = max(top_weight, w)
print(f"\n  total_volume = {total_volume}kg")
print(f"  top_set_intensity = {top_weight}kg")


# ---------------------------------------------------------------------------
# 6. SEARCH — all exercises in catalog matching a muscle group
# ---------------------------------------------------------------------------
print("\n6. SEARCH — all 'chest' exercises from catalog")
print("-" * 40)

data = call("post",
    f"{API}/bitable/v1/apps/{app_token}/tables/{catalog_id}/records/search",
    token,
    json={
        "filter": {
            "conjunction": "and",
            "conditions": [
                {"field_name": "muscle_group", "operator": "is", "value": ["chest"]}
            ],
        },
    },
    label="search chest")
print_records(data["data"]["items"])


# ---------------------------------------------------------------------------
# 7. UPDATE — add RPE to the Bench Press sets (post-workout RPE prompt)
# ---------------------------------------------------------------------------
print("\n7. UPDATE — add RPE 8 to all Bench Press sets")
print("-" * 40)

bench_record_ids = [set_ids[i] for i in range(3)]  # first 3 are bench
for rid in bench_record_ids:
    call("put",
        f"{API}/bitable/v1/apps/{app_token}/tables/{log_id}/records/{rid}",
        token,
        json={"fields": {"RPE": 8}},
        label=f"update RPE {rid[:8]}")
print(f"  updated RPE on {len(bench_record_ids)} records")


# ---------------------------------------------------------------------------
# 8. VERIFY — search Bench Press again to confirm RPE was added
# ---------------------------------------------------------------------------
print("\n8. VERIFY — Bench Press sets with RPE")
print("-" * 40)

data = call("post",
    f"{API}/bitable/v1/apps/{app_token}/tables/{log_id}/records/search",
    token,
    json={
        "filter": {
            "conjunction": "and",
            "conditions": [
                {"field_name": "exercise_name", "operator": "is", "value": ["Bench Press"]}
            ],
        },
        "sort": [{"field_name": "set_number", "desc": False}],
    },
    label="verify RPE")
print_records(data["data"]["items"])


# ---------------------------------------------------------------------------
# 9. DELETE — remove one set (simulate correcting a mislog)
# ---------------------------------------------------------------------------
print("\n9. DELETE — remove the last OHP set (mislog correction)")
print("-" * 40)

last_ohp_id = set_ids[-1]
call("delete",
    f"{API}/bitable/v1/apps/{app_token}/tables/{log_id}/records/{last_ohp_id}",
    token,
    label=f"delete {last_ohp_id[:8]}")
print(f"  deleted record {last_ohp_id}")


# ---------------------------------------------------------------------------
# Done — Base stays alive so you can view it in Lark
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("DEMO COMPLETE")
print(f"  Base:          {app_token}")
print(f"  Open in Lark:  {base_url}")
print(f"  Catalog table: {catalog_id}")
print(f"  Log table:     {log_id}")
print()
print("  Data is still there — go check it in Lark!")
print(f"  To clean up:   python demo_crud.py --cleanup {app_token}")
print("=" * 60)
