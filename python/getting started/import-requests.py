import os                        # Used to read environment variables
import requests                  # Used to make HTTP requests to the IMPLAN API
from dotenv import load_dotenv   # Used to load credentials from a .env file

# Load variables from .env into the environment.
# os.path.dirname(__file__) resolves to the folder containing this script,
# so the .env file is always found regardless of where you run the script from.
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# Read credentials from the environment (set via .env file).
# Using environment variables keeps credentials out of source code.
USER = os.getenv("IMPLAN_USERNAME")
PW   = os.getenv("IMPLAN_PASSWORD")

# API endpoint for authentication
AUTH_URL = "https://api.implan.com/api/auth"

def get_token(username, password):
    print(f"Exchanging credentials for a Bearer token from the IMPLAN API.")

    # Prepare the payload for the authentication request.
    payload = {
        "username": username,
        "password": password
    }

    # Set the headers for the request
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # Make the POST request to get the token.
    # raise_for_status() will raise an exception for any 4xx/5xx response,
    # which gives a clear error instead of a confusing KeyError later.
    resp = requests.post(AUTH_URL, json=payload, headers=headers)
    resp.raise_for_status()
    
    # The IMPLAN API returns the token with "Bearer " already prepended.
    # Strip it here so build_headers can add it back cleanly.
    return resp.text.removeprefix("Bearer ")

def build_headers(token):
    """Build the Authorization headers required for all subsequent API calls."""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

# ── Usage ─────────────────────────────────────
# Get a token using the credentials loaded from .env, then build
# the headers dict that will be passed to every subsequent API request.
token   = get_token(USER, PW)
headers = build_headers(token)

# ── Debug ──────────────────────────────────────
# Confirm authentication succeeded by printing the first/last 6 characters
# of the token. Avoids printing the full token (a security risk in logs)
# while still giving enough to verify it looks like a valid JWT.
if token:
    print(f"Authentication successful! Token preview: {token[:6]}...{token[-6:]}")
else:
    print("Authentication failed: token is empty or None.")
