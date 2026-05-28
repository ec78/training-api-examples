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
#     Identifies the regional model to pull detailed industry data from.

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

# ── Step 2: Pull Study Area Data — Industry Detail ─────────────────────────────
# This endpoint returns the full Study Area Data for the region broken down
# by industry. It shows the complete composition of each industry: how many
# people work there (wage & salary vs. self-employed), what they earn, how much
# the industry produces, and how that production is split across value-added
# components.
#
# This is the granular foundation of IMPLAN's input-output model. Every
# economic multiplier IMPLAN calculates is derived from this underlying data,
# so understanding it helps you interpret impact analysis results.
#
# Response columns:
#   Industry Code            — IMPLAN numeric industry identifier
#   Description              — Industry name (e.g., "Grain farming")
#   Total Output             — Total value of goods/services produced ($)
#   Wage and Salary Employment — Full- and part-time wage/salary jobs (count)
#   Employee Compensation    — Total wages, salaries, and benefits paid ($)
#   Proprietor Employment    — Self-employed / owner-operator jobs (count)
#   Proprietor Income        — Self-employment income ($)
#   Other Property Income    — Returns to capital: rent, interest, dividends ($)
#   Taxes on Production and Imports Net of Subsidies
#                            — Net taxes paid by the industry to governments ($)
#
# The sum of Employee Compensation + Proprietor Income = Labor Income.
# The sum of Labor Income + Other Property Income + Taxes = Value Added.
# Value Added + Intermediate Inputs = Total Output.
#
# Note: GET requests must NOT include Content-Type — only pass Authorization.
#
# Endpoint: GET /api/v1/regions/export/{aggregationSchemeId}/StudyAreaDataIndustryDetail
# Docs:     https://github.com/Implan-Group/api/wiki/Region-Data---Industry-Detail

url <- sprintf("%s/api/v1/regions/export/%d/StudyAreaDataIndustryDetail", BASE_URL, AGGREGATION_SCHEME_ID)

resp <- request(url) |>
  req_headers(Authorization = paste("Bearer", token)) |>
  req_url_query(hashId = GROUP_HASH_ID) |>
  req_perform()

# ── Step 3: Parse and Display Results ─────────────────────────────────────────
# read_csv() parses the raw CSV text from the response body.
# trim_ws = TRUE removes the leading space the IMPLAN API adds after each comma.

df <- read_csv(resp_body_string(resp), trim_ws = TRUE, show_col_types = FALSE)

n_rows <- nrow(df)

cat(sprintf("Study Area Data — Industry Detail  |  hashId: %s\n", GROUP_HASH_ID))
cat(sprintf("  Total industries in region: %d\n", n_rows))
if (!is.null(DISPLAY_ROWS)) {
  cat(sprintf("  Showing first %d rows\n\n", DISPLAY_ROWS))
} else {
  cat("\n")
}

# Print a formatted table showing the key employment and financial columns.
# W&S Emp = Wage and Salary Employment, Prop Emp = Proprietor Employment.
cat(sprintf("  %-6s %-38s %10s %10s %18s %18s\n",
            "Code", "Industry", "W&S Emp", "Prop Emp", "Output", "Emp Comp"))
cat(paste0("  ", strrep("-", 104), "\n"))

display <- if (is.null(DISPLAY_ROWS)) df else head(df, DISPLAY_ROWS)

for (i in seq_len(nrow(display))) {
  row      <- display[i, ]
  code     <- as.character(row[["Industry Code"]])
  desc     <- substr(as.character(row[["Description"]]), 1, 37)
  ws_emp   <- as.numeric(row[["Wage and Salary Employment"]])
  ws_emp   <- if (is.na(ws_emp))   0 else ws_emp
  prop_emp <- as.numeric(row[["Proprietor Employment"]])
  prop_emp <- if (is.na(prop_emp)) 0 else prop_emp
  output   <- as.numeric(row[["Total Output"]])
  output   <- if (is.na(output))   0 else output
  emp_comp <- as.numeric(row[["Employee Compensation"]])
  emp_comp <- if (is.na(emp_comp)) 0 else emp_comp

  cat(sprintf("  %-6s %-38s %10s %10s $%17s $%17s\n",
              code, desc,
              formatC(ws_emp,   format = "f", digits = 1, big.mark = ","),
              formatC(prop_emp, format = "f", digits = 1, big.mark = ","),
              formatC(output,   format = "f", digits = 0, big.mark = ","),
              formatC(emp_comp, format = "f", digits = 0, big.mark = ",")))
}

# ── Summary ────────────────────────────────────────────────────────────────────
total_ws_emp   <- sum(as.numeric(df[["Wage and Salary Employment"]]),                          na.rm = TRUE)
total_prop_emp <- sum(as.numeric(df[["Proprietor Employment"]]),                               na.rm = TRUE)
total_output   <- sum(as.numeric(df[["Total Output"]]),                                        na.rm = TRUE)
total_emp_comp <- sum(as.numeric(df[["Employee Compensation"]]),                               na.rm = TRUE)
total_prop_inc <- sum(as.numeric(df[["Proprietor Income"]]),                                   na.rm = TRUE)
total_opi      <- sum(as.numeric(df[["Other Property Income"]]),                               na.rm = TRUE)
total_topi     <- sum(as.numeric(df[["Taxes on Production and Imports Net of Subsidies"]]),    na.rm = TRUE)

cat(sprintf("\n  Region Totals (all %d industries):\n", n_rows))
cat(sprintf("    Wage & Salary Employment: %12s jobs\n",
            formatC(total_ws_emp,   format = "f", digits = 1, big.mark = ",")))
cat(sprintf("    Proprietor Employment:    %12s jobs\n",
            formatC(total_prop_emp, format = "f", digits = 1, big.mark = ",")))
cat(sprintf("    Total Output:             $%14s\n",
            formatC(total_output,   format = "f", digits = 0, big.mark = ",")))
cat(sprintf("    Employee Compensation:    $%14s\n",
            formatC(total_emp_comp, format = "f", digits = 0, big.mark = ",")))
cat(sprintf("    Proprietor Income:        $%14s\n",
            formatC(total_prop_inc, format = "f", digits = 0, big.mark = ",")))
cat(sprintf("    Other Property Income:    $%14s\n",
            formatC(total_opi,      format = "f", digits = 0, big.mark = ",")))
cat(sprintf("    Taxes (net):              $%14s\n",
            formatC(total_topi,     format = "f", digits = 0, big.mark = ",")))
