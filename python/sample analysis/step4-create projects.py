import os
import requests
from dotenv import load_dotenv

# Load credentials from the .env file next to this script
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

USER = os.getenv("IMPLAN_USERNAME")
PW   = os.getenv("IMPLAN_PASSWORD")

BASE_URL = "https://api.implan.com"
AUTH_URL = f"{BASE_URL}/api/auth"

# ── Configuration ──────────────────────────────────────────────────────────────
# A Project is the container for your entire impact analysis.
# It holds the industry grouping scheme, household data, and all events/groups.

PROJECT_TITLE = "Travis Co. Data Center"  # A descriptive name for this project

AGGREGATION_SCHEME_ID = 14  # 528-industry grouping scheme
                             # Must match what you used in get-datasets.py and
                             # find-region.py — all steps must use the same scheme.

HOUSEHOLD_SET_ID = 1        # Defines which household income categories to use.
                             # 1 is the standard IMPLAN default.

IS_MRIO = False             # Multi-Region Input-Output model.
                             # False = single-region analysis (most common).
                             # True  = analysis that accounts for inter-regional
                             #         trade flows (more complex, use for advanced cases).

# ── Step 1: Authenticate ───────────────────────────────────────────────────────
# Every IMPLAN API request requires a Bearer token obtained by sending credentials
# to the auth endpoint.

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

# ── Step 2: Create the Project ────────────────────────────────────────────────
# A project must be created before you can add events or run an analysis.
# Think of it as opening a new analysis workspace in the IMPLAN app.
#
# The API returns a unique project ID (a GUID) that you will use in every
# subsequent step to refer back to this project.
#
# Endpoint: POST /api/v1/impact/project
# Docs:     https://github.com/Implan-Group/api/wiki/Create-Project

url = f"{BASE_URL}/api/v1/impact/project"

# The request body defines the core settings for this project.
# These settings cannot be changed after the project is created.
project_payload = {
    "Title":                PROJECT_TITLE,
    "AggregationSchemeId":  AGGREGATION_SCHEME_ID,
    "HouseholdSetId":       HOUSEHOLD_SET_ID,
    "IsMrio":               IS_MRIO
    # Do NOT include an "id" field — the API generates one automatically
    # and returns it in the response.
}

resp = requests.post(url, json=project_payload, headers=headers)
resp.raise_for_status()

project = resp.json()

# ── Output ─────────────────────────────────────────────────────────────────────
print("Project created successfully!\n")
print(f"  Title:                {project['title']}")
print(f"  Aggregation Scheme:   {project['aggregationSchemeId']}")
print(f"  Household Set:        {project['householdSetId']}")
print(f"  MRIO:                 {project['isMrio']}")
print(f"\n  --> Project ID: {project['id']}")
print(f"      Copy this ID into add-events.py as PROJECT_ID")
