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

GROUP_HASH_ID <- "0GxZYok7Vp"
# --> From Step 3 (create-group.R): the hashId printed in the group output.
#     Identifies the regional model to pull summary industry data from.

DISPLAY_ROWS <- 20
# How many industry rows to print. Set to NULL to print all rows.

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

# ── Step 2: Pull Study Area Data — Industry Summary ────────────────────────────
# This endpoint returns a per-industry summary of the regional economy, focusing
# on the relationship between output, intermediate inputs, and value added.
#
# Where Industry Detail (step5) shows how output is distributed across labor,
# property income, and taxes, the Industry Summary shows how output is broken
# down across production costs:
#
#   Total Output = Total Intermediate Inputs + Total Value Added
#
#   Intermediate Inputs — goods and services purchased from other industries
#                         to produce output (raw materials, utilities, services)
#   Total Value Added   — what the industry contributes to GDP after subtracting
#                         intermediate inputs; includes all labor income,
#                         property income, and taxes
#   Labor Income        — the portion of Value Added paid to workers
#
# Together with the Industry Detail data from step5, this gives a complete
# picture of how the regional economy is structured industry by industry.
#
# Response columns:
#   Industry Code           — IMPLAN numeric industry identifier
#   Description             — Industry name
#   Total Employment        — All jobs (wage & salary + proprietor combined)
#   Total Output            — Total value of goods/services produced ($)
#   Total Intermediate Inputs — Purchased inputs used in production ($)
#   Total Value Added       — GDP contribution: output minus intermediate inputs ($)
#   Labor Income            — Wages, salaries, and proprietor income ($)
#
# Note: GET requests must NOT include Content-Type — only pass Authorization.
#
# Endpoint: GET /api/v1/regions/export/{aggregationSchemeId}/StudyAreaDataIndustrySummary
# Docs:     https://github.com/Implan-Group/api/wiki/Region-Data---Industry-Summary

url <- sprintf("%s/api/v1/regions/export/%d/StudyAreaDataIndustrySummary", BASE_URL, AGGREGATION_SCHEME_ID)

resp <- request(url) |>
  req_headers(Authorization = paste("Bearer", token)) |>
  req_url_query(hashId = GROUP_HASH_ID) |>
  req_perform()

# ── Step 3: Parse and Display Results ─────────────────────────────────────────
# read_csv() parses the raw CSV text from the response body.
# trim_ws = TRUE removes the leading space the IMPLAN API adds after each comma.

df <- read_csv(resp_body_string(resp), trim_ws = TRUE, show_col_types = FALSE)

n_rows <- nrow(df)

cat(sprintf("Study Area Data — Industry Summary  |  hashId: %s\n", GROUP_HASH_ID))
cat(sprintf("  Total industries in region: %d\n", n_rows))
if (!is.null(DISPLAY_ROWS)) {
  cat(sprintf("  Showing first %d rows\n\n", DISPLAY_ROWS))
} else {
  cat("\n")
}

cat(sprintf("  %-6s %-38s %12s %18s %18s %18s\n",
            "Code", "Industry", "Employment", "Output", "Int. Inputs", "Value Added"))
cat(paste0("  ", strrep("-", 114), "\n"))

display <- if (is.null(DISPLAY_ROWS)) df else head(df, DISPLAY_ROWS)

for (i in seq_len(nrow(display))) {
  row         <- display[i, ]
  code        <- as.character(row[["Industry Code"]])
  desc        <- substr(as.character(row[["Description"]]), 1, 37)
  employment  <- as.numeric(row[["Total Employment"]])
  employment  <- if (is.na(employment))  0 else employment
  output      <- as.numeric(row[["Total Output"]])
  output      <- if (is.na(output))      0 else output
  int_inputs  <- as.numeric(row[["Total Intermediate Inputs"]])
  int_inputs  <- if (is.na(int_inputs))  0 else int_inputs
  value_added <- as.numeric(row[["Total Value Added"]])
  value_added <- if (is.na(value_added)) 0 else value_added

  cat(sprintf("  %-6s %-38s %12s $%17s $%17s $%17s\n",
              code, desc,
              formatC(employment,  format = "f", digits = 1, big.mark = ","),
              formatC(output,      format = "f", digits = 0, big.mark = ","),
              formatC(int_inputs,  format = "f", digits = 0, big.mark = ","),
              formatC(value_added, format = "f", digits = 0, big.mark = ",")))
}

# ── Summary ────────────────────────────────────────────────────────────────────
total_emp        <- sum(as.numeric(df[["Total Employment"]]),          na.rm = TRUE)
total_output     <- sum(as.numeric(df[["Total Output"]]),              na.rm = TRUE)
total_int_inputs <- sum(as.numeric(df[["Total Intermediate Inputs"]]), na.rm = TRUE)
total_val_added  <- sum(as.numeric(df[["Total Value Added"]]),         na.rm = TRUE)
total_labor      <- sum(as.numeric(df[["Labor Income"]]),              na.rm = TRUE)

cat(sprintf("\n  Region Totals (all %d industries):\n", n_rows))
cat(sprintf("    Total Employment:         %12s jobs\n",
            formatC(total_emp,        format = "f", digits = 1, big.mark = ",")))
cat(sprintf("    Total Output:             $%14s\n",
            formatC(total_output,     format = "f", digits = 0, big.mark = ",")))
cat(sprintf("    Total Intermediate Inputs:$%14s\n",
            formatC(total_int_inputs, format = "f", digits = 0, big.mark = ",")))
cat(sprintf("    Total Value Added:        $%14s\n",
            formatC(total_val_added,  format = "f", digits = 0, big.mark = ",")))
cat(sprintf("    Labor Income:             $%14s\n",
            formatC(total_labor,      format = "f", digits = 0, big.mark = ",")))

# Value Added as a share of Output is a useful regional economic metric.
# A higher share means the region retains more of its production value locally
# (rather than spending it on imported inputs).
if (total_output > 0) {
  va_share <- (total_val_added / total_output) * 100
  cat(sprintf("\n  Value Added as %% of Output: %.1f%%\n", va_share))
  cat("  (Higher % = region retains more economic value from its production)\n")
}
