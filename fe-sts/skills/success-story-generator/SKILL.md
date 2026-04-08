---
name: success-story-generator
description: Use when generating STS engagement success stories, writing up customer wins, or documenting post-engagement impact. Triggers on "success story", "customer win", "customer story", "write up a win", "STS win". For working with completed ASQs (Shared Technical Services) and correlating with consumption growth and feature adoption.
user-invocable: true
model: opus
license: Apache-2.0
---

# STS Success Stories

Generate success story documents by correlating completed ASQs with before/after consumption data from `main.field_sts_metrics.gold_shared_asqrelativemetrics`.

**Arguments from invocation:** $ARGUMENTS

**Accepted arguments:** `--account <name>`, `--asq <id>`, `--engineer <name>`, `--top <N>`, `--support-type <type>`, `--period <duration>`

`--period` controls how far back to look for closed ASQs. Accepts `1m` to `12m` for months (e.g., `3m` = 3 months) or `1y` to `5y` for years (e.g., `2y` = 2 years). Use `all` for no time limit. **Default: `3m`**.

## Capabilities

- Query completed ASQs and before/after consumption from the STS metrics gold table
- Score candidates using a 4-criterion rubric (metric relevance, growth magnitude, temporal correlation, engagement depth)
- Map STS service types to the correct $DBU metric columns
- Generate presentation-ready blurbs (3-paragraph Situation/Action/Result format)
- Generate before/after consumption charts with engagement period visualization
- Output as Google Doc, Google Slides, or markdown

## Interactive Menu

**ALWAYS present this menu when the skill is invoked, regardless of whether arguments are provided.** If no arguments are provided, first ask the engineer for filters before showing the menu. Present the filter prompt like this:

```
No arguments provided. What would you like to filter on?

  --asq <id>              Specific ASQ (e.g., AR-000074017)
  --account <name>        Account name
  --engineer <name>       STS engineer name
  --top <N>               Limit results (default: 10)
  --support-type <type>   Filter by service type
  --period <duration>     How far back to look (default: 3m). Examples: 1m, 6m, 1y, 2y, all
```

After collecting the filter flags, confirm them to the user, then show the action menu:

```
What would you like to do?

1. Generate Google Doc        — Full success story document with metrics, blurbs, and scoring
2. Generate Google Slides     — Presentation-ready slide deck with charts and badges
3. Draft Slack Win Post       — Formatted win announcement ready for a channel (show draft first)
4. Send Slack DM              — Send the win summary directly to your Slack DMs
5. Get Customer Feedback      — Search Gmail and Slack for positive customer feedback and thank-you notes
6. Get Win Announcements      — Find Slack posts where account teams tagged you in deal/commit celebrations
7. Score & Rank My ASQs       — Score all your completed ASQs and show top candidates
8. All of the above           — Run the full pipeline: score, generate doc, draft Slack, pull feedback
```

**Rules:**
- **Always show this menu** — even when arguments like `--asq AR-000074017` are provided. Parse the filter flags first, confirm them to the user, then present the menu.
- If the user types a number (e.g., `1`) or a keyword (e.g., `slack`, `feedback`, `score`), map it to the corresponding action.
- Multiple choices are allowed (e.g., `1, 3, 6` or `doc and slack`).
- Option **8** runs Steps 1–5 of the full workflow below and produces all outputs.
- For option **3** (Draft Slack Win Post), show the draft message first and ask for confirmation before posting to a channel.
- For option **4** (Send Slack DM), send immediately to the engineer's DMs — do NOT ask for confirmation.
- For option **5**, search Gmail (via `gmail` skill) and Slack for customer feedback — see Step 2b.
- For option **6**, search Slack for win/commit announcements where the engineer is tagged — see Step 2b.
- For option **7**, run Steps 1–3 (query + score) and display the ranked list without generating docs.

## Workflow

Load `references/METRIC_MAPPINGS.md` at skill start — needed for query construction. Defer loading `references/SCORING.md` until Step 3 and `references/CHART_SPEC.md` until Step 4b to keep context small.

### 1. Resolve Input

Parse `$ARGUMENTS` for named flags:

| Flag | Variable | Description |
|------|----------|-------------|
| `--account <name>` | `$ACCOUNT` | Account name to search |
| `--asq <id>` | `$ASQ_ID` | Specific ASQ (AR-XXXXXX or URL) |
| `--engineer <name>` | `$ENGINEER` | SE name or email |
| `--top <N>` | `$TOP_N` (default: 10) | Limit results |
| `--support-type <type>` | `$SUPPORT_TYPE` | Filter by STS service type |
| `--period <duration>` | `$PERIOD` (default: `3m`) | Only include ASQs closed within this time window from today. `1m`–`12m` for months, `1y`–`5y` for years, `all` for no limit |

**Legacy fallback:** If no `--` flags detected, apply positional heuristic:
- Starts with `AR-` or contains `salesforce.com` → `$ASQ_ID`
- Contains `--top` → last positional arg is SE name → `$ENGINEER`
- Otherwise → try as `$ACCOUNT`, then `$ENGINEER`
- If ambiguous, ask the user.

### 2. Gather Data (PARALLEL)

**CRITICAL: Steps 2a, 2b, 2c, and 2d MUST run in parallel.** Launch all four concurrently — they are independent. Do NOT run them sequentially.

#### 2a. Find Completed ASQs + Consumption (Single Query)

Combine ASQ discovery and before/after consumption into ONE query to eliminate round-trips:

```sql
SELECT
  asq_name, account_name, support_type, additional_services,
  start_date, end_date, owner_name, asq_url,
  months_after_creation, sales_subregion_l1,
  ROUND(total_dollar_consumption_month, 2) AS total_dbus,
  ROUND(dbsql_dollar_dbus, 2) AS dbsql_dbus,
  ROUND(automated_dollar_dbus, 2) AS automated_dbus,
  ROUND(ai_bi_dollar_dbus, 2) AS ai_bi_dbus,
  ROUND(genai_dbu_dollar_dbus, 2) AS genai_dbus,
  ROUND(lakeflow_dollar_dbus, 2) AS lakeflow_dbus,
  ROUND(uc_dollar_dbus, 2) AS uc_dbus,
  ROUND(serverless_dollar_dbus, 2) AS serverless_dbus,
  ROUND(apps_dollar_dbus, 2) AS apps_dbus,
  ROUND(vector_search_dollar_dbus, 2) AS vector_search_dbus
FROM main.field_sts_metrics.gold_shared_asqrelativemetrics
WHERE status = 'Complete'
  AND (<FILTER_CLAUSE>)
ORDER BY asq_name, months_after_creation
```

**Build `<FILTER_CLAUSE>` from parsed flags:**
- `$ACCOUNT` → `account_name LIKE '%<ACCOUNT>%'`
- `$ASQ_ID` → `asq_name = '<ASQ_ID>'`
- `$ENGINEER` → `owner_name LIKE '%<ENGINEER>%'`
- `$SUPPORT_TYPE` → append `AND (support_type LIKE '%<SUPPORT_TYPE>%' OR additional_services LIKE '%<SUPPORT_TYPE>%')`

**Time period filter (ALWAYS applied unless `--period all`):**

Parse `$PERIOD` as free-text into a number of months, then append to the WHERE clause:

```
AND end_date >= DATE_ADD(CURRENT_DATE(), -<N>, 'MONTH')
```

Parse the shorthand: `1m`–`12m` → that many months, `1y`–`5y` → multiply by 12 (e.g., `2y` → 24). If `$PERIOD` is `all`, skip the filter entirely.

**Default:** If `--period` is not specified, default to `3m` (3 months).

This single query returns BOTH the ASQ metadata AND monthly consumption with all key metric columns.

Classify each ASQ using `support_type` + `additional_services` → pick the relevant metric column (see `references/METRIC_MAPPINGS.md`).

#### 2b. Enrich: Glean + Slack + Gmail (PARALLEL within this step)

Launch all searches concurrently:
- **Glean** (via MCP): Search for internal docs, meeting notes, engagement deliverables for the account
- **Slack** (via MCP): Run two targeted searches:
  1. **Win/success announcements mentioning the engineer:** Search for the engineer's Slack user ID (e.g., `<@U07GKLJKP8W>`) in channels like `#emea-gtm`, `#semea_team_all`, `#global-sts`, or win-room channels. These are posts by AEs/SAs celebrating deals where STS contributed — they contain qualitative context, customer feedback, and team shoutouts that enrich the story.
  2. **Commit/deal announcements for the account:** Search for the account name (e.g., `"Enel Group" commit` or `"Enel Group" deal`) to find deal announcements, commit signings, or activation posts. These provide business context like TCV, contract length, and strategic importance.
- **Gmail** (via `gmail` skill): Search received emails for positive customer feedback related to the account or ASQ. Look for:
  1. **Thank-you / feedback emails from customers:** Search for the account name in received emails (e.g., `from:*@enel.com` or `subject:thank`) to find direct customer appreciation, session feedback, or post-engagement follow-ups.
  2. **Internal feedback forwarded by AEs/SAs:** Search for the account name combined with keywords like `feedback`, `thank`, `great work`, `well done`, `appreciate` to find internal emails where account teams share positive customer sentiment.
  These emails often contain the most authentic qualitative quotes for the success story — direct customer voice that Slack and Glean may not capture.

#### 2c. Enrich: Salesforce UCOs

**Salesforce** (via `salesforce-actions` skill):
- UCOs at stages U2-U6 for the account — did they advance post-engagement?
- Account metadata: industry, region, segment

#### 2d. Prepare Chart Environment

Check matplotlib availability and install if needed:
```bash
python3 -c "import matplotlib" 2>/dev/null || uv pip install matplotlib
```

### 3. Score & Rank

Load `references/SCORING.md` now. Apply the 4-criterion scoring rubric:

| Criterion | Max | What It Measures |
|-----------|-----|------------------|
| Metric Relevance | 3 | Did the relevant feature metric grow post-ASQ? |
| Growth Magnitude | 3 | Overall account consumption growth % |
| Temporal Correlation | 2 | Did growth start around the ASQ completion? |
| Engagement Depth | 2 | Effort days, sessions, multi-ASQ accounts |

Compute before/after averages directly from Step 2a results:
- **Pre-ASQ:** `AVG WHERE months_after_creation < 0`
- **Post-ASQ:** `AVG WHERE months_after_creation > 0`
- **Growth multiplier:** post / pre

**Total max: 10.** Rank by score descending, growth % as tiebreaker. When `$TOP_N` is set, keep only the top N results after scoring.

### 4. Generate Output (PARALLEL with Steps 4b and 5)

Start generating output immediately after scoring. Run text output, chart generation, and the duplicate check all in parallel.

#### 4a. Generate Text Output

##### Blurb Format (3-paragraph structure)

**Paragraph 1 — Situation + Action (2-3 sentences):**
Lead with customer name and engagement. Name specific Databricks features and deliverables.

> First Interstate Bank engaged in the Launch Accelerator program to accelerate their migration from Microsoft Fabric, onboarding ETL and data warehousing workloads. By program end, they had a fully private-linked workspace with Unity Catalog governance, declarative YAML pipelines, and a reference Asset Bundle with CI/CD via GitHub Actions.

**Paragraph 2 — Qualitative Result (1-2 sentences):**
What can the customer now do that they couldn't before?

> Phase 1 of the migration is completed with data available up to the silver layer, unblocking adoption across multiple workstreams.

**Paragraph 3 — Quantitative Result (1-2 sentences):**
Specific $DBU metrics with percentage growth tied to the engagement timeline.

> DBSQL $DBUs grew 129% from $5.8K to $13.3K/month (Sep 2025 → Feb 2026), with the inflection point directly following the Lakebridge engagements in December.

##### Full Document Structure

For account-level success stories:

1. **Customer Overview** — Profile, industry, Databricks relationship
2. **STS Engagement Summary** — Completed ASQs, deliverables, timeline, specialists
3. **Challenge** — What the customer needed and what was blocking them
4. **What STS Delivered** — Architecture reviews, Lakebridge sessions, POC support, enablement
5. **Post-Engagement Impact** — Before/after metrics table with growth multipliers + consumption trend chart
6. **Path to Success** — Sustained growth, broadening adoption, active UCO pipeline
7. **Key Metrics** — Summary table of before/after $DBU numbers

##### Slide Badge Population

When generating Google Slides output, populate the 4 header badges using `templates/databricks_slide_template.md`:

| Badge | Source |
|-------|--------|
| 1 | Current month (e.g., "March 2026") |
| 2 | `sales_subregion_l1` + `account_name` from query (e.g., "AMER West – Acme Corp") |
| 3 | `owner_name` from query |
| 4 | `asq_url` + `support_type` from query |

##### Output Destination

Create a Google Doc via the `google-docs` skill. Fall back to markdown if unavailable.

#### 4b. Generate Consumption Charts (PARALLEL — one per ASQ)

Load `references/CHART_SPEC.md` for the JSON schema. For each top-ranked ASQ (up to `$TOP_N`):

1. **Transform Step 2a data** into chart input JSON:
   - Group rows by `months_after_creation` for this ASQ
   - Extract the primary metric column (from METRIC_MAPPINGS)
   - Set `engagement_start_month = 0`, `engagement_end_month = DATEDIFF(month, start_date, end_date)`
   - Optionally add `secondary_data` with `total_dollar_consumption_month`

2. **Write JSON** to `/tmp/chart_data_<asq_name>.json`

3. **Run chart generation** (all ASQs in parallel):
```bash
python3 scripts/generate_chart.py --input /tmp/chart_data_<asq_name>.json --output /tmp/chart_<asq_name>.png
```

4. **Embed chart** in the output:
   - Google Slides: upload PNG to Drive via `google-drive-upload`, insert as image in Option B area
   - Google Doc: upload PNG, insert inline after "Post-Engagement Impact" section
   - Markdown: reference as `![Chart](/tmp/chart_<asq_name>.png)`

5. **Fallback** (no matplotlib): generate a text-based table with trend arrows (see CHART_SPEC.md)

### 5. Check Existing Stories (runs in PARALLEL with Step 4)

Check the **STS Success Stories slide deck** to flag duplicates:
- Read `go/amer-sts-wins` via the Google Slides skill
- If the same account/service is already documented, append a note to the output

### 6. Slack DM Win Summary (Optional — Ask First)

After the success story Google Doc is created, **ask the engineer**:

> "Would you like me to send you the win summary as a Slack DM?"

**If the engineer says no**, skip this step entirely.

**If the engineer says yes**, send the win summary directly to the engineer's Slack DMs using `chat.postMessage`:

```
mcp__slack__slack_write_api_call: chat.postMessage
{
  "channel": "<engineer's Slack user ID>",
  "text": "<formatted win message>"
}
```

#### Win Message Format

```
:tada: *STS Win — {Account Name}*

*Service Type:* {support_type}
*Engineer:* {owner_name}
*Growth:* {GROWTH_PCT}% ({metric_label}: ${pre_avg:,.0f} → ${post_avg:,.0f}/mo)
*ASQ:* {asq_name} ({start_date} → {end_date})

{3-paragraph blurb from Step 4a}

:page_facing_up: <{google_doc_url}|Full Success Story>
```

#### Important

- Always show the draft message to the engineer and get confirmation before sending
- The DM gives the engineer a personal copy they can forward or use to post in a channel themselves

## Parallelization Map

```
Step 1: Resolve Input (parse flags)
  |
  +---> Step 2a: Combined ASQ + Consumption query     ← PARALLEL
  +---> Step 2b: Glean + Slack searches                ← PARALLEL
  +---> Step 2c: Salesforce UCOs                       ← PARALLEL
  +---> Step 2d: Check matplotlib availability          ← PARALLEL
  |
Step 3: Score & Rank (after all Step 2 complete)
  |
  +---> Step 4a: Generate text output                  ← PARALLEL
  +---> Step 4b: Generate charts (N parallel)          ← PARALLEL
  +---> Step 5: Check Existing Stories                  ← PARALLEL
  |
Step 6: Send Slack DM Win Summary (after Step 4a, if engineer opts in)
```

**Performance targets:**
- Single combined SQL query eliminates 2-3 round-trips to Logfood
- `--support-type` filter pushed to SQL WHERE clause — DB-side filtering reduces data transfer
- All enrichment (Glean, Slack, Salesforce) runs concurrently with the main query
- Chart env check runs concurrently — no delay if matplotlib already installed
- Output generation, chart rendering, and duplicate check all start immediately after scoring
- Multiple charts generated in parallel (one python process per ASQ)
- `references/SCORING.md` and `references/CHART_SPEC.md` loaded on-demand, not at skill start
- Total wall-clock time dominated by single SQL query (~10-20s) + chart generation (~5s)

## Examples

### Example: Generate a success story for a specific account
User says: `/success-story --account MetLife`
Result: Finds all completed ASQs for MetLife, pulls before/after consumption from the gold table, scores each engagement, generates consumption charts, and creates a Google Doc with the top stories ranked by impact.

### Example: Write a blurb for a specific ASQ
User says: `/success-story --asq AR-000106066`
Result: Looks up the ASQ, identifies it as a Lakebridge Converter engagement, pulls DBSQL $DBU consumption before/after, generates a time-series chart with engagement period shaded, and outputs a 3-paragraph presentation-ready blurb.

### Example: Find top candidates for an SE filtered by service
User says: `/success-story --engineer "Andres Garcia" --support-type "Data Warehousing" --top 3`
Result: Finds all completed Data Warehousing ASQs owned by Andres Garcia, scores each against the 4-criterion rubric, generates charts for the top 3, and produces a ranked list with consumption tables and blurbs.

### Example: Legacy positional syntax
User says: `/success-story Andres Garcia --top 5`
Result: Detects no `--account`/`--asq`/`--engineer` flags, applies heuristic (not AR- prefix → tries account, then SE), finds matches for "Andres Garcia" as SE, and returns top 5 candidates.
