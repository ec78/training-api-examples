import os
import time
import requests
from dotenv import load_dotenv

# Load credentials from the .env file next to this script
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

USER = os.getenv("IMPLAN_USERNAME")
PW   = os.getenv("IMPLAN_PASSWORD")

BASE_URL = "https://api.implan.com"
AUTH_URL = f"{BASE_URL}/api/auth"

# ── Configuration ──────────────────────────────────────────────────────────────
PROJECT_ID = "77e3ff58-8622-49ed-9880-2eb8cf8cdebf"
# --> From Step 4 (create-project.py) / Step 5 (add-events.py)
#     The project must have at least one Group with at least one Event before
#     you can run the analysis. If the project is incomplete, the API returns 400.

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

# ── Step 2: Run the Analysis ──────────────────────────────────────────────────
# This triggers IMPLAN's input-output model to calculate the economic impact
# of all events in the project. The model computes direct, indirect, and
# induced effects across all industries in the region.
#
# The API returns an integer Run ID — a unique identifier for this specific
# analysis run. You will use it to retrieve results in get-results.py.
#
# Note: Running the same project again produces a new Run ID each time.
#
# Endpoint: POST /api/v1/impact/{projectId}
# Docs:     https://github.com/Implan-Group/api/wiki/Run-Impact-Analysis
# Note: this path does NOT include "project/" — unlike the create/event/group
# endpoints, the run endpoint goes directly to /impact/{projectId}.

url = f"{BASE_URL}/api/v1/impact/{PROJECT_ID}"

resp = requests.post(url, headers=headers)
resp.raise_for_status()

# The response body is a plain integer as text (e.g. "605590"), not JSON.
# We use int(resp.text.strip()) to guarantee a clean integer with no decimal point.
run_id = int(resp.text.strip())

print(f"Analysis triggered. Run ID: {run_id}")

# ── Step 3: Check Status ───────────────────────────────────────────────────────
# Impact calculations run asynchronously in the background. We poll the status
# endpoint until the run reaches a terminal state.
#
# Possible status values:
#   "New"                 — queued but not yet started
#   "InProgress"          — actively running
#   "ReadyForWarehouse"   — still processing (intermediate state)
#   "Complete"            — finished successfully → results are ready
#   "Error"               — failed (check your project for invalid events/groups)
#   "UserCancelled"       — cancelled by the user
#
# Note: Small analyses often complete within seconds. If the status endpoint
# returns an error, the run may have already completed — proceed to get-results.py
# with the Run ID above.
#
# Endpoint: GET /api/v1/impact/status/{runId}
# Docs:     https://github.com/Implan-Group/api/wiki/Get-Impact-Status

status_url = f"{BASE_URL}/api/v1/impact/status/{run_id}"

TERMINAL_STATUSES = {"Complete", "Error", "UserCancelled"}
POLL_INTERVAL     = 10   # seconds between checks

print("Checking status (analyses often complete in seconds)...")

status = None
for attempt in range(12):   # try for up to ~2 minutes
    time.sleep(POLL_INTERVAL)
    resp = requests.get(status_url, headers={"Authorization": headers["Authorization"]})

    if not resp.ok:
        # A 400 here often means the run completed before we could poll it.
        # This is normal for small analyses — proceed to get-results.py.
        print(f"  Status check returned {resp.status_code} — analysis may have already completed.")
        break

    status = resp.text.strip()
    print(f"  Status: {status}")

    if status in TERMINAL_STATUSES:
        break

# ── Output ─────────────────────────────────────────────────────────────────────
print(f"\n  --> Run ID: {run_id}")
print(f"      Copy this into get-results.py as RUN_ID")

if status == "Error":
    print("  Analysis failed. Check your project setup in add-events.py and try again.")
elif status == "UserCancelled":
    print("  Analysis was cancelled.")
