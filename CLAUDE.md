# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

Training examples for the IMPLAN API, written in Python. Scripts are flat, annotated, and intentionally simple — intended for use in presentations and walkthroughs for an introductory audience, not production use.

For deeper API and domain context, see [LLM_REFERENCE.md](LLM_REFERENCE.md).

## Reference Documentation

- API wiki (endpoints, parameters, response formats): https://github.com/Implan-Group/api/wiki
- Sample code and full repo: https://github.com/Implan-Group/api

## Repository Structure

Three series of scripts, each in its own subdirectory under `python/`:

| Series | Location | Purpose |
|---|---|---|
| Getting Started | `python/getting started/` | Eight-step foundational walkthrough (auth → results) |
| Sample Analysis | `python/sample analysis/` | Same workflow pre-configured for Travis County, TX |
| Region Details | `python/region details/` | Six-step workflow for raw regional economic data exports |

Each series has its own `.env` file (gitignored) for credentials.

## Environment

- Python 3.14 via `C:\Users\eric.clower\.local\bin\python3.14.exe`
- Virtual environment: `.venv\` at the project root
- Run scripts: `.venv\Scripts\python.exe "python/getting started/<script>.py"`
- Install a package: `.venv\Scripts\python.exe -m pip install <package>`

## Credentials

All scripts load credentials from a `.env` file in the same directory as the script:

```
IMPLAN_USERNAME=you@firm.com
IMPLAN_PASSWORD=yourpassword
```

`**/.env` is gitignored. Never hardcode credentials in scripts.

## IMPLAN API Patterns

### Authentication (`POST /api/auth`)

- Returns the token as a plain string with `Bearer ` already prepended (e.g. `Bearer eyJ...`)
- Strip the prefix before storing: `resp.text.removeprefix("Bearer ")`
- `build_headers(token)` then re-adds `Bearer ` for all subsequent requests

### Request Headers

**POST/PUT requests** require both headers:
```python
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
```

**GET requests must NOT include `Content-Type: application/json`** — the IMPLAN API returns 400 if that header is present on a GET. Only pass `Authorization` for GET requests.

### Response Formats (Inconsistent — Do Not Assume JSON)

| Endpoint | Format | How to Parse |
|---|---|---|
| `POST /api/auth` | Plain string: `"Bearer eyJ..."` | `resp.text.removeprefix("Bearer ")` |
| `POST /api/v1/impact/{projectId}` | Plain integer: `"605590"` | `int(resp.text.strip())` |
| `GET /api/v1/impact/status/{runId}` | Plain string: `"Complete"` | `resp.text.strip()` |
| Region/industry export endpoints | CSV text | `csv.DictReader(io.StringIO(resp.text), skipinitialspace=True)` |
| All other endpoints | JSON | `resp.json()` |

> The run analysis endpoint may return a float (e.g. `"605590.0"`). Always use `int(resp.text.strip())`, not `resp.json()`, to avoid `/status/605590.0` 400 errors.

### URL Patterns

- Create/event/group: `/api/v1/impact/project/{id}/...`
- Run trigger: `/api/v1/impact/{id}` — no `project/` segment
- Region exports: `/api/v1/regions/export/{aggregationSchemeId}/{exportType}?hashId={hashId}`

### CSV Response Handling

IMPLAN CSV responses use `", "` (comma-space) as a delimiter. Use `skipinitialspace=True` when parsing:

```python
import csv, io
reader = csv.DictReader(io.StringIO(resp.text), skipinitialspace=True)
for row in reader:
    print(row["Employment"])
```

Numeric fields are strings in CSV — convert explicitly: `float(row["Employment"])`.

### Status Polling

- Terminal statuses: `"Complete"`, `"Error"`, `"UserCancelled"`
- Intermediate statuses: `"New"`, `"InProgress"`, `"ReadyForWarehouse"`
- Small analyses may complete before the first poll — a 400 on status immediately after triggering is normal. The Run ID is still valid; go straight to the results endpoint.

## IMPLAN Domain Concepts

### Aggregation Scheme IDs

| ID | Scheme | Description |
|---|---|---|
| `8` | 546-industry | More detailed industry breakdown |
| `14` | 528-industry | Standard default for most analyses |

The scheme must be **consistent across all steps** — dataset lookup, region lookup, industry codes, project creation, and event creation must all use the same scheme ID.

### Region Types

The API supports geographic regions at these levels (passed as `regionTypeFilter`):

| Type | Description |
|---|---|
| `Country` | USA total |
| `State` | 50 states + DC |
| `County` | 3,000+ counties |
| `MSA` | Metropolitan Statistical Area |
| `ZipCode` | ZIP code (limited availability) |

Regions are identified by `hashId` (used in event groups and export queries) and `urid` (used internally).

### Datasets

Each dataset is a specific data year (e.g., `124` = 2024). Use `GET /api/v1/datasets/{schemeId}` to list available IDs. The `isDefault` field identifies the most current year.

### Economic Metrics

| Metric | Definition |
|---|---|
| **Employment** | Wage & salary jobs + proprietor (self-employed) jobs |
| **Labor Income** | Employee compensation + proprietor income |
| **Value Added** | Output minus intermediate inputs; contribution to GDP |
| **Output** | Total value of goods/services produced |
| **Intermediate Inputs** | Goods/services purchased from other industries to produce output |

### Impact Types (from Results Endpoint)

Results report impacts broken into four rows:

| Impact | Meaning |
|---|---|
| Direct | The event itself (e.g., the spending you modeled) |
| Indirect | Supply chain effects (upstream purchases by the affected industry) |
| Induced | Household spending effects (workers spending their wages) |
| Total | Sum of all three |

### Event Types

| Type | When to Use |
|---|---|
| `IndustryOutput` | A change in industry revenue or spending |
| `IndustryEmployment` | A change in the number of jobs |
| `IndustryEmployeeCompensation` | A change in wage and salary payments |
| `IndustryProprietorIncome` | A change in self-employment income |

## Script Conventions

- Each script is self-contained: auth + the feature it demonstrates
- **All code must be thoroughly commented.** The audience is introductory — assume no prior API or Python experience. Comments should explain what each block does, why it's needed, and what the values mean.
- Comments explain *why*, not just *what* — focus on concepts a first-time API user would need to understand
- Debug `[debug]` print statements are temporary and should be removed before finalizing a script for presentation
- Configuration variables (IDs, search terms, amounts) go at the top of the script in a clearly labeled section
- Scripts print a `-->` line at the end to tell the user which ID to copy to the next step
