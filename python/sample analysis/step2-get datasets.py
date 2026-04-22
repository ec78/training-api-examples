import os
import requests
from dotenv import load_dotenv

# Load credentials from the .env file in the same folder as this script
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

USER = os.getenv("IMPLAN_USERNAME")
PW   = os.getenv("IMPLAN_PASSWORD")

BASE_URL = "https://api.implan.com"
AUTH_URL = f"{BASE_URL}/api/auth"

# ── Step 1: Authenticate ───────────────────────────────────────────────────────
# Exchange your credentials for a Bearer token. This token is required
# on every subsequent API request to prove you are authenticated.

def get_token(username, password):
    # Debug: confirm credentials loaded from .env (masks password)
    print(f"[debug] USER={username!r}  PW={'*' * len(password) if password else 'None'}")

    resp = requests.post(AUTH_URL, json={
        "username": username,
        "password": password
    })

    # Debug: show exactly what the API sent back before we try to parse it
    print(f"[debug] status={resp.status_code}  body={resp.text!r}")

    resp.raise_for_status()

    # The API returns the token with "Bearer " already prepended (e.g. "Bearer eyJ...").
    # We strip that prefix here so build_headers can add it back cleanly,
    # avoiding a doubled "Bearer Bearer ..." header that causes a 401.
    return resp.text.removeprefix("Bearer ")

def build_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

token   = get_token(USER, PW)
headers = build_headers(token)
print(f"Authenticated. Token preview: {token[:6]}...{token[-6:]}")

# ── Step 2: Get Available Datasets ─────────────────────────────────────────────
# Datasets represent the data year (e.g. 2021, 2022) available for analysis.
# They are organized under an Aggregation Scheme, which defines the industry
# grouping used. The default IMPLAN scheme is 8 (546 industries).
#
# Endpoint: GET /api/v1/datasets/{aggregation_scheme_id}
# Docs:     https://github.com/Implan-Group/api/wiki/Dataset-by-Id

AGGREGATION_SCHEME_ID = 14  # 528-industry scheme — the standard IMPLAN default

# API URL for fetching datasets under the specified aggregation scheme
url = f"{BASE_URL}/api/v1/datasets/{AGGREGATION_SCHEME_ID}"

resp = requests.get(url, headers=headers)
resp.raise_for_status()

datasets = resp.json()

# ── Step 3: Display Results ────────────────────────────────────────────────────
print(f"\nAvailable datasets for Aggregation Scheme {AGGREGATION_SCHEME_ID}:\n")
print(f"{'ID':<8} {'Year':<10} {'Default'}")
print("-" * 28)

for ds in datasets:
    default_flag = "<-- default" if ds["isDefault"] else ""
    print(f"{ds['id']:<8} {ds['description']:<10} {default_flag}")
