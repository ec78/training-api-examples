"""
Finds and prints the IMPLAN hashId for a given County, using the Impact API directly.

Auth + region-lookup patterns are taken from the IMPLAN API sample code:
- sampleCode/Python - Regional Overview Download/implan_auth.py
- sampleCode/Python/workflow_examples/regional_workflow_examples.py
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

USERNAME = USER
PASSWORD = PW

AGGREGATION_SCHEME_ID = 14  # 528 Unaggregated (US) -- see GET /api/v1/aggregationSchemes
DATASET_ID = 124            # 2024 -- see GET /api/v1/datasets

STATE_NAME = "Missouri"
COUNTY_NAME = "Jackson County, MO"

def get_bearer_token(username: str, password: str) -> str:
    """POST to /auth; the response BODY is the ready-to-use Authorization header
    value as-is -- do not prepend "Bearer " yourself."""
    response = requests.post(f"{BASE_URL}/auth", json={"username": username, "password": password})
    response.raise_for_status()
    return response.text


def get_region_children(token: str, parent_hash_id: str | None, region_type_filter: str) -> list[dict]:
    headers = {"Authorization": token}
    if parent_hash_id:
        url = f"{BASE_URL}/api/v1/region/{AGGREGATION_SCHEME_ID}/{DATASET_ID}/{parent_hash_id}/children"
    else:
        # No parent hashId/URID -> children of the top-level Region (the Country)
        url = f"{BASE_URL}/api/v1/region/{AGGREGATION_SCHEME_ID}/{DATASET_ID}/children"
    response = requests.get(url, params={"regionTypeFilter": region_type_filter}, headers=headers)
    response.raise_for_status()
    return response.json()


def find_county_hash_id(token: str, state_name: str, county_name: str) -> str | None:
    states = get_region_children(token, None, "State")
    state = next((s for s in states if s["description"].lower() == state_name.lower()), None)
    if state is None:
        raise ValueError(f"State '{state_name}' not found for this Aggregation Scheme/Dataset")

    counties = get_region_children(token, state["hashId"], "County")
    county = next((c for c in counties if c["description"].lower() == county_name.lower()), None)
    return county["hashId"] if county else None


if __name__ == "__main__":
    token = get_bearer_token(USERNAME, PASSWORD)
    hash_id = find_county_hash_id(token, STATE_NAME, COUNTY_NAME)

    if hash_id:
        print(f"{COUNTY_NAME} hashId: {hash_id}")
    else:
        print(f"{COUNTY_NAME} not found in {STATE_NAME}.")
