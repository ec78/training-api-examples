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
# Fill in the values from the previous steps before running this script.

PROJECT_ID = "77e3ff58-8622-49ed-9880-2eb8cf8cdebf"
# --> From Step 4 (create-project.py): the GUID returned after project creation.
#     Example: "496256c2-a089-4d42-a1a1-cafe73a43216"

REGION_HASH_ID = "BzxjENLeVN"
# --> From Step 3 (find-region.py): the hashId for the region you want to analyze.
#     Example: "9EbJv6yJb0"

DATASET_ID = 124
# --> From Step 2 (get-datasets.py): the data year ID you are using.
#     Must match the dataset used when you looked up the region.

DOLLAR_YEAR = 2026
# --> The year your monetary values (output, compensation, etc.) are expressed in.
#     This is typically the same year as your dataset.

# ── Event Definition ───────────────────────────────────────────────────────────
# An Event represents the economic activity (the "shock") you are analyzing.
# Here we use an IndustryOutput event — the most common type — which models
# a change in spending within a specific industry.

# Append a timestamp to ensure the title is unique within the project.
# IMPLAN requires all event titles to be unique — re-running the script
# without this would fail with "Impact Event Title must be Unique".
EVENT_TITLE        = f"Example Industry Output Event {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
EVENT_OUTPUT       = 1000000.00   # Total industry output value in dollars

INDUSTRY_CODE = 1
# --> The numeric code for the industry being analyzed.
#     Use get-industry-codes.py to look up valid codes for your aggregation scheme.
#     Example: 1 = Oilseed farming, 2 = Grain farming (scheme 14)
#     This field is REQUIRED — the analysis cannot run without it.

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

# ── Step 2: Create an Event ───────────────────────────────────────────────────
# An Event defines WHAT economic activity is happening — the industry and
# dollar amount of the impact. At this point it is not yet tied to a geography;
# that happens when we create the Group in the next step.
#
# ImpactEventType options include: "IndustryOutput", "IndustryEmployment",
# "IndustryEmployeeCompensation", "IndustryProprietorIncome", and others.
#
# Endpoint: POST /api/v1/impact/project/{projectId}/event
# Docs:     https://github.com/Implan-Group/api/wiki/Create-Event

url = f"{BASE_URL}/api/v1/impact/project/{PROJECT_ID}/event"

event_payload = {
    "ImpactEventType": "IndustryOutput",   # Type of economic activity being modeled
    "Title":           EVENT_TITLE,        # A descriptive label for this event
    "IndustryCode":    INDUSTRY_CODE,      # REQUIRED: which industry this activity belongs to
                                           # Use get-industry-codes.py to find valid codes
    "Output":          EVENT_OUTPUT        # Dollar value of the output change
    # Optional fields you can also include:
    # "Employment":            0.0   # Number of jobs
    # "EmployeeCompensation":  0.0   # Wages and salaries paid ($)
    # "ProprietorIncome":      0.0   # Business owner income ($)
}

resp = requests.post(url, json=event_payload, headers=headers)

if not resp.ok:
    print(f"  Event creation failed ({resp.status_code}): {resp.text!r}")
    resp.raise_for_status()

event = resp.json()

print(f"Event created: '{event['title']}' (ID: {event['id']})\n")

# ── Step 3: Create a Group ────────────────────────────────────────────────────
# A Group links an Event to a geographic Region and a data year.
# Think of it as answering: "WHERE and WHEN does this event occur?"
#
# Without a Group, the Event exists in the project but has no geography,
# and the analysis cannot be run.
#
# The HashId here is the region's hashId from find-region.py — it tells IMPLAN
# which geographic model to use for the input-output calculations.
#
# Endpoint: POST /api/v1/impact/project/{projectId}/group
# Docs:     https://github.com/Implan-Group/api/wiki/Create-Group

url = f"{BASE_URL}/api/v1/impact/project/{PROJECT_ID}/group"

group_payload = {
    "Title":      "Example Group",      # A label for this geographic grouping
    "HashId":     REGION_HASH_ID,       # The region's unique identifier from find-region.py
    "DatasetId":  DATASET_ID,           # The data year for the regional model
    "DollarYear": DOLLAR_YEAR,          # The year your dollar values are expressed in
    "groupEvents": [
        {"eventId": event["id"]}        # Link the event we just created to this region
    ]
}

resp = requests.post(url, json=group_payload, headers=headers)
resp.raise_for_status()

group = resp.json()

# ── Output ─────────────────────────────────────────────────────────────────────
print(f"Group created: '{group['title']}' (ID: {group['id']})")
print(f"  Region (hashId): {group['hashId']}")
print(f"  Dataset:         {group['datasetId']}")
print(f"  Dollar Year:     {group['dollarYear']}")
print(f"  Events linked:   {len(group['groupEvents'])}")
print(f"\nProject '{PROJECT_ID}' is ready to run.")
print(f"\n  --> Copy PROJECT_ID into run-analysis.py as PROJECT_ID")
