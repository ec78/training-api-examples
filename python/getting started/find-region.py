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
# These values come from Step 2 (get-datasets.py).
# Run that script first to find valid IDs, then fill them in here.

AGGREGATION_SCHEME_ID = 14   # 528-industry grouping scheme

DATASET_ID = 124             # The data year to use — replace with an ID from
                             # get-datasets.py (e.g., 124 = 2024 dataset)

# What type of region to search for.
# Common values: "Country", "State", "County", "MSA", "Zip"
REGION_TYPE = "State"

# Text to search for within the returned region descriptions.
# This filters the results to just the region(s) you care about.
REGION_SEARCH = "Minnesota"

# ── Step 1: Authenticate ───────────────────────────────────────────────────────
# Every IMPLAN API request requires a Bearer token. We get it by sending our
# credentials to the auth endpoint, then attach it to all subsequent requests.

def get_token(username, password):
    resp = requests.post(AUTH_URL, json={
        "username": username,
        "password": password
    })
    resp.raise_for_status()
    # The API returns the token with "Bearer " already prepended —
    # we strip it here so build_headers() can add it back cleanly.
    return resp.text.removeprefix("Bearer ")

def build_headers(token):
    # The Authorization header is required on every API call after login.
    # "Bearer" is the authentication scheme — it tells the API this is a
    # token-based request, not a username/password request.
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

token   = get_token(USER, PW)
headers = build_headers(token)
print(f"Authenticated. Token preview: {token[:6]}...{token[-6:]}\n")

# ── Step 2: Get Top-Level Regions ──────────────────────────────────────────────
# IMPLAN regions are organized in a hierarchy: Country → State → County/MSA.
# We start at the top level (Country) for the given aggregation scheme + dataset.
#
# Endpoint: GET /api/v1/region/{aggregationSchemeId}/{datasetId}
# Docs:     https://github.com/Implan-Group/api/wiki/Regions---Top-Level

url = f"{BASE_URL}/api/v1/region/{AGGREGATION_SCHEME_ID}/{DATASET_ID}"

resp = requests.get(url, headers=headers)
resp.raise_for_status()

top_level = resp.json()

# The API returns a single region object (not a list) for the top level —
# this is the United States total. We wrap it in a list so we can print it
# the same way regardless, and to confirm the correct dataset is loaded.
if isinstance(top_level, dict):
    top_level = [top_level]

print("Top-level region(s):")
for region in top_level:
    print(f"  {region['description']}  |  regionType: {region['regionType']}  |  hashId: {region['hashId']}")

# ── Step 3: Get Child Regions (States, Counties, MSAs) ────────────────────────
# To drill down from Country to a State (or County, MSA, etc.), we call the
# "children" endpoint and filter by the desired region type.
#
# The hashId is the unique identifier IMPLAN uses for a region — you will need
# it in later steps (Step 5) to associate your analysis with a specific geography.
#
# Endpoint: GET /api/v1/region/{aggregationSchemeId}/{datasetId}/children
# Docs:     https://github.com/Implan-Group/api/wiki/Regional-Children

url = f"{BASE_URL}/api/v1/region/{AGGREGATION_SCHEME_ID}/{DATASET_ID}/children"

# The regionTypeFilter query parameter narrows the results to one level
# of the geographic hierarchy (e.g., only return states, not counties).
params = {"regionTypeFilter": REGION_TYPE}

resp = requests.get(url, headers=headers, params=params)
resp.raise_for_status()

all_regions = resp.json()

# ── Step 4: Find the Specific Region ──────────────────────────────────────────
# The children endpoint returns ALL regions of the requested type.
# We filter locally to find the one matching our search term.

matches = [r for r in all_regions if REGION_SEARCH.lower() in r["description"].lower()]

print(f"\nRegions matching '{REGION_SEARCH}' (type: {REGION_TYPE}):\n")
print(f"  {'hashId':<15} {'Description':<40} {'RegionType'}")
print("  " + "-" * 65)

for r in matches:
    print(f"  {r['hashId']:<15} {r['description']:<40} {r['regionType']}")

# ── Output ────────────────────────────────────────────────────────────────────
# The hashId from this output is what you will use in Step 5 (add-events.py)
# to assign your analysis to this geographic region.
if matches:
    print(f"\n  --> Use hashId '{matches[0]['hashId']}' in add-events.py as REGION_HASH_ID")
