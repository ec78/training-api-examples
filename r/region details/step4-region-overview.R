library(httr2)   # Modern HTTP client for R — used to make all API requests
library(dotenv)  # Loads credentials from a .env file into the environment
library(readr)   # Parses CSV responses from the IMPLAN API

# Load credentials from the .env file next to this script
load_dot_env(file.path(dirname(sys.frame(1)$ofile), ".env"))

USER <- Sys.getenv("IMPLAN_USERNAME")
PW   <- Sys.getenv("IMPLAN_PASSWORD")

BASE_URL <- "https://api.implan.com"

# ── Configuration ──────────────────────────────────────────────────────────────
AGGREGATION_SCHEME_ID <- 14   # 528-industry grouping scheme
                               # Must match what you used in earlier steps.

GROUP_HASH_ID <- "0GxZYok7Vp"
# --> From Step 3 (create-group.R): the hashId printed in the group output.
#     This is IMPLAN's identifier for the regional economic model that the
#     group was built on — the same identifier is used here to pull that data.

DISPLAY_ROWS <- 20
# How many industry rows to print to the screen.
# Set to NULL to print all rows (may be 500+ for detailed schemes).

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

# ── Step 2: Pull Region Overview Industries ────────────────────────────────────
# This endpoint returns a high-level economic snapshot of the region — one row
# per industry showing total employment, labor income, and output.
#
# This is the same summary you see when you open a region in IMPLAN Cloud and
# click "Overview". It reflects the region's total economic activity as captured
# in IMPLAN's built model for that geography and data year.
#
# Response columns:
#   Display Code        — IMPLAN industry code number
#   Display Description — Industry name (e.g., "Oilseed farming")
#   Employment          — Total jobs (wage & salary + proprietor combined)
#   Labor Income        — Total labor income ($): wages, salaries, and proprietor income
#   Output              — Total industry output ($): the full value of goods and services
#                         produced by this industry in the region
#   Average Employee Compensation per Wage and Salary Employee
#                       — Mean annual compensation per W&S worker ($)
#   Average Proprietor Income per Proprietor
#                       — Mean annual income per self-employed worker ($)
#
# The response is plain CSV text, not JSON. We parse it with readr::read_csv().
#
# Note: GET requests must NOT include Content-Type — only pass Authorization.
#
# Endpoint: GET /api/v1/regions/export/{aggregationSchemeId}/RegionOverviewIndustries
# Docs:     https://github.com/Implan-Group/api/wiki/Region-Data---Overview-Industries

url <- sprintf("%s/api/v1/regions/export/%d/RegionOverviewIndustries", BASE_URL, AGGREGATION_SCHEME_ID)

# The hashId query parameter identifies which region's data to return.
# This is the same hashId stored in the Group from step3-create-group.R.
resp <- request(url) |>
  req_headers(Authorization = paste("Bearer", token)) |>
  req_url_query(hashId = GROUP_HASH_ID) |>
  req_perform()

# ── Step 3: Parse and Display Results ─────────────────────────────────────────
# read_csv() parses the raw CSV text from the response body.
# trim_ws = TRUE removes the leading space the IMPLAN API adds after each comma —
# without it, column names would include a leading space (e.g., " Employment").
# show_col_types = FALSE suppresses the column-type message for cleaner output.

df <- read_csv(resp_body_string(resp), trim_ws = TRUE, show_col_types = FALSE)

n_rows <- nrow(df)

cat(sprintf("Region Overview Industries  |  hashId: %s\n", GROUP_HASH_ID))
cat(sprintf("  Total industries in region: %d\n", n_rows))
if (!is.null(DISPLAY_ROWS)) {
  cat(sprintf("  Showing first %d rows\n\n", DISPLAY_ROWS))
} else {
  cat("\n")
}

# Print a formatted table. Right-align numeric columns for readability.
cat(sprintf("  %-6s %-45s %14s %18s %18s\n",
            "Code", "Industry", "Employment", "Labor Income", "Output"))
cat(paste0("  ", strrep("-", 105), "\n"))

display <- if (is.null(DISPLAY_ROWS)) df else head(df, DISPLAY_ROWS)

for (i in seq_len(nrow(display))) {
  row        <- display[i, ]
  code       <- as.character(row[["Display Code"]])
  desc       <- substr(as.character(row[["Display Description"]]), 1, 44)
  employment <- as.numeric(row[["Employment"]])
  employment <- if (is.na(employment)) 0 else employment
  labor      <- as.numeric(row[["Labor Income"]])
  labor      <- if (is.na(labor)) 0 else labor
  output     <- as.numeric(row[["Output"]])
  output     <- if (is.na(output)) 0 else output

  cat(sprintf("  %-6s %-45s %14s $%17s $%17s\n",
              code, desc,
              formatC(employment, format = "f", digits = 1, big.mark = ","),
              formatC(labor,      format = "f", digits = 0, big.mark = ","),
              formatC(output,     format = "f", digits = 0, big.mark = ",")))
}

# ── Summary ────────────────────────────────────────────────────────────────────
# Sum all industries to get the region's total economic activity.
total_emp    <- sum(as.numeric(df[["Employment"]]),   na.rm = TRUE)
total_labor  <- sum(as.numeric(df[["Labor Income"]]), na.rm = TRUE)
total_output <- sum(as.numeric(df[["Output"]]),       na.rm = TRUE)

cat(sprintf("\n  Region Totals (all %d industries):\n", n_rows))
cat(sprintf("    Employment:   %14s\n",
            formatC(total_emp,    format = "f", digits = 1, big.mark = ",")))
cat(sprintf("    Labor Income: $%17s\n",
            formatC(total_labor,  format = "f", digits = 0, big.mark = ",")))
cat(sprintf("    Output:       $%17s\n",
            formatC(total_output, format = "f", digits = 0, big.mark = ",")))
