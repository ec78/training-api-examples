library(httr2)   # For making HTTP requests to the IMPLAN API
library(dotenv)  # For loading credentials from a .env file

# Load credentials from the .env file next to this script
load_dot_env(file.path(dirname(sys.frame(1)$ofile), ".env"))

USER <- Sys.getenv("IMPLAN_USERNAME")
PW   <- Sys.getenv("IMPLAN_PASSWORD")

BASE_URL <- "https://api.implan.com"

# ── Configuration ─────────────────────────────────────────────────────────────
# These values come from Step 2 (step2-get-datasets.R).
# Run that script first to find valid IDs, then fill them in here.

AGGREGATION_SCHEME_ID <- 14  # 528-industry grouping scheme

DATASET_ID <- 124            # The data year to use — replace with an ID from
                             # step2-get-datasets.R (e.g., 124 = 2024 dataset)

# What type of region to search for.
# Common values: "Country", "State", "County", "MSA", "Zip"
REGION_TYPE <- "County"

# Text to search for within the returned region descriptions.
# This filters the results to just the region(s) you care about.
REGION_SEARCH <- "Travis County"

# ── Step 1: Authenticate ──────────────────────────────────────────────────────
# Every IMPLAN API request requires a Bearer token. We get it by sending our
# credentials to the auth endpoint, then attach it to all subsequent requests.

get_token <- function(username, password) {
  resp <- request(paste0(BASE_URL, "/api/auth")) |>
    req_headers(`Content-Type` = "application/json") |>
    req_body_json(list(username = username, password = password)) |>
    req_perform()

  # The API returns the token with "Bearer " already prepended —
  # we strip it here so we can re-add it cleanly in each request header.
  sub("^Bearer ", "", resp_body_string(resp))
}

token <- get_token(USER, PW)
cat(sprintf("Authenticated. Token preview: %s...%s\n\n",
            substr(token, 1, 6), substr(token, nchar(token) - 5, nchar(token))))

# ── Step 2: Get Top-Level Regions ─────────────────────────────────────────────
# IMPLAN regions are organized in a hierarchy: Country -> State -> County/MSA.
# We start at the top level (Country) for the given aggregation scheme + dataset.
#
# Endpoint: GET /api/v1/region/{aggregationSchemeId}/{datasetId}
# Docs:     https://github.com/Implan-Group/api/wiki/Regions---Top-Level
#
# Note: GET requests must NOT include Content-Type — the IMPLAN API returns
# 400 if that header is present on a GET request.

url <- paste0(BASE_URL, "/api/v1/region/", AGGREGATION_SCHEME_ID, "/", DATASET_ID)

resp <- request(url) |>
  req_headers(Authorization = paste("Bearer", token)) |>
  req_perform()

top_level <- resp_body_json(resp)

# The API may return a single region object (not a list) for the top level —
# this is the United States total. Wrap it in a list if needed so we can
# iterate over it the same way regardless.
if (!is.null(top_level$description)) {
  top_level <- list(top_level)
}

cat("Top-level region(s):\n")
for (region in top_level) {
  cat(sprintf("  %s  |  regionType: %s  |  hashId: %s\n",
              region$description, region$regionType, region$hashId))
}

# ── Step 3: Get Child Regions (States, Counties, MSAs) ────────────────────────
# To drill down from Country to a State (or County, MSA, etc.), we call the
# "children" endpoint and filter by the desired region type.
#
# The hashId is the unique identifier IMPLAN uses for a region — you will need
# it in later steps (Step 5) to associate your analysis with a specific geography.
#
# Endpoint: GET /api/v1/region/{aggregationSchemeId}/{datasetId}/children
# Docs:     https://github.com/Implan-Group/api/wiki/Regional-Children

url <- paste0(BASE_URL, "/api/v1/region/", AGGREGATION_SCHEME_ID, "/", DATASET_ID, "/children")

# The regionTypeFilter query parameter narrows the results to one level
# of the geographic hierarchy (e.g., only return counties, not states).
resp <- request(url) |>
  req_headers(Authorization = paste("Bearer", token)) |>
  req_url_query(regionTypeFilter = REGION_TYPE) |>
  req_perform()

all_regions <- resp_body_json(resp)

# ── Step 4: Find the Specific Region ─────────────────────────────────────────
# The children endpoint returns ALL regions of the requested type.
# We filter locally to find the one(s) matching our search term.

matches <- Filter(function(r) grepl(REGION_SEARCH, r$description, ignore.case = TRUE), all_regions)

cat(sprintf("\nRegions matching '%s' (type: %s):\n\n", REGION_SEARCH, REGION_TYPE))
cat(sprintf("  %-15s %-40s %s\n", "hashId", "Description", "RegionType"))
cat("  ", strrep("-", 65), "\n", sep = "")

for (r in matches) {
  cat(sprintf("  %-15s %-40s %s\n", r$hashId, r$description, r$regionType))
}

# ── Output ────────────────────────────────────────────────────────────────────
# The hashId from this output is what you will use in Step 5 (step5-add-events.R)
# to assign your analysis to this geographic region.
if (length(matches) > 0) {
  cat(sprintf("\n  --> Use hashId '%s' in step5-add-events.R as REGION_HASH_ID\n",
              matches[[1]]$hashId))
}
