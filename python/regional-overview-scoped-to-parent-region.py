"""
Option C — Default regions SCOPED to one parent region instead of the whole US.

This is a variant of sampleCode/Python - Regional Overview Download/main.py
from the Implan-Group/api repo. That script's "default" region fetch always
queries the top-level United States region for every MSA nationwide -- there
is no way to narrow that to, say, "just the MSAs in Texas" without editing
the code, because it calls the top-level `/children` endpoint rather than a
specific parent region's `/children` endpoint.

This version finds one parent region first (PARENT_REGION_SEARCH, e.g. a
state) and then only fetches THAT parent's children of the desired type. The
"default" behavior is preserved (you still get an automatic set of regions
without listing them individually) but it's scoped down from "nationwide" to
one geography -- e.g. every County or MSA inside a single state, instead of
every MSA in the country. Compare to get_top_level_region_children() in
regional-overview-configurable-region-type.py, which always starts from the
top-level US region with no parent.

What stays the same as the original script:
  - Custom combined regions are still built the same way (build combined
    region -> poll for completion). The original parsed these from an Excel
    file with openpyxl; here it's a plain Python dict so this file has no
    extra dependencies beyond `requests` + `python-dotenv`. The underlying
    API calls are identical either way.

See also: ../python/region details/step2-find-region.py, which uses the same
"search top-level children by description, then use its hashId as a parent"
pattern for a single region instead of a whole scoped set.
"""

import os
import re
import time
import requests
from dotenv import load_dotenv

# Reuses the credentials already set up for the "region details" examples in
# this repo, rather than duplicating a .env file in this folder too.
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "region details", ".env"))

USER = os.getenv("IMPLAN_USERNAME")
PW = os.getenv("IMPLAN_PASSWORD")

BASE_URL = "https://api.implan.com"
AUTH_URL = f"{BASE_URL}/api/auth"

# ── Configuration ──────────────────────────────────────────────────────────────

AGGREGATION_SCHEME_ID = 14   # 528-industry grouping scheme
DATASET_ID = 124             # 2024 dataset — must match earlier training examples

# The parent region to scope the "default" set to, and what type of children
# to pull from within it. Change PARENT_REGION_SEARCH to any state name (or
# change PARENT_REGION_TYPE + PARENT_REGION_SEARCH to scope by a different
# kind of parent, e.g. a Congressional District) to retarget this script.
PARENT_REGION_TYPE = "State"
PARENT_REGION_SEARCH = "Texas"
CHILD_REGION_TYPE = "County"   # "County" or "MSA" are the common choices here

# Custom combined regions to build in addition to the scoped default set above.
CUSTOM_COMBINED_REGIONS = {
    "Austin Metro Combo (Travis + Williamson Co, TX)": [48453, 48491],
}

MAX_BUILD_WAIT_SECONDS = 900   # Safety cap so this training script can't hang
                                # forever if a region build gets stuck. The
                                # original script polls indefinitely.

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "reports", "option-c-scoped-to-parent")

# ── Step 1: Authenticate ───────────────────────────────────────────────────────

def get_token(username, password):
    resp = requests.post(AUTH_URL, json={"username": username, "password": password})
    resp.raise_for_status()
    return resp.text.removeprefix("Bearer ")


token = get_token(USER, PW)
AUTH_HEADER = {"Authorization": f"Bearer {token}"}
JSON_HEADERS = {**AUTH_HEADER, "Content-Type": "application/json"}
print(f"Authenticated. Token preview: {token[:6]}...{token[-6:]}\n")

# ── Helpers: Region lookups and builds ─────────────────────────────────────────
# Endpoint docs: https://github.com/Implan-Group/api/blob/main/impact/readme.md


def get_top_level_region_children(region_type):
    """All regions of `region_type` directly under the top-level United States region."""
    url = f"{BASE_URL}/api/v1/region/{AGGREGATION_SCHEME_ID}/{DATASET_ID}/children"
    resp = requests.get(url, headers=AUTH_HEADER, params={"regionTypeFilter": region_type})
    resp.raise_for_status()
    return resp.json()


def get_region_children(parent_hashid, region_type):
    """All regions of `region_type` that are children of a SPECIFIC parent region."""
    url = f"{BASE_URL}/api/v1/region/{AGGREGATION_SCHEME_ID}/{DATASET_ID}/{parent_hashid}/children"
    resp = requests.get(url, headers=AUTH_HEADER, params={"regionTypeFilter": region_type})
    resp.raise_for_status()
    return resp.json()


def get_region_by_hashid(hashid):
    url = f"{BASE_URL}/api/v1/region/{AGGREGATION_SCHEME_ID}/{DATASET_ID}/{hashid}"
    resp = requests.get(url, headers=AUTH_HEADER)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()


def get_user_regions():
    """All user-defined (customized and/or combined) regions."""
    url = f"{BASE_URL}/api/v1/region/{AGGREGATION_SCHEME_ID}/{DATASET_ID}/user"
    resp = requests.get(url, headers=AUTH_HEADER)
    resp.raise_for_status()
    return resp.json()


def build_batch_regions(hashids):
    """Build (but do not combine) one or more Implan-defined regions."""
    url = f"{BASE_URL}/api/v1/region/build-and-return/{AGGREGATION_SCHEME_ID}"
    resp = requests.post(url, headers=JSON_HEADERS, json=hashids)
    resp.raise_for_status()
    return resp.json()


def build_combined_region(description, hashids):
    """Combine several regions (e.g. counties) into a single custom region."""
    url = f"{BASE_URL}/api/v1/region/build/combined/{AGGREGATION_SCHEME_ID}"
    payload = {"description": description, "hashIds": hashids, "urids": []}
    resp = requests.post(url, headers=JSON_HEADERS, json=payload)
    resp.raise_for_status()
    regions = resp.json()
    return regions[0] if regions else None


def wait_for_region_build(hashid, is_custom, poll_seconds=30):
    """Poll until a region's model finishes building."""
    waited = 0
    while True:
        if is_custom:
            region = next((r for r in get_user_regions() if r["hashId"] == hashid), None)
        else:
            region = get_region_by_hashid(hashid)

        if region and region.get("modelBuildStatus") == "Complete":
            return region

        if waited >= MAX_BUILD_WAIT_SECONDS:
            raise TimeoutError(f"Region '{hashid}' did not finish building within {MAX_BUILD_WAIT_SECONDS}s")

        print(f"  ...waiting on region build for '{hashid}' ({waited}s elapsed)")
        time.sleep(poll_seconds)
        waited += poll_seconds


def get_region_overview_csv(hashid):
    url = f"{BASE_URL}/api/v1/regions/export/{AGGREGATION_SCHEME_ID}/RegionOverviewIndustries"
    resp = requests.get(url, headers=AUTH_HEADER, params={"hashId": hashid})
    resp.raise_for_status()
    return resp.text


def sanitize_filename(name):
    return re.sub(r'[<>:"/\\|?*]', "_", name).strip()


# ── Step 2: Build the custom combined region(s) ────────────────────────────────

print("Building custom combined region(s) from CUSTOM_COMBINED_REGIONS...")

county_children = get_top_level_region_children("County")
fips_to_hashid = {c["fipsCode"]: c["hashId"] for c in county_children if c.get("fipsCode")}

regions = []
for name, fips_codes in CUSTOM_COMBINED_REGIONS.items():
    hashids = []
    for fips in fips_codes:
        hashid = fips_to_hashid.get(fips)
        if hashid is None:
            raise SystemExit(f"'{name}': FIPS code {fips} was not found among US counties")
        hashids.append(hashid)

    if len(hashids) > 1:
        built = build_combined_region(name, hashids)
        region = wait_for_region_build(built["hashId"], is_custom=True)
    else:
        built = build_batch_regions(hashids)[0]
        region = wait_for_region_build(built["hashId"], is_custom=False)

    print(f"  Built '{name}' -> hashId {region['hashId']}")
    regions.append(region)

# ── Step 3: Find the parent region, then fetch ITS children as the default set ─
# This is the key difference from the original script: instead of calling
# get_top_level_region_children() (which always starts at the US), we first
# search for one specific parent, then call get_region_children() scoped to
# that parent's hashId.

print(f"\nLooking up parent region matching '{PARENT_REGION_SEARCH}' (type: {PARENT_REGION_TYPE})...")
parent_candidates = get_top_level_region_children(PARENT_REGION_TYPE)
parent_matches = [r for r in parent_candidates if PARENT_REGION_SEARCH.lower() in r["description"].lower()]

if not parent_matches:
    raise SystemExit(f"No {PARENT_REGION_TYPE} region found matching '{PARENT_REGION_SEARCH}'")

parent_region = parent_matches[0]
print(f"  Found parent region '{parent_region['description']}' (hashId: {parent_region['hashId']})")

print(f"Fetching '{CHILD_REGION_TYPE}' regions within '{parent_region['description']}'...")
default_regions = get_region_children(parent_region["hashId"], CHILD_REGION_TYPE)
print(f"  Retrieved {len(default_regions)} region(s) scoped to this parent")

unbuilt_hashids = [r["hashId"] for r in default_regions if r.get("modelBuildStatus") != "Complete"]
if unbuilt_hashids:
    print(f"  Building {len(unbuilt_hashids)} unbuilt region(s)...")
    build_batch_regions(unbuilt_hashids)
    default_regions = [
        wait_for_region_build(r["hashId"], is_custom=False) if r["hashId"] in unbuilt_hashids else r
        for r in default_regions
    ]

regions.extend(default_regions)

# ── Step 4: Download Region Overview Industries reports ───────────────────────

os.makedirs(OUTPUT_DIR, exist_ok=True)
print(f"\nDownloading Region Overview Industries reports for {len(regions)} region(s)...")

for region in regions:
    filename = sanitize_filename(region["description"]) + ".csv"
    filepath = os.path.join(OUTPUT_DIR, filename)

    if os.path.exists(filepath):
        print(f"  Skipping '{region['description']}' (already downloaded)")
        continue

    csv_text = get_region_overview_csv(region["hashId"])
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(csv_text)
    print(f"  Saved '{region['description']}' -> {filename}")

print(f"\nDone. {len(regions)} region report(s) saved in '{OUTPUT_DIR}'")
