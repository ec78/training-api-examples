library(httr2)   # HTTP requests
library(dotenv)  # Load credentials from a .env file
library(readr)   # CSV parsing (read_csv)

# Load credentials from the .env file next to this script
load_dot_env(file.path(dirname(sys.frame(1)$ofile), ".env"))

USER <- Sys.getenv("IMPLAN_USERNAME")
PW   <- Sys.getenv("IMPLAN_PASSWORD")

BASE_URL <- "https://api.implan.com"

# ── Configuration ──────────────────────────────────────────────────────────────
RUN_ID <- 605605
# --> From Step 6 (run-analysis.R): the integer Run ID returned after the
#     analysis completed with status "Complete".
#     Example: 17280

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

# ── Step 2: Retrieve Summary Economic Indicators ──────────────────────────────
# This endpoint returns the core economic impact results: the direct, indirect,
# and induced effects across Employment, Labor Income, Value Added, and Output.
#
# Direct effects   — the immediate impact of the event itself
# Indirect effects — impacts on supplier industries (supply chain)
# Induced effects  — impacts from household spending of income earned
#
# The response is returned as a CSV file, not JSON.
# Each row represents one combination of group, event, region, and impact type.
#
# Endpoint: GET /api/v1/impact/results/SummaryEconomicIndicators/{runId}
# Docs:     https://github.com/Implan-Group/api/wiki/Results---Summary-Economic-Indicators

url <- paste0(BASE_URL, "/api/v1/impact/results/SummaryEconomicIndicators/", RUN_ID)

# GET requests must include ONLY the Authorization header.
# The IMPLAN API returns 400 if Content-Type is present on a GET request.
resp <- request(url) |>
  req_headers(Authorization = paste("Bearer", token)) |>
  req_perform()

# ── Step 3: Parse and Display Results ─────────────────────────────────────────
# The response body is plain CSV text. readr::read_csv can parse it directly
# from a string. trim_ws = TRUE strips the leading space after each comma in
# the CSV — the IMPLAN results CSV uses ", " as its delimiter, which would
# otherwise produce column names like " Employment" instead of "Employment".

csv_data <- readr::read_csv(resp_body_string(resp), trim_ws = TRUE, show_col_types = FALSE)

# Column names returned by the API
col_impact      <- "Impact"       # Direct / Indirect / Induced / Total
col_employment  <- "Employment"   # Number of jobs supported
col_labor       <- "LaborIncome"  # Wages, salaries, and proprietor income ($)
col_value_added <- "ValueAdded"   # GDP contribution ($)
col_output      <- "Output"       # Total industry output ($)

cat(sprintf("Results for Run ID %d:\n\n", RUN_ID))

# Print a header row
cat(sprintf("  %-12s %14s %18s %18s %18s\n",
            "Impact Type", "Employment", "Labor Income", "Value Added", "Output"))
cat("  ", strrep("-", 82), "\n", sep = "")

# Iterate over each row in the results tibble.
# formatC formats numbers with commas and a fixed number of decimal places.
for (i in seq_len(nrow(csv_data))) {
  row <- csv_data[i, ]

  employment  <- formatC(row[[col_employment]],  format = "f", digits = 1, big.mark = ",")
  labor       <- paste0("$", formatC(row[[col_labor]],       format = "f", digits = 0, big.mark = ","))
  value_added <- paste0("$", formatC(row[[col_value_added]], format = "f", digits = 0, big.mark = ","))
  output      <- paste0("$", formatC(row[[col_output]],      format = "f", digits = 0, big.mark = ","))

  cat(sprintf("  %-12s %14s %18s %18s %18s\n",
              row[[col_impact]], employment, labor, value_added, output))
}

# ── Summary ────────────────────────────────────────────────────────────────────
# Find the Total row (if present) for a concise overall impact summary.
total_rows <- csv_data[grepl("total", csv_data[[col_impact]], ignore.case = TRUE), ]

if (nrow(total_rows) > 0) {
  t <- total_rows[1, ]
  cat("\n  Total Economic Impact:\n")
  cat(sprintf("    Employment:   %s jobs\n",
              formatC(t[[col_employment]], format = "f", digits = 1, big.mark = ",")))
  cat(sprintf("    Labor Income: $%s\n",
              formatC(t[[col_labor]],       format = "f", digits = 0, big.mark = ",")))
  cat(sprintf("    Value Added:  $%s\n",
              formatC(t[[col_value_added]], format = "f", digits = 0, big.mark = ",")))
  cat(sprintf("    Output:       $%s\n",
              formatC(t[[col_output]],      format = "f", digits = 0, big.mark = ",")))
}
