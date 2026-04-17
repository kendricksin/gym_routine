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

## Part 2 — Create the Lark Base (Database)

1. In Lark, create a new **Base** (click + → Base)
2. Name it `Gym Tracker`
3. Create the following tables with these exact column names and types:

### Table: `WorkoutLog`
| Field name | Type |
|---|---|
| `log_id` | Auto Number |
| `timestamp` | DateTime |
| `date` | Date |
| `session_type` | Text |
| `exercise_name` | Text |
| `set_number` | Number |
| `weight_kg` | Number |
| `reps` | Number |
| `RPE` | Number |
| `notes` | Text |

### Table: `ExerciseHistory`
| Field name | Type |
|---|---|
| `exercise` | Text |
| `last_date` | Date |
| `last_weight` | Number |
| `last_reps` | Number |
| `last_total_volume` | Number |
| `last_top_set_intensity` | Number |
| `expected_weight` | Number |
| `expected_reps_per_set` | Number |
| `session_count` | Number |
| `streak` | Number |
| `consecutive_rpe_10` | Number |
| `stall_nudge_sent` | Checkbox |

### Table: `SessionSequence`
| Field name | Type |
|---|---|
| `session_number` | Number |
| `session_type` | Text |
| `date` | Date |
| `completed` | Checkbox |

### Table: `SessionTemplates`
| Field name | Type |
|---|---|
| `template_id` | Auto Number |
| `session_type` | Text |
| `exercise_name` | Text |
| `order` | Number |
| `sets` | Number |
| `reps_target` | Text |
| `big_small` | Text |

Seed `SessionTemplates` with the 15 rows from `SPEC.md § 7`.

### Table: `ExerciseCatalog`
| Field name | Type |
|---|---|
| `exercise_id` | Auto Number |
| `name` | Text |
| `category` | Text |
| `muscle_group` | Text |
| `primary` | Checkbox |
| `equipment` | Text |
| `big_small` | Text |

Seed with the 35 exercises from `SPEC.md § 4`.

### Table: `Progress`
| Field name | Type |
|---|---|
| `date` | Date |
| `session_type` | Text |
| `exercises_completed` | Number |
| `total_volume` | Number |
| `first_exercise_time` | DateTime |
| `last_exercise_time` | DateTime |
| `duration_minutes` | Number |
| `notes` | Text |

### Table: `BodyLog`
| Field name | Type |
|---|---|
| `log_date` | Date |
| `weight_kg` | Number |
| `bodyfat_pct` | Number |
| `notes` | Text |

4. For each table, copy its **Table ID** from the URL when the table is selected:
   - URL pattern: `/base/<app_token>?table=<table_id>`
   - Save each table ID as the corresponding env var below

5. Share the Base with your Lark App:
   - In the Base → top-right **Share** → add the bot by its App ID with **Editor** permission

---

## Part 3 — Configure Environment Variables

Create a `.env` file in this directory (never commit it):

```bash
# Lark App credentials
LARK_APP_ID=cli_xxxxxxxxxxxx
LARK_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Lark Base app token (from Base URL: /base/<this_part>)
LARK_APP_TOKEN=GpxxxxxxxxxxxxxxxxxxxxxxxxxxxBc

# Table IDs (from Base URL: ?table=<this_part>)
LARK_TABLE_WORKOUT_LOG=tblxxxxxxxxxxxxxxxxxx
LARK_TABLE_EXERCISE_HISTORY=tblxxxxxxxxxxxxxxxxxx
LARK_TABLE_SESSION_SEQUENCE=tblxxxxxxxxxxxxxxxxxx
LARK_TABLE_SESSION_TEMPLATES=tblxxxxxxxxxxxxxxxxxx
LARK_TABLE_EXERCISE_CATALOG=tblxxxxxxxxxxxxxxxxxx
LARK_TABLE_PROGRESS=tblxxxxxxxxxxxxxxxxxx
LARK_TABLE_BODY_LOG=tblxxxxxxxxxxxxxxxxxx
```

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

## Part 5 — Install Python dependencies

The `lib/lark_base.py` helper is called by the agent via OpenClaw's `exec` tool:

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install lark-oapi python-dotenv
```

Load the `.env` file in your shell before starting OpenClaw, or configure OpenClaw to source it:
```bash
export $(cat .env | xargs)
openclaw start
```

---

## Part 6 — Pre-Flight Checklist

Before running `openclaw start`, verify:

- [ ] `SessionTemplates` seeded with the 15 rows from `SPEC.md § 7`
- [ ] `ExerciseCatalog` seeded with the 35 exercises from `SPEC.md § 4`
- [ ] `SessionSequence` bootstrapped with one row: `session_number=0, session_type=legs, date=<today>, completed=true`
  — this prevents the first `0 % 3` lookup from returning an empty result
- [ ] Lark App has `bitable:app` scope **and** is shared as **Editor** on the Base (read-only will block all progression updates)
- [ ] All 7 table IDs in `.env` are correct (copy from Base URL `?table=<id>` when each table is selected)
- [ ] `.env` is loaded into the shell before `openclaw start` (`export $(cat .env | xargs)`)
- [ ] `send-reminder` cron is enabled (`openclaw cron enable send-reminder`)

### Session auto-close ownership

The session auto-close rules (midnight, 22:00 cutoff, 60-min inactivity) are handled by the **`send-reminder` skill**, which runs nightly at 20:00 and also checks for stale open sessions. The `log-workout` skill independently checks that a session is still open (not `completed=true`) before accepting new set logs — if the session is already closed it will prompt the user to confirm whether they want to continue or start fresh.

### Lark Base rate limits

Lark Base allows up to 10 write requests/second per app. A full session dump (5 exercises × 3 sets = 15 `WorkoutLog` writes, plus ~5 `ExerciseHistory` updates) is within limits but send them sequentially, not in a burst. `lib/lark_base.py` uses `batch_create_records` for WorkoutLog sets (one API call per exercise) to keep writes efficient.

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
| Lark Base permission denied | Confirm the app has `bitable:app` scope and is shared as Editor on the Base |
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
