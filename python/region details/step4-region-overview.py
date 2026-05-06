import os
import csv
import io
import requests
from dotenv import load_dotenv

# Load credentials from the .env file next to this script
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

USER = os.getenv("IMPLAN_USERNAME")
PW   = os.getenv("IMPLAN_PASSWORD")

BASE_URL = "https://api.implan.com"
AUTH_URL = f"{BASE_URL}/api/auth"

# ── Configuration ──────────────────────────────────────────────────────────────
AGGREGATION_SCHEME_ID = 14   # 528-industry grouping scheme
                              # Must match what you used in earlier steps.

GROUP_HASH_ID = "0GxZYok7Vp"
# --> From Step 3 (create-group.py): the hashId printed in the group output.
#     This is IMPLAN's identifier for the regional economic model that the
#     group was built on — the same identifier is used here to pull that data.

DISPLAY_ROWS = 20
# How many industry rows to print to the screen.
# Set to None to print all rows (may be 500+ for detailed schemes).

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

# ── Step 2: Pull Region Overview Industries ────────────────────────────────────
# This endpoint returns a high-level economic snapshot of the region — one row
# per industry showing total employment, labor income, and output.
#
# This is the same summary you see when you open a region in IMPLAN Cloud and
# click "Overview". It reflects the region's total economic activity as captured
# in IMPLAN's built model for that geography and data year.
#
# Response columns:
#   Display Code        — IMPLAN industry code number
#   Display Description — Industry name (e.g., "Oilseed farming")
#   Employment          — Total jobs (wage & salary + proprietor combined)
#   Labor Income        — Total labor income ($): wages, salaries, and proprietor income
#   Output              — Total industry output ($): the full value of goods and services
#                         produced by this industry in the region
#   Average Employee Compensation per Wage and Salary Employee
#                       — Mean annual compensation per W&S worker ($)
#   Average Proprietor Income per Proprietor
#                       — Mean annual income per self-employed worker ($)
#
# The response is plain CSV text, not JSON. We parse it with Python's csv module.
#
# Note: GET requests must NOT include Content-Type — only pass Authorization.
#
# Endpoint: GET /api/v1/regions/export/{aggregationSchemeId}/RegionOverviewIndustries
# Docs:     https://github.com/Implan-Group/api/wiki/Region-Data---Overview-Industries

url = f"{BASE_URL}/api/v1/regions/export/{AGGREGATION_SCHEME_ID}/RegionOverviewIndustries"

# The hashId query parameter identifies which region's data to return.
# This is the same hashId stored in the Group from step3-create-group.py.
params = {"hashId": GROUP_HASH_ID}

resp = requests.get(url, headers={"Authorization": headers["Authorization"]}, params=params)
resp.raise_for_status()

# ── Step 3: Parse and Display Results ─────────────────────────────────────────
# io.StringIO wraps the raw CSV text string so csv.DictReader can treat it
# like a file. skipinitialspace=True removes the leading space that the IMPLAN
# API adds after each comma — without it, column names include a leading space
# (e.g., " Employment" instead of "Employment").

rows = list(csv.DictReader(io.StringIO(resp.text), skipinitialspace=True))

print(f"Region Overview Industries  |  hashId: {GROUP_HASH_ID}")
print(f"  Total industries in region: {len(rows)}")
if DISPLAY_ROWS:
    print(f"  Showing first {DISPLAY_ROWS} rows\n")
else:
    print()

# Print a formatted table. Right-align numeric columns for readability.
print(f"  {'Code':<6} {'Industry':<45} {'Employment':>14} {'Labor Income':>18} {'Output':>18}")
print("  " + "-" * 105)

display = rows if DISPLAY_ROWS is None else rows[:DISPLAY_ROWS]

for row in display:
    code       = row.get("Display Code", "")
    desc       = row.get("Display Description", "")[:44]
    employment = float(row.get("Employment", 0) or 0)
    labor      = float(row.get("Labor Income", 0) or 0)
    output     = float(row.get("Output", 0) or 0)

    print(f"  {code:<6} {desc:<45} {employment:>14,.1f} ${labor:>17,.0f} ${output:>17,.0f}")

# ── Summary ────────────────────────────────────────────────────────────────────
# Sum all industries to get the region's total economic activity.
total_emp    = sum(float(r.get("Employment", 0) or 0) for r in rows)
total_labor  = sum(float(r.get("Labor Income", 0) or 0) for r in rows)
total_output = sum(float(r.get("Output", 0) or 0) for r in rows)

print(f"\n  Region Totals (all {len(rows)} industries):")
print(f"    Employment:   {total_emp:>14,.1f}")
print(f"    Labor Income: ${total_labor:>17,.0f}")
print(f"    Output:       ${total_output:>17,.0f}")
