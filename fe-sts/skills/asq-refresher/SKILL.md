---
name: asq-refresher
description: Generate an ASQ status brief — what happened, where we are, and what's next. Gathers from SFDC, Slack, Gmail, Calendar, DBRA, Logfood, and Genie. Triggers on 'asq status', 'where are we with', 'what is the status', 'summarize meeting', 'meeting summary', 'last meeting', 'recap meeting', 'next meeting', 'upcoming meeting', 'what do I discuss', 'meeting prep', 'refresh me on', 'prep me for', 'deep refresher', 'account brief', 'full brief'.
---

# ASQ Meeting Refresher

**Announce at start:** "Let me pull together a comprehensive meeting brief for you."

**Script:**
```
ASQ_TOOLS=~/.claude/plugins/cache/fe-vibe/fe-sts/*/skills/asq-local-cache/resources/asq_tools.py
ASQ_CACHE=~/.claude/plugins/cache/fe-vibe/fe-sts/*/skills/asq-local-cache/resources/asq_cache.py
GENIE_ROOMS=~/.claude/plugins/cache/fe-vibe/fe-internal-tools/*/skills/genie-rooms/resources/genie_rooms.py
```

## Prerequisites

User config must exist at `~/asq-local-cache/user_config.yaml`. If any command returns `CONFIG_NOT_FOUND`, run the setup flow in asq-local-cache.

### Optional Dependencies (degrade gracefully if absent)

- **DBRA:** `isaac plugin add dbra@experimental` — deep internal research
- **Logfood auth:** `databricks auth login https://adb-2548836972759138.18.azuredatabricks.net/ --profile=logfood`
- **Genie access:** VPN + go/gtm_genie_access

## Workflow

### Step 1: Gather core context (single Bash call)

```bash
python3 $ASQ_TOOLS gather "<customer name or alias>" [--domain customer-email.com]
```

Returns JSON with: `cache`, `sfdc` (ASQ + UCOs), `calendar`, `gmail`, `obsidian`, `sts_content` (index), `slack` (metadata), `flags`, `hints`, `preferences`.

If `cache_hit` is false, upsert discovered metadata afterward:
```bash
python3 $ASQ_CACHE upsert --ar "AR-XXXXXX" --field key=value
```

After gather completes, extract these identifiers for Step 2:
- `account_name` — from `sfdc.asqs[0].Account__r.Name` or `cache.account_name`
- `slack.channel_id` — for Slack history
- `support_type` — from `sfdc.asqs[0].Support_Type__c`
- `sts_content.search_query` — for Glean STS content fetch
- `sfdc_account_id` — from `cache.sfdc_id` or `sfdc.asqs[0].Account__c`. If not available, resolve it:
  ```bash
  sf data query --query "SELECT Id FROM Account WHERE Name LIKE '%<account_name>%' LIMIT 1" --json
  ```
- `genie_room_id` — use `01f0cae151f512bebb0a4cb3c4bd8312` if support_type is "Growth Accelerator for PAYG", otherwise use default `01f0467310751d7f9fb77993b8e49975`

### Step 2: Parallel enrichment (issue ALL in a single message)

Launch all of the following calls simultaneously in one message. They are independent of each other.

#### 2a: Slack channel history

If `slack.channel_id` is present:
```
mcp__slack__slack_read_api_call: conversations.history, {"channel": "<id>", "limit": 30}
```

If no channel: skip and note "Slack: no channel set up yet."

#### 2b: STS service context

If `sts_content` is present, use the `search_query` to fetch fresh content about expected milestones and deliverables:
1. **Preferred:** Search Glean with the `search_query`
2. **Alternative:** Obsidian MCP or Confluence with page titles

If unavailable: skip and note "STS content: unavailable."

#### 2c: DBRA deep research

Invoke the DBRA skill:
```
/dbra "Internal context for <account_name>: recent escalations, engineering blockers, support tickets, internal discussions about this customer's <support_type> engagement, any strategic notes or account plans"
```

If DBRA is not installed or returns an error: skip and note "DBRA: unavailable — install with `isaac plugin add dbra@experimental`."

#### 2d: Logfood consumption metrics

Check auth first:
```bash
databricks auth profiles | grep logfood
```

If authenticated, select a warehouse and run two queries against `main.fin_live_gold.paid_usage_metering`. Replace `<ACCOUNT_ID>` with the SFDC Account ID from Step 1.

**Query 1 — Current 30-day spend by product:**
```sql
SELECT
  product_type,
  ROUND(SUM(usage_dollars), 2) AS dollars,
  ROUND(SUM(usage_dollars) / SUM(SUM(usage_dollars)) OVER () * 100, 1) AS pct
FROM main.fin_live_gold.paid_usage_metering
WHERE sfdc_account_id = '<ACCOUNT_ID>'
  AND date >= DATEADD(DAY, -30, CURRENT_DATE())
  AND paying_status = 'PAYING_STATUS_PAYING'
GROUP BY product_type
ORDER BY dollars DESC
```

**Query 2 — 30-day vs prior 30-day growth trend:**
```sql
WITH monthly AS (
  SELECT
    product_type,
    SUM(CASE WHEN date >= DATEADD(DAY, -30, CURRENT_DATE()) THEN usage_dollars ELSE 0 END) AS current_30d,
    SUM(CASE WHEN date >= DATEADD(DAY, -60, CURRENT_DATE()) AND date < DATEADD(DAY, -30, CURRENT_DATE()) THEN usage_dollars ELSE 0 END) AS prior_30d
  FROM main.fin_live_gold.paid_usage_metering
  WHERE sfdc_account_id = '<ACCOUNT_ID>'
    AND date >= DATEADD(DAY, -60, CURRENT_DATE())
    AND paying_status = 'PAYING_STATUS_PAYING'
  GROUP BY product_type
)
SELECT
  product_type,
  ROUND(prior_30d, 2) AS prior_30d,
  ROUND(current_30d, 2) AS current_30d,
  ROUND(current_30d - prior_30d, 2) AS delta,
  CASE WHEN prior_30d > 0 THEN ROUND((current_30d - prior_30d) / prior_30d * 100, 1) ELSE NULL END AS pct_change
FROM monthly
WHERE current_30d > 0 OR prior_30d > 0
ORDER BY ABS(current_30d - prior_30d) DESC
```

Execute via:
```bash
databricks api post /api/2.0/sql/statements/ --profile=logfood --json='{"statement": "<SQL>", "warehouse_id": "<id>", "format":"JSON_ARRAY", "wait_timeout":"50s"}'
```

If Logfood auth fails or queries error: skip and note "Logfood: unavailable — run `databricks auth login https://adb-2548836972759138.18.azuredatabricks.net/ --profile=logfood`."

#### 2e: Genie room metrics

```bash
python3 $GENIE_ROOMS --room-id <genie_room_id> --profile logfood ask "Account consumption summary for <account_name>: total spend, top products, month-over-month trend, and any notable changes in the last 12 months"
```

If Genie times out (>120s) or returns an error: skip and note "Genie: unavailable." Logfood data from 2d provides a fallback for consumption metrics.

### Step 3: LLM Synthesis

Using ALL data gathered in Steps 1 and 2, synthesize a meeting brief following the template in `references/brief-template.md`.

Key synthesis rules:
- **Cross-reference and deduplicate** — same fact from multiple sources should appear once
- **Executive Summary is 2-3 sentences max** — a quick orientation on what the ASQ is about and its current state, not a deep dive
- **Meeting Recap sourced by priority** — populate from: (1) meeting notes (Obsidian, Slack thread, Gmail follow-up), (2) DBRA (internal Slack discussions, Confluence, support tickets), (3) SFDC status notes, (4) SFDC description as fallback. Cross-reference across sources and organize into numbered topics
- **Meeting Timeline replaces ASQ Context** — build from Calendar events and SFDC status notes, but ONLY include meetings where the current user was an attendee. Bold the row for the meeting this refresher was triggered for
- **Consumption Summary only for Launch/Growth Accelerator** — only include Consumption Summary section if `support_type` is "Growth Accelerator for PAYG" or "Launch Accelerator". For all other ASQ types, skip consumption entirely
- **Integrate DBRA context into relevant sections** — an escalation goes into Next Steps & Open Risks, not just the Internal Context section
- **Tag facts with source** — use `[SFDC]`, `[Slack]`, `[Gmail]`, `[Logfood]`, `[Genie]`, `[DBRA]`, `[Glean]`, `[Calendar]`, `[Obsidian]`
- **Flag contradictions** — if sources disagree, call it out explicitly
- **Next Steps & Open Risks as one table** — merge open items, risks, and next meeting agenda into a single table with a Notes column for additional context. Order by risk (High first). Only include items directly tied to the ASQ scope
- **No inferred items** — do not add "Create Slack channel" unless explicitly requested in SFDC/Slack. Do not add language preferences or cultural notes unless in the ASQ description

### Step 4: Present brief

Display the synthesized brief in the terminal.

At the bottom, include a data sources footer showing which sources contributed and which were unavailable.

### Step 5: Output routing (conditional — only if user requests)

If the user explicitly asks for Google Doc or Slack output:

**Google Doc:**
1. Write the brief as markdown to `/tmp/asq_brief_<ar_number>.md`
2. Convert:
   ```bash
   python3 ~/.claude/plugins/cache/fe-vibe/fe-google-tools/*/skills/google-docs/resources/markdown_to_gdocs.py \
     --input /tmp/asq_brief_<ar_number>.md \
     --title "Meeting Brief: <account_name> — <date>"
   ```
3. Present the Google Doc URL to the user.

**Slack:**
Post to the ASQ Slack channel:
```
mcp__slack__slack_write_api_call: chat.postMessage, {"channel": "<slack.channel_id>", "text": "<brief in Slack mrkdwn format>"}
```

**NEVER create a Google Doc or post to Slack without explicit user request. Terminal output is the default.**

## Rules

- **Read-only** — no SFDC writes, no Slack posts, no emails (unless output routing in Step 5)
- **Speed over completeness** — present what you have if a source errored
- **Graceful degradation** — each source in Step 2 fails independently; never block the brief because one source is down
- **Deduplicate across sources** — same information from SFDC + Slack + Gmail should appear once
- **Consumption only for Launch/Growth Accelerator ASQs** — skip Logfood/Genie enrichment entirely for other types
- **DBRA results integrated** into relevant sections, not dumped as raw output
- **No inferred actions** — do not suggest Slack channel creation or language considerations unless explicitly in the ASQ description
- **Source attribution** — tag facts with `[SFDC]`, `[Slack]`, `[Logfood]`, `[DBRA]`, etc.
