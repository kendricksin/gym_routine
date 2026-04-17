---
name: log-bodyweight
description: Records a bodyweight check-in and tracks bulk progress toward the 65kg goal. Also accepts bodyfat estimates.
user-invocable: true
metadata: {"triggers": ["I weigh", "weight is", "kg today", "bodyfat", "weigh in", "checked my weight", "scale said", "I'm at"]}
---

# Log Bodyweight

Triggered when the user reports their bodyweight or bodyfat.

## Step 1 — Parse the input

Extract:
- `weight_kg` — required (e.g., "63.5kg", "63.5", "I'm at 63.5")
- `bodyfat_pct` — optional (e.g., "about 18% bodyfat", "bf 18")

If only one number is present and it is between 40–150, treat it as bodyweight.
If two numbers are present and one is plausibly a percentage (5–40), treat that as bodyfat.

## Step 2 — Write to BodyLog

Create a row in `BodyLog`:
```
log_date    → today (YYYY-MM-DD)
weight_kg   → parsed value
bodyfat_pct → parsed value or null
notes       → empty
```

## Step 3 — Fetch previous entry for comparison

Query `BodyLog`, sort by `log_date` descending, take the second-most-recent row.

Compute:
- `delta_weight` = new − previous
- `days_since_last` = today − previous log_date

## Step 4 — Format the response

**If weight increased:**
```
✅ Logged: 63.8kg
↑ +0.3kg since last check-in (7 days ago)
Goal: 65kg — 1.2kg to go. On track. 💪
```

**If weight held steady:**
```
📊 Logged: 63.5kg
→ No change since last check-in (5 days ago)
Goal: 65kg — 1.5kg to go.
Consistent is fine — make sure you're eating enough.
```

**If weight dropped and user has been stalling on lifts:**
```
📉 Logged: 63.0kg
↓ −0.5kg since last check-in (10 days ago)
Goal: 65kg — 2.0kg to go.

Your lifts have also been stalling — you're likely in a deficit.
Add an extra meal or more carbs around training. The scale and the bar both need fuel.
```

**If weight dropped but lifts are progressing:**
```
📉 Logged: 63.0kg
↓ −0.3kg since last check-in (7 days ago)

Lifts are still progressing though — could just be water weight or timing.
Keep an eye on it. Weigh in again in 5–7 days.
```

**If bodyfat also logged:**
```
Also logged: ~18% bodyfat
Lean mass estimate: ~52.5kg
```

## Notes

- The user's bulk goal is 65kg. Always show progress toward it.
- Do not push protein tracking — bodyweight trend is the signal.
- For pull-up volume calculations, the new bodyweight is used immediately in the next log-workout session.
- The reminder trigger (send-reminder skill) will nudge the user if no check-in in 7–14 days.
