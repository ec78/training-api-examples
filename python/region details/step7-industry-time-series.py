import os
import csv
import io
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load credentials from the .env file next to this script
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

USER = os.getenv("IMPLAN_USERNAME")
PW   = os.getenv("IMPLAN_PASSWORD")

BASE_URL = "https://api.implan.com"
AUTH_URL = f"{BASE_URL}/api/auth"

# ── Configuration ──────────────────────────────────────────────────────────────
# This script combines the region search (step2), project/group creation (step3),
# and Industry Detail export (step5) into one loop that repeats them for every
# state, for every year IMPLAN has published data for. The result is a time
# series: how one industry has grown or shrunk, state by state, over time.

AGGREGATION_SCHEME_ID = 14   # 528-industry grouping scheme

INDUSTRY_CODE = "40"
# The single industry to track, identified by its numeric IMPLAN code.
# Run get-industry-codes.py (in "python/getting started/") to find the code for
# the industry you're interested in. The industry's name is not hardcoded here —
# it's read back from the first matching row returned by the API below.

STATE_REGION_TYPE = "State"
# IMPLAN groups all 50 states + Washington, DC under regionType "State"
# (see step2-find-region.py). "Country" would give just the US total.

# Append a timestamp to ensure the title is unique in your account. IMPLAN
# requires all Project titles to be unique account-wide — re-running this
# script without a timestamp would fail with "A saved Project with this name
# already exists."
PROJECT_TITLE = f"US Industry Time Series Study {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
HOUSEHOLD_SET_ID = 1                               # 1 is the standard IMPLAN default
IS_MRIO = False                                    # Single-region analysis (most common)

MAX_STATES = 3
# How many states to pull, alphabetically. None = all 50 states + DC (51 regions).
# Each state requires its own Group and CSV export per year, so leaving this and
# MAX_DATASETS at None means hundreds of API calls. Lower this (e.g. 5) for a
# quick test run before doing a full pull.

MAX_DATASETS = None
# How many data years to pull, most recent first. None = every year IMPLAN has
# published for this aggregation scheme.

# ── Step 1: Authenticate ───────────────────────────────────────────────────────
def get_token(username, password):
    resp = requests.post(AUTH_URL, json={
        "username": username,
        "password": password
    })
    resp.raise_for_status()
    return resp.text.removeprefix("Bearer ")

def build_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

token   = get_token(USER, PW)
headers = build_headers(token)
print(f"Authenticated. Token preview: {token[:6]}...{token[-6:]}\n")

# ── Step 2: Get Every Available Data Year ──────────────────────────────────────
# "All possible time periods" means every dataset IMPLAN has published for this
# aggregation scheme — each dataset is a complete regional economic model for one
# specific year.
#
# Note: GET requests must NOT include Content-Type — only pass Authorization.
#
# Endpoint: GET /api/v1/datasets/{aggregationSchemeId}
# Docs:     https://github.com/Implan-Group/api/wiki/Dataset-by-Id

url = f"{BASE_URL}/api/v1/datasets/{AGGREGATION_SCHEME_ID}"

resp = requests.get(url, headers={"Authorization": headers["Authorization"]})
resp.raise_for_status()

datasets = sorted(resp.json(), key=lambda d: d["description"])   # oldest -> newest
if MAX_DATASETS:
    datasets = datasets[-MAX_DATASETS:]   # keep the N most recent years

print(f"Data years to pull ({len(datasets)}): {', '.join(d['description'] for d in datasets)}\n")

# ── Step 3: Get Every State (+ DC) ──────────────────────────────────────────────
# A region's hashId does not change from year to year, so we only need to look
# up the state list once — using the most recent dataset as the reference point.
#
# Endpoint: GET /api/v1/region/{aggregationSchemeId}/{datasetId}/children
# Docs:     https://github.com/Implan-Group/api/wiki/Regional-Children

reference_dataset_id = datasets[-1]["id"]

url = f"{BASE_URL}/api/v1/region/{AGGREGATION_SCHEME_ID}/{reference_dataset_id}/children"
params = {"regionTypeFilter": STATE_REGION_TYPE}

resp = requests.get(url, headers={"Authorization": headers["Authorization"]}, params=params)
resp.raise_for_status()

states = sorted(resp.json(), key=lambda r: r["description"])
if MAX_STATES:
    states = states[:MAX_STATES]

print(f"States to pull ({len(states)} of 51 possible: 50 states + DC)\n")

# ── Step 4: Create One Project ──────────────────────────────────────────────────
# A single Project can hold many Groups, so we create one Project up front and
# add a Group to it for every state/year combination in the loop below —
# rather than creating a new Project each time.
#
# Endpoint: POST /api/v1/impact/project
# Docs:     https://github.com/Implan-Group/api/wiki/Create-Project

url = f"{BASE_URL}/api/v1/impact/project"

project_payload = {
    "Title":               PROJECT_TITLE,
    "AggregationSchemeId": AGGREGATION_SCHEME_ID,
    "HouseholdSetId":      HOUSEHOLD_SET_ID,
    "IsMrio":              IS_MRIO
}

resp = requests.post(url, json=project_payload, headers=headers)

if not resp.ok:
    print(f"  Project creation failed ({resp.status_code}): {resp.text!r}")
    resp.raise_for_status()

project_id = resp.json()["id"]

print(f"Project created (ID: {project_id})\n")

# ── Step 5: Loop Over Every State x Every Year ─────────────────────────────────
# For each state/year combination we:
#   1. Create a Group tying that state's region to that year's dataset
#      (same pattern as step3-create-group.py)
#   2. Pull the Study Area Data — Industry Detail CSV for that Group
#      (same pattern as step5-industry-detail.py)
#   3. Find the one row matching INDUSTRY_CODE and record its metrics
#
# Expect this to take a while when MAX_STATES and MAX_DATASETS are left at
# None — it means two API calls (create Group + export CSV) per combination,
# which adds up to hundreds of requests for the full 51-state, multi-year pull.

group_url  = f"{BASE_URL}/api/v1/impact/project/{project_id}/group"
export_url = f"{BASE_URL}/api/v1/regions/export/{AGGREGATION_SCHEME_ID}/StudyAreaDataIndustryDetail"

# results[state description][year] = {"employment": ..., "output": ...}
results = {}
industry_description = None   # filled in from the first matching CSV row we find

print(f"Pulling Industry Code {INDUSTRY_CODE} for {len(states)} states x {len(datasets)} years "
      f"({len(states) * len(datasets)} combinations)...\n")

for dataset in datasets:
    year = dataset["description"]

    for state in states:
        # Group payload: same shape as step3-create-group.py, but DatasetId and
        # DollarYear change on every iteration to match the current data year.
        group_payload = {
            "Title":       f"{state['description']} {year}",
            "HashId":      state["hashId"],
            "DatasetId":   dataset["id"],
            "DollarYear":  int(year),
            "groupEvents": []
        }

        resp = requests.post(group_url, json=group_payload, headers=headers)
        resp.raise_for_status()
        group_hash_id = resp.json()["hashId"]

        resp = requests.get(
            export_url,
            headers={"Authorization": headers["Authorization"]},
            params={"hashId": group_hash_id}
        )
        resp.raise_for_status()

        rows = csv.DictReader(io.StringIO(resp.text), skipinitialspace=True)
        match = next(
            (r for r in rows if r.get("Industry Code", "").strip() == str(INDUSTRY_CODE)),
            None
        )

        state_results = results.setdefault(state["description"], {})

        if match is None:
            state_results[year] = None
            print(f"  [!] {state['description']} ({year}): Industry Code {INDUSTRY_CODE} not found")
            continue

        if industry_description is None:
            industry_description = match["Description"]

        # Total Employment = Wage & Salary Employment + Proprietor Employment
        ws_emp   = float(match.get("Wage and Salary Employment", 0) or 0)
        prop_emp = float(match.get("Proprietor Employment", 0) or 0)
        output   = float(match.get("Total Output", 0) or 0)

        state_results[year] = {"employment": ws_emp + prop_emp, "output": output}
        print(f"  {state['description']} ({year}): employment={ws_emp + prop_emp:,.1f}  output=${output:,.0f}")

# ── Step 6: Print the Time Series Matrices ──────────────────────────────────────
# One row per state, one column per year — this makes it easy to scan across a
# row and see how the industry changed over time in a given state.

years = [d["description"] for d in datasets]
state_names = sorted(results.keys())

def print_matrix(title, metric_key, fmt):
    print(f"\n{title} — Industry {INDUSTRY_CODE} ({industry_description or 'unknown'})")
    print(f"  {'State':<25}" + "".join(f"{y:>14}" for y in years))
    print("  " + "-" * (25 + 14 * len(years)))

    for name in state_names:
        cells = []
        for y in years:
            cell = results[name].get(y)
            cells.append(fmt(cell[metric_key]) if cell else "n/a")
        print(f"  {name:<25}" + "".join(f"{c:>14}" for c in cells))

print_matrix("Employment (jobs)", "employment", lambda v: f"{v:,.1f}")
print_matrix("Output ($)", "output", lambda v: f"${v:,.0f}")
