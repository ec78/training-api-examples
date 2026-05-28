library(httr2)   # Modern HTTP client for R — used to make all API requests
library(dotenv)  # Loads credentials from a .env file into the environment

# Load credentials from the .env file next to this script
load_dot_env(file.path(dirname(sys.frame(1)$ofile), ".env"))

USER <- Sys.getenv("IMPLAN_USERNAME")
PW   <- Sys.getenv("IMPLAN_PASSWORD")

BASE_URL <- "https://api.implan.com"

# ── Configuration ──────────────────────────────────────────────────────────────
# A Project is the workspace that organizes your analysis.
# A Group lives inside a Project and defines WHERE the analysis occurs —
# it links a specific region (by hashId) to a data year (dataset).
#
# When pulling Region Details data, the Group's hashId is the identifier
# you pass to the region data export endpoints. This step establishes that
# connection between your project and the region you want to study.

PROJECT_TITLE <- "Travis Co. Region Study"   # A descriptive name for this project

AGGREGATION_SCHEME_ID <- 14   # 528-industry grouping scheme
                               # Must match what you used in step2-find-region.R.

HOUSEHOLD_SET_ID <- 1         # Defines which household income categories to use.
                               # 1 is the standard IMPLAN default.

IS_MRIO <- FALSE              # Multi-Region Input-Output model.
                               # FALSE = single-region analysis (most common).

REGION_HASH_ID <- "0GxZYok7Vp"
# --> From Step 2 (find-region.R): the hashId for the region you want to study.
#     Example: "0GxZYok7Vp" = Travis County, TX

DATASET_ID <- 124
# --> From get-datasets.R: the data year for the regional model.
#     Example: 124 = 2024 dataset. Must match the year used in step2-find-region.R.

DOLLAR_YEAR <- 2024
# --> The year your monetary values are expressed in.
#     For region data exploration, set this to match the dataset year.

GROUP_TITLE <- "Travis County Study Area"   # A descriptive label for this group

# ── Step 1: Authenticate ───────────────────────────────────────────────────────
# Every IMPLAN API request requires a Bearer token. We get it by sending our
# credentials to the auth endpoint, then attach it to all subsequent requests.

get_token <- function(username, password) {
  resp <- request(paste0(BASE_URL, "/api/auth")) |>
    req_headers(`Content-Type` = "application/json") |>
    req_body_json(list(username = username, password = password)) |>
    req_perform()
  sub("^Bearer ", "", resp_body_string(resp))
}

token <- get_token(USER, PW)
cat(sprintf("Authenticated. Token preview: %s...%s\n\n",
            substr(token, 1, 6), substr(token, nchar(token) - 5, nchar(token))))

# ── Step 2: Create the Project ─────────────────────────────────────────────────
# A Project is required before you can create a Group. Think of it as opening
# a new analysis workspace. The aggregation scheme set here determines which
# industry grouping is used throughout the project and in the region data exports.
#
# Endpoint: POST /api/v1/impact/project
# Docs:     https://github.com/Implan-Group/api/wiki/Create-Project

url <- paste0(BASE_URL, "/api/v1/impact/project")

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

project    <- resp_body_json(resp)
project_id <- project$id

cat(sprintf("Project created: '%s' (ID: %s)\n\n", project$title, project_id))

# ── Step 3: Create a Group ─────────────────────────────────────────────────────
# A Group assigns a region (via hashId) and a data year to the project.
# Creating the Group answers: "My study area is THIS region, using THIS data year."
#
# The Group response includes several region identifiers. The hashId is the
# one used by the Region Details endpoints in the next steps to retrieve the
# underlying economic data for this area.
#
# Note: In a full impact analysis you would also add Events to this Group to
# model specific economic activities (see the sample analysis series). For this
# workflow, we only need the Group to establish the study area.
#
# Endpoint: POST /api/v1/impact/project/{projectId}/group
# Docs:     https://github.com/Implan-Group/api/wiki/Create-Group

url <- sprintf("%s/api/v1/impact/project/%s/group", BASE_URL, project_id)

resp <- request(url) |>
  req_headers(
    Authorization  = paste("Bearer", token),
    `Content-Type` = "application/json"
  ) |>
  req_body_json(list(
    Title       = GROUP_TITLE,
    HashId      = REGION_HASH_ID,  # The region's unique identifier from step2-find-region.R
    DatasetId   = DATASET_ID,      # Which data year's economic model to use
    DollarYear  = DOLLAR_YEAR,     # The year monetary values are expressed in
    groupEvents = list()           # No events needed for region data —
                                   # add events here for a full impact analysis
  )) |>
  req_perform()

group <- resp_body_json(resp)

# ── Output ─────────────────────────────────────────────────────────────────────
# The Group response confirms which region model IMPLAN has loaded.
# Any of the identifiers below (hashId, urid, modelId) can be passed to the
# region data export endpoints — hashId is the most commonly used.
urid    <- if (!is.null(group$urid))    group$urid    else "N/A"
model_id <- if (!is.null(group$modelId)) group$modelId else "N/A"

cat(sprintf("Group created: '%s' (ID: %s)\n", group$title, group$id))
cat("\n  Region identifiers returned by the API:\n")
cat(sprintf("    hashId:  %s\n", group$hashId))
cat(sprintf("    urid:    %s\n", urid))
cat(sprintf("    modelId: %s\n", model_id))
cat(sprintf("  Dataset:   %s\n", group$datasetId))
cat(sprintf("  DollarYear:%s\n", group$dollarYear))
cat(sprintf('\n  --> GROUP_HASH_ID = "%s"\n', group$hashId))
cat("      Copy this into steps 4-6 as GROUP_HASH_ID\n")
