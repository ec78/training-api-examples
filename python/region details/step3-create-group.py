import os
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
# A Project is the workspace that organizes your analysis.
# A Group lives inside a Project and defines WHERE the analysis occurs —
# it links a specific region (by hashId) to a data year (dataset).
#
# When pulling Region Details data, the Group's hashId is the identifier
# you pass to the region data export endpoints. This step establishes that
# connection between your project and the region you want to study.

# Append a timestamp to ensure the title is unique in your account. IMPLAN
# requires all Project titles to be unique account-wide — re-running this
# script without a timestamp would fail with "A saved Project with this name
# already exists."
PROJECT_TITLE = f"Travis Co. Region Study {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

AGGREGATION_SCHEME_ID = 14   # 528-industry grouping scheme
                              # Must match what you used in step2-find-region.py.

HOUSEHOLD_SET_ID = 1         # Defines which household income categories to use.
                              # 1 is the standard IMPLAN default.

IS_MRIO = False              # Multi-Region Input-Output model.
                              # False = single-region analysis (most common).

REGION_HASH_ID = "0GxZYok7Vp"
# --> From Step 2 (find-region.py): the hashId for the region you want to study.
#     Example: "0GxZYok7Vp" = Travis County, TX

DATASET_ID = 124
# --> From get-datasets.py: the data year for the regional model.
#     Example: 124 = 2024 dataset. Must match the year used in step2-find-region.py.

DOLLAR_YEAR = 2024
# --> The year your monetary values are expressed in.
#     For region data exploration, set this to match the dataset year.

GROUP_TITLE = "Travis County Study Area"   # A descriptive label for this group

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

# ── Step 2: Create the Project ─────────────────────────────────────────────────
# A Project is required before you can create a Group. Think of it as opening
# a new analysis workspace. The aggregation scheme set here determines which
# industry grouping is used throughout the project and in the region data exports.
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

project = resp.json()
project_id = project["id"]

print(f"Project created: '{project['title']}' (ID: {project_id})\n")

# ── Step 3: Create a Group ─────────────────────────────────────────────────────
# A Group assigns a region (via hashId) and a data year to the project.
# Creating the Group answers: "My study area is THIS region, using THIS data year."
#
# The Group response includes several region identifiers. The hashId is the
# one used by the Region Details endpoints in the next steps to retrieve the
# underlying economic data for this area.
#
# Note: In a full impact analysis you would also add Events to this Group to
# model specific economic activities (see the sample analysis series). For this
# workflow, we only need the Group to establish the study area.
#
# Endpoint: POST /api/v1/impact/project/{projectId}/group
# Docs:     https://github.com/Implan-Group/api/wiki/Create-Group

url = f"{BASE_URL}/api/v1/impact/project/{project_id}/group"

group_payload = {
    "Title":       GROUP_TITLE,
    "HashId":      REGION_HASH_ID,    # The region's unique identifier from step2-find-region.py
    "DatasetId":   DATASET_ID,        # Which data year's economic model to use
    "DollarYear":  DOLLAR_YEAR,       # The year monetary values are expressed in
    "groupEvents": []                  # No events needed for region data —
                                       # add events here for a full impact analysis
}

resp = requests.post(url, json=group_payload, headers=headers)
resp.raise_for_status()

group = resp.json()

# ── Output ─────────────────────────────────────────────────────────────────────
# The Group response confirms which region model IMPLAN has loaded.
# Any of the identifiers below (hashId, urid, modelId) can be passed to the
# region data export endpoints — hashId is the most commonly used.
print(f"Group created: '{group['title']}' (ID: {group['id']})")
print(f"\n  Region identifiers returned by the API:")
print(f"    hashId:  {group['hashId']}")
print(f"    urid:    {group.get('urid', 'N/A')}")
print(f"    modelId: {group.get('modelId', 'N/A')}")
print(f"  Dataset:   {group['datasetId']}")
print(f"  DollarYear:{group['dollarYear']}")
print(f"\n  --> GROUP_HASH_ID = \"{group['hashId']}\"")
print(f"      Copy this into steps 4–6 as GROUP_HASH_ID")
