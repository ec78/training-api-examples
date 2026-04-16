import os
import requests
from dotenv import load_dotenv

# Load credentials from the .env file next to this script
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

USER = os.getenv("IMPLAN_USERNAME")
PW   = os.getenv("IMPLAN_PASSWORD")

BASE_URL = "https://api.implan.com"
AUTH_URL = f"{BASE_URL}/api/auth"

# ── Configuration ──────────────────────────────────────────────────────────────
AGGREGATION_SCHEME_ID = 14   # Must match the scheme used in your other scripts

# Optional: filter results to industries whose description contains this text.
# Set to "" to print all industries (there will be hundreds).
SEARCH = "construction"

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

# ── Step 2: Get Industry Codes ─────────────────────────────────────────────────
# Industry codes define which sector of the economy an event belongs to.
# Every IndustryOutput (and related) event requires an IndustryCode.
# The available codes depend on which aggregation scheme you are using —
# different schemes group industries differently and have different code sets.
#
# Each result includes:
#   code        — the integer you pass as "IndustryCode" in add-events.py
#   description — human-readable industry name (e.g. "Grain farming")
#
# Endpoint: GET /api/v1/IndustryCodes/{aggregationSchemeId}
# Docs:     https://github.com/Implan-Group/api/wiki/Industry-Codes-by-Aggregation-Scheme

url = f"{BASE_URL}/api/v1/IndustryCodes/{AGGREGATION_SCHEME_ID}"

resp = requests.get(url, headers=headers)
resp.raise_for_status()

industries = resp.json()

# ── Step 3: Display Results ────────────────────────────────────────────────────
# Filter by search term if provided, otherwise show all
if SEARCH:
    matches = [i for i in industries if SEARCH.lower() in i["description"].lower()]
    print(f"Industries matching '{SEARCH}' (aggregation scheme {AGGREGATION_SCHEME_ID}):\n")
else:
    matches = industries
    print(f"All industries for aggregation scheme {AGGREGATION_SCHEME_ID}:\n")

print(f"  {'Code':<8} Description")
print("  " + "-" * 50)

for industry in matches:
    print(f"  {industry['code']:<8} {industry['description']}")

print(f"\n  {len(matches)} result(s) found.")
print(f"\n  --> Set INDUSTRY_CODE in add-events.py to the 'Code' value for your industry.")
