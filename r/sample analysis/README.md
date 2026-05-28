# Series 2 — Sample Analysis (R)

Seven scripts running the full IMPLAN workflow for a pre-configured example: a $500 million data center investment in Travis County, TX (aggregation scheme 14, 2024 data, industry code 50).

Most values are already set — you only need to paste IDs forward from one step to the next where indicated.

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
Rscript "r/sample analysis/step1-authentication.R"
```

---

## Scripts and configurable variables

### `step1-authentication.R`
No configurable variables. Credentials load from `.env`.

---

### `step2-get-datasets.R`
| Variable | Default | Notes |
|---|---|---|
| `AGGREGATION_SCHEME_ID` | `14` | Pre-set. Change only if using a different scheme throughout. |

---

### `step3-get-regions.R`
| Variable | Default | Notes |
|---|---|---|
| `AGGREGATION_SCHEME_ID` | `14` | Pre-set |
| `DATASET_ID` | `124` | Pre-set (2024 data) |
| `REGION_TYPE` | `"County"` | Pre-set. Change to search a different geographic level. |
| `REGION_SEARCH` | `"Travis County"` | Pre-set. Change to analyze a different county. |

---

### `step4-create-project.R`
| Variable | Default | Notes |
|---|---|---|
| `PROJECT_TITLE` | `"Travis Co. Data Center"` | **Must be unique in your account.** Change if you have already created a project with this name. |
| `AGGREGATION_SCHEME_ID` | `14` | Pre-set |
| `HOUSEHOLD_SET_ID` | `1` | Leave as `1` |
| `IS_MRIO` | `FALSE` | Pre-set |

---

### `step5-add-events.R`
| Variable | Default | Notes |
|---|---|---|
| `PROJECT_ID` | *(paste from previous step)* | Copy from `step4-create-project.R` output |
| `REGION_HASH_ID` | *(paste from previous step)* | Copy from `step3-get-regions.R` output |
| `DATASET_ID` | `124` | Pre-set (2024 data) |
| `DOLLAR_YEAR` | `2026` | Pre-set |
| `EVENT_TITLE` | `"Data Center Construction"` | Pre-set. Must be unique within the project. |
| `EVENT_OUTPUT` | `500000000` | Pre-set ($500M investment). Change to model a different amount. |
| `INDUSTRY_CODE` | `50` | Pre-set (construction of new commercial structures). Change to model a different industry. |

---

### `step6-run-project.R`
| Variable | Default | Notes |
|---|---|---|
| `PROJECT_ID` | *(paste from previous step)* | Copy from `step4-create-project.R` output |
| `POLL_INTERVAL` | `10` | Seconds between status checks |

---

### `step7-get-results.R`
| Variable | Default | Notes |
|---|---|---|
| `RUN_ID` | *(paste from previous step)* | Copy from `step6-run-project.R` output |
