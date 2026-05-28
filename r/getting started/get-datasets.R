library(httr2)   # HTTP requests
library(dotenv)  # Load credentials from a .env file

# Load credentials from the .env file in the same folder as this script
load_dot_env(file.path(dirname(sys.frame(1)$ofile), ".env"))

USER <- Sys.getenv("IMPLAN_USERNAME")
PW   <- Sys.getenv("IMPLAN_PASSWORD")

BASE_URL <- "https://api.implan.com"

# ── Step 1: Authenticate ───────────────────────────────────────────────────────
# Exchange your credentials for a Bearer token. This token is required
# on every subsequent API request to prove you are authenticated.

get_token <- function(username, password) {
  resp <- request(paste0(BASE_URL, "/api/auth")) |>
    req_headers(`Content-Type` = "application/json") |>
    req_body_json(list(username = username, password = password)) |>
    req_perform()

  # The API returns the token with "Bearer " already prepended (e.g. "Bearer eyJ...").
  # Strip that prefix here so we can re-add it cleanly in Authorization headers,
  # avoiding a doubled "Bearer Bearer ..." header that causes a 401.
  sub("^Bearer ", "", resp_body_string(resp))
}

token <- get_token(USER, PW)
cat(sprintf("Authenticated. Token preview: %s...%s\n",
            substr(token, 1, 6), substr(token, nchar(token) - 5, nchar(token))))

# ── Step 2: Get Available Datasets ─────────────────────────────────────────────
# Datasets represent the data year (e.g. 2021, 2022) available for analysis.
# They are organized under an Aggregation Scheme, which defines the industry
# grouping used. Scheme 14 is the 528-industry standard IMPLAN default.
#
# Endpoint: GET /api/v1/datasets/{aggregationSchemeId}
# Docs:     https://github.com/Implan-Group/api/wiki/Dataset-by-Id

# ── Configuration ──────────────────────────────────────────────────────────────
AGGREGATION_SCHEME_ID <- 14  # 528-industry scheme — the standard IMPLAN default

url <- paste0(BASE_URL, "/api/v1/datasets/", AGGREGATION_SCHEME_ID)

# GET requests must include ONLY the Authorization header.
# The IMPLAN API returns 400 if Content-Type is present on a GET request.
resp <- request(url) |>
  req_headers(Authorization = paste("Bearer", token)) |>
  req_perform()

datasets <- resp_body_json(resp)

# ── Step 3: Display Results ────────────────────────────────────────────────────
cat(sprintf("\nAvailable datasets for Aggregation Scheme %d:\n\n", AGGREGATION_SCHEME_ID))
cat(sprintf("%-8s %-12s %s\n", "ID", "Year", "Default"))
cat(strrep("-", 32), "\n")

# Each element in `datasets` is a named list with fields like id, description, isDefault.
for (ds in datasets) {
  default_flag <- if (isTRUE(ds$isDefault)) "<-- default" else ""
  cat(sprintf("%-8d %-12s %s\n", ds$id, ds$description, default_flag))
}
