# Series 3 — Region Details (Python)

Six scripts for retrieving raw regional economic data — employment, output, value added, and industry structure — without running a full impact analysis. Useful when you need baseline regional statistics rather than impact multipliers.

## Setup

Create a `.env` file in this folder with your credentials:
```
IMPLAN_USERNAME=you@yourfirm.com
IMPLAN_PASSWORD=yourpassword
```

## How to run (from the repo root)

```
.venv\Scripts\python.exe "python/region details/step1-authentication.py"
```

---

## Scripts and configurable variables

### `step1-authentication.py`
No configurable variables. Credentials load from `.env`.

---

### `step2-find-region.py`
| Variable | Default | Notes |
|---|---|---|
| `AGGREGATION_SCHEME_ID` | `14` | Must match all subsequent steps |
| `DATASET_ID` | `124` | Data year ID. Run `get-datasets.py` from the getting started series to see valid IDs. |
| `REGION_TYPE` | `"County"` | Geographic level: `"Country"`, `"State"`, `"County"`, `"MSA"`, or `"Zip"` |
| `REGION_SEARCH` | `"Travis County"` | Text to match against region names. Change to your target geography. |

---

### `step3-create-group.py`
| Variable | Default | Notes |
|---|---|---|
| `PROJECT_TITLE` | `"Travis Co. Region Study"` | **Must be unique in your account.** |
| `AGGREGATION_SCHEME_ID` | `14` | Must match `step2-find-region.py` |
| `HOUSEHOLD_SET_ID` | `1` | Leave as `1` |
| `IS_MRIO` | `False` | Leave as `False` for single-region |
| `REGION_HASH_ID` | *(paste from previous step)* | Copy from `step2-find-region.py` output |
| `DATASET_ID` | `124` | Must match `step2-find-region.py` |
| `DOLLAR_YEAR` | `2024` | Year monetary values are expressed in. |
| `GROUP_TITLE` | `"Travis County Study Area"` | Descriptive label for this group. |

---

### `step4-region-overview.py`
| Variable | Default | Notes |
|---|---|---|
| `AGGREGATION_SCHEME_ID` | `14` | Must match earlier steps |
| `GROUP_HASH_ID` | *(paste from previous step)* | Copy from `step3-create-group.py` output |
| `DISPLAY_ROWS` | `20` | Number of industry rows to print. Set to `None` to print all rows. |

---

### `step5-industry-detail.py`
| Variable | Default | Notes |
|---|---|---|
| `AGGREGATION_SCHEME_ID` | `14` | Must match earlier steps |
| `GROUP_HASH_ID` | *(paste from previous step)* | Copy from `step3-create-group.py` output |
| `DISPLAY_ROWS` | `20` | Number of industry rows to print. Set to `None` to print all rows. |

---

### `step6-industry-summary.py`
| Variable | Default | Notes |
|---|---|---|
| `AGGREGATION_SCHEME_ID` | `14` | Must match earlier steps |
| `GROUP_HASH_ID` | *(paste from previous step)* | Copy from `step3-create-group.py` output |
| `DISPLAY_ROWS` | `20` | Number of industry rows to print. Set to `None` to print all rows. |
