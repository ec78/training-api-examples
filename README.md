# IMPLAN API Training Examples

A set of beginner-friendly Python scripts that walk through the full IMPLAN API workflow — from authentication to retrieving economic impact results. Each script is self-contained, heavily annotated, and designed to be run one step at a time.

**API Reference:** https://github.com/Implan-Group/api/wiki  
**Sample Code:** https://github.com/Implan-Group/api

---

## What You Will Build

By the end of this walkthrough you will have used the IMPLAN API to run a complete economic impact analysis programmatically:

```
Authenticate → Get Datasets → Find Region → Get Industry Codes
    → Create Project → Add Events → Run Analysis → Get Results
```

---

## Prerequisites

- Python 3.9 or later
- A valid IMPLAN account with API access

---

## Setup

**1. Clone the repository**

```bash
git clone https://github.com/<your-username>/training-api-examples.git
cd training-api-examples
```

**2. Create a virtual environment**

```bash
python -m venv .venv
```

Activate it:
- Windows: `.venv\Scripts\activate`
- Mac/Linux: `source .venv/bin/activate`

**3. Install dependencies**

```bash
pip install requests python-dotenv
```

**4. Create your credentials file**

Create a file at `python/getting started/.env` with your IMPLAN login:

```
IMPLAN_USERNAME=you@yourfirm.com
IMPLAN_PASSWORD=yourpassword
```

> **Important:** The `.env` file is listed in `.gitignore` and will not be committed to GitHub. Never hardcode credentials in your scripts.

---

## The Workflow: Step by Step

All scripts are in the `python/getting started/` folder. Each script prints the ID(s) you need to carry into the next step.

---

### Step 1 — Authenticate
**File:** `python/getting started/import-requests.py`

Exchanges your credentials for a Bearer token. This is a reference script — all subsequent scripts include authentication internally.

**Key concept:** The IMPLAN API returns the token as a plain string with `Bearer ` already prepended (e.g. `Bearer eyJ...`). Strip the prefix before storing it, then re-add it in request headers.

---

### Step 2 — Get Available Datasets
**File:** `python/getting started/get-datasets.py`

```bash
python "python/getting started/get-datasets.py"
```

Returns the data years available for your aggregation scheme (e.g. 2021, 2022, 2023). Each dataset has a numeric ID.

**What to copy forward:** The `ID` for the data year you want to use.

---

### Step 3 — Find Your Region
**File:** `python/getting started/find-region.py`

```bash
python "python/getting started/find-region.py"
```

Looks up geographic regions (states, counties, MSAs) available for your dataset. Edit the configuration section at the top to set your aggregation scheme ID, dataset ID, region type, and search term.

**What to copy forward:** The `hashId` for your target region.

---

### Step 4 — Look Up Industry Codes
**File:** `python/getting started/get-industry-codes.py`

```bash
python "python/getting started/get-industry-codes.py"
```

Returns the list of industries available under your aggregation scheme. Edit the `SEARCH` variable to filter by keyword (e.g. `"construction"`, `"health"`, `"retail"`).

**What to copy forward:** The `Code` integer for the industry you want to analyze.

---

### Step 5 — Create a Project
**File:** `python/getting started/create-project.py`

```bash
python "python/getting started/create-project.py"
```

Creates the project container that will hold your analysis. A project ties together the aggregation scheme, household data, and all events.

**What to copy forward:** The `Project ID` (a GUID) printed at the end.

---

### Step 6 — Add Events and Groups
**File:** `python/getting started/add-events.py`

```bash
python "python/getting started/add-events.py"
```

This script does two things:
1. **Creates an Event** — defines *what* economic activity is happening (industry + dollar value)
2. **Creates a Group** — links the event to a *region* and *data year*

Edit the configuration section with your Project ID, Region Hash ID, Dataset ID, and Industry Code from the previous steps.

**What to copy forward:** The `Project ID` (same as before — you're now ready to run it).

---

### Step 7 — Run the Analysis
**File:** `python/getting started/run-analysis.py`

```bash
python "python/getting started/run-analysis.py"
```

Triggers the I-O model calculation. IMPLAN processes the analysis in the background and returns a Run ID immediately. Small analyses typically complete within seconds.

**What to copy forward:** The `Run ID` printed at the end.

---

### Step 8 — Get Results
**File:** `python/getting started/get-results.py`

```bash
python "python/getting started/get-results.py"
```

Retrieves the Summary Economic Indicators for your completed analysis — direct, indirect, and induced effects across Employment, Labor Income, Value Added, and Output.

Set `RUN_ID` in the configuration section to the integer from Step 7.

---

## Pointers for Success

**Pass IDs forward carefully.** Each step produces an ID that the next step needs. The most common source of errors is using an ID from the wrong step or a stale run. The scripts print a `-->` line at the end to tell you exactly what to copy.

**Aggregation scheme must be consistent.** The scheme ID you choose in Step 2 must be the same in every subsequent step. Mixing scheme IDs will cause silent failures or 400 errors.

**Event titles must be unique within a project.** If you re-run `add-events.py` against the same project, the script automatically appends a timestamp to avoid conflicts.

**The IMPLAN API is inconsistent about response formats.** Some endpoints return JSON, others return plain strings or integers. If you get a `JSONDecodeError`, the response is likely plain text — use `resp.text` instead of `resp.json()`.

**GET requests should not include `Content-Type: application/json`.** Only include that header on POST/PUT requests with a body. Sending it on GET requests causes 400 errors from the IMPLAN API.

**Small analyses complete faster than polling can detect.** If the status endpoint returns a 400 immediately after triggering a run, it often means the analysis finished before the first poll. The Run ID is still valid — go straight to `get-results.py`.

---

## Key Intuition: How the Pieces Fit Together

Understanding *why* the workflow is structured this way makes it easier to debug and extend:

| Concept | What it is | Why it matters |
|---|---|---|
| **Aggregation Scheme** | How industries are grouped (e.g. 528 vs 546 sectors) | Must be consistent across all steps — it defines the model's industry vocabulary |
| **Dataset** | A specific data year (e.g. 2022) | IMPLAN's regional economic data is published annually; you pick the year that matches your analysis period |
| **Region / HashId** | A geographic area (state, county, MSA) | The I-O model is region-specific — the multipliers for a rural county are very different from a major metro |
| **Project** | A container for your analysis | One project can hold multiple events and groups, letting you compare scenarios |
| **Event** | The economic "shock" being analyzed | Defines *what* changed — which industry, and by how much |
| **Group** | Links an Event to a Region and data year | Defines *where* and *when* the event occurs; required to run the model |
| **Run ID** | A unique ID for a single model execution | Each time you run a project, you get a new Run ID and a fresh set of results |

---

## Tips for Using LLMs (ChatGPT, Claude, etc.)

LLMs are excellent companions for API work. Here are the most effective ways to use them with these scripts:

**Paste the error, not just the description.** LLMs diagnose errors much faster when you share the full traceback. Copy everything from `Traceback (most recent call last):` through the final error line.

**Include the relevant code block.** When asking about a specific error, paste the function or section where it occurred — not the entire script. The LLM can then reason about the exact context.

**Ask it to explain API responses.** If you get an unexpected response, paste it and ask "what does this mean?" For example: *"The IMPLAN auth endpoint returned `Bearer eyJ...` as a plain string. Why does `resp.json()` fail on this?"*

**Use it to look up field names and endpoint patterns.** Prompt: *"I'm using the IMPLAN API. Based on this wiki page [paste content], what is the correct request body to create an IndustryOutput event?"*

**Ask it to adapt scripts to new scenarios.** Once you understand the base workflow, you can prompt: *"Modify add-events.py to loop over a list of industries and create one event per industry."* The annotated comments in these scripts give the LLM the context it needs to make accurate modifications.

**Verify suggestions against the official docs.** LLMs can hallucinate API details (wrong field names, incorrect URLs). Always cross-check against the [IMPLAN API Wiki](https://github.com/Implan-Group/api/wiki) before assuming a suggestion is correct.

---

## Repository Structure

```
training-api-examples/
├── python/
│   └── getting started/
│       ├── .env                  # Your credentials (gitignored — never committed)
│       ├── import-requests.py    # Step 1: Authentication reference
│       ├── get-datasets.py       # Step 2: Available data years
│       ├── find-region.py        # Step 3: Geographic region lookup
│       ├── get-industry-codes.py # Step 4: Industry code lookup
│       ├── create-project.py     # Step 5: Create analysis project
│       ├── add-events.py         # Step 6: Add events and groups
│       ├── run-analysis.py       # Step 7: Trigger I-O model
│       └── get-results.py        # Step 8: Retrieve results
├── .gitignore
├── CLAUDE.md
└── README.md
```
