library(httr2)   # HTTP requests
library(dotenv)  # Load credentials from a .env file

# Load credentials from the .env file next to this script
load_dot_env(file.path(dirname(sys.frame(1)$ofile), ".env"))

USER <- Sys.getenv("IMPLAN_USERNAME")
PW   <- Sys.getenv("IMPLAN_PASSWORD")

BASE_URL <- "https://api.implan.com"

# ── Configuration ──────────────────────────────────────────────────────────────
AGGREGATION_SCHEME_ID <- 14  # Must match the scheme used in your other scripts

# Optional: filter results to industries whose description contains this text.
# Set to "" to print all industries (there will be hundreds).
SEARCH <- "nuclear"

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

# ── Step 2: Get Industry Codes ─────────────────────────────────────────────────
# Industry codes define which sector of the economy an event belongs to.
# Every IndustryOutput (and related) event requires an IndustryCode.
# The available codes depend on which aggregation scheme you are using —
# different schemes group industries differently and have different code sets.
#
# Each result includes:
#   code        — the integer you pass as "industryCode" in add-events.R
#   description — human-readable industry name (e.g. "Grain farming")
#
# Endpoint: GET /api/v1/IndustryCodes/{aggregationSchemeId}
# Docs:     https://github.com/Implan-Group/api/wiki/Industry-Codes-by-Aggregation-Scheme

url <- paste0(BASE_URL, "/api/v1/IndustryCodes/", AGGREGATION_SCHEME_ID)

# GET requests must include ONLY the Authorization header.
# The IMPLAN API returns 400 if Content-Type is present on a GET request.
resp <- request(url) |>
  req_headers(Authorization = paste("Bearer", token)) |>
  req_perform()

industries <- resp_body_json(resp)

# ── Step 3: Display Results ────────────────────────────────────────────────────
# Filter by search term if provided, otherwise show all
if (nchar(SEARCH) > 0) {
  matches <- industries[sapply(industries, function(i) {
    grepl(SEARCH, i$description, ignore.case = TRUE)
  })]
  cat(sprintf("Industries matching '%s' (aggregation scheme %d):\n\n",
              SEARCH, AGGREGATION_SCHEME_ID))
} else {
  matches <- industries
  cat(sprintf("All industries for aggregation scheme %d:\n\n", AGGREGATION_SCHEME_ID))
}

cat(sprintf("  %-8s %s\n", "Code", "Description"))
cat("  ", strrep("-", 50), "\n", sep = "")

for (industry in matches) {
  cat(sprintf("  %-8d %s\n", industry$code, industry$description))
}

cat(sprintf("\n  %d result(s) found.\n", length(matches)))
cat("\n  --> Set INDUSTRY_CODE in add-events.R to the 'Code' value for your industry.\n")
