# CLAUDE.md — RetailIQ: AI-Powered Retail Intelligence & Decision Analytics

This file guides Claude (and any collaborator) working in this repository.
Read it fully before starting any task.

---

## 1. Project Objective

Build an AI-powered retail business intelligence application using the
historical **Walmart M5 Forecasting Competition** dataset.

The finished project must demonstrate **both**:
- **Business intelligence**: clear, decision-oriented views of sales performance.
- **Technical AI capability**: a generative AI copilot that answers business
  questions by generating, validating, and explaining SQL against real data.

---

## 2. Main Components

### 2.1 Executive BI Dashboard
- Estimated product sales value (see Section 4.3 for definition)
- Sales volume (units)
- Category performance
- Geographic comparisons (state and store level)
- Seasonal trends

### 2.2 Advanced Analytics
- Sales decomposition (trend / seasonality / residual)
- Holiday and event shopping patterns
- Category contributions to totals and to change over time
- Price-volume analysis

### 2.3 Generative AI Copilot
- Natural-language-to-SQL over the project's SQLite database
- Validated queries: read-only, schema-checked, safe to execute
- Evidence-backed explanations: every answer shows the SQL used and the
  result rows it is based on
- Business recommendations that are clearly tied to the returned evidence
  and labelled as suggestions, not proven outcomes

### 2.4 AI Evaluation Requirement
Test the copilot against **15–20 independently verified business questions**.
For each question, record:
- SQL execution success
- Numerical accuracy
- Unsupported claims
- Response time

---

## 3. Technology Stack

| Purpose            | Tool       |
|--------------------|------------|
| Language           | Python     |
| Data processing    | Pandas     |
| Database           | SQLite     |
| Application / UI   | Streamlit  |
| Charts             | Plotly     |
| AI copilot         | An LLM API |

Do not add other frameworks (e.g. LangChain, ORMs, web backends, Docker,
cloud services) unless the user explicitly approves them.

---

## 4. Dataset Requirements

### 4.1 Source
Use only the **official Walmart M5 Forecasting competition files** (Kaggle).
Expected files (to be confirmed when the data is obtained):
- `calendar.csv` — dates, weekdays, events, SNAP indicators, week keys
- `sell_prices.csv` — weekly item prices per store
- `sales_train_validation.csv` / `sales_train_evaluation.csv` — daily unit
  sales per item per store
- `sample_submission.csv` — competition submission format (not needed for BI)

Raw files are never edited. Store them unchanged in `data/raw/`.

### 4.2 Data Integrity Validation
Before any analysis, validate and record the results of:
- Row and column counts per file
- Expected keys and uniqueness (e.g. item/store IDs, day columns, week keys)
- Missing values and how they are handled
- Join coverage between sales, calendar, and prices
- Date range and continuity of daily data
- Non-negative unit sales

Record actual observed values only — never assume or copy figures from
external descriptions of the dataset without verifying them on the files.

### 4.3 Estimated Product Sales Value vs. Revenue
- **Estimated product sales value** = units sold × weekly listed sell price
  for that item, store, and week.
- This is an **estimate**. It is **not** audited revenue: it excludes
  discounts, promotions at checkout, returns, taxes, and other adjustments,
  and prices may be missing for some item-weeks.
- The dashboard, copilot answers, and documentation must always use the term
  "estimated product sales value" (or "estimated sales value"), never
  "revenue", and must note this limitation where values are shown.

### 4.4 Transformation Documentation
Every transformation (reshaping, joins, filters, derived columns, missing
value handling) must be documented in `docs/data_transformations.md` with:
- What was done and why
- Input and output tables
- Row counts before and after

---

## 5. Development Timeline

**Four days. Priority: a reliable MVP over extra features.**

| Day | Focus |
|-----|-------|
| 1 | Environment setup, dataset acquisition, validation, and SQLite database |
| 2 | Executive BI Dashboard and core advanced analytics |
| 3 | Generative AI Copilot, natural-language-to-SQL, and query validation |
| 4 | Remaining advanced analytics, AI evaluation, testing, documentation, and deployment if feasible |

If time runs short, cut scope from the end of the list — never cut data
validation or copilot query validation.

---

## 6. Working Instructions for Claude

- **Very small steps.** Break work into the smallest useful units.
- **Explain before implementing.** Describe each task and why it is needed
  before writing code or running commands.
- **Confirm milestones.** Ask for the user's confirmation before moving to
  the next milestone. Do not continue without it.
- **Be exact.** Provide exact filenames, commands, and expected results for
  every step.
- **Stay minimal.** Avoid unnecessary frameworks, abstractions, and features.
- **Never fabricate.** Do not invent data, analytical findings, performance
  metrics, accuracy figures, or business impact. Report only what the code
  and data actually produce; if something is unknown, say so.
- **Maintain the checklist.** Update the progress checklist below as tasks
  are completed.
- **Show both sides.** Keep the project balanced between business
  intelligence value and technical AI capability.

---

## 7. Development Progress Checklist

### Milestone 0 — Project Setup
- [x] Create `CLAUDE.md`
- [ ] Confirm project folder structure
- [ ] Set up Python environment and `requirements.txt`

### Milestone 1 — Data Foundation (Day 1)
- [ ] Obtain official M5 files into `data/raw/`
- [ ] Run and record data integrity validation
- [ ] Reshape and join data; document transformations
- [ ] Compute estimated product sales value
- [ ] Load cleaned tables into SQLite

### Milestone 2 — Executive BI Dashboard (Day 2)
- [ ] Streamlit app skeleton
- [ ] KPI summary: estimated sales value and units
- [ ] Category performance view
- [ ] Geographic comparison view
- [ ] Seasonal trend view

### Milestone 3 — Advanced Analytics (Day 3)
- [ ] Sales decomposition
- [ ] Holiday / event shopping patterns
- [ ] Category contribution analysis
- [ ] Price-volume analysis

### Milestone 4 — Generative AI Copilot (Day 4)
- [ ] LLM API connection (key kept out of source control)
- [ ] Natural-language-to-SQL generation
- [ ] SQL validation (read-only, schema-checked)
- [ ] Evidence-backed explanations (show SQL and results)
- [ ] Business recommendations tied to evidence

### Milestone 5 — Finalization (Day 4)
- [ ] End-to-end testing
- [ ] README with setup and run instructions
- [ ] Final review of documentation and limitations
