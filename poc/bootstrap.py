"""
Bootstrap — creates the Gym Tracker Base, all 7 tables, seeds data,
shares with the user, and writes IDs back to .env.

Usage:
    uv run --with requests --with python-dotenv python poc/bootstrap.py

Requires .env with: LARK_APP_ID, LARK_APP_SECRET, LARK_OWNER_EMAIL
"""

import os
import re
import sys
import time

import requests
from dotenv import load_dotenv

load_dotenv()

APP_ID = os.environ["LARK_APP_ID"]
APP_SECRET = os.environ["LARK_APP_SECRET"]
OWNER_EMAIL = os.environ.get("LARK_OWNER_EMAIL", "")
API = "https://open.larksuite.com/open-apis"
ENV_PATH = os.path.join(os.path.dirname(__file__), "..", ".env")


def auth() -> str:
    r = requests.post(f"{API}/auth/v3/tenant_access_token/internal",
                      json={"app_id": APP_ID, "app_secret": APP_SECRET}).json()
    if r.get("code", -1) != 0:
        print(f"[AUTH FAILED] {r}")
        sys.exit(1)
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


def update_env(key: str, value: str):
    """Write or update a key in the .env file."""
    env_path = os.path.abspath(ENV_PATH)
    if not os.path.exists(env_path):
        with open(env_path, "a") as f:
            f.write(f"{key}={value}\n")
        return

    with open(env_path, "r") as f:
        content = f.read()

    pattern = rf"^{re.escape(key)}=.*$"
    if re.search(pattern, content, re.MULTILINE):
        content = re.sub(pattern, f"{key}={value}", content, flags=re.MULTILINE)
    else:
        content += f"\n{key}={value}\n"

    with open(env_path, "w") as f:
        f.write(content)


# ============================================================================
print("=" * 60)
print("BOOTSTRAP — Gym Tracker Lark Base")
print("=" * 60)

token = auth()
print("[AUTH OK]")

today_ms = int(time.mktime(time.strptime(time.strftime("%Y-%m-%d"), "%Y-%m-%d")) * 1000)

# --------------------------------------------------------------------------
# 1. Create Base
# --------------------------------------------------------------------------
print("\n1. Creating Base...")
data = call("post", f"{API}/bitable/v1/apps", token,
            json={"name": "Gym Tracker"}, label="create base")
app_token = data["data"]["app"]["app_token"]
base_url = data["data"]["app"].get("url", "")
print(f"   app_token: {app_token}")
print(f"   url: {base_url}")
update_env("LARK_APP_TOKEN", app_token)

# --------------------------------------------------------------------------
# 2. Create tables
# --------------------------------------------------------------------------
print("\n2. Creating tables...")

TABLE_DEFS = {
    "LARK_TABLE_WORKOUT_LOG": {
        "name": "WorkoutLog",
        "fields": [
            {"field_name": "date",          "type": 5},
            {"field_name": "session_type",  "type": 1},
            {"field_name": "exercise_name", "type": 1},
            {"field_name": "set_number",    "type": 2},
            {"field_name": "weight_kg",     "type": 2},
            {"field_name": "reps",          "type": 2},
            {"field_name": "RPE",           "type": 2},
            {"field_name": "notes",         "type": 1},
        ],
    },
    "LARK_TABLE_EXERCISE_HISTORY": {
        "name": "ExerciseHistory",
        "fields": [
            {"field_name": "exercise",              "type": 1},
            {"field_name": "last_date",             "type": 5},
            {"field_name": "last_weight",           "type": 2},
            {"field_name": "last_reps",             "type": 2},
            {"field_name": "last_total_volume",     "type": 2},
            {"field_name": "last_top_set_intensity","type": 2},
            {"field_name": "expected_weight",       "type": 2},
            {"field_name": "expected_reps_per_set", "type": 2},
            {"field_name": "session_count",         "type": 2},
            {"field_name": "streak",                "type": 2},
            {"field_name": "consecutive_rpe_10",    "type": 2},
            {"field_name": "stall_nudge_sent",      "type": 7},
        ],
    },
    "LARK_TABLE_SESSION_SEQUENCE": {
        "name": "SessionSequence",
        "fields": [
            {"field_name": "session_number", "type": 2},
            {"field_name": "session_type",   "type": 1},
            {"field_name": "date",           "type": 5},
            {"field_name": "completed",      "type": 7},
        ],
    },
    "LARK_TABLE_SESSION_TEMPLATES": {
        "name": "SessionTemplates",
        "fields": [
            {"field_name": "session_type",  "type": 1},
            {"field_name": "exercise_name", "type": 1},
            {"field_name": "order",         "type": 2},
            {"field_name": "sets",          "type": 2},
            {"field_name": "reps_target",   "type": 1},
            {"field_name": "big_small",     "type": 1},
        ],
    },
    "LARK_TABLE_EXERCISE_CATALOG": {
        "name": "ExerciseCatalog",
        "fields": [
            {"field_name": "name",         "type": 1},
            {"field_name": "category",     "type": 1},
            {"field_name": "muscle_group", "type": 1},
            {"field_name": "primary",      "type": 7},
            {"field_name": "equipment",    "type": 1},
            {"field_name": "big_small",    "type": 1},
        ],
    },
    "LARK_TABLE_PROGRESS": {
        "name": "Progress",
        "fields": [
            {"field_name": "date",                "type": 5},
            {"field_name": "session_type",        "type": 1},
            {"field_name": "exercises_completed", "type": 2},
            {"field_name": "total_volume",        "type": 2},
            {"field_name": "first_exercise_time", "type": 5},
            {"field_name": "last_exercise_time",  "type": 5},
            {"field_name": "duration_minutes",    "type": 2},
            {"field_name": "notes",               "type": 1},
        ],
    },
    "LARK_TABLE_BODY_LOG": {
        "name": "BodyLog",
        "fields": [
            {"field_name": "log_date",    "type": 5},
            {"field_name": "weight_kg",   "type": 2},
            {"field_name": "bodyfat_pct", "type": 2},
            {"field_name": "notes",       "type": 1},
        ],
    },
}

table_ids = {}
for env_key, defn in TABLE_DEFS.items():
    data = call("post", f"{API}/bitable/v1/apps/{app_token}/tables", token,
                json={"table": {"name": defn["name"], "default_view_name": "Default", "fields": defn["fields"]}},
                label=f"create {defn['name']}")
    tid = data["data"]["table_id"]
    table_ids[env_key] = tid
    update_env(env_key, tid)
    print(f"   {defn['name']:25s} → {tid}")

# --------------------------------------------------------------------------
# 3. Seed ExerciseCatalog (35 exercises from SPEC § 4)
# --------------------------------------------------------------------------
print("\n3. Seeding ExerciseCatalog...")

EXERCISES = [
    {"name": "Bench Press",              "category": "push", "muscle_group": "chest",      "primary": True,  "equipment": "barbell",    "big_small": "BIG"},
    {"name": "Incline Bench Press",      "category": "push", "muscle_group": "chest",      "primary": True,  "equipment": "barbell",    "big_small": "BIG"},
    {"name": "Chest Press Machine",      "category": "push", "muscle_group": "chest",      "primary": True,  "equipment": "machine",    "big_small": "BIG"},
    {"name": "Cable Fly",                "category": "push", "muscle_group": "chest",      "primary": False, "equipment": "cable",      "big_small": "SMALL"},
    {"name": "Pec Deck",                 "category": "push", "muscle_group": "chest",      "primary": False, "equipment": "machine",    "big_small": "SMALL"},
    {"name": "Overhead Press",           "category": "push", "muscle_group": "shoulders",  "primary": True,  "equipment": "barbell",    "big_small": "BIG"},
    {"name": "Shoulder Press Machine",   "category": "push", "muscle_group": "shoulders",  "primary": True,  "equipment": "machine",    "big_small": "BIG"},
    {"name": "Lateral Raises",           "category": "push", "muscle_group": "shoulders",  "primary": False, "equipment": "dumbbell",   "big_small": "SMALL"},
    {"name": "Tricep Pushdown",          "category": "push", "muscle_group": "triceps",    "primary": False, "equipment": "cable",      "big_small": "SMALL"},
    {"name": "Overhead Tricep Extension","category": "push", "muscle_group": "triceps",    "primary": False, "equipment": "dumbbell",   "big_small": "SMALL"},
    {"name": "Skull Crushers",           "category": "push", "muscle_group": "triceps",    "primary": False, "equipment": "barbell",    "big_small": "SMALL"},
    {"name": "Pull-ups",                 "category": "pull", "muscle_group": "back",       "primary": True,  "equipment": "bodyweight", "big_small": "BIG"},
    {"name": "Lat Pulldown",             "category": "pull", "muscle_group": "back",       "primary": True,  "equipment": "cable",      "big_small": "BIG"},
    {"name": "Seated Cable Row",         "category": "pull", "muscle_group": "back",       "primary": False, "equipment": "cable",      "big_small": "SMALL"},
    {"name": "Single Arm Dumbbell Row",  "category": "pull", "muscle_group": "back",       "primary": False, "equipment": "dumbbell",   "big_small": "SMALL"},
    {"name": "Face Pulls",               "category": "pull", "muscle_group": "rear delts", "primary": False, "equipment": "cable",      "big_small": "SMALL"},
    {"name": "Rear Delt Flyes",          "category": "pull", "muscle_group": "rear delts", "primary": False, "equipment": "dumbbell",   "big_small": "SMALL"},
    {"name": "Bicep Curl Machine",       "category": "pull", "muscle_group": "biceps",     "primary": False, "equipment": "machine",    "big_small": "SMALL"},
    {"name": "Dumbbell Bicep Curls",     "category": "pull", "muscle_group": "biceps",     "primary": False, "equipment": "dumbbell",   "big_small": "SMALL"},
    {"name": "Hammer Curls",             "category": "pull", "muscle_group": "biceps",     "primary": False, "equipment": "dumbbell",   "big_small": "SMALL"},
    {"name": "Plank",                    "category": "pull", "muscle_group": "core",       "primary": False, "equipment": "bodyweight", "big_small": "SMALL"},
    {"name": "Ab Wheel",                 "category": "pull", "muscle_group": "core",       "primary": False, "equipment": "ab wheel",   "big_small": "SMALL"},
    {"name": "Leg Press",                "category": "legs", "muscle_group": "quads",      "primary": True,  "equipment": "machine",    "big_small": "BIG"},
    {"name": "Barbell Squat",            "category": "legs", "muscle_group": "quads",      "primary": True,  "equipment": "barbell",    "big_small": "BIG"},
    {"name": "Hack Squat Machine",       "category": "legs", "muscle_group": "quads",      "primary": True,  "equipment": "machine",    "big_small": "BIG"},
    {"name": "Leg Extension",            "category": "legs", "muscle_group": "quads",      "primary": False, "equipment": "machine",    "big_small": "SMALL"},
    {"name": "Romanian Deadlift",        "category": "legs", "muscle_group": "hamstrings", "primary": True,  "equipment": "barbell",    "big_small": "BIG"},
    {"name": "Lying Leg Curl",           "category": "legs", "muscle_group": "hamstrings", "primary": True,  "equipment": "machine",    "big_small": "BIG"},
    {"name": "Seated Leg Curl",          "category": "legs", "muscle_group": "hamstrings", "primary": True,  "equipment": "machine",    "big_small": "BIG"},
    {"name": "Hip Abductor",             "category": "legs", "muscle_group": "glutes",     "primary": False, "equipment": "machine",    "big_small": "SMALL"},
    {"name": "Hip Adductor",             "category": "legs", "muscle_group": "glutes",     "primary": False, "equipment": "machine",    "big_small": "SMALL"},
    {"name": "Calf Raises",              "category": "legs", "muscle_group": "calves",     "primary": False, "equipment": "machine",    "big_small": "SMALL"},
    {"name": "Glute Kickback",           "category": "legs", "muscle_group": "glutes",     "primary": False, "equipment": "machine",    "big_small": "SMALL"},
    {"name": "Glute Press",              "category": "legs", "muscle_group": "glutes",     "primary": True,  "equipment": "machine",    "big_small": "BIG"},
    {"name": "Weighted Back Extension",  "category": "legs", "muscle_group": "lower back", "primary": True,  "equipment": "machine",    "big_small": "BIG"},
]

catalog_tid = table_ids["LARK_TABLE_EXERCISE_CATALOG"]
call("post", f"{API}/bitable/v1/apps/{app_token}/tables/{catalog_tid}/records/batch_create",
     token, json={"records": [{"fields": ex} for ex in EXERCISES]}, label="seed catalog")
print(f"   inserted {len(EXERCISES)} exercises")

# --------------------------------------------------------------------------
# 4. Seed SessionTemplates (15 rows from SPEC § 7)
# --------------------------------------------------------------------------
print("\n4. Seeding SessionTemplates...")

TEMPLATES = [
    {"session_type": "push", "exercise_name": "Bench Press",        "order": 1, "sets": 3, "reps_target": "8-10",  "big_small": "BIG"},
    {"session_type": "push", "exercise_name": "Lateral Raises",     "order": 2, "sets": 3, "reps_target": "10-12", "big_small": "SMALL"},
    {"session_type": "push", "exercise_name": "Overhead Press",     "order": 3, "sets": 3, "reps_target": "8-10",  "big_small": "BIG"},
    {"session_type": "push", "exercise_name": "Cable Fly",          "order": 4, "sets": 3, "reps_target": "10-12", "big_small": "SMALL"},
    {"session_type": "push", "exercise_name": "Tricep Pushdown",    "order": 5, "sets": 3, "reps_target": "10-12", "big_small": "SMALL"},
    {"session_type": "pull", "exercise_name": "Pull-ups",           "order": 1, "sets": 3, "reps_target": "6-10",  "big_small": "BIG"},
    {"session_type": "pull", "exercise_name": "Seated Cable Row",   "order": 2, "sets": 3, "reps_target": "10-12", "big_small": "SMALL"},
    {"session_type": "pull", "exercise_name": "Face Pulls",         "order": 3, "sets": 3, "reps_target": "12-15", "big_small": "SMALL"},
    {"session_type": "pull", "exercise_name": "Bicep Curl Machine", "order": 4, "sets": 3, "reps_target": "10-12", "big_small": "SMALL"},
    {"session_type": "pull", "exercise_name": "Plank",              "order": 5, "sets": 3, "reps_target": "60s",   "big_small": "SMALL"},
    {"session_type": "legs", "exercise_name": "Leg Press",          "order": 1, "sets": 3, "reps_target": "10-12", "big_small": "BIG"},
    {"session_type": "legs", "exercise_name": "Leg Extension",      "order": 2, "sets": 3, "reps_target": "10-12", "big_small": "SMALL"},
    {"session_type": "legs", "exercise_name": "Romanian Deadlift",  "order": 3, "sets": 3, "reps_target": "8-10",  "big_small": "BIG"},
    {"session_type": "legs", "exercise_name": "Hip Abductor",       "order": 4, "sets": 3, "reps_target": "12-15", "big_small": "SMALL"},
    {"session_type": "legs", "exercise_name": "Calf Raises",        "order": 5, "sets": 3, "reps_target": "15-20", "big_small": "SMALL"},
]

templates_tid = table_ids["LARK_TABLE_SESSION_TEMPLATES"]
call("post", f"{API}/bitable/v1/apps/{app_token}/tables/{templates_tid}/records/batch_create",
     token, json={"records": [{"fields": t} for t in TEMPLATES]}, label="seed templates")
print(f"   inserted {len(TEMPLATES)} templates")

# --------------------------------------------------------------------------
# 5. Bootstrap SessionSequence (session 0 → next is session 1 = PUSH)
# --------------------------------------------------------------------------
print("\n5. Bootstrapping SessionSequence...")

seq_tid = table_ids["LARK_TABLE_SESSION_SEQUENCE"]
call("post", f"{API}/bitable/v1/apps/{app_token}/tables/{seq_tid}/records",
     token, json={"fields": {"session_number": 0, "session_type": "legs", "date": today_ms, "completed": True}},
     label="bootstrap session 0")
print("   session_number=0, session_type=legs, completed=true")
print("   → next session will be #1 = PUSH")

# --------------------------------------------------------------------------
# 6. Share Base with user
# --------------------------------------------------------------------------
if OWNER_EMAIL:
    print(f"\n6. Sharing Base with {OWNER_EMAIL}...")
    data = call("post",
        f"{API}/drive/v1/permissions/{app_token}/members?type=bitable&need_notification=true",
        token,
        json={"member_type": "email", "member_id": OWNER_EMAIL, "perm": "full_access"},
        label="share base")
    print(f"   shared with full_access")
else:
    print("\n6. Skipping share (no LARK_OWNER_EMAIL in .env)")

# --------------------------------------------------------------------------
# 7. Delete the default table that Lark auto-creates
# --------------------------------------------------------------------------
print("\n7. Cleaning up default table...")
data = call("get", f"{API}/bitable/v1/apps/{app_token}/tables", token, label="list tables")
for table in data["data"].get("items", []):
    if table["table_id"] not in table_ids.values():
        requests.delete(f"{API}/bitable/v1/apps/{app_token}/tables/{table['table_id']}",
                        headers=h(token))
        print(f"   deleted default table: {table['table_id']}")

# --------------------------------------------------------------------------
# Done
# --------------------------------------------------------------------------
print("\n" + "=" * 60)
print("BOOTSTRAP COMPLETE")
print(f"  Base URL:  {base_url}")
print(f"  app_token: {app_token}")
print()
for env_key, tid in table_ids.items():
    print(f"  {env_key}={tid}")
print()
print("  All IDs written to .env")
print("  Open the Base URL in Lark to verify.")
print("=" * 60)
