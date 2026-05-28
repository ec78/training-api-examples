library(httr2)   # For making HTTP requests to the IMPLAN API
library(dotenv)  # For loading credentials from a .env file

# Load credentials from the .env file next to this script
load_dot_env(file.path(dirname(sys.frame(1)$ofile), ".env"))

USER <- Sys.getenv("IMPLAN_USERNAME")
PW   <- Sys.getenv("IMPLAN_PASSWORD")

BASE_URL <- "https://api.implan.com"

# ── Configuration ─────────────────────────────────────────────────────────────
PROJECT_ID <- "531b9cea-9c82-495d-bc23-a2b6f05f8b1f"
# --> From Step 4 (step4-create-project.R) / Step 5 (step5-add-events.R)
#     The project must have at least one Group with at least one Event before
#     you can run the analysis. If the project is incomplete, the API returns 400.

POLL_INTERVAL <- 10  # seconds between status checks

# ── Step 1: Authenticate ──────────────────────────────────────────────────────
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

# ── Step 2: Run the Analysis ──────────────────────────────────────────────────
# This triggers IMPLAN's input-output model to calculate the economic impact
# of all events in the project. The model computes direct, indirect, and
# induced effects across all industries in the region.
#
# The API returns an integer Run ID — a unique identifier for this specific
# analysis run. You will use it to retrieve results in step7-get-results.R.
#
# Note: Running the same project again produces a new Run ID each time.
#
# Endpoint: POST /api/v1/impact/{projectId}
# Docs:     https://github.com/Implan-Group/api/wiki/Run-Impact-Analysis
# Note: this path does NOT include "project/" — unlike the create/event/group
# endpoints, the run endpoint goes directly to /impact/{projectId}.

url <- paste0(BASE_URL, "/api/v1/impact/", PROJECT_ID)


# req_method("POST") is required: httr2 defaults to GET when no body is
# attached. The trigger endpoint expects POST but takes no request body,
# so we must set the method explicitly — omitting this causes a 404.
resp <- request(url) |>
  req_headers(
    Authorization  = paste("Bearer", token),
    `Content-Type` = "application/json"
  ) |>
  req_method("POST") |>
  req_perform()

# The response body is a plain integer as text (e.g. "605590"), not JSON.
# The API may also return a float string like "605590.0" — always use
# as.integer(trimws(...)) to avoid building a status URL like "/status/605590.0"
# which would cause a 400 error.
run_id <- as.integer(trimws(resp_body_string(resp)))

cat(sprintf("Analysis triggered. Run ID: %d\n", run_id))

# ── Step 3: Check Status ──────────────────────────────────────────────────────
# Impact calculations run asynchronously in the background. We poll the status
# endpoint until the run reaches a terminal state.
#
# Possible status values:
#   "New"               — queued but not yet started
#   "InProgress"        — actively running
#   "ReadyForWarehouse" — still processing (intermediate state)
#   "Complete"          — finished successfully -> results are ready
#   "Error"             — failed (check your project for invalid events/groups)
#   "UserCancelled"     — cancelled by the user
#
# Note: Small analyses often complete within seconds. If the status endpoint
# returns a non-200 response, the run may have already completed — proceed to
# step7-get-results.R with the Run ID above.
#
# Endpoint: GET /api/v1/impact/status/{runId}
# Docs:     https://github.com/Implan-Group/api/wiki/Get-Impact-Status

status_url <- paste0(BASE_URL, "/api/v1/impact/status/", run_id)

cat("Checking status (analyses often complete in seconds)...\n")

status <- NULL

repeat {
  Sys.sleep(POLL_INTERVAL)

  status_resp <- request(status_url) |>
    req_headers(Authorization = paste("Bearer", token)) |>
    req_error(is_error = \(r) FALSE) |>
    req_perform()

  if (resp_status(status_resp) != 200) {
    # A non-200 here often means the run completed before we could poll it.
    # This is normal for small analyses — proceed to step7-get-results.R.
    cat(sprintf("  Status check returned %d — analysis may have already completed.\n",
                resp_status(status_resp)))
    break
  }

  status <- trimws(resp_body_string(status_resp))
  cat(sprintf("  Status: %s\n", status))

  if (status %in% c("Complete", "Error", "UserCancelled")) break
}

# ── Output ────────────────────────────────────────────────────────────────────
cat(sprintf("\n  --> Run ID: %d\n", run_id))
cat("      Copy this into step7-get-results.R as RUN_ID\n")

if (!is.null(status) && status == "Error") {
  cat("  Analysis failed. Check your project setup in step5-add-events.R and try again.\n")
} else if (!is.null(status) && status == "UserCancelled") {
  cat("  Analysis was cancelled.\n")
}
