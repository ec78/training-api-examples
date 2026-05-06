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

GROUP_HASH_ID = "0GxZYok7Vp"
# --> From Step 3 (create-group.py): the hashId printed in the group output.
#     Identifies the regional model to pull summary industry data from.

DISPLAY_ROWS = 20
# How many industry rows to print. Set to None to print all rows.

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

# ── Step 2: Pull Study Area Data — Industry Summary ────────────────────────────
# This endpoint returns a per-industry summary of the regional economy, focusing
# on the relationship between output, intermediate inputs, and value added.
#
# Where Industry Detail (step5) shows how output is distributed across labor,
# property income, and taxes, the Industry Summary shows how output is broken
# down across production costs:
#
#   Total Output = Total Intermediate Inputs + Total Value Added
#
#   Intermediate Inputs — goods and services purchased from other industries
#                         to produce output (raw materials, utilities, services)
#   Total Value Added   — what the industry contributes to GDP after subtracting
#                         intermediate inputs; includes all labor income,
#                         property income, and taxes
#   Labor Income        — the portion of Value Added paid to workers
#
# Together with the Industry Detail data from step5, this gives a complete
# picture of how the regional economy is structured industry by industry.
#
# Response columns:
#   Industry Code           — IMPLAN numeric industry identifier
#   Description             — Industry name
#   Total Employment        — All jobs (wage & salary + proprietor combined)
#   Total Output            — Total value of goods/services produced ($)
#   Total Intermediate Inputs — Purchased inputs used in production ($)
#   Total Value Added       — GDP contribution: output minus intermediate inputs ($)
#   Labor Income            — Wages, salaries, and proprietor income ($)
#
# Note: GET requests must NOT include Content-Type — only pass Authorization.
#
# Endpoint: GET /api/v1/regions/export/{aggregationSchemeId}/StudyAreaDataIndustrySummary
# Docs:     https://github.com/Implan-Group/api/wiki/Region-Data---Industry-Summary

url = f"{BASE_URL}/api/v1/regions/export/{AGGREGATION_SCHEME_ID}/StudyAreaDataIndustrySummary"

params = {"hashId": GROUP_HASH_ID}

resp = requests.get(url, headers={"Authorization": headers["Authorization"]}, params=params)
resp.raise_for_status()

# ── Step 3: Parse and Display Results ─────────────────────────────────────────
rows = list(csv.DictReader(io.StringIO(resp.text), skipinitialspace=True))

print(f"Study Area Data — Industry Summary  |  hashId: {GROUP_HASH_ID}")
print(f"  Total industries in region: {len(rows)}")
if DISPLAY_ROWS:
    print(f"  Showing first {DISPLAY_ROWS} rows\n")
else:
    print()

print(f"  {'Code':<6} {'Industry':<38} {'Employment':>12} {'Output':>18} {'Int. Inputs':>18} {'Value Added':>18}")
print("  " + "-" * 114)

display = rows if DISPLAY_ROWS is None else rows[:DISPLAY_ROWS]

for row in display:
    code        = row.get("Industry Code", "")
    desc        = row.get("Description", "")[:37]
    employment  = float(row.get("Total Employment", 0) or 0)
    output      = float(row.get("Total Output", 0) or 0)
    int_inputs  = float(row.get("Total Intermediate Inputs", 0) or 0)
    value_added = float(row.get("Total Value Added", 0) or 0)

    print(f"  {code:<6} {desc:<38} {employment:>12,.1f} ${output:>17,.0f} ${int_inputs:>17,.0f} ${value_added:>17,.0f}")

# ── Summary ────────────────────────────────────────────────────────────────────
total_emp        = sum(float(r.get("Total Employment", 0) or 0) for r in rows)
total_output     = sum(float(r.get("Total Output", 0) or 0) for r in rows)
total_int_inputs = sum(float(r.get("Total Intermediate Inputs", 0) or 0) for r in rows)
total_val_added  = sum(float(r.get("Total Value Added", 0) or 0) for r in rows)
total_labor      = sum(float(r.get("Labor Income", 0) or 0) for r in rows)

print(f"\n  Region Totals (all {len(rows)} industries):")
print(f"    Total Employment:         {total_emp:>12,.1f} jobs")
print(f"    Total Output:             ${total_output:>14,.0f}")
print(f"    Total Intermediate Inputs:${total_int_inputs:>14,.0f}")
print(f"    Total Value Added:        ${total_val_added:>14,.0f}")
print(f"    Labor Income:             ${total_labor:>14,.0f}")

# Value Added as a share of Output is a useful regional economic metric.
# A higher share means the region retains more of its production value locally
# (rather than spending it on imported inputs).
if total_output > 0:
    va_share = (total_val_added / total_output) * 100
    print(f"\n  Value Added as % of Output: {va_share:.1f}%")
    print(f"  (Higher % = region retains more economic value from its production)")
