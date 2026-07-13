# IMPLAN API Training Examples

Beginner-friendly scripts that walk through the full IMPLAN API workflow — from authentication to retrieving economic impact results. Each script is self-contained, heavily annotated, and designed to be run one step at a time. Examples are available in both **Python** and **R**.

**API Reference:** https://github.com/Implan-Group/api/wiki  
**Sample Code:** https://github.com/Implan-Group/api  
**LLM Reference:** [LLM_REFERENCE.md](LLM_REFERENCE.md) — context file for AI-assisted development

---

## Who This Is For

Developers and analysts who have IMPLAN API access and want to understand how to drive the API programmatically. No prior API experience is assumed. The scripts and comments are written for a first-time audience.

---

## Prerequisites

**Both languages**
- A valid IMPLAN account with API access enabled

**Python**
- Python 3.9 or later
- `requests` and `python-dotenv` packages (installed in setup below)

**R**
- R 4.1 or later
- `httr2`, `dotenv`, and `readr` packages (installed in setup below)

---

## Setup

**1. Clone the repository**

```bash
git clone https://github.com/Implan-Group/training-api-examples.git
cd training-api-examples
```

**2. Install dependencies**

*Python:*
```bash
python -m venv .venv
```
Activate it:
- Windows: `.venv\Scripts\activate`
- Mac/Linux: `source .venv/bin/activate`

```bash
pip install requests python-dotenv
```

*R:*
```r
install.packages(c("httr2", "dotenv", "readr"))
```

**3. Create your credentials file**

Each series folder has its own `.env` file. Create one in the folder you plan to run — for example, `python/getting started/.env` or `r/getting started/.env`:

```
IMPLAN_USERNAME=you@yourfirm.com
IMPLAN_PASSWORD=yourpassword
```

> The `.env` file is listed in `.gitignore` and will never be committed. Never hardcode credentials in scripts.

---

## Example Series

This repository contains three series of scripts, each available in Python and R. The logic, structure, and output are identical across both languages. Start with **Getting Started** if this is your first time.

---

### Series 1 — Getting Started

**Python:** `python/getting started/` &nbsp;|&nbsp; **R:** `r/getting started/`

The foundational walkthrough. Eight self-contained scripts, each covering one step of the full impact analysis workflow:

```
Authenticate → Get Datasets → Find Region → Get Industry Codes
    → Create Project → Add Events → Run Analysis → Get Results
```

| Step | Python | R | What It Does |
|---|---|---|---|
| 1 | `api-authenticate.py` | `api-authenticate.R` | Exchange credentials for a Bearer token |
| 2 | `get-datasets.py` | `get-datasets.R` | List available data years for your aggregation scheme |
| 3 | `find-region.py` | `find-region.R` | Look up geographic regions (states, counties, MSAs) |
| 4 | `get-industry-codes.py` | `get-industry-codes.R` | Browse industries by code and keyword |
| 5 | `create-project.py` | `create-project.R` | Create the project container for your analysis |
| 6 | `add-events.py` | `add-events.R` | Define an economic event and link it to a region and year |
| 7 | `run-analysis.py` | `run-analysis.R` | Trigger the I-O model and poll for completion |
| 8 | `get-results.py` | `get-results.R` | Retrieve direct, indirect, and induced economic impacts |

Each script prints the ID(s) you need to carry into the next step.

The Python series also includes a bonus script, `find-region-children.py`: it looks up a County and then lists the Zip codes inside it, demonstrating a parent/child region lookup instead of `find-region.py`'s flat, nationwide search.

---

### Series 2 — Sample Analysis

**Python:** `python/sample analysis/` &nbsp;|&nbsp; **R:** `r/sample analysis/`

The same workflow, pre-configured with a concrete example: a $500 million data center investment in Travis County, TX (2024 data, industry code 50). Run these scripts end-to-end to see a complete impact analysis with real numbers.

---

### Series 3 — Region Details

**Python:** `python/region details/` &nbsp;|&nbsp; **R:** `r/region details/`

A six-step workflow for accessing raw regional economic data — employment, output, value added, and input-output structure — without running a full impact analysis. Useful when you need baseline regional statistics rather than impact multipliers.

| Step | Python | R | What It Does |
|---|---|---|---|
| 1 | `step1-authentication.py` | `step1-authentication.R` | Authenticate |
| 2 | `step2-find-region.py` | `step2-find-region.R` | Look up a region by name or type |
| 3 | `step3-create-group.py` | `step3-create-group.R` | Create a project and group to anchor the regional model |
| 4 | `step4-region-overview.py` | `step4-region-overview.R` | Export high-level employment, labor income, and output by industry |
| 5 | `step5-industry-detail.py` | `step5-industry-detail.R` | Export granular industry data (compensation, proprietor income, taxes) |
| 6 | `step6-industry-summary.py` | `step6-industry-summary.R` | Export input-output structure (output, intermediate inputs, value added) |

The Python series also includes a bonus 7th script, `step7-industry-time-series.py`, with no R equivalent yet: it pulls one industry across every state and every published data year, printing an Employment and Output matrix over time.

---

## How the Pieces Fit Together

| Concept | What it is | Why it matters |
|---|---|---|
| **Aggregation Scheme** | How industries are grouped (528 vs 546 sectors) | Must be consistent across all steps — defines the model's industry vocabulary |
| **Dataset** | A specific data year (e.g. 2024) | IMPLAN's regional data is published annually; pick the year matching your analysis period |
| **Region / HashId** | A geographic area (state, county, MSA, ZIP) | The I-O model is region-specific — multipliers for a rural county differ from a major metro |
| **Project** | A container for your analysis | One project can hold multiple events and groups for scenario comparison |
| **Event** | The economic "shock" being analyzed | Defines *what* changed — which industry, and by how much |
| **Group** | Links an Event to a Region and data year | Defines *where* and *when* the event occurs; required to run the model |
| **Run ID** | A unique ID for one model execution | Each run produces a new Run ID and a fresh set of results |

---

## Common Pitfalls

**Project titles must be unique.** The API returns an error if you attempt to create a project with a title that already exists in your account. Every script that creates a project appends a timestamp to `PROJECT_TITLE` for this reason, so re-running them is safe. If you hardcode your own title, re-running without changing it will fail — either update the title or delete the existing project in IMPLAN Cloud first.

**Pass IDs forward carefully.** Each step produces an ID the next step needs. Scripts print a `-->` line at the end to tell you exactly what to copy.

**Aggregation scheme must be consistent.** The scheme ID you choose for datasets must match every subsequent step. Mixing scheme IDs causes silent failures or 400 errors.

**Response formats vary by endpoint.** Authentication returns a plain string, run analysis returns a plain integer, status returns a plain string, and results return CSV. Other endpoints return JSON. If you get a parse error, check `LLM_REFERENCE.md` for the expected format for each endpoint.

**Omit `Content-Type` on GET requests.** The IMPLAN API returns 400 if `Content-Type: application/json` is sent on a GET. Only include it on POST/PUT.

**Small analyses complete before polling starts.** If the status endpoint returns a non-200 response immediately after triggering a run, the analysis finished before the first poll. The Run ID is still valid — go straight to the results script.

---

## Using an LLM to Write or Extend Scripts

LLMs are effective for API scripting tasks. For best results:

- Share `LLM_REFERENCE.md` and `CLAUDE.md` with the LLM as context before asking it to write or modify scripts
- Paste the full traceback when debugging — not just a description of the error
- Ask the LLM to explain unexpected API responses by pasting the raw response
- Always verify field names and endpoint paths against the [IMPLAN API Wiki](https://github.com/Implan-Group/api/wiki) — LLMs can hallucinate API details

See [LLM_REFERENCE.md](LLM_REFERENCE.md) for example prompts, code patterns, and a full API reference designed for LLM context.

---

## Repository Structure

```
training-api-examples/
├── python/
│   ├── getting started/
│   │   ├── README.md                  # Scripts and configurable variables
│   │   ├── .env                       # Your credentials (gitignored)
│   │   ├── api-authenticate.py
│   │   ├── get-datasets.py
│   │   ├── find-region.py
│   │   ├── find-region-children.py    # Bonus: parent/child region lookup (County -> Zip)
│   │   ├── get-region-hashid.py       # Standalone county hashId lookup (undocumented, unverified)
│   │   ├── get-industry-codes.py
│   │   ├── create-project.py
│   │   ├── add-events.py
│   │   ├── run-analysis.py
│   │   └── get-results.py
│   ├── sample analysis/
│   │   ├── README.md                  # Scripts and configurable variables
│   │   ├── .env                       # Your credentials (gitignored)
│   │   └── step1-authentication.py … step7-get results.py
│   └── region details/
│       ├── README.md                  # Scripts and configurable variables
│       ├── .env                       # Your credentials (gitignored)
│       └── step1-authentication.py … step7-industry-time-series.py
├── r/
│   ├── getting started/
│   │   ├── README.md                  # Scripts and configurable variables
│   │   ├── .env                       # Your credentials (gitignored)
│   │   ├── api-authenticate.R
│   │   ├── get-datasets.R
│   │   ├── find-region.R
│   │   ├── get-industry-codes.R
│   │   ├── create-project.R
│   │   ├── add-events.R
│   │   ├── run-analysis.R
│   │   └── get-results.R
│   ├── sample analysis/
│   │   ├── README.md                  # Scripts and configurable variables
│   │   ├── .env                       # Your credentials (gitignored)
│   │   └── step1-authentication.R … step7-get-results.R
│   └── region details/
│       ├── README.md                  # Scripts and configurable variables
│       ├── .env                       # Your credentials (gitignored)
│       └── step1-authentication.R … step6-industry-summary.R
├── LLM_REFERENCE.md                   # AI-assisted development reference
├── CLAUDE.md                          # Claude Code agent instructions
├── .gitignore
└── README.md
```
