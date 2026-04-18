# Lark Base POC

Minimal proof-of-concept: CRUD operations against a Lark Base table using raw HTTP requests (no SDK dependency).

## Setup

1. Create a Lark app at https://open.larksuite.com/app — enable **Bitable** permissions (`bitable:app`)
2. Create a Base with one test table called `TestExercises` with these fields:
   - `name` (Text)
   - `weight_kg` (Number)
   - `reps` (Number)
   - `date` (Date)
   - `completed` (Checkbox)
3. Share the Base with your app (Editor permission)
4. Copy `.env.example` to `.env` and fill in your credentials
5. Run:
   ```bash
   cd poc
   python -m venv .venv && source .venv/bin/activate
   pip install requests python-dotenv
   python lark_base_poc.py
   ```

## What the POC tests

1. **Auth** — get tenant_access_token
2. **Create** — insert a record
3. **Search** — find records with filters
4. **Update** — modify an existing record
5. **Batch create** — insert multiple records at once
6. **List tables** — enumerate all tables in the Base

Each step prints the result so you can verify it works before wiring up the full agent.
