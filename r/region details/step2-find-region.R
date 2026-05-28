library(httr2)   # Modern HTTP client for R — used to make all API requests
library(dotenv)  # Loads credentials from a .env file into the environment

# Load credentials from the .env file next to this script
load_dot_env(file.path(dirname(sys.frame(1)$ofile), ".env"))

USER <- Sys.getenv("IMPLAN_USERNAME")
PW   <- Sys.getenv("IMPLAN_PASSWORD")

BASE_URL <- "https://api.implan.com"

# ── Configuration ──────────────────────────────────────────────────────────────
# A region's hashId is the key identifier used in this workflow for two things:
#   1. Creating a Group in a project (to establish the geographic study area)
#   2. Pulling Region Details data (to retrieve the economic data for that area)
# This script helps you find the hashId for the region you want to analyze.

AGGREGATION_SCHEME_ID <- 14   # 528-industry grouping scheme
                               # Must match what you use in all other steps.

DATASET_ID <- 124             # The data year to search within.
                               # Run get-datasets.R to see available IDs.
                               # Example: 124 = 2024 dataset

REGION_TYPE <- "County"       # The geographic level to search.
                               # Common values: "Country", "State", "County", "MSA", "Zip"

REGION_SEARCH <- "Travis County"   # Text to match against region descriptions.
                                    # The script filters all regions of REGION_TYPE
                                    # to find those whose name contains this string.

# ── Step 1: Authenticate ───────────────────────────────────────────────────────
# Every IMPLAN API request requires a Bearer token. We get it by sending our
# credentials to the auth endpoint, then attach it to all subsequent requests.

get_token <- function(username, password) {
  resp <- request(paste0(BASE_URL, "/api/auth")) |>
    req_headers(`Content-Type` = "application/json") |>
    req_body_json(list(username = username, password = password)) |>
    req_perform()
  # The API returns the token with "Bearer " already prepended —
  # we strip it here so we can re-add it cleanly when building headers.
  sub("^Bearer ", "", resp_body_string(resp))
}

token <- get_token(USER, PW)
cat(sprintf("Authenticated. Token preview: %s...%s\n\n",
            substr(token, 1, 6), substr(token, nchar(token) - 5, nchar(token))))

# ── Step 2: Get the Top-Level Region ──────────────────────────────────────────
# IMPLAN regions are organized in a hierarchy: Country → State → County/MSA.
# Fetching the top level confirms that the aggregation scheme and dataset
# combination is valid before we try to search for a specific region.
#
# Endpoint: GET /api/v1/region/{aggregationSchemeId}/{datasetId}
# Docs:     https://github.com/Implan-Group/api/wiki/Regions---Top-Level
#
# Note: GET requests must NOT include Content-Type — only pass Authorization.

url <- sprintf("%s/api/v1/region/%d/%d", BASE_URL, AGGREGATION_SCHEME_ID, DATASET_ID)

resp <- request(url) |>
  req_headers(Authorization = paste("Bearer", token)) |>
  req_perform()

top_level <- resp_body_json(resp)

# The API returns a single region object (not a list) for the top level —
# this is the United States total. Check if it's a single object by looking
# for a hashId field directly on it, and if so, wrap it in a list for
# uniform handling.
if (!is.null(top_level$hashId)) top_level <- list(top_level)

cat("Top-level region (confirms dataset is valid):\n")
for (region in top_level) {
  cat(sprintf("  %s  |  regionType: %s  |  hashId: %s\n",
              region$description, region$regionType, region$hashId))
}

# ── Step 3: Get Child Regions ─────────────────────────────────────────────────
# Retrieve all regions of the specified type (e.g., all counties in the US).
# We then filter this list locally to find the specific region we want.
#
# Endpoint: GET /api/v1/region/{aggregationSchemeId}/{datasetId}/children
# Docs:     https://github.com/Implan-Group/api/wiki/Regional-Children

url <- sprintf("%s/api/v1/region/%d/%d/children", BASE_URL, AGGREGATION_SCHEME_ID, DATASET_ID)

# regionTypeFilter narrows the results to one geographic level so we are not
# comparing counties against states in the same list.
resp <- request(url) |>
  req_headers(Authorization = paste("Bearer", token)) |>
  req_url_query(regionTypeFilter = REGION_TYPE) |>
  req_perform()

all_regions <- resp_body_json(resp)

# ── Step 4: Filter to the Region You Need ─────────────────────────────────────
# The children endpoint returns every region of the requested type.
# We do a case-insensitive search to find the one(s) matching our term.
matches <- Filter(function(r) grepl(REGION_SEARCH, r$description, ignore.case = TRUE), all_regions)

cat(sprintf("\nRegions matching '%s' (type: %s):\n\n", REGION_SEARCH, REGION_TYPE))
cat(sprintf("  %-15s %-12s %-42s %s\n", "hashId", "urid", "Description", "RegionType"))
cat(paste0("  ", strrep("-", 83), "\n"))

for (r in matches) {
  urid <- if (!is.null(r$urid)) as.character(r$urid) else ""
  cat(sprintf("  %-15s %-12s %-42s %s\n",
              r$hashId, urid, r$description, r$regionType))
}

# ── Output ─────────────────────────────────────────────────────────────────────
# The hashId is used in Step 3 to create a Group (which ties this region to your
# project) and in Steps 4-6 to pull the Region Details data for this area.
if (length(matches) > 0) {
  cat(sprintf("\n  --> hashId: '%s'\n", matches[[1]]$hashId))
  cat("      Copy this into step3-create-group.R as REGION_HASH_ID\n")
}
