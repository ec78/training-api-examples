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
#     Identifies the regional model to pull detailed industry data from.

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

# ── Step 2: Pull Study Area Data — Industry Detail ─────────────────────────────
# This endpoint returns the full Study Area Data for the region broken down
# by industry. It shows the complete composition of each industry: how many
# people work there (wage & salary vs. self-employed), what they earn, how much
# the industry produces, and how that production is split across value-added
# components.
#
# This is the granular foundation of IMPLAN's input-output model. Every
# economic multiplier IMPLAN calculates is derived from this underlying data,
# so understanding it helps you interpret impact analysis results.
#
# Response columns:
#   Industry Code            — IMPLAN numeric industry identifier
#   Description              — Industry name (e.g., "Grain farming")
#   Total Output             — Total value of goods/services produced ($)
#   Wage and Salary Employment — Full- and part-time wage/salary jobs (count)
#   Employee Compensation    — Total wages, salaries, and benefits paid ($)
#   Proprietor Employment    — Self-employed / owner-operator jobs (count)
#   Proprietor Income        — Self-employment income ($)
#   Other Property Income    — Returns to capital: rent, interest, dividends ($)
#   Taxes on Production and Imports Net of Subsidies
#                            — Net taxes paid by the industry to governments ($)
#
# The sum of Employee Compensation + Proprietor Income = Labor Income.
# The sum of Labor Income + Other Property Income + Taxes = Value Added.
# Value Added + Intermediate Inputs = Total Output.
#
# Note: GET requests must NOT include Content-Type — only pass Authorization.
#
# Endpoint: GET /api/v1/regions/export/{aggregationSchemeId}/StudyAreaDataIndustryDetail
# Docs:     https://github.com/Implan-Group/api/wiki/Region-Data---Industry-Detail

url = f"{BASE_URL}/api/v1/regions/export/{AGGREGATION_SCHEME_ID}/StudyAreaDataIndustryDetail"

params = {"hashId": GROUP_HASH_ID}

resp = requests.get(url, headers={"Authorization": headers["Authorization"]}, params=params)
resp.raise_for_status()

# ── Step 3: Parse and Display Results ─────────────────────────────────────────
rows = list(csv.DictReader(io.StringIO(resp.text), skipinitialspace=True))

print(f"Study Area Data — Industry Detail  |  hashId: {GROUP_HASH_ID}")
print(f"  Total industries in region: {len(rows)}")
if DISPLAY_ROWS:
    print(f"  Showing first {DISPLAY_ROWS} rows\n")
else:
    print()

# Print a formatted table showing the key employment and financial columns.
# W&S Emp = Wage and Salary Employment, Prop Emp = Proprietor Employment.
print(f"  {'Code':<6} {'Industry':<38} {'W&S Emp':>10} {'Prop Emp':>10} {'Output':>18} {'Emp Comp':>18}")
print("  " + "-" * 104)

display = rows if DISPLAY_ROWS is None else rows[:DISPLAY_ROWS]

for row in display:
    code     = row.get("Industry Code", "")
    desc     = row.get("Description", "")[:37]
    ws_emp   = float(row.get("Wage and Salary Employment", 0) or 0)
    prop_emp = float(row.get("Proprietor Employment", 0) or 0)
    output   = float(row.get("Total Output", 0) or 0)
    emp_comp = float(row.get("Employee Compensation", 0) or 0)

    print(f"  {code:<6} {desc:<38} {ws_emp:>10,.1f} {prop_emp:>10,.1f} ${output:>17,.0f} ${emp_comp:>17,.0f}")

# ── Summary ────────────────────────────────────────────────────────────────────
total_ws_emp   = sum(float(r.get("Wage and Salary Employment", 0) or 0) for r in rows)
total_prop_emp = sum(float(r.get("Proprietor Employment", 0) or 0) for r in rows)
total_output   = sum(float(r.get("Total Output", 0) or 0) for r in rows)
total_emp_comp = sum(float(r.get("Employee Compensation", 0) or 0) for r in rows)
total_prop_inc = sum(float(r.get("Proprietor Income", 0) or 0) for r in rows)
total_opi      = sum(float(r.get("Other Property Income", 0) or 0) for r in rows)
total_topi     = sum(float(r.get("Taxes on Production and Imports Net of Subsidies", 0) or 0) for r in rows)

print(f"\n  Region Totals (all {len(rows)} industries):")
print(f"    Wage & Salary Employment: {total_ws_emp:>12,.1f} jobs")
print(f"    Proprietor Employment:    {total_prop_emp:>12,.1f} jobs")
print(f"    Total Output:             ${total_output:>14,.0f}")
print(f"    Employee Compensation:    ${total_emp_comp:>14,.0f}")
print(f"    Proprietor Income:        ${total_prop_inc:>14,.0f}")
print(f"    Other Property Income:    ${total_opi:>14,.0f}")
print(f"    Taxes (net):              ${total_topi:>14,.0f}")
