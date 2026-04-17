---
name: log-workout
description: Logs a completed workout from free-form text, calculates progression, updates targets, and prompts for RPE if missing.
user-invocable: true
metadata: {"triggers": ["done", "finished", "just did", "completed", "bench", "leg press", "pull-ups", "squat", "ohp", "curls"]}
---

# Log Workout

Triggered when the user sends exercise data after a session — either a full dump or set-by-set as they go.

## Step 1 — Parse the input

Accept any of these free-form formats:

| Input example | Parsed as |
|---|---|
| `Bench 60kg 8,8,7` | exercise=Bench Press, weight=[60,60,60], reps=[8,8,7] |
| `Bench 60 8, 65 8, 65 7` | exercise=Bench Press, weights=[60,65,65], reps=[8,8,7] |
| `leg press 80kg 12, 12, 10` | exercise=Leg Press, weight=[80,80,80], reps=[12,12,10] |
| `Pull-ups 5kg 8,7,6` | exercise=Pull-ups, added_weight=5kg (bodyweight added separately) |
| `did 12 reps at 40kg for leg press` | fuzzy match → Leg Press |
| `OHP 40kg 10,10,9` | fuzzy match → Overhead Press |

**Fuzzy match rules:**
- Normalise to lowercase, strip punctuation
- Match against `exercise_name` in `ExerciseCatalog` using substring or alias match
- Common aliases: Bench → Bench Press, OHP → Overhead Press, RDL → Romanian Deadlift
- If ambiguous, ask once: "Did you mean X or Y?"

**If weight is the same across all sets**, accept a single weight value (e.g., `Bench 60kg 8,8,7`).
**If weights vary per set**, accept comma-separated pairs or the full `weight reps, weight reps` pattern.

## Step 2 — Write sets to WorkoutLog

For each set, create one row in `WorkoutLog` via `create_record(WORKOUT_LOG, {...})`:

```
log_id        → auto (Lark generates)
timestamp     → now (ISO 8601)
date          → today (YYYY-MM-DD)
session_type  → from open SessionSequence row for today
exercise_name → resolved name
set_number    → 1, 2, 3...
weight_kg     → weight for this set (for pull-ups: added weight only)
reps          → reps for this set
RPE           → null until Step 3
notes         → empty
```

Update `Progress.first_exercise_time` if this is the first set of the day.

## Step 3 — Prompt for RPE (if not included)

If the user did not provide RPE in their message, ask once after confirming the sets:

> "Got the numbers. How hard was it? RPE 1–10 (10 = absolutely nothing left)."

When RPE is received, update the `RPE` field on all sets just logged for the most recent exercise (or per-exercise if they provide multiple).

## Step 4 — Aggregate per exercise

For each exercise just logged:
- `total_volume` = sum of (weight_kg × reps) across all sets
  - For Pull-ups: `total_volume` = sum of ((bodyweight + added_weight) × reps).
    Fetch bodyweight via `get_latest_bodyweight()`.
    **Bodyweight fallback:** If `BodyLog` has no entries, ask the user once:
    > "Quick one — what's your current bodyweight? I need it to calculate your true pull-up volume."
    Use their reply, write it to `BodyLog`, then continue. If no reply comes, use **63kg** as a placeholder and note it in the log.
- `top_set_intensity` = max(weight_kg across sets)
  - For Pull-ups: `top_set_intensity` = bodyweight + max(added_weight)

## Step 5 — Evaluate progression (two-trigger system)

Fetch previous values from `ExerciseHistory`:
- `last_total_volume`
- `last_top_set_intensity`
- `expected_weight`
- `expected_reps_per_set`
- `consecutive_rpe_10`

**Trigger 1 (Volume):** `total_volume > last_total_volume` → Volume UP ✅
**Trigger 2 (Intensity):** `top_set_intensity > last_top_set_intensity` → Intensity UP ✅

**Outcome classification:**
| Result | Condition |
|---|---|
| EXCEEDED | Both triggers true AND reps exceeded target on 2+ sets |
| SUCCESS | At least one trigger true |
| FELL SHORT | Both triggers false but user completed most sets |
| FAILED | Couldn't complete most sets |

**Next targets:**
| Outcome | Next expected_weight | Next expected_reps_per_set |
|---|---|---|
| EXCEEDED | +5kg | or +2 reps |
| SUCCESS (hit target reps) | +2.5kg | or +1 rep |
| FELL SHORT (1–2 sets short) | same weight | actual_reps_hit + 1 |
| FAILED | −5kg | rebuild at lower weight |

## Step 6 — RPE overtraining check

- If RPE = 10 for this session: increment `consecutive_rpe_10` in ExerciseHistory.
- If RPE < 10: reset `consecutive_rpe_10` to 0.
- If `consecutive_rpe_10` reaches 3: flag this exercise for forced deload next session.

## Step 7 — Stall / "choking" detection

If BOTH triggers failed (volume ≤ last AND intensity ≤ last) AND this was not already flagged:

Send nudge (once per stall event — track in ExerciseHistory `stall_nudge_sent` flag):
```
Hey — zero progress on [exercise] this session.
No volume gain AND no intensity gain.

Time to eat more? You might be in a slight deficit.
Options: extra meal, peanut butter in shakes, don't skip carbs.

Not a lecture — just the data. Let me know when you've loaded up.
```

Reset `stall_nudge_sent` when progress resumes.

## Step 8 — Update ExerciseHistory (immediately)

For each exercise logged, update the row in `ExerciseHistory`:
```
last_date              → today
last_weight            → top_set_intensity (added weight only for pull-ups)
last_reps              → reps on heaviest set
last_total_volume      → total_volume (true volume for pull-ups)
last_top_set_intensity → top_set_intensity
expected_weight        → calculated in Step 5
expected_reps_per_set  → calculated in Step 5
session_count          → +1
streak                 → +1 if SUCCESS or EXCEEDED, else 0
consecutive_rpe_10     → updated in Step 6
stall_nudge_sent       → updated in Step 7
```

## Step 9 — Close session if this was a "Done" message

If the user sent a batch dump (all exercises at once) or explicitly said "done"/"finished":
- Update `SessionSequence` row for today: `completed = true`
- Update `Progress` row: `last_exercise_time = now`, `duration_minutes = (last − first)`
- Tell the user what's next: "Next: PULL day (Session N+1)"

If the user is logging set-by-set mid-session, do not close — just confirm each set.

## Step 10 — Format the progression report

```
✅ Logged PUSH session:

| Exercise        | Set 1    | Set 2    | Set 3    | Total Vol |
|-----------------|----------|----------|----------|-----------|
| Bench Press     | 60kg × 8 | 65kg × 8 | 65kg × 7 | 1,455kg   |
| ...             | ...      | ...      | ...      | ...       |

📈 PROGRESSION REPORT:
• Bench Press: 1,455kg total, top set 65kg
   → Trigger 1 (Volume): 1,455 < 1,500 ❌
   → Trigger 2 (Intensity): 65kg > 60kg ✅ INTENSITY UP!
   → SUCCESS — next: 67.5kg × 8×3 or 65kg × 10×3

• [exercise showing stall] → [stall nudge]

🔥 3/5 exercises hit at least one trigger.
Next: PULL day (Session N+1)
```

For Pull-ups, show true weight explicitly:
```
| Pull-ups | 5kg added | 68kg true | 8,7,6 | 1,428kg |
```
