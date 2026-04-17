---
name: suggest-swap
description: Suggests alternative exercises when the user wants to swap an exercise in today's session.
user-invocable: true
metadata: {"triggers": ["swap", "instead of", "replace", "alternative to", "can I do something else", "don't want to do", "substitute"]}
---

# Suggest Swap

Triggered when the user wants to replace an exercise with an alternative.

## Step 1 — Identify the exercise to replace

Parse the current exercise name from the user's message. Fuzzy match against ExerciseCatalog.

Example: "Can I swap bench press for something else?" → exercise=Bench Press

## Step 2 — Find alternatives

Query `ExerciseCatalog` where:
- `category` matches (push / pull / legs)
- `muscle_group` matches (e.g., chest)
- `exercise_id` ≠ current exercise

Return up to 3 alternatives. Prefer same `big_small` classification first (swap a BIG for a BIG, SMALL for a SMALL). If no same-class alternative, offer a cross-class swap with a note.

## Step 3 — Fetch history for each alternative

For each alternative, run `get_exercise_history(exercise_name)`:
- If history exists: show `expected_weight × expected_reps_per_set`
- If no history: show "first time — use template target"

## Step 4 — Format the response

```
Sure! For PUSH day chest (replacing Bench Press):

• Incline Bench Press — last: 55kg × 8×3 (same BIG)
• Chest Press Machine — last: 50kg × 10×3 (same BIG)
• Cable Fly — last: 12kg × 12×3 (isolation, SMALL)

Which one? I'll update today's plan.
```

## Step 5 — Confirm the swap

When user picks one:
- Update today's session plan in the conversation context
- Note the swap clearly so it's logged correctly in log-workout
- Progressive overload history for the chosen exercise carries over independently

## Notes

- Never suggest an exercise from a different session type (no suggesting Pull-ups on PUSH day).
- If the user asks to swap mid-session (already logged some sets), flag that: "You've already done 2 sets of Bench — want to finish or log what you have and swap for remaining sets?"
