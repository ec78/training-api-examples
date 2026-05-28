library(httr2)   # For making HTTP requests to the IMPLAN API
library(dotenv)  # For loading credentials from a .env file
library(readr)   # For parsing CSV responses

# Load credentials from the .env file next to this script
load_dot_env(file.path(dirname(sys.frame(1)$ofile), ".env"))

USER <- Sys.getenv("IMPLAN_USERNAME")
PW   <- Sys.getenv("IMPLAN_PASSWORD")

BASE_URL <- "https://api.implan.com"

# ── Configuration ─────────────────────────────────────────────────────────────
RUN_ID <- 607581
# --> From Step 6 (step6-run-project.R): the integer Run ID returned after the
#     analysis completed with status "Complete".
#     Example: 17280

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
#
# Note: GET requests must NOT include Content-Type — only pass Authorization.

url <- paste0(BASE_URL, "/api/v1/impact/results/SummaryEconomicIndicators/", RUN_ID)

resp <- request(url) |>
  req_headers(Authorization = paste("Bearer", token)) |>
  req_perform()

# ── Step 3: Parse and Display Results ────────────────────────────────────────
# The response body is plain CSV text. readr::read_csv() can parse it directly
# from the string. trim_ws = TRUE strips the leading space after each comma
# in the CSV — the IMPLAN results CSV uses ", " as its delimiter, which would
# otherwise produce column names like " Employment" instead of "Employment".

df <- readr::read_csv(resp_body_string(resp), trim_ws = TRUE, show_col_types = FALSE)

cat(sprintf("Results for Run ID %d:\n\n", RUN_ID))

# Print a formatted table header. Width specifiers align each column for
# easy reading — impact type is left-aligned, numeric columns are right-aligned.
cat(sprintf("  %-12s %14s %18s %18s %18s\n",
            "Impact Type", "Employment", "Labor Income", "Value Added", "Output"))
cat("  ", strrep("-", 84), "\n", sep = "")

# Iterate over each row (Direct, Indirect, Induced, Total).
# Numeric fields come back as strings in CSV — convert explicitly before formatting.
# formatC() formats numbers with commas and a fixed number of decimal places.
for (i in seq_len(nrow(df))) {
  row         <- df[i, ]
  employment  <- formatC(as.numeric(row$Employment),  format = "f", digits = 1, big.mark = ",")
  labor       <- paste0("$", formatC(as.numeric(row$LaborIncome),  format = "f", digits = 0, big.mark = ","))
  value_added <- paste0("$", formatC(as.numeric(row$ValueAdded),   format = "f", digits = 0, big.mark = ","))
  output      <- paste0("$", formatC(as.numeric(row$Output),       format = "f", digits = 0, big.mark = ","))

  cat(sprintf("  %-12s %14s %18s %18s %18s\n",
              row$Impact, employment, labor, value_added, output))
}

# ── Summary ───────────────────────────────────────────────────────────────────
# Pull out the Total row for a quick bottom-line overview.
# grepl() with ignore.case = TRUE catches "Total", "total", "TOTAL", etc.
total_rows <- df[grepl("total", df$Impact, ignore.case = TRUE), ]

if (nrow(total_rows) > 0) {
  t <- total_rows[1, ]
  cat("\n  Total Economic Impact:\n")
  cat(sprintf("    Employment:   %s jobs\n",
              formatC(as.numeric(t$Employment), format = "f", digits = 1, big.mark = ",")))
  cat(sprintf("    Labor Income:  $%s\n",
              formatC(as.numeric(t$LaborIncome), format = "f", digits = 0, big.mark = ",")))
  cat(sprintf("    Value Added:   $%s\n",
              formatC(as.numeric(t$ValueAdded), format = "f", digits = 0, big.mark = ",")))
  cat(sprintf("    Output:        $%s\n",
              formatC(as.numeric(t$Output), format = "f", digits = 0, big.mark = ",")))
}
