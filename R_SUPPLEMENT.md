# R Supplement — IMPLAN API

Use alongside `LLM_REFERENCE.md`. This file covers R-specific conventions only.
All endpoint paths, request rules, response formats, and field names in
`LLM_REFERENCE.md` apply unchanged.

---

## Packages

```r
# Install if needed:
# install.packages(c("httr2", "readr", "jsonlite", "dotenv", "dplyr", "purrr", "stringr"))

library(httr2)      # HTTP requests (preferred over httr)
library(readr)      # CSV response parsing
library(jsonlite)   # JSON parsing (backup / manual use)
library(dotenv)     # .env credential loading
library(dplyr)      # Data manipulation
library(purrr)      # Iteration (map_dfr for loop results)
library(stringr)    # String helpers (str_remove for Bearer prefix)
```

---

## Credentials

Store credentials in a `.env` file in the working directory. Never hardcode them.

```
# .env
IMPLAN_USERNAME=you@yourfirm.com
IMPLAN_PASSWORD=yourpassword
```

```r
dotenv::load_dot_env(".env")
username <- Sys.getenv("IMPLAN_USERNAME")
password <- Sys.getenv("IMPLAN_PASSWORD")
```

---

## Authentication

The IMPLAN auth endpoint returns a plain string with `"Bearer "` already prepended.
Strip it here so it can be re-added consistently in all subsequent requests.

```r
BASE_URL <- "https://api.implan.com"

get_token <- function(username, password) {
  resp <- request(paste0(BASE_URL, "/api/auth")) |>
    req_body_json(list(username = username, password = password)) |>
    req_perform()
  resp_body_string(resp) |> str_remove("^Bearer ")
}

token <- get_token(username, password)
```

---

## Header Rules

| Request type | Headers required |
|---|---|
| POST / PUT | `Authorization` + `Content-Type: application/json` |
| GET | `Authorization` only — omit `Content-Type` (API returns 400 if included) |

`httr2` sets `Content-Type: application/json` automatically when `req_body_json()` is
used, and does **not** add it on plain GET requests — so the rules above are handled
correctly by default. Do not manually add `Content-Type` to GET requests.

---

## Core Helper Functions

### GET → JSON

```r
get_json <- function(path, token) {
  request(paste0(BASE_URL, path)) |>
    req_headers(Authorization = paste("Bearer", token)) |>
    req_perform() |>
    resp_body_json()
}
```

### GET → CSV (used for impact results and regional exports)

Several IMPLAN endpoints return CSV rather than JSON. Use `read_csv()` with
`show_col_types = FALSE`. IMPLAN uses `", "` (comma-space) as a delimiter;
`read_csv()` handles this correctly without extra configuration.

```r
get_csv <- function(path, token) {
  raw <- request(paste0(BASE_URL, path)) |>
    req_headers(Authorization = paste("Bearer", token)) |>
    req_perform() |>
    resp_body_string()
  read_csv(raw, show_col_types = FALSE)
}
```

### POST → JSON

```r
post_json <- function(path, token, body) {
  request(paste0(BASE_URL, path)) |>
    req_headers(Authorization = paste("Bearer", token)) |>
    req_body_json(body) |>
    req_perform() |>
    resp_body_json()
}
```

---

## Workflow Functions

### 1. Get Datasets

```r
get_datasets <- function(token, aggregation_scheme_id) {
  get_json(paste0("/api/v1/datasets/", aggregation_scheme_id), token)
}

# Example: get default dataset ID for scheme 14
datasets   <- get_datasets(token, aggregation_scheme_id = 14)
dataset_id <- datasets |> keep(\(d) isTRUE(d$isDefault)) |> pluck(1, "id")
```

### 2. Find Region by Name

```r
get_regions <- function(token, aggregation_scheme_id, dataset_id,
                        region_type = "County") {
  path <- paste0(
    "/api/v1/region/", aggregation_scheme_id, "/", dataset_id,
    "/children?regionTypeFilter=", region_type
  )
  get_json(path, token)
}

find_region <- function(regions_list, name_pattern) {
  match <- regions_list |>
    keep(\(r) grepl(name_pattern, r$description, ignore.case = TRUE))
  if (length(match) == 0) stop("Region not found: ", name_pattern)
  if (length(match) > 1) warning("Multiple matches — using first: ",
                                  match[[1]]$description)
  match[[1]]
}

# Example
regions <- get_regions(token, 14, dataset_id)
region  <- find_region(regions, "Travis, TX")
hash_id <- region$hashId
```

### 3. Create Project

```r
create_project <- function(token, title,
                           aggregation_scheme_id = 14,
                           household_set_id = 1,
                           is_mrio = FALSE) {
  body <- list(
    Title               = title,
    AggregationSchemeId = aggregation_scheme_id,
    HouseholdSetId      = household_set_id,
    IsMrio              = is_mrio
  )
  result <- post_json("/api/v1/impact/project", token, body)
  result$id  # GUID string
}
```

### 4. Add Event

```r
add_event <- function(token, project_id, title, industry_code, output_value,
                      event_type = "IndustryOutput") {
  body <- list(
    ImpactEventType = event_type,
    Title           = title,
    IndustryCode    = industry_code,
    Output          = output_value
  )
  result <- post_json(
    paste0("/api/v1/impact/project/", project_id, "/event"), token, body
  )
  result$id  # integer
}
```

### 5. Create Group

```r
create_group <- function(token, project_id, title, hash_id, dataset_id,
                         dollar_year, event_ids) {
  body <- list(
    Title       = title,
    HashId      = hash_id,
    DatasetId   = dataset_id,
    DollarYear  = dollar_year,
    groupEvents = lapply(event_ids, \(id) list(eventId = id))
  )
  post_json(paste0("/api/v1/impact/project/", project_id, "/group"), token, body)
}
```

### 6. Run Analysis

The run endpoint path does **not** include `"project/"` (unlike create/event/group).
The response is a plain integer string — parse carefully to avoid float issues.
See `LLM_REFERENCE.md` § Run Analysis for details.

```r
run_analysis <- function(token, project_id) {
  resp <- request(paste0(BASE_URL, "/api/v1/impact/", project_id)) |>
    req_headers(Authorization  = paste("Bearer", token),
                `Content-Type` = "application/json") |>
    req_body_raw("", type = "application/json") |>
    req_perform()
  # Plain integer string — avoid as.numeric() which risks float conversion
  as.integer(trimws(resp_body_string(resp)))
}
```

### 7. Poll Until Complete

```r
poll_until_complete <- function(token, run_id, interval = 10) {
  terminal <- c("Complete", "Error", "UserCancelled")
  repeat {
    status_resp <- request(
      paste0(BASE_URL, "/api/v1/impact/status/", run_id)
    ) |>
      req_headers(Authorization = paste("Bearer", token)) |>
      req_error(is_error = \(r) FALSE) |>  # suppress auto-error on 400
      req_perform()

    # 400 immediately after triggering = analysis finished before first poll
    if (resp_status(status_resp) == 400) {
      message("  Run ", run_id, ": complete (fast finish)")
      return(invisible(run_id))
    }

    status <- trimws(resp_body_string(status_resp))
    message("  Run ", run_id, " status: ", status)

    if (status == "Complete") return(invisible(run_id))
    if (status %in% c("Error", "UserCancelled"))
      stop("Analysis failed with status: ", status)
    Sys.sleep(interval)
  }
}
```

### 8. Get Results

`SummaryEconomicIndicators` returns CSV. `Impact` column values are
`"1 - Direct"`, `"2 - Indirect"`, `"3 - Induced"` — no pre-aggregated Total row.
Compute totals by summing the three rows.

```r
get_results <- function(token, run_id) {
  get_csv(
    paste0("/api/v1/impact/results/SummaryEconomicIndicators/", run_id),
    token
  )
}

# Add a Total row per project
add_totals <- function(results_df) {
  totals <- results_df |>
    group_by(GroupName, EventName, ModelName, TagName) |>
    summarise(
      across(c(Employment, LaborIncome, ValueAdded, Output), sum),
      Impact = "Total",
      .groups = "drop"
    )
  bind_rows(results_df, totals) |>
    arrange(GroupName, EventName, Impact)
}
```

---

## Full Loop Pattern

Loops over a data frame of project inputs, runs each analysis, and compiles
results into a single data frame. Respects the batch rate limit (6/min) by
sleeping 10 seconds between project runs.

```r
run_implan_batch <- function(token, project_inputs_df,
                             aggregation_scheme_id = 14,
                             poll_interval = 10,
                             batch_sleep   = 10) {
  # project_inputs_df must have columns:
  #   label, region_name, industry_code, output_value, data_year
  #
  # Returns a compiled data frame of SummaryEconomicIndicators results
  # with an added `project_label` column.

  datasets   <- get_datasets(token, aggregation_scheme_id)
  dataset_id <- datasets |> keep(\(d) isTRUE(d$isDefault)) |> pluck(1, "id")
  regions    <- get_regions(token, aggregation_scheme_id, dataset_id)

  purrr::map_dfr(seq_len(nrow(project_inputs_df)), function(i) {
    row <- project_inputs_df[i, ]
    message("\n[", i, "/", nrow(project_inputs_df), "] ", row$label)

    region     <- find_region(regions, row$region_name)
    project_id <- create_project(token, title = row$label,
                                 aggregation_scheme_id = aggregation_scheme_id)

    event_id   <- add_event(token, project_id,
                            title         = paste(row$label, "event"),
                            industry_code = row$industry_code,
                            output_value  = row$output_value)

    create_group(token, project_id,
                 title      = paste(row$label, "group"),
                 hash_id    = region$hashId,
                 dataset_id = dataset_id,
                 dollar_year = row$data_year,
                 event_ids  = list(event_id))

    run_id <- run_analysis(token, project_id)
    poll_until_complete(token, run_id, interval = poll_interval)

    results <- get_results(token, run_id) |>
      mutate(project_label = row$label)

    Sys.sleep(batch_sleep)  # respect batch rate limit (6/min)
    results
  })
}
```

---

## Putting It All Together

```r
# Load credentials and authenticate
dotenv::load_dot_env(".env")
token <- get_token(Sys.getenv("IMPLAN_USERNAME"), Sys.getenv("IMPLAN_PASSWORD"))

# Define project inputs (replace with your customer data parsing logic)
project_inputs <- tibble::tibble(
  label         = c("Project A", "Project B"),
  region_name   = c("Travis, TX", "Denver, CO"),
  industry_code = c(50L, 55L),
  output_value  = c(500e6, 250e6),
  data_year     = c(2024L, 2024L)
)

# Run all projects and compile results
all_results <- run_implan_batch(token, project_inputs)

# Add total rows and write output
final <- add_totals(all_results)
readr::write_csv(final, "results_output.csv")
message("Done. Results written to results_output.csv")
```

---

## Common Pitfalls (R-specific)

**`resp_body_json()` fails on plain-text responses.** Auth, run analysis, and
status endpoints return plain strings — use `resp_body_string()` for those.

**`as.numeric()` on Run ID can produce a float.** Use `as.integer(trimws(...))`.

**`list()` vs named vector in `req_body_json()`.** Always pass a named `list()` —
not a character vector or data frame row — to `req_body_json()`.

**`httr2` does not retry on 429 by default.** Add `req_retry(max_tries = 3,
is_transient = \(r) resp_status(r) == 429)` to requests inside a loop if you
want automatic backoff on rate-limit errors.

**`purrr::map_dfr()` is deprecated in newer purrr.** Use
`purrr::map(... ) |> list_rbind()` if you see a deprecation warning.
