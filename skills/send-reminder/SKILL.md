---
name: send-reminder
description: Proactive scheduled reminders — weigh-in nudges, session nudges, and forced deload alerts. Runs on a cron schedule, not triggered by user messages.
user-invocable: false
disable-model-invocation: false
metadata: {"schedule": "0 20 * * *", "note": "Runs at 8pm daily. Checks conditions and sends nudge only if a trigger is met."}
---

# Send Reminder

This skill runs on a daily cron schedule (8pm). It checks multiple conditions and sends a message only if a trigger is met. It is not triggered by user messages.

**Important:** Each nudge type is sent at most once per trigger event. The agent must track when a nudge was last sent to avoid repeated nagging.

---

## Check 1 — Weigh-in reminder

Query `BodyLog`, find the most recent `log_date`.

If `today − last_log_date ≥ 7 days`:

Send:
```
Hey — time to step on the scale 📊
It's been [N] days since your last check-in.
Just reply with your weight when you get a chance.
```

Condition: Only send if not already sent in the last 7 days for this reason.

---

## Check 2 — Session nudge (48-hour inactivity)

Query `SessionSequence`, find the most recent `date` where `completed = true`.

If `today − last_completed_date ≥ 2 days`:

Determine next session type (same logic as plan-session):
- `next_session_number = last_session_number + 1`
- session_type from `next_session_number % 3`

Send:
```
It's been [N] days since your last session.
Next up: [PUSH / PULL / LEGS] day (Session N).
Ready when you are — just say "heading to gym."
```

Condition: Only send once per gap event (not daily if they keep ignoring it).

---

## Check 3 — Forced deload alert

Query `ExerciseHistory`. Find any exercise where `consecutive_rpe_10 ≥ 3`.

For each such exercise, send:
```
⚠️ Deload required: [Exercise Name]
You've hit RPE 10 three sessions in a row.
Next session, I'll drop the weight 5kg and add 2 reps to the target.
This isn't optional — your CNS needs recovery. Trust the process.
```

Condition: Only send once per exercise per deload event (reset when deload is confirmed or weight drops).

---

## Check 4 — Session auto-close (10pm cutoff)

Query `SessionSequence`. Find any row where `date = today` and `completed = false`.

If current time ≥ 22:00:
- Update the row: `completed = true`
- Compute `duration_minutes` from `first_exercise_time` to `last_exercise_time` in WorkoutLog for today
- Update `Progress` row with `last_exercise_time` and `duration_minutes`
- Do NOT send a message to the user (silent close)

Also applies inactivity close: if last WorkoutLog entry for today has `timestamp` more than 60 minutes ago and session is still open — close it silently.

---

## Notes

- This skill never nags. Each check has a per-event cooldown.
- The 10pm auto-close and inactivity close are silent (no message sent).
- Weigh-in reminder and session nudge are conversational (message sent to user in Lark DM).
- Forced deload alert is sent as a Lark DM and also flagged in the next plan-session output.
