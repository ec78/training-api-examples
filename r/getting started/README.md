# Series 1 — Getting Started (R)

Eight scripts covering the full IMPLAN API workflow, one step at a time. Run them in order — each script prints the ID(s) needed by the next step.

## Setup

Create a `.env` file in this folder with your credentials:
```
IMPLAN_USERNAME=you@yourfirm.com
IMPLAN_PASSWORD=yourpassword
```

Install required packages (once):
```r
install.packages(c("httr2", "dotenv", "readr"))
```

## How to run

Open any script in RStudio and click **Run**, or from the terminal:
```
Rscript "r/getting started/api-authenticate.R"
```

---

## Scripts and configurable variables

### `api-authenticate.R`
No configurable variables. Credentials load from `.env`.

---

### `get-datasets.R`
| Variable | Default | Notes |
|---|---|---|
| `AGGREGATION_SCHEME_ID` | `14` | Industry grouping scheme. `14` = 528-industry (standard), `8` = 546-industry. Must match across all scripts. |

---

### `find-region.R`
| Variable | Default | Notes |
|---|---|---|
| `AGGREGATION_SCHEME_ID` | `14` | Must match `get-datasets.R` |
| `DATASET_ID` | `124` | Data year ID — copy from `get-datasets.R` output |
| `REGION_TYPE` | `"State"` | Geographic level to search: `"Country"`, `"State"`, `"County"`, `"MSA"`, or `"Zip"` |
| `REGION_SEARCH` | `"Minnesota"` | Text to match against region names. Change to your target geography. |

---

### `get-industry-codes.R`
| Variable | Default | Notes |
|---|---|---|
| `AGGREGATION_SCHEME_ID` | `14` | Must match other scripts |
| `SEARCH` | `"construction"` | Keyword to filter industry names. Set to `""` to list all industries. |

---

### `create-project.R`
| Variable | Default | Notes |
|---|---|---|
| `PROJECT_TITLE` | `"Training API Example"` | Name for this project. **Must be unique in your account.** |
| `AGGREGATION_SCHEME_ID` | `14` | Must match all other scripts. Cannot be changed after project creation. |
| `HOUSEHOLD_SET_ID` | `1` | Leave as `1` for standard IMPLAN household data. |
| `IS_MRIO` | `FALSE` | `FALSE` = single-region analysis (standard). `TRUE` = multi-region (advanced). |

---

### `add-events.R`
| Variable | Default | Notes |
|---|---|---|
| `PROJECT_ID` | *(paste from previous step)* | Copy from `create-project.R` output |
| `REGION_HASH_ID` | *(paste from previous step)* | Copy from `find-region.R` output |
| `DATASET_ID` | `124` | Must match `find-region.R` |
| `DOLLAR_YEAR` | `2026` | Year monetary values are expressed in. Typically matches the dataset year. |
| `EVENT_TITLE` | *(timestamped)* | Label for this event. Must be unique within the project. |
| `EVENT_OUTPUT` | `1000000` | Dollar value of the economic activity being modeled. |
| `INDUSTRY_CODE` | `1` | Industry code from `get-industry-codes.R`. Required — the analysis cannot run without it. |

---

### `run-analysis.R`
| Variable | Default | Notes |
|---|---|---|
| `PROJECT_ID` | *(paste from previous step)* | Copy from `create-project.R` output |
| `POLL_INTERVAL` | `10` | Seconds between status checks. |

---

### `get-results.R`
| Variable | Default | Notes |
|---|---|---|
| `RUN_ID` | *(paste from previous step)* | Copy from `run-analysis.R` output |
