# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

Training examples for the IMPLAN API, written in Python. Scripts are flat, annotated, and intentionally simple — intended for use in presentations and walkthroughs for an introductory audience, not production use.

## Reference Documentation

- API wiki (endpoints, parameters, response formats): https://github.com/Implan-Group/api/wiki
- Sample code and full repo: https://github.com/Implan-Group/api

## Environment

- Python 3.14 via `C:\Users\eric.clower\.local\bin\python3.14.exe`
- Virtual environment: `.venv\` at the project root
- Run scripts: `.venv\Scripts\python.exe python\<script>.py`
- Install a package: `.venv\Scripts\python.exe -m pip install <package>`

## Credentials

All scripts load credentials from `python\.env`:

```
IMPLAN_USERNAME=you@firm.com
IMPLAN_PASSWORD=yourpassword
```

`python\.env` is gitignored. Never hardcode credentials in scripts.

## IMPLAN API Patterns

**Authentication** (`POST /api/auth`):
- Returns the token as a plain string with `Bearer ` already prepended (e.g. `Bearer eyJ...`)
- Strip the prefix before storing: `resp.text.removeprefix("Bearer ")`
- `build_headers(token)` then re-adds `Bearer ` for all subsequent requests

**Subsequent requests** all require:
```python
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
```

**GET requests must not include `Content-Type: application/json`** — the IMPLAN API returns 400 if that header is present on a GET. Only pass `Authorization` for GET requests; include `Content-Type` only on POST/PUT.

**Response formats are inconsistent across endpoints — do not assume JSON:**
- `POST /api/auth` → plain string with `Bearer ` prefix → use `resp.text.removeprefix("Bearer ")`
- `POST /api/v1/impact/{projectId}` (run analysis) → plain integer text → use `int(resp.text.strip())` (not `resp.json()` — may return float causing `/status/605590.0` 400 errors)
- `GET /api/v1/impact/status/{runId}` → plain string (e.g. `InProgress`) → use `resp.text.strip()`
- Most other endpoints (datasets, regions, projects, events, results) → JSON → use `resp.json()`

**Run analysis URL is different from other project endpoints:**
- Create/event/group: `/api/v1/impact/project/{id}/...`
- Run trigger: `/api/v1/impact/{id}` ← no `project/` segment

**Aggregation Scheme IDs** (required parameter for dataset/industry endpoints):
- `8`  = 546-industry scheme
- `14` = 528-industry scheme

## Script Conventions

- Each script is self-contained: auth + the feature it demonstrates
- **All code must be thoroughly commented.** The audience is introductory — assume no prior API or Python experience. Comments should explain what each block does, why it's needed, and what the values mean (e.g. what an aggregation scheme ID is, why headers are required).
- Comments explain *why*, not just *what* — focus on concepts a first-time API user would need to understand.
- Debug `[debug]` print statements are temporary and should be removed before finalizing a script for presentation.
