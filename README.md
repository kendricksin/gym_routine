# Gym Routine — AI Coach Setup

Push/Pull/Legs tracking agent running on OpenClaw, with Lark Base as the database and Lark Bot as the chat interface.

---

## Overview

```
You (Lark DM)
    ↕
Lark Bot (WebSocket)
    ↕
OpenClaw agent
    ├── skills/        ← intent routing + workout logic
    ├── SOUL.md        ← coach persona
    └── lib/lark_base.py
    ↕
Lark Base (Bitable)   ← all workout data
```

---

## Prerequisites

- A Lark / Feishu workspace (admin access or ability to create apps)
- A machine to run OpenClaw (laptop, VPS, or homelab — always-on preferred)
- Python 3.13+ with `lark-oapi` installed
- OpenClaw CLI installed

---

## Part 1 — Create the Lark App (Bot)

1. Go to [Lark Open Platform](https://open.feishu.cn/app) → **Create App** → **Custom App**
2. Give it a name (e.g., "Gym Coach") and an icon
3. Under **App Capabilities** → enable **Bot**
4. Under **Permissions & Scopes**, add:
   - `im:message` — send and receive messages
   - `im:message.group_at_msg` — receive @mentions in groups
   - `bitable:app` — read/write Lark Base records
5. Under **Event Subscriptions** → set connection mode to **WebSocket (Persistent Connection)**
   - No public URL needed
6. **Publish** the app (or submit for review if on a managed workspace)
7. Go to **Credentials & Basic Info** → copy:
   - `App ID` → save as `LARK_APP_ID`
   - `App Secret` → save as `LARK_APP_SECRET`

---

## Part 2 — Create the Lark Base (Database) via API

**Important:** You cannot share an existing Base with an app through the Lark UI — apps don't appear in the share search. The app must **create the Base itself** via API so it becomes the owner with full write access.

### How it works

1. The app calls `POST /bitable/v1/apps` to create a new Base → it becomes the **owner**
2. The app calls `POST /bitable/v1/apps/:app_token/tables` to create each table with typed fields
3. The app calls `POST /drive/v1/permissions/:token/members` to share the Base with the user

### Lark Base API Reference

**Base URL:** `https://open.larksuite.com/open-apis`

**Auth:** All requests need `Authorization: Bearer <tenant_access_token>` header.

Get a token:
```
POST /auth/v3/tenant_access_token/internal
Body: {"app_id": "<APP_ID>", "app_secret": "<APP_SECRET>"}
Returns: {"tenant_access_token": "t-xxx", "expire": 7200}
```

#### Create Base (app becomes owner)
```
POST /bitable/v1/apps
Body: {"name": "Gym Tracker"}
Returns: {"data": {"app": {"app_token": "xxx", "default_table_id": "tblxxx", "url": "https://..."}}}
```

#### Create Table (with typed fields)
```
POST /bitable/v1/apps/:app_token/tables
Body: {
  "table": {
    "name": "WorkoutLog",
    "default_view_name": "All Sets",
    "fields": [
      {"field_name": "date",          "type": 5},
      {"field_name": "exercise_name", "type": 1},
      {"field_name": "weight_kg",     "type": 2}
    ]
  }
}
Returns: {"data": {"table_id": "tblxxx"}}
```

**Field type codes:**

| Code | Type | Example |
|------|------|---------|
| 1 | Text | `"Bench Press"` |
| 2 | Number | `60`, `62.5` |
| 5 | Date | `1776441600000` (millisecond timestamp) |
| 7 | Checkbox | `true` / `false` |

#### Share Base with a user
```
POST /drive/v1/permissions/:app_token/members?type=bitable&need_notification=true
Body: {"member_type": "email", "member_id": "user@example.com", "perm": "full_access"}
```

`perm` options: `view`, `edit`, `full_access`

#### Create Record
```
POST /bitable/v1/apps/:app_token/tables/:table_id/records
Body: {"fields": {"name": "Bench Press", "weight_kg": 60, "reps": 8, "date": 1776441600000}}
Returns: {"data": {"record": {"record_id": "recxxx", "fields": {...}}}}
```

#### Batch Create Records (up to 500 per call)
```
POST /bitable/v1/apps/:app_token/tables/:table_id/records/batch_create
Body: {"records": [{"fields": {...}}, {"fields": {...}}]}
Returns: {"data": {"records": [{"record_id": "recxxx", "fields": {...}}, ...]}}
```

#### Search Records (replaces deprecated List endpoint)
```
POST /bitable/v1/apps/:app_token/tables/:table_id/records/search
Body: {
  "filter": {
    "conjunction": "and",
    "conditions": [
      {"field_name": "exercise_name", "operator": "is", "value": ["Bench Press"]}
    ]
  },
  "sort": [{"field_name": "set_number", "desc": false}],
  "automatic_fields": true
}
Returns: {"data": {"items": [{"record_id": "recxxx", "fields": {...}}, ...], "total": 3, "has_more": false}}
```

**Filter operators:** `is`, `isNot`, `contains`, `doesNotContain`, `isEmpty`, `isNotEmpty`, `isGreater`, `isGreaterEqual`, `isLess`, `isLessEqual`

**Note:** Text fields return as rich-text arrays from Search: `[{"text": "Bench Press", "type": "text"}]`. Normalise to plain strings when reading.

#### Update Record
```
PUT /bitable/v1/apps/:app_token/tables/:table_id/records/:record_id
Body: {"fields": {"weight_kg": 62.5, "RPE": 8}}
```

#### Delete Record
```
DELETE /bitable/v1/apps/:app_token/tables/:table_id/records/:record_id
```

### Table Definitions

The app creates these 7 tables on first run. Field names must match exactly.

**WorkoutLog** — one row per set
| Field | Type code | Description |
|---|---|---|
| `date` | 5 (Date) | Workout date (ms timestamp) |
| `session_type` | 1 (Text) | push / pull / legs |
| `exercise_name` | 1 (Text) | Exact exercise name |
| `set_number` | 2 (Number) | 1, 2, 3... |
| `weight_kg` | 2 (Number) | Weight for this set |
| `reps` | 2 (Number) | Reps performed |
| `RPE` | 2 (Number) | 1–10 scale (optional) |
| `notes` | 1 (Text) | Form notes, variations |

**ExerciseHistory** — one row per exercise, updated after every session
| Field | Type code | Description |
|---|---|---|
| `exercise` | 1 (Text) | Exercise name |
| `last_date` | 5 (Date) | Last performed |
| `last_weight` | 2 (Number) | Weight on heaviest set |
| `last_reps` | 2 (Number) | Reps on heaviest set |
| `last_total_volume` | 2 (Number) | Sum of weight×reps across all sets |
| `last_top_set_intensity` | 2 (Number) | Weight on heaviest single set |
| `expected_weight` | 2 (Number) | Target weight for next session |
| `expected_reps_per_set` | 2 (Number) | Target reps per set for next session |
| `session_count` | 2 (Number) | Times performed |
| `streak` | 2 (Number) | Consecutive sessions meeting target |
| `consecutive_rpe_10` | 2 (Number) | Consecutive RPE 10 sessions |
| `stall_nudge_sent` | 7 (Checkbox) | Whether "eat more" nudge was sent |

**SessionSequence** — tracks position in A-B-C rotation
| Field | Type code | Description |
|---|---|---|
| `session_number` | 2 (Number) | Sequential count (1, 2, 3...) |
| `session_type` | 1 (Text) | push / pull / legs |
| `date` | 5 (Date) | When performed |
| `completed` | 7 (Checkbox) | Whether session was completed |

**SessionTemplates** — pre-defined exercise order per session type
| Field | Type code | Description |
|---|---|---|
| `session_type` | 1 (Text) | push / pull / legs |
| `exercise_name` | 1 (Text) | Exercise name |
| `order` | 2 (Number) | Position in session (1–5) |
| `sets` | 2 (Number) | Always 3 |
| `reps_target` | 1 (Text) | e.g. "8-10", "10-12" |
| `big_small` | 1 (Text) | BIG or SMALL |

**ExerciseCatalog** — all available exercises
| Field | Type code | Description |
|---|---|---|
| `name` | 1 (Text) | Exercise name |
| `category` | 1 (Text) | push / pull / legs |
| `muscle_group` | 1 (Text) | e.g. chest, back, quads |
| `primary` | 7 (Checkbox) | Is it a primary compound? |
| `equipment` | 1 (Text) | barbell / machine / cable / dumbbell / bodyweight |
| `big_small` | 1 (Text) | BIG or SMALL |

**Progress** — one row per completed session
| Field | Type code | Description |
|---|---|---|
| `date` | 5 (Date) | Session date |
| `session_type` | 1 (Text) | push / pull / legs |
| `exercises_completed` | 2 (Number) | Count |
| `total_volume` | 2 (Number) | Sum of weight×reps |
| `first_exercise_time` | 5 (Date) | Timestamp of first set |
| `last_exercise_time` | 5 (Date) | Timestamp of last set |
| `duration_minutes` | 2 (Number) | Derived on session close |
| `notes` | 1 (Text) | How session felt |

**BodyLog** — periodic bodyweight tracking
| Field | Type code | Description |
|---|---|---|
| `log_date` | 5 (Date) | Date measured |
| `weight_kg` | 2 (Number) | Bodyweight in kg |
| `bodyfat_pct` | 2 (Number) | Estimated body fat % |
| `notes` | 1 (Text) | Observations |

---

## Part 3 — Configure Environment Variables

Create a `.env` file in this directory (never commit it):

```bash
# Lark App credentials (required before first run)
LARK_APP_ID=cli_xxxxxxxxxxxx
LARK_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# User email to share the Base with (so you can view it in Lark)
LARK_OWNER_EMAIL=you@yourcompany.com

# --- The values below are generated by the bootstrap script (Part 6) ---
# Lark Base app token (created by the app via API)
LARK_APP_TOKEN=
# Table IDs (created by the app via API)
LARK_TABLE_WORKOUT_LOG=
LARK_TABLE_EXERCISE_HISTORY=
LARK_TABLE_SESSION_SEQUENCE=
LARK_TABLE_SESSION_TEMPLATES=
LARK_TABLE_EXERCISE_CATALOG=
LARK_TABLE_PROGRESS=
LARK_TABLE_BODY_LOG=
```

You only need to fill in `LARK_APP_ID`, `LARK_APP_SECRET`, and `LARK_OWNER_EMAIL` manually.
The bootstrap script (Part 6) creates the Base + tables and fills in the rest.

---

## Part 4 — Install and Configure OpenClaw

1. Install OpenClaw CLI:
   ```bash
   npm install -g openclaw
   # or via their installer: https://docs.openclaw.ai/install
   ```

2. Connect OpenClaw to your Lark Bot:
   ```bash
   openclaw channels login --channel feishu
   # Scan the QR code in the Lark mobile app
   ```
   OpenClaw uses WebSocket — no public URL or webhook needed.

3. Point OpenClaw at this workspace directory:
   ```bash
   cd /path/to/gym_routine
   openclaw start
   ```
   OpenClaw will auto-discover `SOUL.md` and all `skills/*/SKILL.md` files.

4. Verify skills are loaded:
   ```bash
   openclaw skills list
   # Should show: plan-session, log-workout, query-history,
   #              suggest-swap, suggest-deload, log-bodyweight, send-reminder
   ```

5. Set up the cron for `send-reminder` (runs nightly at 8pm):
   ```bash
   openclaw cron enable send-reminder
   ```

---

## Part 5 — Python runtime (no install needed)

`lib/lark_base.py` uses only the Python stdlib (`urllib.request`, `json`, `os`, `pathlib`). The OpenClaw container ships Python 3 — no `pip install`, no venv, no external deps.

It auto-loads `.env` from the workspace root, so no shell export step is required either. Just make sure the file is present.

*Host-side bootstrap (Part 6) is the one exception — that script runs once on the host before the agent is live, and uses `uv run --with requests` to pull `requests` ephemerally.*

---

## Part 6 — Bootstrap the Database

Run the bootstrap script to create the Base, all 7 tables, and seed data in one go:

```bash
uv run --with requests --with python-dotenv python poc/bootstrap.py
```

This script will:
1. Authenticate with your Lark app credentials
2. Create a new Base called "Gym Tracker" (app becomes owner)
3. Create all 7 tables with correctly typed fields
4. Seed `ExerciseCatalog` with 35 exercises from SPEC § 4
5. Seed `SessionTemplates` with 15 rows from SPEC § 7
6. Bootstrap `SessionSequence` with one row (`session_number=0, session_type=legs, completed=true`)
7. Share the Base with `LARK_OWNER_EMAIL` (full access)
8. Print all generated IDs and the Base URL
9. Write the IDs back to `.env` automatically

After running, verify:
- [ ] You can open the Base URL in Lark and see all 7 tables
- [ ] `.env` has all `LARK_APP_TOKEN` and `LARK_TABLE_*` values filled in
- [ ] `send-reminder` cron is enabled (`openclaw cron enable send-reminder`)

### Session auto-close ownership

The session auto-close rules (midnight, 22:00 cutoff, 60-min inactivity) are handled by the **`send-reminder` skill**, which runs nightly at 20:00 and also checks for stale open sessions. The `log-workout` skill independently checks that a session is still open (not `completed=true`) before accepting new set logs — if the session is already closed it will prompt the user to confirm whether they want to continue or start fresh.

### Lark Base rate limits

| Operation | Rate limit |
|---|---|
| Search records | 20 req/sec |
| Create record | 50 req/sec |
| Batch create (up to 500 records) | 10 req/sec |
| Update record | 50 req/sec |
| Create Base | 20 req/min |

A full session dump (5 exercises × 3 sets = 15 sets) should use `batch_create` per exercise (5 API calls, not 15). `ExerciseHistory` updates are individual `PUT` calls (5 more). Total: ~10 API calls per session — well within limits.

---

## Part 7 — Test it

Open a DM with your bot in Lark and send:

```
heading to gym
```

The bot should respond with your next session type and exercise targets.

Then try:
```
Done! Bench 60kg 8,8,7  OHP 40kg 10,10,9  Lateral 8kg 12,12,10  Cable fly 12kg 12,12,12  Tricep 25kg 12,12,12
```

The bot should log the sets, run the progression report, and update your targets.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Bot doesn't respond in Lark | Check `openclaw gateway status` — WebSocket may have dropped |
| "Table not found" errors | Double-check table IDs in `.env` match the Lark Base URLs |
| Skills not loading | Ensure `SOUL.md` and `skills/` are in the same directory OpenClaw was started from |
| Lark Base permission denied (91403) | The app must **create** the Base via API to be the owner. You cannot share a Base with an app via UI. Re-run `poc/bootstrap.py` to create a fresh Base. |
| Cron not firing | Run `openclaw cron list` to verify `send-reminder` is enabled |

---

## File Reference

```
gym_routine/
├── README.md              ← this file
├── SOUL.md                ← agent persona (loaded by OpenClaw automatically)
├── SPEC.md                ← full system specification
├── .env                   ← secrets (do not commit)
├── lib/
│   └── lark_base.py       ← Lark Base API wrapper
└── skills/
    ├── plan-session/      ← "heading to gym" intent
    ├── log-workout/       ← post-session logging + progression
    ├── query-history/     ← PR and trend queries
    ├── suggest-swap/      ← exercise alternatives
    ├── suggest-deload/    ← lighter session options
    ├── log-bodyweight/    ← weigh-in tracking
    └── send-reminder/     ← nightly cron nudges
```
