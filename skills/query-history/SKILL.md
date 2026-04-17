---
name: query-history
description: Answers questions about past workout performance, PRs, trends, and exercise history from Lark Base.
user-invocable: true
metadata: {"triggers": ["what's my PR", "show me my", "how am I doing", "history", "last time I did", "how much did I lift", "progress", "bench history", "pull-up PR", "best set"]}
---

# Query History

Triggered when the user asks about past performance, personal records, or trends.

## Step 1 — Parse the query

Identify:
- **Which exercise(s)?** Fuzzy match against ExerciseCatalog names.
- **What metric?** PR (max weight or volume), last session, trend over N sessions, streak.
- **Scope?** Single exercise, full session, or all exercises.

Examples:
- "What's my pull-up PR?" → exercise=Pull-ups, metric=all-time max top_set_intensity
- "How much did I bench last session?" → exercise=Bench Press, metric=last session
- "Show me my bench press history" → exercise=Bench Press, metric=trend (last 5 sessions)
- "How am I doing overall?" → all exercises, metric=current streak + last session summary

## Step 2 — Fetch data

**For a single exercise:**
1. `get_exercise_history(exercise_name)` → current state row
2. Query `WorkoutLog` filtered by `exercise_name`, sorted by date descending, limit 5 sessions

**For all-time PR:**
- Scan WorkoutLog for max `weight_kg` (top set) and max session volume for that exercise
- For Pull-ups: PR uses true weight (bodyweight + added_weight at the time — use BodyLog closest to that date)

**For trend:**
- Group WorkoutLog rows by date for the exercise
- Compute total_volume and top_set_intensity per session date
- Show last 5 sessions with direction indicator (↑ ↓ →)

## Step 3 — Format the response

**Single exercise — last session:**
```
Last Legs day (April 10): Leg Press 80kg × 12, 12, 10
Total volume: 2,880kg | Top set: 80kg
Next target: 82.5kg × 10×3
```

**Trend view:**
```
📊 Bench Press — last 5 sessions:
Apr 14  65kg top | 1,455kg vol  ✅ PR vol
Apr 10  62.5kg   | 1,500kg vol  ↑
Apr 7   60kg     | 1,440kg vol  ↑
Apr 3   60kg     | 1,350kg vol  →
Mar 31  57.5kg   | 1,320kg vol  ↑
Current streak: 3 ✅
```

**PR query:**
```
Pull-up PR:
  Max added weight: 10kg (true 73kg) — March 15
  Max session volume: 1,512kg — April 2
  Current bodyweight: 63kg | Today's true weight: 68kg (5kg added)
```

## Notes

- For Pull-up volume comparisons, always use true weight (bodyweight + added).
- If no history exists for an exercise, say so clearly: "No history found for Romanian Deadlift yet."
- Keep responses tight — lead with the number the user asked for, add context after.
