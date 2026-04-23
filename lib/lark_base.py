"""
Lark Base (Bitable) helper for gym tracker tables.

Uses urllib (stdlib) instead of lark_oapi — no pip install needed.

Usage:
    from lib.lark_base import LarkBase
    db = LarkBase()
    records = db.list_records(db.WORKOUT_LOG)
    db.create_record(db.WORKOUT_LOG, {"exercise_name": "Bench Press", "weight_kg": 60, "reps": 8})

Auto-loads env from: /home/node/.openclaw/workspace/gym_routine/.env
(contains LARK_APP_ID, LARK_APP_SECRET, LARK_APP_TOKEN, and all LARK_TABLE_* IDs)

Table IDs (from gym_routine/.env):
    LARK_TABLE_WORKOUT_LOG       — WorkoutLog
    LARK_TABLE_EXERCISE_HISTORY  — ExerciseHistory
    LARK_TABLE_SESSION_SEQUENCE  — SessionSequence
    LARK_TABLE_SESSION_TEMPLATES — SessionTemplates
    LARK_TABLE_EXERCISE_CATALOG  — ExerciseCatalog
    LARK_TABLE_PROGRESS          — Progress
    LARK_TABLE_BODY_LOG          — BodyLog
"""

import os
from pathlib import Path
from typing import Any
import urllib.request
import json

# Auto-load env from gym_routine/.env
_ENV_PATH = Path("/home/node/.openclaw/workspace/gym_routine/.env")
if _ENV_PATH.exists():
    with open(_ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k, v)

API = "https://open.larksuite.com/open-apis"


def _auth() -> str:
    """Get tenant access token."""
    data = json.dumps({
        "app_id": os.environ["LARK_APP_ID"],
        "app_secret": os.environ["LARK_APP_SECRET"]
    }).encode()
    req = urllib.request.Request(
        f"{API}/auth/v3/tenant_access_token/internal",
        data=data, headers={"Content-Type": "application/json"}
    )
    return json.loads(urllib.request.urlopen(req).read())["tenant_access_token"]


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=utf-8"}


def _call(method: str, url: str, token: str, data: dict | None = None) -> dict:
    """Make an API call. Returns parsed JSON response.data."""
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, headers=_headers(token), method=method)
    resp = json.loads(urllib.request.urlopen(req).read())
    if resp.get("code") != 0:
        raise RuntimeError(f"Lark API error [{resp.get('code')}]: {resp.get('msg')} — {resp}")
    return resp.get("data", {})


class LarkBase:
    # Table ID constants — loaded from gym_routine/.env
    WORKOUT_LOG = os.environ.get("LARK_TABLE_WORKOUT_LOG", "")
    EXERCISE_HISTORY = os.environ.get("LARK_TABLE_EXERCISE_HISTORY", "")
    SESSION_SEQUENCE = os.environ.get("LARK_TABLE_SESSION_SEQUENCE", "")
    SESSION_TEMPLATES = os.environ.get("LARK_TABLE_SESSION_TEMPLATES", "")
    EXERCISE_CATALOG = os.environ.get("LARK_TABLE_EXERCISE_CATALOG", "")
    PROGRESS = os.environ.get("LARK_TABLE_PROGRESS", "")
    BODY_LOG = os.environ.get("LARK_TABLE_BODY_LOG", "")

    def __init__(self):
        self.app_token = os.environ["LARK_APP_TOKEN"]
        self._token = _auth()

    def _refresh_token(self):
        self._token = _auth()

    def _url(self, path: str) -> str:
        return f"{API}/bitable/v1/apps/{self.app_token}{path}"

    # -------------------------------------------------------------------------
    # Read
    # -------------------------------------------------------------------------

    def list_records(self, table_id: str, page_size: int = 500) -> list[dict]:
        """Return all records from a table as list of field dicts.
        Each includes '__record_id'.
        """
        records = []
        page_token = None
        while True:
            url = f"{self._url(f'/tables/{table_id}/records')}?page_size={page_size}"
            if page_token:
                url += f"&page_token={page_token}"
            data = _call("GET", url, self._token)
            for item in data.get("items", []):
                row = _flatten_fields(item["fields"])
                row["__record_id"] = item["record_id"]
                records.append(row)
            if not data.get("has_more"):
                break
            page_token = data.get("page_token")
        return records

    def get_record(self, table_id: str, record_id: str) -> dict:
        """Fetch a single record by record_id."""
        data = _call("GET", f"{self._url(f'/tables/{table_id}/records/{record_id}')}", self._token)
        row = _flatten_fields(data["record"]["fields"])
        row["__record_id"] = data["record"]["record_id"]
        return row

    def find_records(self, table_id: str, filter_expr: dict | None = None) -> list[dict]:
        """Search records using a Lark filter expression. Returns list with '__record_id'."""
        body = {}
        if filter_expr:
            body["filter"] = filter_expr
        data = _call("POST", f"{self._url(f'/tables/{table_id}/records/search')}", self._token, body)
        records = []
        for item in data.get("items", []):
            row = _flatten_fields(item["fields"])
            row["__record_id"] = item["record_id"]
            records.append(row)
        return records

    # -------------------------------------------------------------------------
    # Write
    # -------------------------------------------------------------------------

    def create_record(self, table_id: str, fields: dict[str, Any]) -> str:
        """Create a single record. Returns the new record_id."""
        # Handle rich text fields (e.g., exercise_name stored as [{"text": "...", "type": "text"}])
        flat_fields = _unflatten_fields(fields)
        data = _call("POST", f"{self._url(f'/tables/{table_id}/records')}", self._token,
                     {"fields": flat_fields})
        return data["record"]["record_id"]

    def batch_create_records(self, table_id: str, rows: list[dict[str, Any]]) -> list[str]:
        """Batch create up to 500 records. Returns list of new record_ids."""
        flat_rows = [{"fields": _unflatten_fields(r)} for r in rows]
        data = _call("POST", f"{self._url(f'/tables/{table_id}/records/batch_create')}", self._token,
                     {"records": flat_rows})
        return [r["record_id"] for r in data.get("records", [])]

    def update_record(self, table_id: str, record_id: str, fields: dict[str, Any]) -> None:
        """Update an existing record by record_id."""
        flat_fields = _unflatten_fields(fields)
        _call("PUT", f"{self._url(f'/tables/{table_id}/records/{record_id}')}", self._token,
              {"fields": flat_fields})

    def add_field(self, table_id: str, field_name: str, field_type: int = 2) -> None:
        """Add a new field to a table. field_type: 1=text, 2=number, 5=date, 7=checkbox."""
        _call("POST", f"{self._url(f'/tables/{table_id}/fields')}", self._token,
              {"field_name": field_name, "type": field_type})

    # -------------------------------------------------------------------------
    # Convenience queries for gym tracker
    # -------------------------------------------------------------------------

    def get_exercise_history(self, exercise_name: str) -> dict | None:
        """Return the ExerciseHistory row for a given exercise, or None."""
        rows = self.find_records(
            self.EXERCISE_HISTORY,
            {"conjunction": "and", "conditions": [
                {"field_name": "exercise", "operator": "is", "value": [exercise_name]}
            ]},
        )
        return rows[0] if rows else None

    def get_last_session_sequence(self) -> dict | None:
        """Return the most recent SessionSequence row (highest session_number)."""
        rows = self.list_records(self.SESSION_SEQUENCE)
        if not rows:
            return None
        return max(rows, key=lambda r: int(r.get("session_number", 0)))

    def get_latest_bodyweight(self) -> float | None:
        """Return the most recent bodyweight from BodyLog, or None."""
        rows = self.list_records(self.BODY_LOG)
        if not rows:
            return None
        latest = max(rows, key=lambda r: r.get("log_date", ""))
        return latest.get("weight_kg")

    def get_session_template(self, session_type: str) -> list[dict]:
        """Return SessionTemplates rows for push/pull/legs, sorted by order."""
        rows = self.find_records(
            self.SESSION_TEMPLATES,
            {"conjunction": "and", "conditions": [
                {"field_name": "session_type", "operator": "is", "value": [session_type]}
            ]},
        )
        return sorted(rows, key=lambda r: int(r.get("order", 0)))

    def get_workout_sets_for_exercise(self, exercise_name: str, date: str) -> list[dict]:
        """Return all WorkoutLog sets for an exercise on a given date (YYYY-MM-DD)."""
        rows = self.find_records(
            self.WORKOUT_LOG,
            {"conjunction": "and", "conditions": [
                {"field_name": "exercise_name", "operator": "is", "value": [exercise_name]},
                {"field_name": "date", "operator": "is", "value": [date]},
            ]},
        )
        return sorted(rows, key=lambda r: r.get("set_number", 0))


# -------------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------------

def _flatten_fields(fields: dict) -> dict:
    """Lark returns rich text fields as [{text, type}]. Flatten to plain strings."""
    out = {}
    for k, v in fields.items():
        if isinstance(v, list) and v and isinstance(v[0], dict) and v[0].get("type") == "text":
            out[k] = "".join(seg.get("text", "") for seg in v)
        else:
            out[k] = v
    return out


def _unflatten_fields(fields: dict) -> dict:
    """Convert plain strings back to Lark rich text format for writes."""
    out = {}
    for k, v in fields.items():
        if isinstance(v, str):
            out[k] = [{"text": v, "type": "text"}]
        else:
            out[k] = v
    return out
