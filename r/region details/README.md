# Series 3 — Region Details (R)

Six scripts for retrieving raw regional economic data — employment, output, value added, and industry structure — without running a full impact analysis. Useful when you need baseline regional statistics rather than impact multipliers.

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
Rscript "r/region details/step1-authentication.R"
```

---

## Scripts and configurable variables

### `step1-authentication.R`
No configurable variables. Credentials load from `.env`.

---

### `step2-find-region.R`
| Variable | Default | Notes |
|---|---|---|
| `AGGREGATION_SCHEME_ID` | `14` | Must match all subsequent steps |
| `DATASET_ID` | `124` | Data year ID. Run `get-datasets.R` from the getting started series to see valid IDs. |
| `REGION_TYPE` | `"County"` | Geographic level: `"Country"`, `"State"`, `"County"`, `"MSA"`, or `"ZipCode"` |
| `REGION_SEARCH` | `"Travis County"` | Text to match against region names. Change to your target geography. |

---

### `step3-create-group.R`
| Variable | Default | Notes |
|---|---|---|
| `PROJECT_TITLE` | `"Travis Co. Region Study"` | **Must be unique in your account.** |
| `AGGREGATION_SCHEME_ID` | `14` | Must match `step2-find-region.R` |
| `HOUSEHOLD_SET_ID` | `1` | Leave as `1` |
| `IS_MRIO` | `FALSE` | Leave as `FALSE` for single-region |
| `REGION_HASH_ID` | *(paste from previous step)* | Copy from `step2-find-region.R` output |
| `DATASET_ID` | `124` | Must match `step2-find-region.R` |
| `DOLLAR_YEAR` | `2024` | Year monetary values are expressed in. |
| `GROUP_TITLE` | `"Travis County Study Area"` | Descriptive label for this group. |

---

### `step4-region-overview.R`
| Variable | Default | Notes |
|---|---|---|
| `AGGREGATION_SCHEME_ID` | `14` | Must match earlier steps |
| `GROUP_HASH_ID` | *(paste from previous step)* | Copy from `step3-create-group.R` output |
| `DISPLAY_ROWS` | `20` | Number of industry rows to print. Set to `NULL` to print all rows. |

---

### `step5-industry-detail.R`
| Variable | Default | Notes |
|---|---|---|
| `AGGREGATION_SCHEME_ID` | `14` | Must match earlier steps |
| `GROUP_HASH_ID` | *(paste from previous step)* | Copy from `step3-create-group.R` output |
| `DISPLAY_ROWS` | `20` | Number of industry rows to print. Set to `NULL` to print all rows. |

---

### `step6-industry-summary.R`
| Variable | Default | Notes |
|---|---|---|
| `AGGREGATION_SCHEME_ID` | `14` | Must match earlier steps |
| `GROUP_HASH_ID` | *(paste from previous step)* | Copy from `step3-create-group.R` output |
| `DISPLAY_ROWS` | `20` | Number of industry rows to print. Set to `NULL` to print all rows. |
