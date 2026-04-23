# TOOLS.md — Lark Base cheat sheet

## Location

- Workspace: `/home/node/.openclaw/workspace/` (inside container) = `~/gym_routine/` on host
- `.env` with credentials lives at workspace root

## Usage

`lib/lark_base.py` auto-loads `.env`. Typical entrypoint:

```python
from lib.lark_base import LarkBase
db = LarkBase()
db.get_session_template('push')          # exercises + targets for push day
db.get_last_session_sequence()           # most recent SessionSequence row
db.get_exercise_history('Bench Press')   # per-exercise progression state
db.get_latest_bodyweight()               # for pull-up true weight
```

## Rich-text gotcha

Text fields come back from Search as rich-text arrays:

```json
[{"text": "Bench Press", "type": "text"}]
```

`list_records` and `find_records` auto-flatten to plain strings. **Write plain strings** — the helper converts on the way in.

## Key tables

| Table const | Purpose |
|---|---|
| `WORKOUT_LOG` | One row per set (exercise, weight, reps, RPE, date, session_type) |
| `SESSION_SEQUENCE` | Session counter (session_number, session_type, completed) |
| `SESSION_TEMPLATES` | Exercise lineup per session type (push/pull/legs) |
| `EXERCISE_HISTORY` | Per-exercise state (last weight, reps, volume, streak, expected_*) |
| `EXERCISE_CATALOG` | All available exercises with category and equipment |
| `BODY_LOG` | Bodyweight entries |
| `PROGRESS` | One row per completed session (derived totals) |

## Reading history

```python
db.list_records(db.WORKOUT_LOG)                              # everything
db.find_records(db.WORKOUT_LOG, {                            # filtered
  "conjunction": "and",
  "conditions": [{"field_name": "session_type", "operator": "is", "value": ["push"]}]
})
db.get_workout_sets_for_exercise("Bench Press", "2026-04-22")  # one session
```

## Rate limits

Search 20/sec • Create 50/sec • Batch create 10/sec • Update 50/sec. A full session dump uses ~10 API calls — well within limits.
