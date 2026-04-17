---
name: suggest-deload
description: Offers deload or maintenance options when the user feels weak or wants to drop the weight on an exercise.
user-invocable: true
metadata: {"triggers": ["feeling weak", "deload", "drop the weight", "lighter today", "easy session", "take it easy", "too heavy", "struggling"]}
---

# Suggest Deload

Triggered when the user signals they want a lighter session or to deload a specific exercise.

## Step 1 — Identify scope

Is the user asking to deload:
- A **specific exercise**: "can I drop the weight on bench?"
- **All exercises today**: "feeling weak, easy session today"

## Step 2 — Fetch current targets

For each affected exercise, run `get_exercise_history(exercise_name)`:
- Read `expected_weight` and `expected_reps_per_set`

## Step 3 — Calculate options

| Option | Weight | Reps | When to suggest |
|---|---|---|---|
| **Deload** | expected_weight − 5kg | expected_reps + 2 per set | User feels noticeably weak or RPE has been high |
| **Maintenance** | expected_weight − 2.5kg | same reps | Transitional — not feeling 100% but not bad |
| **Intensity Swap** | same weight | fewer reps, note longer rest | Psychological break without losing the adaptation |

Show the volume comparison so the user understands the trade-off:
- Deload volume = (expected_weight − 5kg) × (expected_reps + 2) × 3
- vs. Target volume = expected_weight × expected_reps × 3

## Step 4 — Format the response

```
No problem. For Bench Press, here are your options:

| Option      | Weight  | Reps target | Approx volume |
|-------------|---------|-------------|---------------|
| Deload      | 55kg    | 10×3        | 1,650kg       |
| Maintenance | 57.5kg  | 8×3         | 1,380kg       |

Last session was 60kg × 8×3 (1,440kg).
Deload keeps volume healthy while giving your CNS a break.

Which one? Or just tell me the weight and I'll log it.
```

## Step 5 — Confirm and update

When user confirms:
- Update `expected_weight` and `expected_reps_per_set` in ExerciseHistory for the chosen option
- Reset `consecutive_rpe_10` to 0 for that exercise (deload counts as a reset)
- Log the session normally via log-workout skill — deload sessions still count for streak continuity

## Notes

- Never judge the user for deloading — it is part of the plan.
- If `consecutive_rpe_10` is already ≥ 3, the deload is forced (not optional) — lead with: "Your data says it's time for a deload — this isn't optional. Here's your plan for today."
- A full-session deload (all exercises) runs this logic for every exercise in today's template.
