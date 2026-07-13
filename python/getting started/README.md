# Series 1 — Getting Started (Python)

Eight scripts covering the full IMPLAN API workflow, one step at a time. Run them in order — each script prints the ID(s) needed by the next step.

## Setup

Create a `.env` file in this folder with your credentials:
```
IMPLAN_USERNAME=you@yourfirm.com
IMPLAN_PASSWORD=yourpassword
```

## How to run (from the repo root)

```
.venv\Scripts\python.exe "python/getting started/api-authenticate.py"
```

---

## Scripts and configurable variables

### `api-authenticate.py`
No configurable variables. Credentials load from `.env`.

---

### `get-datasets.py`
| Variable | Default | Notes |
|---|---|---|
| `AGGREGATION_SCHEME_ID` | `14` | Industry grouping scheme. `14` = 528-industry (standard), `8` = 546-industry. Must match across all scripts. |

---

### `find-region.py`
| Variable | Default | Notes |
|---|---|---|
| `AGGREGATION_SCHEME_ID` | `14` | Must match `get-datasets.py` |
| `DATASET_ID` | `124` | Data year ID — copy from `get-datasets.py` output |
| `REGION_TYPE` | `"State"` | Geographic level to search: `"Country"`, `"State"`, `"County"`, `"MSA"`, or `"ZipCode"` |
| `REGION_SEARCH` | `"Minnesota"` | Text to match against region names. Change to your target geography. |

---

### `find-region-children.py` *(bonus — not part of the numbered 8-step sequence)*
Finds a County, then asks the API for the Zip codes that live inside it — a parent/child region lookup rather than `find-region.py`'s flat, nationwide search.

| Variable | Default | Notes |
|---|---|---|
| `AGGREGATION_SCHEME_ID` | `14` | Must match other scripts |
| `DATASET_ID` | `124` | Data year ID — copy from `get-datasets.py` output |
| `COUNTY_SEARCH` | `"Travis County"` | Text to match against County names. Change to your target county. |

---

### `get-industry-codes.py`
| Variable | Default | Notes |
|---|---|---|
| `AGGREGATION_SCHEME_ID` | `14` | Must match other scripts |
| `SEARCH` | `"construction"` | Keyword to filter industry names. Set to `""` to list all industries. |

---

### `create-project.py`
| Variable | Default | Notes |
|---|---|---|
| `PROJECT_TITLE` | *(timestamped)* | e.g. `"Training API Example 2026-07-13 14:32:01"`. Project titles must be unique account-wide — the timestamp guarantees that on every run. |
| `AGGREGATION_SCHEME_ID` | `14` | Must match all other scripts. Cannot be changed after project creation. |
| `HOUSEHOLD_SET_ID` | `1` | Leave as `1` for standard IMPLAN household data. |
| `IS_MRIO` | `False` | `False` = single-region analysis (standard). `True` = multi-region (advanced). |

---

### `add-events.py`
| Variable | Default | Notes |
|---|---|---|
| `PROJECT_ID` | *(paste from previous step)* | Copy from `create-project.py` output |
| `REGION_HASH_ID` | *(paste from previous step)* | Copy from `find-region.py` output |
| `DATASET_ID` | `124` | Must match `find-region.py` |
| `DOLLAR_YEAR` | `2026` | Year monetary values are expressed in. |
| `EVENT_TITLE` | *(timestamped)* | Label for this event. Must be unique within the project. |
| `EVENT_OUTPUT` | `1000000` | Dollar value of the economic activity being modeled. |
| `INDUSTRY_CODE` | `1` | Industry code from `get-industry-codes.py`. Required — the analysis cannot run without it. |

---

### `run-analysis.py`
| Variable | Default | Notes |
|---|---|---|
| `PROJECT_ID` | *(paste from previous step)* | Copy from `create-project.py` output |
| `POLL_INTERVAL` | `10` | Seconds between status checks. |

---

### `get-results.py`
| Variable | Default | Notes |
|---|---|---|
| `RUN_ID` | *(paste from previous step)* | Copy from `run-analysis.py` output |
