# LLM Reference — IMPLAN API

This file is designed to be shared with an LLM (Claude, ChatGPT, etc.) as context when writing or extending IMPLAN API scripts. It summarizes the domain concepts, endpoint patterns, and coding conventions used in this repository.

For agent-specific instructions, also share [CLAUDE.md](CLAUDE.md).

---

## 1. IMPLAN Data Concepts

### What IMPLAN Does

IMPLAN is an input-output (I-O) economic modeling platform. It estimates the total economic impact of an activity — the direct effect plus ripple effects through the supply chain (indirect) and household spending (induced). The API lets you define an economic "event" (e.g., $500M in construction spending) and retrieve how it propagates through a regional economy.

### Aggregation Schemes

An aggregation scheme defines how IMPLAN groups industries. All requests that reference industries or datasets must use a consistent scheme ID.

| Scheme ID | Industry Count | Notes |
|---|---|---|
| `8` | 546 | More granular breakdown |
| `14` | 528 | Standard default for most analyses |

The scheme ID is a required parameter in: dataset lookups, region lookups, industry code lookups, project creation, and regional data exports.

### Datasets

A dataset represents IMPLAN's regional economic data for a specific year. IMPLAN publishes new datasets annually.

- Retrieve available datasets with `GET /api/v1/datasets/{aggregationSchemeId}`
- Response fields: `id` (integer, used in all subsequent calls), `description` (e.g. `"2024"`), `isDefault` (boolean)
- Example: dataset ID `124` = 2024 data year

### Regions

IMPLAN models are region-specific. The I-O multipliers for a rural county differ significantly from a major metropolitan area.

**Region types** (geographic granularity):

| Type | Description |
|---|---|
| `Country` | United States total |
| `State` | 50 states + DC |
| `County` | 3,000+ counties |
| `MSA` | Metropolitan Statistical Area (major metros) |
| `Zip` | ZIP code level (limited availability) |

**Key identifiers:**
- `hashId` — used in event groups and regional export queries; the primary region reference in API calls
- `urid` — IMPLAN's internal unique region identifier; returned by region lookups but used less often
- `description` — human-readable name (e.g., `"Travis, TX"`)

### Industry Codes

Industries are identified by a numeric `code` within an aggregation scheme. Codes are scheme-specific — code 50 in the 546-industry scheme refers to a different industry than code 50 in the 528-industry scheme.

Retrieve the full list with `GET /api/v1/IndustryCodes/{aggregationSchemeId}`. Response fields: `code` (integer), `description` (string).

### Economic Metrics

| Metric | Definition |
|---|---|
| **Employment** | Total jobs: wage & salary employees + proprietors (self-employed) |
| **Labor Income** | Wages, salaries, and proprietor income combined |
| **Employee Compensation** | Wages, salaries, and benefits for wage & salary employees |
| **Proprietor Income** | Net income for self-employed individuals |
| **Output** | Total value of goods and services produced by an industry |
| **Intermediate Inputs** | Goods and services purchased from other industries to produce output |
| **Value Added** | Output minus intermediate inputs; the industry's contribution to GDP |
| **Other Property Income** | Returns to capital (profit, rent, interest) beyond labor |
| **Taxes on Production and Imports** | Business taxes net of subsidies |

**Identity relationships:**
- Labor Income = Employee Compensation + Proprietor Income
- Value Added = Labor Income + Other Property Income + Taxes on Production and Imports
- Output = Intermediate Inputs + Value Added

### Impact Decomposition

Impact analysis results are broken into four rows:

| Impact | Meaning |
|---|---|
| **Direct** | The economic activity you modeled (the "event" itself) |
| **Indirect** | Supply chain effects — upstream purchases by the affected industry |
| **Induced** | Household spending effects — workers spending their wages |
| **Total** | Sum of Direct + Indirect + Induced |

---

## 2. API Reference

### Base URL

```
https://api.implan.com
```

### Authentication

**Endpoint:** `POST /api/auth`

**Request body:**
```json
{ "username": "you@firm.com", "password": "yourpassword" }
```

**Response:** Plain string — `"Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9..."`

**Critical:** The API prepends `"Bearer "` to the token. Strip it before storing, then re-add in headers:
```python
token = resp.text.removeprefix("Bearer ")
headers = {"Authorization": f"Bearer {token}"}
```

### Header Rules

| Request type | Required headers |
|---|---|
| POST / PUT | `Authorization`, `Content-Type: application/json` |
| GET | `Authorization` only — omit `Content-Type` (API returns 400 if included) |

### Core Endpoints

#### Get Datasets
```
GET /api/v1/datasets/{aggregationSchemeId}
```
Returns available data years. Response: JSON array.
```json
[{ "id": 124, "description": "2024", "isDefault": true }, ...]
```

#### Get Regions (top-level)
```
GET /api/v1/region/{aggregationSchemeId}/{datasetId}
```
Returns the top-level region (USA). Confirms the dataset is valid.

#### Get Child Regions
```
GET /api/v1/region/{aggregationSchemeId}/{datasetId}/children?regionTypeFilter={type}
```
Returns regions of a given type (State, County, MSA, Zip). Response: JSON array.
```json
[{ "hashId": "abc123", "description": "Travis, TX", "regionType": "County", "urid": 99999 }, ...]
```

#### Get Industry Codes
```
GET /api/v1/IndustryCodes/{aggregationSchemeId}
```
Returns all industries for the scheme. Response: JSON array.
```json
[{ "code": 50, "description": "Construction of new commercial structures" }, ...]
```

#### Create Project
```
POST /api/v1/impact/project
```
Request body:
```json
{
  "Title": "My Analysis",
  "AggregationSchemeId": 14,
  "HouseholdSetId": 1,
  "IsMrio": false
}
```
Response: JSON object with `id` (GUID string) — the project ID used in subsequent calls.

- `HouseholdSetId`: Use `1` (default household data)
- `IsMrio`: `false` = single-region model (standard); `true` = multi-region

#### Create Event
```
POST /api/v1/impact/project/{projectId}/event
```
Request body:
```json
{
  "ImpactEventType": "IndustryOutput",
  "Title": "Data Center Construction",
  "IndustryCode": 50,
  "Output": 500000000
}
```
Event types: `IndustryOutput`, `IndustryEmployment`, `IndustryEmployeeCompensation`, `IndustryProprietorIncome`

Response: JSON object with `id` (integer) — the event ID used when creating a group.

#### Create Group
```
POST /api/v1/impact/project/{projectId}/group
```
Request body:
```json
{
  "Title": "Travis County 2024",
  "HashId": "abc123",
  "DatasetId": 124,
  "DollarYear": 2024,
  "groupEvents": [{ "eventId": 42 }]
}
```
A group links one or more events to a specific region and data year.

#### Run Analysis
```
POST /api/v1/impact/{projectId}
```
Note: no `project/` in the path (unlike create/event/group endpoints).

Response: **Plain integer text** — e.g., `"605590"`. Parse with `int(resp.text.strip())`. Do not use `resp.json()` — the API may return a float string (`"605590.0"`) which breaks status URL construction.

#### Check Analysis Status
```
GET /api/v1/impact/status/{runId}
```
Response: Plain string — one of: `"New"`, `"InProgress"`, `"ReadyForWarehouse"`, `"Complete"`, `"Error"`, `"UserCancelled"`

Terminal states: `"Complete"`, `"Error"`, `"UserCancelled"`

If a 400 is returned immediately after triggering a run, the analysis finished before the first poll. The Run ID is valid — proceed to results.

#### Get Impact Results
```
GET /api/v1/impact/results/SummaryEconomicIndicators/{runId}
```
Response: **CSV text** (not JSON). Columns: `Impact`, `Employment`, `LaborIncome`, `ValueAdded`, `Output`

`Impact` values: `Direct`, `Indirect`, `Induced`, `Total`

#### Export Regional Overview
```
GET /api/v1/regions/export/{aggregationSchemeId}/RegionOverviewIndustries?hashId={hashId}
```
Response: CSV. Columns include `Display Code`, `Display Description`, `Employment`, `Labor Income`, `Output`, `Average Employee Compensation per Wage and Salary Employee`, `Average Proprietor Income per Proprietor`

#### Export Industry Detail
```
GET /api/v1/regions/export/{aggregationSchemeId}/StudyAreaDataIndustryDetail?hashId={hashId}
```
Response: CSV. Columns: `Industry Code`, `Description`, `Total Output`, `Wage and Salary Employment`, `Employee Compensation`, `Proprietor Employment`, `Proprietor Income`, `Other Property Income`, `Taxes on Production and Imports Net of Subsidies`

#### Export Industry Summary
```
GET /api/v1/regions/export/{aggregationSchemeId}/StudyAreaDataIndustrySummary?hashId={hashId}
```
Response: CSV. Columns: `Industry Code`, `Description`, `Total Employment`, `Total Output`, `Total Intermediate Inputs`, `Total Value Added`, `Labor Income`

### Pagination and Rate Limiting

No pagination has been observed in the scripts in this repository — the datasets, region, and industry endpoints appear to return complete lists. No rate limiting behavior has been documented; avoid rapid-fire polling (10-second poll intervals work well for status checks).

---

## 3. Prompt Patterns for LLM-Assisted Development

Share both `LLM_REFERENCE.md` and `CLAUDE.md` with the LLM before asking it to write or modify scripts.

---

**Prompt 1 — Write a new script from scratch**

> I'm writing a Python script that uses the IMPLAN API. Here is the full API reference and coding conventions for this project: [paste LLM_REFERENCE.md and CLAUDE.md].
>
> Write a self-contained script that authenticates using credentials from a `.env` file, then retrieves all counties in California for aggregation scheme 14 and dataset 124, and prints a table of county names and their hashIds. Follow the conventions in CLAUDE.md — heavily commented, no hardcoded credentials, GET requests must omit Content-Type.

---

**Prompt 2 — Extend an existing script**

> Here is an existing IMPLAN API script: [paste script].
>
> Extend it to loop over a list of industry codes (50, 55, 60) and create one IndustryOutput event per industry, each with $1,000,000 in output. Each event title must be unique — append the industry code to ensure uniqueness. Use the same conventions as the existing script.

---

**Prompt 3 — Debug an error**

> I'm using the IMPLAN API and getting this error when running my script: [paste full traceback].
>
> Here is the relevant code: [paste the function or block]. Here is the API reference: [paste LLM_REFERENCE.md].
>
> What is the likely cause, and what is the fix?

---

**Prompt 4 — Export and analyze regional data**

> Using the IMPLAN API (reference: [paste LLM_REFERENCE.md]), write a script that:
> 1. Authenticates from `.env`
> 2. Finds the hashId for "Denver, CO" (county, aggregation scheme 14, dataset 124)
> 3. Exports the StudyAreaDataIndustrySummary for that region
> 4. Prints the top 10 industries by Total Output in descending order
>
> Parse the CSV response using `csv.DictReader` with `skipinitialspace=True`. Convert numeric fields to float before sorting.

---

**Prompt 5 — Run a full analysis end-to-end**

> I want a single Python script that runs a complete IMPLAN impact analysis using the API. Here is the full API reference: [paste LLM_REFERENCE.md].
>
> The script should:
> 1. Authenticate from `.env`
> 2. Use aggregation scheme 14, dataset 124 (2024)
> 3. Find Travis County, TX by name
> 4. Create a project titled "Warehouse Construction"
> 5. Add an IndustryOutput event for industry code 50 with $250,000,000 in output
> 6. Create a group linking the event to Travis County 2024
> 7. Run the analysis and poll every 10 seconds until complete
> 8. Print the Summary Economic Indicators table (Direct / Indirect / Induced / Total)
>
> Follow conventions in CLAUDE.md throughout.

---

## 4. Code Patterns

### Pattern 1 — Authentication and Header Construction

Every script authenticates the same way. This pattern handles the `"Bearer "` prefix quirk:

```python
import os
import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
USER = os.getenv("IMPLAN_USERNAME")
PW   = os.getenv("IMPLAN_PASSWORD")

BASE_URL = "https://api.implan.com"

def get_token(username, password):
    # The IMPLAN auth endpoint returns the token as a plain string with
    # "Bearer " already prepended. Strip the prefix here so we can re-add
    # it consistently in build_headers() below.
    resp = requests.post(f"{BASE_URL}/api/auth", json={"username": username, "password": password})
    resp.raise_for_status()
    return resp.text.removeprefix("Bearer ")

def build_headers(token):
    # Use this for POST/PUT requests only. For GET requests, omit
    # Content-Type — the IMPLAN API returns 400 if it's present on a GET.
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

token = get_token(USER, PW)
```

---

### Pattern 2 — Polling Until Complete

The run analysis endpoint is asynchronous. This loop polls until a terminal state is reached:

```python
import time

def run_and_wait(token, project_id):
    # Trigger the analysis. Note: no "project/" in this path.
    headers = build_headers(token)
    resp = requests.post(f"{BASE_URL}/api/v1/impact/{project_id}", headers=headers)
    resp.raise_for_status()
    # Response is a plain integer string, not JSON. Parse carefully to
    # avoid float issues ("605590.0") that break the status URL.
    run_id = int(resp.text.strip())
    print(f"Run ID: {run_id}")

    # GET requests use auth header only — no Content-Type.
    get_headers = {"Authorization": f"Bearer {token}"}

    while True:
        status_resp = requests.get(
            f"{BASE_URL}/api/v1/impact/status/{run_id}", headers=get_headers
        )
        # A 400 immediately after triggering usually means the analysis
        # finished before we polled. Treat it as complete.
        if status_resp.status_code == 400:
            print("Analysis completed before first poll.")
            break
        status_resp.raise_for_status()
        status = status_resp.text.strip()
        print(f"Status: {status}")
        if status == "Complete":
            break
        if status in ("Error", "UserCancelled"):
            raise RuntimeError(f"Analysis failed with status: {status}")
        time.sleep(10)

    return run_id
```

---

### Pattern 3 — Parsing CSV Responses

Several endpoints return CSV rather than JSON. IMPLAN uses `", "` (comma-space) as a delimiter, so `skipinitialspace=True` is required to strip leading whitespace from column names and values:

```python
import csv
import io

def fetch_csv(token, url):
    # GET request — no Content-Type header.
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    # skipinitialspace=True handles the ", " delimiter: without it,
    # " Employment" would not match the key "Employment".
    reader = csv.DictReader(io.StringIO(resp.text), skipinitialspace=True)
    return list(reader)

# Usage example — get impact results
rows = fetch_csv(token, f"{BASE_URL}/api/v1/impact/results/SummaryEconomicIndicators/{run_id}")
for row in rows:
    print(f"{row['Impact']:10s}  Employment: {float(row['Employment']):>12,.1f}")
```
