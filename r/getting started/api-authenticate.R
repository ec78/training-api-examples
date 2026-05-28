library(httr2)   # HTTP requests (modern replacement for httr)
library(dotenv)  # Load credentials from a .env file

# Load variables from .env into the environment.
# sys.frame(1)$ofile resolves to this script's path, so the .env file is
# always found regardless of where you run the script from.
load_dot_env(file.path(dirname(sys.frame(1)$ofile), ".env"))

# Read credentials from the environment (set via .env file).
# Using environment variables keeps credentials out of source code.
USER <- Sys.getenv("IMPLAN_USERNAME")
PW   <- Sys.getenv("IMPLAN_PASSWORD")

# Base URL for the IMPLAN API
BASE_URL <- "https://api.implan.com"

# ── Step 1: Authenticate ───────────────────────────────────────────────────────
# The IMPLAN API uses Bearer token authentication.
# We POST our credentials and receive a token that must be included
# in the Authorization header of every subsequent request.

get_token <- function(username, password) {
  cat("Exchanging credentials for a Bearer token from the IMPLAN API.\n")

  # POST to the auth endpoint with our credentials as a JSON body.
  # httr2 automatically serializes the list to JSON and sets Content-Type.
  resp <- request(paste0(BASE_URL, "/api/auth")) |>
    req_headers(`Content-Type` = "application/json") |>
    req_body_json(list(username = username, password = password)) |>
    req_perform()

  # The IMPLAN API returns the token with "Bearer " already prepended
  # (e.g., "Bearer eyJ..."). Strip that prefix here so we can re-add
  # it cleanly when building Authorization headers for later requests.
  sub("^Bearer ", "", resp_body_string(resp))
}

# ── Helper: build the Authorization header for subsequent requests ─────────────
# GET requests need ONLY the Authorization header — the IMPLAN API returns
# a 400 error if Content-Type is present on a GET.
# POST/PUT requests also need Content-Type: application/json; add that inline.
auth_header <- function(token) {
  c(Authorization = paste("Bearer", token))
}

# ── Usage ──────────────────────────────────────────────────────────────────────
# Get a token using the credentials loaded from .env.
token <- get_token(USER, PW)

# Confirm authentication succeeded by printing the first and last 6 characters
# of the token. Avoids printing the full token (a security risk in logs)
# while still giving enough to verify it looks like a valid JWT.
if (nchar(token) > 0) {
  cat(sprintf("Authentication successful! Token preview: %s...%s\n",
              substr(token, 1, 6), substr(token, nchar(token) - 5, nchar(token))))
} else {
  cat("Authentication failed: token is empty.\n")
}
