library(httr2)   # Modern HTTP client for R — used to make all API requests
library(dotenv)  # Loads credentials from a .env file into the environment

# Load variables from .env into the environment.
# sys.frame(1)$ofile resolves to the path of this script file,
# so the .env file is always found regardless of where you run the script from.
load_dot_env(file.path(dirname(sys.frame(1)$ofile), ".env"))

# Read credentials from the environment (set via .env file).
# Using environment variables keeps credentials out of source code.
USER <- Sys.getenv("IMPLAN_USERNAME")
PW   <- Sys.getenv("IMPLAN_PASSWORD")

# Base URL and authentication endpoint
BASE_URL <- "https://api.implan.com"
AUTH_URL <- paste0(BASE_URL, "/api/auth")

# ── Authentication helper ──────────────────────────────────────────────────────
# Sends credentials to the IMPLAN auth endpoint and returns a Bearer token.
# The API returns the token with "Bearer " already prepended — we strip it here
# so we can re-add it cleanly when building headers for subsequent requests.

get_token <- function(username, password) {
  cat("Exchanging credentials for a Bearer token from the IMPLAN API.\n")

  resp <- request(AUTH_URL) |>
    req_headers(`Content-Type` = "application/json") |>
    req_body_json(list(username = username, password = password)) |>
    req_perform()

  # The response body is a plain string like "Bearer eyJ..."
  # Strip the prefix so build_headers() can add it back cleanly.
  sub("^Bearer ", "", resp_body_string(resp))
}

# ── Usage ──────────────────────────────────────────────────────────────────────
# Get a token using the credentials loaded from .env. The token is then passed
# to every subsequent API request via the Authorization header.
token <- get_token(USER, PW)

# ── Confirm authentication succeeded ──────────────────────────────────────────
# Print the first and last 6 characters of the token as a sanity check.
# Avoids printing the full token (a security risk in logs) while still giving
# enough to verify it looks like a valid JWT.
if (nchar(token) > 0) {
  cat(sprintf("Authentication successful! Token preview: %s...%s\n",
              substr(token, 1, 6), substr(token, nchar(token) - 5, nchar(token))))
} else {
  cat("Authentication failed: token is empty.\n")
}
