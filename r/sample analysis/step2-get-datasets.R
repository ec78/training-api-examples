library(httr2)   # For making HTTP requests to the IMPLAN API
library(dotenv)  # For loading credentials from a .env file

# Load credentials from the .env file in the same folder as this script
load_dot_env(file.path(dirname(sys.frame(1)$ofile), ".env"))

USER <- Sys.getenv("IMPLAN_USERNAME")
PW   <- Sys.getenv("IMPLAN_PASSWORD")

BASE_URL <- "https://api.implan.com"

# ── Configuration ─────────────────────────────────────────────────────────────
# The Aggregation Scheme determines the industry grouping used throughout
# the entire analysis. All subsequent steps (regions, projects, events) must
# use the same scheme ID to get consistent results.
#   8  = 546-industry scheme (more detailed)
#   14 = 528-industry scheme (standard IMPLAN default)
AGGREGATION_SCHEME_ID <- 14

# ── Step 1: Authenticate ──────────────────────────────────────────────────────
# Exchange your credentials for a Bearer token. This token is required
# on every subsequent API request to prove you are authenticated.

get_token <- function(username, password) {
  resp <- request(paste0(BASE_URL, "/api/auth")) |>
    req_headers(`Content-Type` = "application/json") |>
    req_body_json(list(username = username, password = password)) |>
    req_perform()

  # The API returns the token with "Bearer " already prepended (e.g. "Bearer eyJ...").
  # Strip the prefix here so we can re-add it cleanly in each request header,
  # avoiding a doubled "Bearer Bearer ..." that would cause a 401.
  sub("^Bearer ", "", resp_body_string(resp))
}

token <- get_token(USER, PW)
cat(sprintf("Authenticated. Token preview: %s...%s\n",
            substr(token, 1, 6), substr(token, nchar(token) - 5, nchar(token))))

# ── Step 2: Get Available Datasets ────────────────────────────────────────────
# Datasets represent the data year (e.g. 2021, 2022) available for analysis.
# They are organized under an Aggregation Scheme, which defines the industry
# grouping used.
#
# Endpoint: GET /api/v1/datasets/{aggregationSchemeId}
# Docs:     https://github.com/Implan-Group/api/wiki/Dataset-by-Id
#
# Note: GET requests must NOT include Content-Type — the IMPLAN API returns
# 400 if that header is present on a GET request.

url <- paste0(BASE_URL, "/api/v1/datasets/", AGGREGATION_SCHEME_ID)

resp <- request(url) |>
  req_headers(Authorization = paste("Bearer", token)) |>
  req_perform()

# resp_body_json() returns a list of named lists — one entry per dataset.
datasets <- resp_body_json(resp)

# ── Step 3: Display Results ───────────────────────────────────────────────────
# Print each dataset's ID and description (the data year), and flag
# the default dataset — that is the most current year available.
cat(sprintf("\nAvailable datasets for Aggregation Scheme %d:\n\n", AGGREGATION_SCHEME_ID))
cat(sprintf("%-8s %-12s %s\n", "ID", "Year", "Default"))
cat(strrep("-", 32), "\n")

for (ds in datasets) {
  default_flag <- if (isTRUE(ds$isDefault)) "<-- default" else ""
  cat(sprintf("%-8d %-12s %s\n", ds$id, ds$description, default_flag))
}
