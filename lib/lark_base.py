"""
Lark Base (Bitable) helper — thin wrapper around lark_oapi for gym tracker tables.

Usage:
    from lib.lark_base import LarkBase
    db = LarkBase()
    records = db.list_records(db.WORKOUT_LOG)
    db.create_record(db.WORKOUT_LOG, {"exercise_name": "Bench Press", "weight_kg": 60, "reps": 8})

Environment variables required:
    LARK_APP_ID       — from Lark Open Platform app credentials
    LARK_APP_SECRET   — from Lark Open Platform app credentials
    LARK_APP_TOKEN    — the Bitable app token (from Base URL: /base/<app_token>)

Table IDs — fill in after creating the Base tables in Lark:
    LARK_TABLE_WORKOUT_LOG
    LARK_TABLE_EXERCISE_HISTORY
    LARK_TABLE_SESSION_SEQUENCE
    LARK_TABLE_SESSION_TEMPLATES
    LARK_TABLE_EXERCISE_CATALOG
    LARK_TABLE_PROGRESS
    LARK_TABLE_BODY_LOG
"""

import os
from typing import Any

import lark_oapi as lark
from lark_oapi.api.bitable.v1 import (
    AppTableRecord,
    BatchCreateAppTableRecordRequest,
    BatchCreateAppTableRecordRequestBody,
    CreateAppTableRecordRequest,
    ListAppTableRecordRequest,
    SearchAppTableRecordRequest,
    SearchAppTableRecordRequestBody,
    UpdateAppTableRecordRequest,
)


class LarkBase:
    # Table ID constants — set via environment variables after tables are created
    WORKOUT_LOG = os.environ.get("LARK_TABLE_WORKOUT_LOG", "")
    EXERCISE_HISTORY = os.environ.get("LARK_TABLE_EXERCISE_HISTORY", "")
    SESSION_SEQUENCE = os.environ.get("LARK_TABLE_SESSION_SEQUENCE", "")
    SESSION_TEMPLATES = os.environ.get("LARK_TABLE_SESSION_TEMPLATES", "")
    EXERCISE_CATALOG = os.environ.get("LARK_TABLE_EXERCISE_CATALOG", "")
    PROGRESS = os.environ.get("LARK_TABLE_PROGRESS", "")
    BODY_LOG = os.environ.get("LARK_TABLE_BODY_LOG", "")

    def __init__(self):
        self.app_token = os.environ["LARK_APP_TOKEN"]
        self.client = (
            lark.Client.builder()
            .app_id(os.environ["LARK_APP_ID"])
            .app_secret(os.environ["LARK_APP_SECRET"])
            .build()
        )

    # -------------------------------------------------------------------------
    # Read
    # -------------------------------------------------------------------------

    def list_records(self, table_id: str, page_size: int = 500) -> list[dict]:
        """Return all records from a table as a list of field dicts.
        Each item also includes the Lark record_id under key '__record_id'.
        """
        records = []
        page_token = None

        while True:
            builder = (
                ListAppTableRecordRequest.builder()
                .app_token(self.app_token)
                .table_id(table_id)
                .page_size(page_size)
            )
            if page_token:
                builder = builder.page_token(page_token)

            response = self.client.bitable.v1.app_table_record.list(builder.build())
            if not response.success():
                raise RuntimeError(
                    f"list_records failed [{response.code}]: {response.msg}"
                )

            for item in response.data.items or []:
                row = dict(item.fields)
                row["__record_id"] = item.record_id
                records.append(row)

            if not response.data.has_more:
                break
            page_token = response.data.page_token

        return records

    def get_record(self, table_id: str, record_id: str) -> dict:
        """Fetch a single record by its Lark record_id."""
        from lark_oapi.api.bitable.v1 import GetAppTableRecordRequest

        response = self.client.bitable.v1.app_table_record.get(
            GetAppTableRecordRequest.builder()
            .app_token(self.app_token)
            .table_id(table_id)
            .record_id(record_id)
            .build()
        )
        if not response.success():
            raise RuntimeError(f"get_record failed [{response.code}]: {response.msg}")
        row = dict(response.data.record.fields)
        row["__record_id"] = response.data.record.record_id
        return row

    def find_records(self, table_id: str, filter_expr: dict | None = None) -> list[dict]:
        """Search records using a Lark filter expression.

        filter_expr example:
            {
                "conjunction": "and",
                "conditions": [
                    {"field_name": "exercise_name", "operator": "is", "value": ["Bench Press"]}
                ]
            }
        Returns list of field dicts, each with '__record_id'.
        """
        body_builder = SearchAppTableRecordRequestBody.builder()
        if filter_expr:
            body_builder = body_builder.filter(filter_expr)

        response = self.client.bitable.v1.app_table_record.search(
            SearchAppTableRecordRequest.builder()
            .app_token(self.app_token)
            .table_id(table_id)
            .request_body(body_builder.build())
            .build()
        )
        if not response.success():
            raise RuntimeError(
                f"find_records failed [{response.code}]: {response.msg}"
            )
        records = []
        for item in response.data.items or []:
            row = dict(item.fields)
            row["__record_id"] = item.record_id
            records.append(row)
        return records

    # -------------------------------------------------------------------------
    # Write
    # -------------------------------------------------------------------------

    def create_record(self, table_id: str, fields: dict[str, Any]) -> str:
        """Create a single record. Returns the new record_id."""
        response = self.client.bitable.v1.app_table_record.create(
            CreateAppTableRecordRequest.builder()
            .app_token(self.app_token)
            .table_id(table_id)
            .request_body(
                AppTableRecord.builder().fields(fields).build()
            )
            .build()
        )
        if not response.success():
            raise RuntimeError(
                f"create_record failed [{response.code}]: {response.msg}"
            )
        return response.data.record.record_id

    def batch_create_records(
        self, table_id: str, rows: list[dict[str, Any]]
    ) -> list[str]:
        """Batch create up to 500 records. Returns list of new record_ids."""
        records = [AppTableRecord.builder().fields(r).build() for r in rows]
        response = self.client.bitable.v1.app_table_record.batch_create(
            BatchCreateAppTableRecordRequest.builder()
            .app_token(self.app_token)
            .table_id(table_id)
            .request_body(
                BatchCreateAppTableRecordRequestBody.builder()
                .records(records)
                .build()
            )
            .build()
        )
        if not response.success():
            raise RuntimeError(
                f"batch_create_records failed [{response.code}]: {response.msg}"
            )
        return [r.record_id for r in response.data.records]

    def update_record(
        self, table_id: str, record_id: str, fields: dict[str, Any]
    ) -> None:
        """Update an existing record by record_id."""
        response = self.client.bitable.v1.app_table_record.update(
            UpdateAppTableRecordRequest.builder()
            .app_token(self.app_token)
            .table_id(table_id)
            .record_id(record_id)
            .request_body(
                AppTableRecord.builder().fields(fields).build()
            )
            .build()
        )
        if not response.success():
            raise RuntimeError(
                f"update_record failed [{response.code}]: {response.msg}"
            )

    # -------------------------------------------------------------------------
    # Convenience queries for gym tracker
    # -------------------------------------------------------------------------

    def get_exercise_history(self, exercise_name: str) -> dict | None:
        """Return the ExerciseHistory row for a given exercise, or None."""
        rows = self.find_records(
            self.EXERCISE_HISTORY,
            {
                "conjunction": "and",
                "conditions": [
                    {
                        "field_name": "exercise",
                        "operator": "is",
                        "value": [exercise_name],
                    }
                ],
            },
        )
        return rows[0] if rows else None

    def get_last_session_sequence(self) -> dict | None:
        """Return the most recent SessionSequence row (highest session_number)."""
        rows = self.list_records(self.SESSION_SEQUENCE)
        if not rows:
            return None
        return max(rows, key=lambda r: r.get("session_number", 0))

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
            {
                "conjunction": "and",
                "conditions": [
                    {
                        "field_name": "session_type",
                        "operator": "is",
                        "value": [session_type],
                    }
                ],
            },
        )
        return sorted(rows, key=lambda r: r.get("order", 0))

    def get_workout_sets_for_exercise(
        self, exercise_name: str, date: str
    ) -> list[dict]:
        """Return all WorkoutLog sets for a given exercise on a given date (YYYY-MM-DD)."""
        rows = self.find_records(
            self.WORKOUT_LOG,
            {
                "conjunction": "and",
                "conditions": [
                    {
                        "field_name": "exercise_name",
                        "operator": "is",
                        "value": [exercise_name],
                    },
                    {
                        "field_name": "date",
                        "operator": "is",
                        "value": [date],
                    },
                ],
            },
        )
        return sorted(rows, key=lambda r: r.get("set_number", 0))
