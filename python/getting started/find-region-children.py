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
# find-region.py finds a single region by searching one flat list (e.g. every
# County in the US). This script goes one step further: it finds a County,
# then asks the API for the Zip codes that live INSIDE that specific County —
# a parent/child lookup rather than a flat search.

AGGREGATION_SCHEME_ID = 14   # 528-industry grouping scheme

DATASET_ID = 124             # The data year to use — replace with an ID from
                             # get-datasets.py (e.g., 124 = 2024 dataset)

# The County to use as the "parent" region. Travis County, TX is used here as
# a representative example — change this to any county name.
COUNTY_SEARCH = "Travis County"

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

# GET requests must NOT include Content-Type — the API returns 400 if it's
# present. Only POST/PUT need the full headers dict built above.
get_headers = {"Authorization": headers["Authorization"]}

# ── Step 2: Find the County (the "parent" region) ──────────────────────────────
# Same pattern as find-region.py: pull every County in the US, then filter
# locally for the one matching COUNTY_SEARCH. Its hashId becomes the parent
# we scope the Zip code lookup to in Step 3.
#
# Endpoint: GET /api/v1/region/{aggregationSchemeId}/{datasetId}/children
# Docs:     https://github.com/Implan-Group/api/wiki/Regional-Children

url = f"{BASE_URL}/api/v1/region/{AGGREGATION_SCHEME_ID}/{DATASET_ID}/children"
params = {"regionTypeFilter": "County"}

resp = requests.get(url, headers=get_headers, params=params)
resp.raise_for_status()

all_counties = resp.json()
county_matches = [r for r in all_counties if COUNTY_SEARCH.lower() in r["description"].lower()]

if not county_matches:
    raise SystemExit(f"No County found matching '{COUNTY_SEARCH}'")

county = county_matches[0]
print(f"Parent region: {county['description']}  |  hashId: {county['hashId']}\n")

# ── Step 3: Get the Zip Codes Inside That County ───────────────────────────────
# This is the key difference from find-region.py: instead of calling the
# top-level "children" endpoint (which returns every region of a type in the
# whole country), we call the SAME endpoint with the county's hashId inserted
# into the path. That scopes the results to children of just that one region.
#
# Endpoint: GET /api/v1/region/{aggregationSchemeId}/{datasetId}/{parentHashId}/children
# Docs:     https://github.com/Implan-Group/api/wiki/Regional-Children
#
# Note: Zip-level data has limited availability in IMPLAN — some counties may
# return zero Zip regions if IMPLAN does not publish Zip-level models there.

url = f"{BASE_URL}/api/v1/region/{AGGREGATION_SCHEME_ID}/{DATASET_ID}/{county['hashId']}/children"
params = {"regionTypeFilter": "ZipCode"}
# Note: despite "Zip" being the region type shown in region descriptions
# elsewhere, the API's regionTypeFilter query parameter only accepts
# "ZipCode" — passing "Zip" here returns a 400 Bad Request.

resp = requests.get(url, headers=get_headers, params=params)
resp.raise_for_status()

zip_codes = resp.json()

# ── Step 4: Display Results ─────────────────────────────────────────────────────
print(f"Zip codes inside '{county['description']}': {len(zip_codes)} found\n")

if zip_codes:
    print(f"  {'hashId':<15} {'Description':<20} {'RegionType'}")
    print("  " + "-" * 50)
    for z in zip_codes:
        print(f"  {z['hashId']:<15} {z['description']:<20} {z['regionType']}")

    # ── Output ───────────────────────────────────────────────────────────────────
    # Any of these hashIds can be used exactly like a County or State hashId in
    # the rest of this repo's examples (e.g. add-events.py, or the "region
    # details" series) to run analysis at the Zip code level.
    print(f"\n  --> Use hashId '{zip_codes[0]['hashId']}' in add-events.py as REGION_HASH_ID")
    print(f"      to analyze Zip code '{zip_codes[0]['description']}' specifically")
else:
    print("  No Zip-level regions are available for this county in this dataset.")
