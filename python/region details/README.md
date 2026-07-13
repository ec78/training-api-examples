# Series 3 — Region Details (Python)

Seven scripts for retrieving raw regional economic data — employment, output, value added, and industry structure — without running a full impact analysis. Useful when you need baseline regional statistics rather than impact multipliers.

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
| `REGION_TYPE` | `"County"` | Geographic level: `"Country"`, `"State"`, `"County"`, `"MSA"`, or `"ZipCode"` |
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

---

### `step7-industry-time-series.py`
Pulls one industry across every state (+ DC) and every published data year, combining the region search (step2), project/group creation (step3), and Industry Detail export (step5) into a single loop. Prints an Employment and an Output matrix — states as rows, years as columns. This script does not use `GROUP_HASH_ID`; it creates its own Project and Groups internally, one per state/year combination.

| Variable | Default | Notes |
|---|---|---|
| `AGGREGATION_SCHEME_ID` | `14` | Must match earlier steps |
| `INDUSTRY_CODE` | `"40"` | The single industry to track. Run `get-industry-codes.py` (getting started series) to find a code. |
| `STATE_REGION_TYPE` | `"State"` | Leave as `"State"` to cover all 50 states + DC |
| `PROJECT_TITLE` | `"US Industry Time Series Study"` | **Must be unique in your account.** |
| `HOUSEHOLD_SET_ID` | `1` | Leave as `1` |
| `IS_MRIO` | `False` | Leave as `False` for single-region |
| `MAX_STATES` | `None` | Cap the number of states pulled (alphabetically). Set low (e.g. `3`) for a quick test — the full run makes hundreds of API calls. |
| `MAX_DATASETS` | `None` | Cap the number of data years pulled (most recent first). |
