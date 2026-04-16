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
RUN_ID = 605605
# --> From Step 6 (run-analysis.py): the integer Run ID returned after the
#     analysis completed with status "Complete".
#     Example: 17280

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

# ── Step 2: Retrieve Summary Economic Indicators ──────────────────────────────
# This endpoint returns the core economic impact results: the direct, indirect,
# and induced effects across Employment, Labor Income, Value Added, and Output.
#
# Direct effects   — the immediate impact of the event itself
# Indirect effects — impacts on supplier industries (supply chain)
# Induced effects  — impacts from household spending of income earned
#
# The response is returned as a CSV file, not JSON.
# Each row represents one combination of group, event, region, and impact type.
#
# Endpoint: GET /api/v1/impact/results/SummaryEconomicIndicators/{runId}
# Docs:     https://github.com/Implan-Group/api/wiki/Results---Summary-Economic-Indicators

url = f"{BASE_URL}/api/v1/impact/results/SummaryEconomicIndicators/{RUN_ID}"

# Use only the Authorization header — Content-Type is not needed on GET requests
resp = requests.get(url, headers={"Authorization": headers["Authorization"]})
resp.raise_for_status()

# ── Step 3: Parse and Display Results ─────────────────────────────────────────
# The response body is plain CSV text. Python's built-in csv module can parse it.
# io.StringIO wraps the raw text string so csv.DictReader can treat it like a file.

# skipinitialspace=True strips the leading space after each comma in the CSV.
# The IMPLAN results CSV uses ", " as its delimiter, which would otherwise
# produce column names like " Employment" instead of "Employment".
csv_data = list(csv.DictReader(io.StringIO(resp.text), skipinitialspace=True))

# Debug: print the actual column names returned by the API so we can
# verify they match what the code expects below.
if csv_data:
    print(f"[debug] CSV columns: {list(csv_data[0].keys())}\n")

print(f"Results for Run ID {RUN_ID}:\n")

# Print a header row using the column names from the CSV
col_impact      = "Impact"           # Direct / Indirect / Induced / Total
col_employment  = "Employment"       # Number of jobs supported
col_labor       = "LaborIncome"      # Wages, salaries, and proprietor income ($)
col_value_added = "ValueAdded"       # GDP contribution ($)
col_output      = "Output"           # Total industry output ($)

print(f"  {'Impact Type':<12} {'Employment':>14} {'Labor Income':>18} {'Value Added':>18} {'Output':>18}")
print("  " + "-" * 82)

for row in csv_data:
    # Format large dollar amounts with commas for readability
    employment  = f"{float(row[col_employment]):>14,.1f}"
    labor       = f"${float(row[col_labor]):>17,.0f}"
    value_added = f"${float(row[col_value_added]):>17,.0f}"
    output      = f"${float(row[col_output]):>17,.0f}"

    print(f"  {row[col_impact]:<12} {employment} {labor} {value_added} {output}")

# ── Summary ────────────────────────────────────────────────────────────────────
# Sum up the Total row (or all rows if no explicit Total) for a quick overview.
total_rows = [r for r in csv_data if "total" in r.get(col_impact, "").lower()]

if total_rows:
    t = total_rows[0]
    print(f"\n  Total Economic Impact:")
    print(f"    Employment:  {float(t[col_employment]):>12,.1f} jobs")
    print(f"    Labor Income: ${float(t[col_labor]):>14,.0f}")
    print(f"    Value Added:  ${float(t[col_value_added]):>14,.0f}")
    print(f"    Output:       ${float(t[col_output]):>14,.0f}")
