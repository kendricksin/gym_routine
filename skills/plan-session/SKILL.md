---
name: plan-session
description: Plans the next gym session with progressive overload targets when the user says they are heading to the gym or asks what to do today.
user-invocable: true
metadata: {"triggers": ["heading to gym", "going to gym", "what to do today", "what's today", "starting push day", "starting pull day", "starting legs day", "session plan", "plan my session"]}
---

# Plan Session

Triggered when the user signals they are heading to the gym or wants to know what to do today.

## Step 1 — Determine next session type

Run `lib/lark_base.py` → `get_last_session_sequence()`.

- If no rows exist yet, session_number = 0 (next will be 1 → PUSH).
- `next_session_number = last_session_number + 1`
- Session type:
  - `next_session_number % 3 == 1` → **PUSH**
  - `next_session_number % 3 == 2` → **PULL**
  - `next_session_number % 3 == 0` → **LEGS**
- If the user explicitly says "starting push/pull/legs day", trust them and use that type instead.

## Step 2 — Load session template

Run `get_session_template(session_type)` → returns ordered list of exercises with `reps_target` and `big_small`.

## Step 3 — Load progressive overload targets for each exercise

For each exercise in the template:
1. Run `get_exercise_history(exercise_name)`.
2. If no history: use the `reps_target` from the template as the starting guide; note "first session — set your own baseline."
3. If history exists, read `expected_weight` and `expected_reps_per_set` — these are today's **Target**.
4. Calculate **Stretch Goal**:
   - If the last session was a SUCCESS → Stretch = `expected_weight + 2.5kg × same_reps` OR `expected_weight × (expected_reps + 1)`.
   - If the last session EXCEEDED → Stretch = `expected_weight + 5kg`.
   - If last session FELL SHORT → no Stretch; show same target with note "hit the reps first."
5. For Pull-ups specifically: run `get_latest_bodyweight()` and display `true_weight = bodyweight + added_weight`.
   **Bodyweight fallback:** If `BodyLog` is empty, ask the user before presenting the plan:
   > "Before we start — what's your current bodyweight? I need it for your pull-up volume tracking."
   Write the reply to `BodyLog` and continue. If no BodyLog entry and no reply, use **63kg** as placeholder and flag it: "(using 63kg placeholder — update with `/weigh in`)."
6. Check `consecutive_rpe_10`:
   - ≥ 2 → add a `⚠️ DELOAD FLAG` warning for that exercise.
   - ≥ 3 → **force** a deload suggestion (drop 5kg, add 2 reps target).

## Step 4 — Format and send session plan

Output the plan as a table:

```
🔄 Next up: PUSH day (Session N in sequence)

📊 Your targets (3 sets each):
┌─────────────────────┬──────────────┬──────────────┬──────────────┐
│ Exercise            │ Last Session │ Target Today │ Stretch Goal │
├─────────────────────┼──────────────┼──────────────┼──────────────┤
│ Bench Press         │ 60kg × 8×3   │ 62.5kg × 8×3 │ 65kg × 8×3   │
│ ...                 │ ...          │ ...          │ ...          │
└─────────────────────┴──────────────┴──────────────┴──────────────┘

💡 weight × reps × sets
💪 Hit "Target Today" → I'll bump weight next session.
📈 "Stretch Goal" → only if you feel strong.

Swap any exercise? Otherwise, crush it.
```

If any exercise has a `⚠️ DELOAD FLAG`, append it below the table.

## Step 5 — Open the session

Insert a new row in `SessionSequence`:
- `session_number` = next_session_number
- `session_type` = determined type
- `date` = today's date
- `completed` = false

Record `first_exercise_time` as null until the first set is logged.

## Notes

- Do NOT tie sessions to days of the week. Rotation is sequential only.
- If the user messages "heading to gym" and a session is already open today (same date, completed=false): remind them of the current session state, list exercises already logged, and continue — do not open a new session.
- This same logic runs when user says "starting [type] day" (SESSION_OPEN intent).
