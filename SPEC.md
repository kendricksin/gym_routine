# Gym Routine Tracking System — Specification

## 1. Concept & Vision

A lightweight workout tracking system rotating through **Push**, **Pull**, and **Legs** sessions across a 5-day week. The system acts as a knowledgeable gym buddy: when you say you're heading to the gym, it checks your history, suggests today's exercises with appropriate weights, and logs your workout afterward. No more wondering what to do or what weight to start with.

## 2. Core Philosophy

- **Sequential rotation:** A → B → C → A → B → C (no days tied to sessions)
  - Some weeks 5 sessions, some weeks 6 sessions — agent tracks position in sequence
  - If you miss a session, you continue from where you left off (not restart)
- **Big first:** Each session starts with the primary compound movement
- **Small between:** Isolation exercises are scattered between sets of compounds for active recovery
- **Progressive overload:** **Every session must be harder than the last.** Agent tracks expected vs actual and sets new targets accordingly. Weight OR reps must go up — never plateau.
- **Intensity matters:** Progression is a "Success" if EITHER total volume increases OR the weight on the heaviest set increases. This prevents the "lower weight to chase volume" trap.
- **Event-driven:** Lark Base functions as an event log — the agent queries history to inform today's session

## 2.1 Progressive Overload Rules (CRITICAL)

Each exercise: **3 sets × target reps per set**

The rep target is per set. So "8-10 reps" means 3 sets of 8-10 reps each (24-30 total reps).

### Success Criteria (Two Triggers)

Progression is a "Success" if **EITHER**:
1. **Volume increased:** Total volume (sum of weight×reps across all sets) > last session's volume
2. **Top set intensity increased:** Weight used on the heaviest set increased

**Why both?** Example: 60kg×10=600kg vs 65kg×8=520kg — volume dropped but intensity went up. Agent recognizes this as success, not failure.

### Standard Progression

| Last Session Result | Next Session Target |
|--------------------|---------------------|
| All 3 sets hit target reps | **+2.5kg** or **+1 rep per set** |
| Exceeded target (hit more reps on 2+ sets) | **+5kg** or **+2 reps per set** |
| Fell short on reps (1-2 sets) | **Same weight, chase those reps first** |
| Failed completely (couldn't complete most sets) | **Drop 5kg, rebuild** |

### Deload Option (When Feeling Weak)

If the user сообщает they feel weak or wants a lighter session, the agent can suggest:

| Option | Weight | Reps | Notes |
|--------|--------|------|-------|
| **Deload** | -5kg from last session | +2 reps per set | Same volume feel, less strain |
| **Maintenance** | -2.5kg | Same reps | Transitional |
| **Intensity Swap** | Same weight | Fewer reps, longer rest | Psychological break |

### Overtraining Flag (RPE-Based)

If user logs **RPE 10** (Absolute Max Effort) for 3 consecutive sessions on the same exercise, the agent **must** force a deload recommendation, even if rep targets were met.

**RPE Scale:**
- 1-5: Light (warmup)
- 6-7: Moderate (could do 3+ more reps)
- 8: Challenging (could do 1-2 more reps)
- 9: Very hard (could do 1 more rep)
- 10: Absolute max (nothing left)

### "Choking" Detection — Eat More Reminder

If an exercise shows **zero progress on BOTH triggers** (no volume increase AND no intensity increase) for **one session**, the agent sends an "eat more" nudge:

```
Agent: Hey — I'm seeing zero progress on Squats this session.
       No volume gain AND no intensity gain.

       🍗 Time to eat more? You might be in a slight deficit.
       
       Options:
       • Eat an extra meal today
       • Add peanut butter to your shakes
       • Don't skip the carbs — they're your friend for lifts
       
       This isn't a lecture, just tracking the data. 
       Keep pushing and let me know when you've loaded up!
```

**Trigger condition:** Both triggers fail (volume ≤ last AND intensity ≤ last) for the same exercise in the same session.

**One nudge per stall event** — agent tracks if it already nudged for this stall and doesn't repeat. Resets when user shows progress again.

### Bodyweight-Adjusted Volume (For Pull-ups)

For pull-up exercises, "volume" includes bodyweight. The agent pulls the latest weight from `BodyLog` to calculate **Total Pulling Weight = Bodyweight + Added Weight**.

Example: 63kg person with 5kg added weight doing 8 reps = 68kg × 8 = 544kg true pulling volume.

**Volume tracking:** Total volume = `weight × reps_per_set × 3_sets`. This must increase each session.

**Rep range guidance:**
- BIG exercises: 8-10 reps (compound, heavier weight)
- SMALL exercises: 10-12 reps (isolation, lighter weight, higher reps acceptable)

## 3. Session Structure

### Session 1: PUSH (Chest, Shoulders, Triceps)
**Theme:** Upper body pushing muscles

**Exercise Order:**
1. **Compound (BIG):** Bench Press / Chest Press / Incline Press
2. **Isolation:** Lateral Raises
3. **Compound (BIG):** Overhead Press / Shoulder Press
4. **Isolation:** Cable Fly / Pec Deck
5. **Isolation:** Tricep Pushdown / Overhead Extension

### Session 2: PULL (Back, Biceps, Rear Delts)
**Theme:** Upper body pulling muscles

**Exercise Order:**
1. **Compound (BIG):** Pull-ups / Lat Pulldown
2. **Isolation:** Seated Cable Row / Single Arm Row
3. **Compound (BIG):** Face Pulls / Rear Delt Flyes
4. **Isolation:** Bicep Curl Machine / Dumbbell Curls
5. **Isolation:** Plank / Ab Wheel (for core)

### Session 3: LEGS (Quads, Hamstrings, Glutes, Calves)
**Theme:** Lower body

**Exercise Order:**
1. **Compound (BIG):** Leg Press / Squats
2. **Isolation:** Leg Extension (teardrop)
3. **Compound (BIG):** Romanian Deadlift / Leg Curl
4. **Isolation:** Hip Abductor / Adductor
5. **Isolation:** Calf Raises / Glute Kickback

## 4. Exercise Catalog (Lark Base Table: `ExerciseCatalog`)

Each exercise has variants so the agent can suggest alternatives and the user can swap based on mood/equipment.

| exercise_id | name | category | muscle_group | primary | equipment | big_small |
|-------------|------|----------|--------------|---------|-----------|-----------|
| 1 | Bench Press | push | chest | yes | barbell | BIG |
| 2 | Incline Bench Press | push | chest | yes | barbell | BIG |
| 3 | Chest Press Machine | push | chest | yes | machine | BIG |
| 4 | Cable Fly | push | chest | no | cable | SMALL |
| 5 | Pec Deck | push | chest | no | machine | SMALL |
| 6 | Overhead Press | push | shoulders | yes | barbell | BIG |
| 7 | Shoulder Press Machine | push | shoulders | yes | machine | BIG |
| 8 | Lateral Raises | push | shoulders | no | dumbbell | SMALL |
| 9 | Tricep Pushdown | push | triceps | no | cable | SMALL |
| 10 | Overhead Tricep Extension | push | triceps | no | dumbbell | SMALL |
| 11 | Skull Crushers | push | triceps | no | barbell | SMALL |
| 12 | Pull-ups | pull | back | yes | bodyweight | BIG |
| 13 | Lat Pulldown | pull | back | yes | cable | BIG |
| 14 | Seated Cable Row | pull | back | no | cable | SMALL |
| 15 | Single Arm Dumbbell Row | pull | back | no | dumbbell | SMALL |
| 16 | Face Pulls | pull | rear delts | no | cable | SMALL |
| 17 | Rear Delt Flyes | pull | rear delts | no | dumbbell | SMALL |
| 18 | Bicep Curl Machine | pull | biceps | no | machine | SMALL |
| 19 | Dumbbell Bicep Curls | pull | biceps | no | dumbbell | SMALL |
| 20 | Hammer Curls | pull | biceps | no | dumbbell | SMALL |
| 21 | Plank | pull | core | no | bodyweight | SMALL |
| 22 | Ab Wheel | pull | core | no | ab wheel | SMALL |
| 23 | Leg Press | legs | quads | yes | machine | BIG |
| 24 | Barbell Squat | legs | quads | yes | barbell | BIG |
| 25 | Hack Squat Machine | legs | quads | yes | machine | BIG |
| 26 | Leg Extension | legs | quads | no | machine | SMALL |
| 27 | Romanian Deadlift | legs | hamstrings | yes | barbell | BIG |
| 28 | Lying Leg Curl | legs | hamstrings | yes | machine | BIG |
| 29 | Seated Leg Curl | legs | hamstrings | yes | machine | BIG |
| 30 | Hip Abductor | legs | glutes | no | machine | SMALL |
| 31 | Hip Adductor | legs | glutes | no | machine | SMALL |
| 32 | Calf Raises | legs | calves | no | machine | SMALL |
| 33 | Glute Kickback | legs | glutes | no | machine | SMALL |
| 34 | Glute Press | legs | glutes | yes | machine | BIG |
| 35 | Weighted Back Extension | legs | lower back | yes | machine | BIG |

## 5. Lark Base Structure

### Table: `ExerciseCatalog`
Seed with 35+ exercises above. Agent reads this to suggest options.

### Table: `Sessions`
| column | type | description |
|--------|------|-------------|
| session_id | int | 1=Push, 2=Pull, 3=Legs |
| name | string | Push / Pull / Legs |
| description | string | Theme description |

### Table: `WorkoutLog` (Event Log — One Row Per Set)

Each set is logged separately. This allows weights to vary between sets (e.g., warmup sets, failure sets, progressive sets).

| column | type | description |
|--------|------|-------------|
| log_id | int | Auto-increment |
| timestamp | datetime | When logged |
| date | date | Date of workout |
| session_type | string | "push", "pull", or "legs" |
| exercise_name | string | Exact name performed |
| set_number | int | Set 1, 2, 3... |
| weight_kg | float | Weight used for this set |
| reps | int | Reps performed for this set |
| RPE | int | 1-10 scale (optional) |
| notes | string | Form notes, variations, etc. |

**Example logging (Leg Curl across a session):**
```
log_id=101, date=2026-04-14, exercise_name="Leg Curl", set_number=1, weight_kg=40, reps=8
log_id=102, date=2026-04-14, exercise_name="Leg Curl", set_number=2, weight_kg=42.5, reps=8
log_id=103, date=2026-04-14, exercise_name="Leg Curl", set_number=3, weight_kg=42.5, reps=8
```

**This structure allows the agent to:**
- See exact weights used per set
- Detect if weights increased/decreased during the session
- Calculate volume accurately per exercise per session
- Suggest deload options when needed

### Table: `ExerciseHistory` (State — Agent Updates Immediately After Workout)

| column | type | description |
|--------|------|-------------|
| exercise | string | Exercise name |
| last_date | date | Last performed |
| last_weight | float | Weight used on heaviest set (most recent) |
| last_reps | int | Reps on heaviest set |
| last_total_volume | float | Sum of (weight × reps) across all sets in last session |
| last_top_set_intensity | float | Weight on heaviest single set |
| expected_weight | float | Target weight for NEXT session |
| expected_reps_per_set | int | Target reps per set for NEXT session |
| session_count | int | Times performed |
| streak | int | Consecutive sessions meeting expectations |
| consecutive_rpe_10 | int | Count of consecutive sessions with RPE 10 on this exercise |

**The `expected_weight` and `expected_reps_per_set` columns are what the agent uses when planning a session. These are updated immediately after every logged workout based on the progressive overload rules.**

**Example row:** Bench Press | 2026-04-14 | 65kg | 7 | 1,455kg | 65kg | 62.5kg | 8 | 5 | 3 | 0

**The agent updates this table immediately after logging a workout** (not lazily derived on query). This enables instant feedback like "That's a 4-session PR streak on Bench Press!"

**consecutive_rpe_10** tracks if a deload should be forced.

### Table: `Progress`
| column | type | description |
|--------|------|-------------|
| date | date | Session date |
| session_type | string | push/pull/legs |
| exercises_completed | int | Count |
| total_volume | float | weight × reps sum |
| first_exercise_time | datetime | Timestamp of first set logged in session |
| last_exercise_time | datetime | Timestamp of last set logged in session |
| duration_minutes | int | Derived: (last_exercise_time − first_exercise_time) in minutes. Set when session closes. |
| notes | string | How session felt |

### Table: `BodyLog` (Periodic Weight/Bodyfat Tracking)

Track bodyweight periodically to calculate true pulling volume for pull-ups and monitor 63kg→65kg bulk progress.

| column | type | description |
|--------|------|-------------|
| log_date | date | Date measured |
| weight_kg | float | Bodyweight in kg |
| bodyfat_pct | float | Estimated body fat % (optional) |
| notes | string | Any observations |

**Agent uses this to:**
- Calculate true pull-up volume: `Total Pulling Weight = Bodyweight + Added Weight`
- Track bulk progress toward 65kg goal

**Agent sends random reminders:**
- Every 7-14 days: "Hey, time to weigh in? 📊" (user just replies with their weight)
- Occasional: "Got a sec to estimate your bodyfat? No pressure, just tracking the trend."

**No protein tracking** — it's too exhausting to count. Agent focuses on weight and bodyfat trends instead.

### Table: `SessionSequence` (State — Tracks Position in A-B-C Rotation)

Because the rotation is sequential (A-B-C-A-B-C) not tied to days of the week, the agent must track where you are in the sequence.

| column | type | description |
|--------|------|-------------|
| session_number | int | Sequential session count (1, 2, 3...) |
| session_type | string | "push", "pull", or "legs" |
| date | date | When performed |
| completed | bool | Whether session was completed |

**The agent uses this to determine "what's next" when you message "heading to gym."**

## 6. Agent Interaction Flow

### Flow 1: "I'm going to the gym" → Agent Plans Session (with Progressive Overload)

```
User: Heading to the gym

Agent: 🔄 Next up: PUSH day (Session 7 in sequence)

📊 Your progression targets (3 sets each):
┌─────────────────────┬──────────────┬──────────────┬──────────────┐
│ Exercise            │ Last Session │ Target Today │ Stretch Goal │
├─────────────────────┼──────────────┼──────────────┼──────────────┤
│ Bench Press         │ 60kg × 8×3   │ 62.5kg × 8×3 │ 65kg × 8×3   │
│ Lateral Raises      │ 8kg × 12×3   │ 8kg × 13×3   │ 10kg × 12×3  │
│ Overhead Press      │ 40kg × 10×3  │ 42.5kg × 10×3│ 45kg × 9×3   │
│ Cable Fly           │ 12kg × 12×3  │ 12kg × 13×3  │ 15kg × 12×3  │
│ Tricep Pushdown     │ 25kg × 12×3  │ 25kg × 13×3  │ 27.5kg × 12×3│
└─────────────────────┴──────────────┴──────────────┴──────────────┘

💡 Format: weight × reps × sets
💪 "Target Today" = your goal. Hit these reps and I'll bump weight next time.
📈 "Stretch Goal" = if you're feeling strong, go for these.

⚠️ DELOAD FLAG: Lateral Raises — RPE 10 logged 2 sessions in a row.
   Consider a lighter session: 8kg × 14×3 instead.

Swap any exercise? Otherwise, crush it! 🔥
```

**Progressive overload context shown:** User met Bench Press target last time (60kg×8×3 = 60kg, 8 reps, 3 sets), so today's target is 62.5kg×8×3. Stretch shows 65kg if feeling strong.

**If user had fallen short last time:**
```
Agent: 📊 Your progression targets:
• Bench Press: Last was 60kg × 6×3 (fell short of 60kg × 8×3)
  → Same 60kg today, goal is 60kg × 8×3. Get those reps back first!
```

### Flow 2: Post-Workout Logging (with Set-by-Set Detail)

```
User: Done! Bench 60kg 8, 65kg 8, 65kg 7  Lateral 10kg 12,10,10  
      OHP 40kg 10,10,9  Cable fly 15kg 12,12,12  Tricep 30kg 12,12,12

Agent: ✅ Logged PUSH session:
        
        | Exercise         │ Set 1    │ Set 2    │ Set 3    │ Total Vol │
        |------------------|----------|----------|----------|-----------|
        | Bench Press      │ 60kg × 8 │ 65kg × 8│ 65kg × 7│ 1,455kg  |
        | Lateral Raises   │ 10kg×12  │ 10kg×10 │ 10kg×10 │ 320kg    |
        | Overhead Press   │ 40kg×10  │ 40kg×10 │ 40kg × 9│ 1,160kg  |
        | Cable Fly        │ 15kg×12  │ 15kg×12 │ 15kg×12 │ 540kg    |
        | Tricep Pushdown  | 30kg×12  │ 30kg×12 │ 30kg×12 │ 1,080kg  |
        
        📈 PROGRESSION REPORT (3 sets each):
        • Bench Press: 1,455kg total, top set 65kg
           → Trigger 1 (Volume): 1,455 < 1,500 ❌
           → Trigger 2 (Top Set): 65kg > 60kg ✅ INTENSITY UP!
           → SUCCESS — weight increased even though volume dipped slightly
           → Next: 67.5kg × 8×3 or 65kg × 10×3 💪
        • Lateral Raises: 320kg total, top set 10kg
           → Both triggers fell short
           → Same weight, aim for 10kg × 13×3 next time
        • OHP: 1,160kg total, top set 40kg
           → Fell short on volume and intensity
           → Fell short. Next: 40kg × 10×3 to rebuild confidence, then bump weight
        • Cable Fly: 540kg total, top set 15kg
           → Trigger 1 (Volume): 540 > 468 ✅ VOLUME UP!
           → SUCCESS
           → Next: 15kg × 13×3 or 17.5kg × 12×3
        • Tricep Pushdown: 1,080kg total, top set 30kg
           → Trigger 1 (Volume): 1,080 > 900 ✅ VOLUME UP!
           → SUCCESS
           → Next: 32.5kg × 12×3 or 30kg × 14×3
        
        🔥 3/5 exercises hit at least one trigger (success)!
        Same targets next time for Lateral Raises and OHP.
        Next: PULL day (Session 8) 💪
```

**Volume calculation:** Sum of (weight × reps) for each set. If weights vary across sets, each set is calculated separately then summed.

### Flow 3: Post-Workout Logging — When Falling Short

```
User: Done! Bench 55kg 6,6,5  Lateral 8kg 10,10,9  OHP 40kg 8,7,7
      Cable fly 12kg 10,10,10  Tricep 25kg 10,10,10

Agent: ✅ Logged PUSH session:
        
        📉 PROGRESSION REPORT (3 sets each):
        • Bench Press: 55kg × 17 total, top set 55kg
           → Both triggers fell short — rebuilding phase
           → Next: 55kg × 8×3 to get reps back, then bump weight
        • Lateral Raises: 8kg × 29 total, top set 8kg
           → Same weight, aim for 8kg × 13×3 next time
        • OHP: 40kg × 22 total, top set 40kg
           → Same weight next time
        • Cable Fly: 12kg × 30 total, top set 12kg
           → Hit target 12kg × 12×3 ✓
           → Next: 12kg × 13×3
        • Tricep Pushdown: 25kg × 30 total, top set 25kg
           → Hit target 25kg × 12×3 ✓
           → Next: 25kg × 13×3
        
        Rebuilding session — 2/5 hit target. 
        Same weights next time, focus on hitting those rep targets first.
        Next: PULL day (Session 8) 💪
```

### Flow 3b: Requesting Deload Option

```
User: I'm feeling weak today, can I drop the weights on bench?

Agent: No problem! For Bench Press, here are your deload options:
       
       | Option      | Weight | Target Reps | Notes              |
       |-------------|--------|-------------|---------------------|
       | Deload      | 55kg   | 10-12 × 3   | Same feel, less strain |
       | Maintenance | 57.5kg | 8-10 × 3    | Transitional         |
       
       Your last session was 60kg × 8×3.
       Go with 55kg × 10×3 and you'll rebuild that mind-muscle connection.
       Want me to set up a deload session plan?
```

### Flow 3c: Logging Pull-ups (With Bodyweight Adjustment)

```
User: Done! Pull-ups 5kg 8,7,6

Agent: ✅ Logged PULL session:
       
       Your bodyweight today: 63.0kg
       
       | Exercise │ Added Wt │ True Wt │ Sets │ Total Vol │
       |----------|----------|---------|------|-----------|
       | Pull-ups | 5kg     | 68kg    │ 8,7,6│ 1,428kg  |
       
       📈 PROGRESSION REPORT:
       • Pull-ups: 68kg true weight × 21 reps = 1,428kg total
          → Previous true volume: 1,365kg (65kg × 21 reps)
          → VOLUME UP! +63kg 💪
          → Next: 5kg added (68kg true) × 8-10 × 3
       
       Next: LEGS day (Session 9) — don't skip leg day! 💪
```

**Bodyweight auto-added:** When logging pull-ups, the agent pulls latest bodyweight from `BodyLog` and adds it to the logged weight to calculate true pulling volume.

### Flow 4: Exercise Swap Request

```
User: Can I swap bench press for something else?

Agent: Sure! For Push day chest exercises you could do:
       • Incline Bench Press (60kg last time)
       • Chest Press Machine (50kg last time)
       • Cable Fly (pure isolation, 12kg last time)
       
       Let me know which one and I'll update the plan.
```

## 7. Session Templates (Lark Base Table: `SessionTemplates`)

Pre-defined exercise order per session type. **All exercises: 3 sets.** Agent reads this to construct the session plan, then overlays historical weights.

| template_id | session_type | exercise_name | order | sets | reps_target | small_big |
|-------------|--------------|---------------|-------|------|-------------|-----------|
| 1 | push | Bench Press | 1 | 3 | 8-10 | BIG |
| 2 | push | Lateral Raises | 2 | 3 | 10-12 | SMALL |
| 3 | push | Overhead Press | 3 | 3 | 8-10 | BIG |
| 4 | push | Cable Fly | 4 | 3 | 10-12 | SMALL |
| 5 | push | Tricep Pushdown | 5 | 3 | 10-12 | SMALL |
| 6 | pull | Pull-ups | 1 | 3 | 6-10 | BIG |
| 7 | pull | Seated Cable Row | 2 | 3 | 10-12 | SMALL |
| 8 | pull | Face Pulls | 3 | 3 | 12-15 | SMALL |
| 9 | pull | Bicep Curl Machine | 4 | 3 | 10-12 | SMALL |
| 10 | pull | Plank | 5 | 3 | 60s | SMALL |
| 11 | legs | Leg Press | 1 | 3 | 10-12 | BIG |
| 12 | legs | Leg Extension | 2 | 3 | 10-12 | SMALL |
| 13 | legs | Romanian Deadlift | 3 | 3 | 8-10 | BIG |
| 14 | legs | Hip Abductor | 4 | 3 | 12-15 | SMALL |
| 15 | legs | Calf Raises | 5 | 3 | 15-20 | SMALL |

**reps_target** = target reps per set. 3 sets of 8 = 24 total reps. 3 sets of 10 = 30 total reps.

## 8. Session Rotation (Sequential A-B-C)

The rotation is **sequential**, not tied to calendar days:
- Session 1 = PUSH, Session 2 = PULL, Session 3 = LEGS
- Then back to PUSH → PULL → LEGS → PUSH...
- Some weeks you might do 5 sessions, some weeks 6

**No session is "skipped" — if you miss Wednesday, Thursday is still PULL (not Legs to "catch up"). The sequence continues from where you left off.**

**SessionSequence table tracks:**
- `session_number` (1, 2, 3, 4, 5...) — sequential count, never resets
- `session_type` — push/pull/legs based on `(session_number % 3)`
  - session_number % 3 == 1 → push
  - session_number % 3 == 2 → pull
  - session_number % 3 == 0 → legs
- `date` — when it happened
- `completed` — bool

## 9. Agent Skill Architecture (Proactive Coach)

The agent operates as a **Proactive Coach** — not a passive spreadsheet. It has five core skills that work together to create a "gym buddy" experience.

---

### Skill 1: Semantic Log Parser ("The Listener")

Parses messy real-world text into clean Lark Base records. Hands shake after pull-ups — you shouldn't have to type into cells.

**Input patterns recognized:**
- `"Bench 60 8,8,7"` → exercise=Bench Press, weights=[60,60,60], reps=[8,8,7]
- `"leg press 80kg 12, 12, 10"` → exercise=Leg Press, weights=[80,80,80], reps=[12,12,10]
- `"did 12 reps at 40kg for leg press"` → fuzzy match to "Leg Press"
- `"Pull-ups 5kg 8,7,6"` → exercise=Pull-ups (added weight only, bodyweight auto-added)

**Coach Layer — Validation Loop:**
If user provides weight/reps but omits RPE, agent prompts:
> *"Got the numbers. How was the intensity? Give me an RPE from 1–10 (10 being absolute failure)."*

---

### Skill 2: Statistical Query Engine ("The Historian")

Instant retrieval of historical data during conversation.

**User queries:**
- *"What's my pull-up PR?"*
- *"How much did I lift last legs day?"*
- *"Show me my bench press history"*

**Agent response example:**
> *"Last Legs day (April 10), you hit 80kg on Leg Press for 12, 12, 10. Your all-time volume PR for that exercise is 2,880kg. Let's aim for 2,900kg today."*

---

### Skill 3: Logical Progression Brain ("The Strategist")

Applies Section 2.1 rules in real-time and **explains the why**.

**Agent explains every weight bump:**
> *"Since you hit all 10 reps on Chest Press last time, I've bumped you up +2.5kg today. It's going to feel heavy, but the data says you're ready."*

**Agent explains every regression:**
> *"Your Shoulder Press stalled twice. I'm dropping you to 40kg to rebuild confidence before we push again. Trust the process."*

---

### Skill 4: Reminder Trigger (Technical Capability)

**What it IS (Technical):** Time-based or event-based triggers that send messages based on Lark Base data conditions.

**Trigger conditions:**
- Last BodyLog entry is 7+ days old → send weigh-in reminder
- Last session was 48+ hours ago → send "ready for next session?" nudge
- An exercise shows zero progress on both triggers (one session) → send "eat more" nudge
- consecutive_rpe_10 ≥ 3 on an exercise → send forced deload recommendation

**Implementation:** Runs as an OpenClaw cron skill (scheduled nightly at 20:00). Polls Lark Base and sends Lark Bot DMs when trigger conditions are met.

---

### Skill 5: RPE Corrector (Technical Capability)

**What it IS (Technical):** Compares Weight/Reps against RPE to detect ego-lifting risk.

**Rule:** If user hits target reps but RPE ≥ 9 on 2+ consecutive sessions, recommend **keeping same weight** next session with focus on controlled reps at RPE 8.

**Implementation:** Runs during LOG_WORKOUT. No external trigger needed.

---

## Persona: Proactive Coach (Wrapper Layer)

**NOT a separate skill** — this is the *tone and presentation* applied to all skill outputs.

**When active, the coach:**
- Explains the "why" behind every weight decision
- Celebrates with data: *"That's a 5% volume jump!"*
- Offers encouragement when stalling: *"Trust the process — deload week rebuilds stronger"*
- Nudges proactively instead of waiting to be asked

**When "silent assistant" mode is active,** the same skills produce the same data but without explanatory text — just bullet points and numbers.

**The user's choice:** Coach mode (default) or Silent mode (toggleable).

---

### Session Open Protocol

To keep agent "active" during a session:

```
User: "Starting Push Day"
Agent: "Copy that. Session 7 — PUSH. Your mission:
         • Bench Press: 62.5kg × 8×3
         • Lateral Raises: 8kg × 13×3
         • Overhead Press: 42.5kg × 10×3
         • Cable Fly: 12kg × 13×3
         • Tricep Pushdown: 25kg × 13×3

         I'll be waiting for each set. Start whenever."
```

**During session, agent:**
- Confirms each logged set
- Flags immediately if reps fall short of target
- Offers deload option mid-session if user struggles

### Session Auto-Close Rules

A session is considered **closed** when ANY of the following conditions are met:

1. **New date:** A new calendar date begins (midnight). One session per day — a new date always means the previous session is closed.
2. **10pm cutoff:** Any session still open at 22:00 is automatically closed.
3. **Inactivity timeout:** No new exercise sets have been logged for 60 minutes — session is closed.

When a session closes:
- Agent writes final row to `Progress`, including `first_exercise_time`, `last_exercise_time`, and derived `duration_minutes`
- If session closes without a "Done" message from user, agent does not prompt for RPE (session was likely abandoned or user forgot to close)
- `SessionSequence` is marked `completed = true`

**One session per day is enforced.** If the user messages "heading to gym" twice in the same calendar day, the agent treats it as a continuation of the same session (or asks for clarification if the previous session was already closed).

---

## 10. Agent Decision Logic

```
1. Parse user intent:
   - "going to gym" / "what to do today" / "planning" → PLAN_SESSION
   - "done" / "finished" / "logged" / "completed" → LOG_WORKOUT
   - "progress" / "history" / "how am I doing" → QUERY_HISTORY
   - "swap" / "replace" / "instead of" → SUGGEST_SWAP
   - "deload" / "feeling weak" / "drop the weight" → SUGGEST_DELOAD
   - "weigh" / "weight is" / "bodyfat" → LOG_BODY_WEIGHT (also triggered on random interval)

2. If PLAN_SESSION:
   a. Query SessionSequence for last session_number → determine next session_type
      - session_number % 3 == 1 → push
      - session_number % 3 == 2 → pull
      - session_number % 3 == 0 → legs
   b. Read SessionTemplates for session_type
   c. For each exercise in template:
      - Query ExerciseHistory for expected_weight, expected_reps_per_set
      - If no history exists, use prescribed rep range from template
      - For pull-up exercises: Query BodyLog for latest bodyweight
        → Calculate total_pulling_weight = bodyweight + added_weight
   d. Apply progressive overload context:
      - If user met expectations last time → show a "stretch" target (+2.5kg or +1 rep)
      - If user exceeded expectations → show "push beyond" target
      - If user fell short → show same target, encourage hitting reps first
      - If consecutive_rpe_10 >= 2 on any exercise → FORCE deload suggestion
   e. Format and send session plan with expected targets

3. If LOG_WORKOUT:
   a. Parse message for exercise name, weight, and reps per set
      - User may log as: "Bench 60kg 8, 65kg 8, 65kg 7" (varying weights)
      - Or: "Bench 60kg 8,8,8" (same weight all sets)
      - For pull-ups: User logs "Pull-ups 5kg 8, 8, 7" (added weight only — bodyweight auto-added)
   b. For each set logged:
      - Write row to WorkoutLog with set_number auto-incremented
      - For pull-ups: Log actual weight as user specified (agent adds bodyweight separately for volume calc)
   c. Aggregate per exercise:
      - Find heaviest set → last_top_set_intensity
      - Sum total_volume = sum(weight × reps for each set)
      - For pull-ups: total_volume includes bodyweight in calculation
   d. Evaluate success using TWO triggers:
      - Trigger 1: total_volume > last_session's total_volume?
      - Trigger 2: heaviest_set_weight > last_session's heaviest_set_weight?
      - SUCCESS if EITHER trigger is true
   e. Calculate new expected values:
      - If SUCCESS (met expectations): expected_weight += 2.5kg OR expected_reps += 1
      - If EXCEEDED (got extra reps): expected_weight += 5kg OR expected_reps += 2
      - If FELL SHORT (missed reps on 1-2 sets): 
        keep same expected_weight, set expected_reps_per_set to actual_reps_hit + 1
      - If FAILED COMPLETELY (couldn't finish most sets): expected_weight -= 5kg, rebuild
   f. Track RPE: If any set logged with RPE 10, increment consecutive_rpe_10 for that exercise
      - If consecutive_rpe_10 reaches 3 → Flag exercise for forced deload next session
   g. Update ExerciseHistory row for each exercise (IMMEDIATELY, not lazily)
   h. Append to SessionSequence: session_number += 1, session_type, date, completed=true
   i. Update Progress table with session summary
   j. Check for "choking" on any exercise:
      - If BOTH triggers failed (volume ≤ last, intensity ≤ last) AND streak broken:
        → Send "eat more" reminder (one nudge per stall, not repeated nagging)
   k. Generate feedback message with:
      - Volume comparison (current vs expected)
      - Which success trigger(s) were hit
      - Streak update
      - Next session targets
      - RPE warning if applicable
      - Eat more nudge if choking detected

4. If QUERY_HISTORY:
   a. Parse which exercise(s) to check
   b. Query ExerciseHistory
   c. Return formatted progress report with trend indicators

5. If SUGGEST_SWAP:
   a. Parse current exercise and desired swap
   b. Query ExerciseCatalog for same category/muscle_group
   c. Return alternative options with their own history/expectations
   d. If swapping, recalculate progressive overload expectations for new exercise

6. If SUGGEST_DELOAD:
   a. Parse which exercise(s) user wants to deload
   b. Query ExerciseHistory for current expected values
   c. Calculate deload options:
      - Deload: expected_weight - 5kg, expected_reps_per_set + 2
      - Maintenance: expected_weight - 2.5kg, same reps
   d. Return options with volume comparison so user understands trade-off
   e. If user confirms, update expected_* values and reset consecutive_rpe_10 for exercise

7. If LOG_BODY_WEIGHT:
   a. Parse weight (and optional bodyfat) from message
   b. Write row to BodyLog with current date
   c. Return confirmation with trend vs last measurement
   d. If bodyweight increased from last session → celebrate
   e. If bodyweight dropped and user has been "choking" → reassure, mention bulking goal

8. If SESSION_OPEN:
   a. Check if a session is already open today (same calendar date in SessionSequence with completed=false)
      - If yes → remind user of current session state, list exercises already logged, continue
      - If no → open new session
   b. Determine next session_type (same logic as PLAN_SESSION step a)
   c. Run PLAN_SESSION steps b-e to generate the session plan
   d. Mark session as open in SessionSequence (completed=false, date=today)
   e. Record session start context; agent enters active-session mode:
      - Confirms each set as it is logged
      - Flags immediately if reps fall short mid-session
      - Offers deload option if user struggles on a set
   f. Session remains open until auto-close rules are met (see Session Auto-Close Rules)
   g. On close: write Progress row with first_exercise_time, last_exercise_time, duration_minutes

```

## 10. Intent Mapping to Technical Skills

| Intent | Technical Skills Used | Description |
|--------|----------------------|-------------|
| `PLAN_SESSION` | Progression Calculator + Query Engine | Builds plan, retrieves history |
| `LOG_WORKOUT` | Parser + RPE Corrector | Parses input, applies RPE logic |
| `QUERY_HISTORY` | Query Engine | Instant historical data retrieval |
| `SUGGEST_SWAP` | Progression Calculator | Recommends alternative exercises |
| `SUGGEST_DELOAD` | Progression Calculator + RPE Corrector | Calculates deload options |
| `LOG_BODY_WEIGHT` | (direct write) | Updates BodyLog table |
| `SESSION_OPEN` | Parser + Progression Calculator | Activates session, confirms plan |
| `RPE_PROMPT` | RPE Corrector | Asks for intensity after workout data |
| `RANDOM_REMINDER` | Reminder Trigger | Out-of-gym scheduled nudges |

**Persona (Coach vs Silent):** The same intents produce the same data. Coach mode wraps outputs in explanatory, encouraging text. Silent mode outputs bullets and numbers only. Toggle controlled by user preference (stored in Lark Base `UserPreferences` table or as an agent state variable).

## 11. Lark Base

All workout data lives in a single Lark Base (Bitable) shared with the bot app. See `README.md § Part 2` for table creation instructions and field definitions.

**Base name:** `Gym Tracker`
**Tables:** WorkoutLog, ExerciseHistory, SessionSequence, SessionTemplates, ExerciseCatalog, Progress, BodyLog

Bot access: the Lark App must be shared as **Editor** on the Base so it can read and write records.

## 12. Technical Stack

| Layer | Technology |
|---|---|
| **Messaging channel** | Lark Bot (WebSocket persistent connection via Lark Open Platform) |
| **Agent orchestration** | OpenClaw (workspace-level skills + SOUL.md) |
| **Skill definitions** | OpenClaw `SKILL.md` files (natural language instructions + YAML frontmatter) |
| **Agent persona** | `SOUL.md` (injected into system prompt at runtime) |
| **Data storage** | Lark Base (Bitable) — 7 tables, REST API |
| **Lark API SDK** | `lark-oapi` Python SDK (`larksuite/oapi-sdk-python`) |
| **Base helper** | `lib/lark_base.py` — thin wrapper for CRUD on gym tracker tables |
| **Scheduled triggers** | OpenClaw cron (nightly 20:00) → `send-reminder` skill |
| **Runtime** | Python 3.13+ in `.venv` |

## 13. Out of Scope (V1)

- Rest timers
- Nutrition logging (beyond bodyweight)
- Workout program generation (templates are pre-defined)
- Social features
