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
# A region's hashId is the key identifier used in this workflow for two things:
#   1. Creating a Group in a project (to establish the geographic study area)
#   2. Pulling Region Details data (to retrieve the economic data for that area)
# This script helps you find the hashId for the region you want to analyze.

AGGREGATION_SCHEME_ID = 14   # 528-industry grouping scheme
                              # Must match what you use in all other steps.

DATASET_ID = 124             # The data year to search within.
                              # Run get-datasets.py to see available IDs.
                              # Example: 124 = 2024 dataset

REGION_TYPE = "County"       # The geographic level to search.
                              # Common values: "Country", "State", "County", "MSA", "Zip"

REGION_SEARCH = "Travis County"   # Text to match against region descriptions.
                                   # The script filters all regions of REGION_TYPE
                                   # to find those whose name contains this string.

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
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

token   = get_token(USER, PW)
headers = build_headers(token)
print(f"Authenticated. Token preview: {token[:6]}...{token[-6:]}\n")

# ── Step 2: Get the Top-Level Region ──────────────────────────────────────────
# IMPLAN regions are organized in a hierarchy: Country → State → County/MSA.
# Fetching the top level confirms that the aggregation scheme and dataset
# combination is valid before we try to search for a specific region.
#
# Endpoint: GET /api/v1/region/{aggregationSchemeId}/{datasetId}
# Docs:     https://github.com/Implan-Group/api/wiki/Regions---Top-Level
#
# Note: GET requests must NOT include Content-Type — only pass Authorization.

url = f"{BASE_URL}/api/v1/region/{AGGREGATION_SCHEME_ID}/{DATASET_ID}"

resp = requests.get(url, headers={"Authorization": headers["Authorization"]})
resp.raise_for_status()

top_level = resp.json()

# The API returns a single region object (not a list) for the top level —
# this is the United States total. Wrap it in a list for uniform handling.
if isinstance(top_level, dict):
    top_level = [top_level]

print("Top-level region (confirms dataset is valid):")
for region in top_level:
    print(f"  {region['description']}  |  regionType: {region['regionType']}  |  hashId: {region['hashId']}")

# ── Step 3: Get Child Regions ─────────────────────────────────────────────────
# Retrieve all regions of the specified type (e.g., all counties in the US).
# We then filter this list locally to find the specific region we want.
#
# Endpoint: GET /api/v1/region/{aggregationSchemeId}/{datasetId}/children
# Docs:     https://github.com/Implan-Group/api/wiki/Regional-Children

url = f"{BASE_URL}/api/v1/region/{AGGREGATION_SCHEME_ID}/{DATASET_ID}/children"

# regionTypeFilter narrows the results to one geographic level so we are not
# comparing counties against states in the same list.
params = {"regionTypeFilter": REGION_TYPE}

resp = requests.get(url, headers={"Authorization": headers["Authorization"]}, params=params)
resp.raise_for_status()

all_regions = resp.json()

# ── Step 4: Filter to the Region You Need ─────────────────────────────────────
# The children endpoint returns every region of the requested type.
# We do a case-insensitive search to find the one(s) matching our term.
matches = [r for r in all_regions if REGION_SEARCH.lower() in r["description"].lower()]

print(f"\nRegions matching '{REGION_SEARCH}' (type: {REGION_TYPE}):\n")
print(f"  {'hashId':<15} {'urid':<12} {'Description':<42} {'RegionType'}")
print("  " + "-" * 83)

for r in matches:
    print(f"  {r['hashId']:<15} {str(r.get('urid', '')):<12} {r['description']:<42} {r['regionType']}")

# ── Output ─────────────────────────────────────────────────────────────────────
# The hashId is used in Step 3 to create a Group (which ties this region to your
# project) and in Steps 4–6 to pull the Region Details data for this area.
if matches:
    print(f"\n  --> hashId: '{matches[0]['hashId']}'")
    print(f"      Copy this into step3-create-group.py as REGION_HASH_ID")
