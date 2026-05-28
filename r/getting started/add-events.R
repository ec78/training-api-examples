library(httr2)   # HTTP requests
library(dotenv)  # Load credentials from a .env file

# Load credentials from the .env file next to this script
load_dot_env(file.path(dirname(sys.frame(1)$ofile), ".env"))

USER <- Sys.getenv("IMPLAN_USERNAME")
PW   <- Sys.getenv("IMPLAN_PASSWORD")

BASE_URL <- "https://api.implan.com"

# ── Configuration ──────────────────────────────────────────────────────────────
# Fill in the values from the previous steps before running this script.

PROJECT_ID <- "77e3ff58-8622-49ed-9880-2eb8cf8cdebf"
# --> From Step 4 (create-project.R): the GUID returned after project creation.
#     Example: "496256c2-a089-4d42-a1a1-cafe73a43216"

REGION_HASH_ID <- "BzxjENLeVN"
# --> From Step 3 (find-region.R): the hashId for the region you want to analyze.
#     Example: "9EbJv6yJb0"

DATASET_ID <- 124
# --> From Step 2 (get-datasets.R): the data year ID you are using.
#     Must match the dataset used when you looked up the region.

DOLLAR_YEAR <- 2026
# --> The year your monetary values (output, compensation, etc.) are expressed in.
#     This is typically the same year as your dataset.

# ── Event Definition ───────────────────────────────────────────────────────────
# An Event represents the economic activity (the "shock") you are analyzing.
# Here we use an IndustryOutput event — the most common type — which models
# a change in spending within a specific industry.

# Append a timestamp to ensure the title is unique within the project.
# IMPLAN requires all event titles to be unique — re-running the script
# without this would fail with "Impact Event Title must be Unique".
EVENT_TITLE  <- paste("Example Industry Output Event", format(Sys.time(), "%Y-%m-%d %H:%M:%S"))
EVENT_OUTPUT <- 1000000.00  # Total industry output value in dollars

INDUSTRY_CODE <- 1
# --> The numeric code for the industry being analyzed.
#     Use get-industry-codes.R to look up valid codes for your aggregation scheme.
#     Example: 1 = Oilseed farming, 2 = Grain farming (scheme 14)
#     This field is REQUIRED — the analysis cannot run without it.

# ── Step 1: Authenticate ───────────────────────────────────────────────────────
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

# ── Step 2: Create an Event ───────────────────────────────────────────────────
# An Event defines WHAT economic activity is happening — the industry and
# dollar amount of the impact. At this point it is not yet tied to a geography;
# that happens when we create the Group in the next step.
#
# ImpactEventType options include: "IndustryOutput", "IndustryEmployment",
# "IndustryEmployeeCompensation", "IndustryProprietorIncome", and others.
#
# Endpoint: POST /api/v1/impact/project/{projectId}/event
# Docs:     https://github.com/Implan-Group/api/wiki/Create-Event

url <- paste0(BASE_URL, "/api/v1/impact/project/", PROJECT_ID, "/event")

event_payload <- list(
  ImpactEventType = "IndustryOutput",  # Type of economic activity being modeled
  Title           = EVENT_TITLE,       # A descriptive label for this event
  IndustryCode    = INDUSTRY_CODE,     # REQUIRED: which industry this activity belongs to
                                       # Use get-industry-codes.R to find valid codes
  Output          = EVENT_OUTPUT       # Dollar value of the output change
  # Optional fields you can also include:
  # Employment           = 0.0   # Number of jobs
  # EmployeeCompensation = 0.0   # Wages and salaries paid ($)
  # ProprietorIncome     = 0.0   # Business owner income ($)
)

# POST requests require both Authorization and Content-Type headers.
resp <- request(url) |>
  req_headers(
    Authorization  = paste("Bearer", token),
    `Content-Type` = "application/json"
  ) |>
  req_body_json(event_payload) |>
  req_error(is_error = \(r) FALSE) |>
  req_perform()

if (resp_status(resp) < 200 || resp_status(resp) >= 300) {
  cat(sprintf("  Event creation failed (%d): %s\n",
              resp_status(resp), resp_body_string(resp)))
  stop("Event creation failed.")
}

event <- resp_body_json(resp)

cat(sprintf("Event created: '%s' (ID: %s)\n\n", event$title, event$id))

# ── Step 3: Create a Group ────────────────────────────────────────────────────
# A Group links an Event to a geographic Region and a data year.
# Think of it as answering: "WHERE and WHEN does this event occur?"
#
# Without a Group, the Event exists in the project but has no geography,
# and the analysis cannot be run.
#
# The HashId here is the region's hashId from find-region.R — it tells IMPLAN
# which geographic model to use for the input-output calculations.
#
# Endpoint: POST /api/v1/impact/project/{projectId}/group
# Docs:     https://github.com/Implan-Group/api/wiki/Create-Group

url <- paste0(BASE_URL, "/api/v1/impact/project/", PROJECT_ID, "/group")

group_payload <- list(
  Title      = "Example Group",        # A label for this geographic grouping
  HashId     = REGION_HASH_ID,         # The region's unique identifier from find-region.R
  DatasetId  = DATASET_ID,             # The data year for the regional model
  DollarYear = DOLLAR_YEAR,            # The year your dollar values are expressed in
  groupEvents = list(
    list(eventId = event$id)           # Link the event we just created to this region
  )
)

resp <- request(url) |>
  req_headers(
    Authorization  = paste("Bearer", token),
    `Content-Type` = "application/json"
  ) |>
  req_body_json(group_payload) |>
  req_perform()

group <- resp_body_json(resp)

# ── Output ─────────────────────────────────────────────────────────────────────
cat(sprintf("Group created: '%s' (ID: %s)\n", group$title, group$id))
cat(sprintf("  Region (hashId): %s\n", group$hashId))
cat(sprintf("  Dataset:         %d\n", group$datasetId))
cat(sprintf("  Dollar Year:     %d\n", group$dollarYear))
cat(sprintf("  Events linked:   %d\n", length(group$groupEvents)))
cat(sprintf("\nProject '%s' is ready to run.\n", PROJECT_ID))
cat("\n  --> Copy PROJECT_ID into run-analysis.R as PROJECT_ID\n")
