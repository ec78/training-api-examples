library(httr2)   # For making HTTP requests to the IMPLAN API
library(dotenv)  # For loading credentials from a .env file

# Load variables from .env into the environment.
# file.path(dirname(sys.frame(1)$ofile), ".env") resolves to the folder
# containing this script, so the .env file is always found regardless of
# where you run the script from.
load_dot_env(file.path(dirname(sys.frame(1)$ofile), ".env"))

# Read credentials from the environment (set via .env file).
# Using environment variables keeps credentials out of source code.
USER <- Sys.getenv("IMPLAN_USERNAME")
PW   <- Sys.getenv("IMPLAN_PASSWORD")

# Base URL for all IMPLAN API calls
BASE_URL <- "https://api.implan.com"

# ── Authentication ────────────────────────────────────────────────────────────
# get_token() exchanges your username and password for a Bearer token.
# Every subsequent API call will include this token in its Authorization header.

get_token <- function(username, password) {
  cat("Exchanging credentials for a Bearer token from the IMPLAN API.\n")

  # Make a POST request to the auth endpoint.
  # The body is sent as JSON (req_body_json handles Content-Type automatically).
  resp <- request(paste0(BASE_URL, "/api/auth")) |>
    req_headers(`Content-Type` = "application/json") |>
    req_body_json(list(username = username, password = password)) |>
    req_perform()

  # The IMPLAN API returns the token as a plain string with "Bearer " already
  # prepended (e.g. "Bearer eyJ..."). Strip the prefix here so we can store
  # the raw token and re-add "Bearer " cleanly in each subsequent request.
  sub("^Bearer ", "", resp_body_string(resp))
}

# ── Usage ─────────────────────────────────────────────────────────────────────
# Call get_token() with the credentials loaded from .env.
# The resulting token is a raw JWT string (no "Bearer " prefix).
token <- get_token(USER, PW)

# ── Confirm authentication ────────────────────────────────────────────────────
# Print only the first and last 6 characters of the token as a sanity check.
# Avoids logging the full token (a security risk) while still confirming
# it looks like a valid JWT.
if (nchar(token) > 0) {
  cat(sprintf("Authentication successful! Token preview: %s...%s\n",
              substr(token, 1, 6), substr(token, nchar(token) - 5, nchar(token))))
} else {
  cat("Authentication failed: token is empty.\n")
}
