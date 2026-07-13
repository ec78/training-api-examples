"""
Option B — Custom regions ONLY (default region fetch removed entirely).

This is a variant of sampleCode/Python - Regional Overview Download/main.py
from the Implan-Group/api repo. That script always fetches every MSA in the
United States, in addition to whatever custom regions you defined in the
Combined Region Builder xlsx input -- the Excel input only ever adds to that
default set, it never replaces or filters it.

This version is the direct fix for that: the "fetch every MSA" section has
been deleted outright. Only the regions you explicitly define in
CUSTOM_COMBINED_REGIONS below get built and processed. If you don't want any
automatic "everything else" behavior at all, this is the pattern to use --
comment out or remove the block, rather than trying to configure it away.

What stays the same as the original script:
  - Custom combined regions are still built the same way (build combined
    region -> poll for completion). The original parsed these from an Excel
    file with openpyxl; here it's a plain Python dict so this file has no
    extra dependencies beyond `requests` + `python-dotenv`. The underlying
    API calls are identical either way.

See also: ../python/region details/step2-find-region.py for the region
lookup pattern this borrows from.
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

# Custom combined regions to build. There is intentionally no "default region
# type" variable in this file -- see the docstring above.
CUSTOM_COMBINED_REGIONS = {
    "Austin Metro Combo (Travis + Williamson Co, TX)": [48453, 48491],
}

MAX_BUILD_WAIT_SECONDS = 900   # Safety cap so this training script can't hang
                                # forever if a region build gets stuck. The
                                # original script polls indefinitely.

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "reports", "option-b-custom-only")

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

# ── There is no Step 3 here. ───────────────────────────────────────────────────
# This is the whole point of this variant: the original script's "fetch every
# MSA in the US" block has been removed rather than reconfigured. `regions`
# contains only what CUSTOM_COMBINED_REGIONS defined above.

print(f"\nNo default region set is fetched in this variant -- processing only "
      f"the {len(regions)} custom region(s) defined above.")

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
