library(httr2)   # For making HTTP requests to the IMPLAN API
library(dotenv)  # For loading credentials from a .env file

# Load credentials from the .env file next to this script
load_dot_env(file.path(dirname(sys.frame(1)$ofile), ".env"))

USER <- Sys.getenv("IMPLAN_USERNAME")
PW   <- Sys.getenv("IMPLAN_PASSWORD")

BASE_URL <- "https://api.implan.com"

# ── Configuration ─────────────────────────────────────────────────────────────
# A Project is the container for your entire impact analysis.
# It holds the industry grouping scheme, household data, and all events/groups.

PROJECT_TITLE <- "Travis Co. Data Center"  # A descriptive name for this project

AGGREGATION_SCHEME_ID <- 14  # 528-industry grouping scheme
                              # Must match what you used in step2 and step3 —
                              # all steps must use the same scheme.

HOUSEHOLD_SET_ID <- 1        # Defines which household income categories to use.
                              # 1 is the standard IMPLAN default.

IS_MRIO <- FALSE             # Multi-Region Input-Output model.
                              # FALSE = single-region analysis (most common).
                              # TRUE  = analysis that accounts for inter-regional
                              #         trade flows (more complex, for advanced cases).

# ── Step 1: Authenticate ──────────────────────────────────────────────────────
# Every IMPLAN API request requires a Bearer token obtained by sending credentials
# to the auth endpoint.

get_token <- function(username, password) {
  resp <- request(paste0(BASE_URL, "/api/auth")) |>
    req_headers(`Content-Type` = "application/json") |>
    req_body_json(list(username = username, password = password)) |>
    req_perform()

  # The API returns the token with "Bearer " already prepended —
  # strip it here so we can re-add it cleanly in each subsequent request header.
  sub("^Bearer ", "", resp_body_string(resp))
}

token <- get_token(USER, PW)
cat(sprintf("Authenticated. Token preview: %s...%s\n\n",
            substr(token, 1, 6), substr(token, nchar(token) - 5, nchar(token))))

# ── Step 2: Create the Project ────────────────────────────────────────────────
# A project must be created before you can add events or run an analysis.
# Think of it as opening a new analysis workspace in the IMPLAN app.
#
# The API returns a unique project ID (a GUID) that you will use in every
# subsequent step to refer back to this project.
#
# Endpoint: POST /api/v1/impact/project
# Docs:     https://github.com/Implan-Group/api/wiki/Create-Project

url <- paste0(BASE_URL, "/api/v1/impact/project")

# The request body defines the core settings for this project.
# These settings cannot be changed after the project is created.
# Do NOT include an "id" field — the API generates one automatically
# and returns it in the response.
resp <- request(url) |>
  req_headers(
    Authorization  = paste("Bearer", token),
    `Content-Type` = "application/json"
  ) |>
  req_body_json(list(
    Title               = PROJECT_TITLE,
    AggregationSchemeId = AGGREGATION_SCHEME_ID,
    HouseholdSetId      = HOUSEHOLD_SET_ID,
    IsMrio              = IS_MRIO
  )) |>
  req_perform()

# resp_body_json() returns a named list with the newly created project's details.
project <- resp_body_json(resp)

# ── Output ────────────────────────────────────────────────────────────────────
cat("Project created successfully!\n\n")
cat(sprintf("  Title:               %s\n", project$title))
cat(sprintf("  Aggregation Scheme:  %s\n", project$aggregationSchemeId))
cat(sprintf("  Household Set:       %s\n", project$householdSetId))
cat(sprintf("  MRIO:                %s\n", project$isMrio))
cat(sprintf("\n  --> Project ID: %s\n", project$id))
cat("      Copy this ID into step5-add-events.R as PROJECT_ID\n")
