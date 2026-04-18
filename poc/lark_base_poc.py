"""
Lark Base POC — raw HTTP CRUD operations.

The app creates its OWN Base (so it's the owner with full write access),
creates a table with fields, then runs create/search/update/batch/delete.

Usage:
    cp .env.example .env   # fill in LARK_APP_ID and LARK_APP_SECRET only
    pip install requests python-dotenv
    python lark_base_poc.py
"""

import os
import sys
import time
from pprint import pprint

import requests
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Config — only app credentials needed; the Base is created by the app
# ---------------------------------------------------------------------------
APP_ID = os.environ["LARK_APP_ID"]
APP_SECRET = os.environ["LARK_APP_SECRET"]
BASE_URL = "https://open.larksuite.com/open-apis"


def headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8",
    }


def check(resp: requests.Response, label: str) -> dict:
    data = resp.json()
    if data.get("code") != 0:
        print(f"\n[{label} FAILED] code={data['code']} msg={data['msg']}")
        pprint(data)
        sys.exit(1)
    print(f"[{label} OK]")
    return data


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
def get_token() -> str:
    resp = requests.post(
        f"{BASE_URL}/auth/v3/tenant_access_token/internal",
        json={"app_id": APP_ID, "app_secret": APP_SECRET},
    )
    data = check(resp, "AUTH")
    token = data["tenant_access_token"]
    print(f"  token: {token[:20]}...")
    return token


# ---------------------------------------------------------------------------
# Create a Base (the app becomes the owner → full write access)
# ---------------------------------------------------------------------------
def create_base(token: str) -> tuple[str, str]:
    """Create a new Base. Returns (app_token, default_table_id)."""
    resp = requests.post(
        f"{BASE_URL}/bitable/v1/apps",
        headers=headers(token),
        json={"name": "POC Gym Tracker (auto-created)"},
    )
    data = check(resp, "CREATE BASE")
    app = data["data"]["app"]
    print(f"  app_token: {app['app_token']}")
    print(f"  default_table_id: {app.get('default_table_id', 'N/A')}")
    print(f"  url: {app.get('url', 'N/A')}")
    return app["app_token"], app.get("default_table_id", "")


# ---------------------------------------------------------------------------
# Create a table with specific fields
# ---------------------------------------------------------------------------
def create_table(token: str, app_token: str) -> str:
    """Create a TestExercises table with typed fields. Returns table_id."""
    resp = requests.post(
        f"{BASE_URL}/bitable/v1/apps/{app_token}/tables",
        headers=headers(token),
        json={
            "table": {
                "name": "TestExercises",
                "default_view_name": "Grid View",
                "fields": [
                    {"field_name": "name", "type": 1},       # 1 = Text
                    {"field_name": "weight_kg", "type": 2},   # 2 = Number
                    {"field_name": "reps", "type": 2},        # 2 = Number
                    {"field_name": "date", "type": 5},        # 5 = Date
                    {"field_name": "completed", "type": 7},   # 7 = Checkbox
                ],
            }
        },
    )
    data = check(resp, "CREATE TABLE")
    table_id = data["data"]["table_id"]
    print(f"  table_id: {table_id}")
    return table_id


# ---------------------------------------------------------------------------
# Create a single record
# ---------------------------------------------------------------------------
def create_record(token: str, app_token: str, table_id: str) -> str:
    now_ms = int(time.time() * 1000)
    resp = requests.post(
        f"{BASE_URL}/bitable/v1/apps/{app_token}/tables/{table_id}/records",
        headers=headers(token),
        json={
            "fields": {
                "name": "Bench Press",
                "weight_kg": 60,
                "reps": 8,
                "date": now_ms,
                "completed": True,
            }
        },
    )
    data = check(resp, "CREATE RECORD")
    record = data["data"]["record"]
    print(f"  record_id: {record['record_id']}")
    print(f"  fields: {record['fields']}")
    return record["record_id"]


# ---------------------------------------------------------------------------
# Search records
# ---------------------------------------------------------------------------
def search_records(
    token: str, app_token: str, table_id: str,
    field_name: str = None, value: str = None,
) -> list:
    payload = {"automatic_fields": True}
    if field_name and value:
        payload["filter"] = {
            "conjunction": "and",
            "conditions": [
                {"field_name": field_name, "operator": "is", "value": [value]}
            ],
        }

    resp = requests.post(
        f"{BASE_URL}/bitable/v1/apps/{app_token}/tables/{table_id}/records/search",
        headers=headers(token),
        json=payload,
    )
    data = check(resp, "SEARCH")
    items = data["data"].get("items") or []
    print(f"  total: {data['data'].get('total', 0)}")
    for item in items:
        print(f"  - {item['record_id']}: {item['fields']}")
    return items


# ---------------------------------------------------------------------------
# Update a record
# ---------------------------------------------------------------------------
def update_record(token: str, app_token: str, table_id: str, record_id: str):
    resp = requests.put(
        f"{BASE_URL}/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}",
        headers=headers(token),
        json={"fields": {"weight_kg": 62.5, "reps": 10}},
    )
    data = check(resp, "UPDATE RECORD")
    print(f"  updated: {data['data']['record']['fields']}")


# ---------------------------------------------------------------------------
# Batch create records
# ---------------------------------------------------------------------------
def batch_create(token: str, app_token: str, table_id: str) -> list[str]:
    now_ms = int(time.time() * 1000)
    resp = requests.post(
        f"{BASE_URL}/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create",
        headers=headers(token),
        json={
            "records": [
                {"fields": {"name": "Overhead Press", "weight_kg": 40, "reps": 10, "date": now_ms, "completed": True}},
                {"fields": {"name": "Lateral Raises", "weight_kg": 8, "reps": 12, "date": now_ms, "completed": True}},
                {"fields": {"name": "Cable Fly", "weight_kg": 12, "reps": 12, "date": now_ms, "completed": False}},
            ]
        },
    )
    data = check(resp, "BATCH CREATE")
    ids = []
    for r in data["data"]["records"]:
        print(f"  - {r['record_id']}: {r['fields']}")
        ids.append(r["record_id"])
    return ids


# ---------------------------------------------------------------------------
# Delete a record
# ---------------------------------------------------------------------------
def delete_record(token: str, app_token: str, table_id: str, record_id: str):
    resp = requests.delete(
        f"{BASE_URL}/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}",
        headers=headers(token),
    )
    check(resp, f"DELETE {record_id[:8]}")


# ---------------------------------------------------------------------------
# Delete the entire Base (cleanup)
# ---------------------------------------------------------------------------
def delete_base(token: str, app_token: str):
    resp = requests.delete(
        f"{BASE_URL}/drive/v1/files/{app_token}?type=bitable",
        headers=headers(token),
    )
    # Some Lark tenants don't support delete — treat as non-fatal
    data = resp.json()
    if data.get("code") == 0:
        print(f"[DELETE BASE OK] {app_token}")
    else:
        print(f"[DELETE BASE SKIPPED] code={data['code']} msg={data['msg']}")
        print("  (you can delete the Base manually in Lark)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("=" * 60)
    print("LARK BASE POC — App-Owned CRUD Test")
    print("=" * 60)

    token = get_token()

    # App creates its own Base → it's the owner → full write access
    app_token, default_table_id = create_base(token)

    # Create a properly typed table
    table_id = create_table(token, app_token)

    # CRUD operations
    record_id = create_record(token, app_token, table_id)
    search_records(token, app_token, table_id)
    search_records(token, app_token, table_id, field_name="name", value="Bench Press")
    update_record(token, app_token, table_id, record_id)
    search_records(token, app_token, table_id, field_name="name", value="Bench Press")
    batch_ids = batch_create(token, app_token, table_id)

    print("\n--- Final state ---")
    search_records(token, app_token, table_id)

    # Cleanup
    print("\n--- Cleanup ---")
    for rid in [record_id] + batch_ids:
        delete_record(token, app_token, table_id, rid)
    delete_base(token, app_token)

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED")
    print(f"  (Base was: {app_token})")
    print("=" * 60)


if __name__ == "__main__":
    main()
