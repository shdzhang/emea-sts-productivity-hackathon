# EMEA STS Productivity Hackathon — Pillar 3

Clone of [fe-sts](https://github.com/databricks-field-eng/vibe/tree/main/plugins/fe-sts) from the Vibe plugin marketplace, plus [sts-success-stories](https://github.com/databricks-eng/plugin-marketplace/tree/main/experimental/teams/fe-sts/sts-success-stories) from the experimental plugin marketplace.

**Goal:** Extend the fe-sts plugin to cover the complete STS engagement lifecycle — from triage to success story — with AI-driven automation at every step.

**Team:** 5 people | **Duration:** 1 day | **Platform:** [go/vibe](https://github.com/databricks-field-eng/vibe) Claude Code plugins

---

## ASQ Lifecycle — AI Automation Map

```mermaid
graph TD
    A["<b>New ASQ Arrives</b>"] --> B

    subgraph B["1 - TRIAGE"]
        B1["Validate UC Stage"] --> B2["Check Consumption"]
        B2 --> B3["LLM Scope Scoring"]
        B3 --> B4["Auto-Assign to Engineer"]
    end

    B --> I

    subgraph I["2 - INTAKE"]
        I1["Extract SFDC Data"] --> I2["Classify Engagement"]
        I2 --> I3["Create Knowledge Base"]
    end

    I --> C

    subgraph C["3 - ONBOARDING"]
        C1["Create Slack Channel → Invite AT → Update SFDC"]
    end

    C --> D

    subgraph D["4 - ENGAGEMENT LOOP"]
        D1["Meeting Prep"] --> D2["Customer Meeting"]
        D2 --> D3["Post-Meeting Actions"]
        D3 -.-> D1
    end

    D --> E

    subgraph E["5 - CLOSE"]
        E1["Consumption Analysis"] --> E2["STAR Close Notes"]
        E2 --> E3["Update SFDC + Slack"]
    end

    E --> F

    subgraph F["6 - SUCCESS STORY"]
        F1["Score Worthiness"] --> F2["Generate Narrative + Charts"]
        F2 --> F3["Publish to Docs + Slack"]
    end

    KB[("KNOWLEDGE BASE\n(Google Drive)\nCONTEXT + STATUS docs")]
    I -- "creates" --> KB
    D -- "reads & writes" --> KB
    E -- "reads" --> KB
    F -- "reads" --> KB

    G["SCHEDULER  ⏳ Planned"] -.->|"auto-triage"| B
    G -.->|"daily prep"| D
    G -.->|"weekly digest"| E

    style B fill:#2e7d32,color:#fff,stroke:#1b5e20,stroke-width:3px
    style I fill:#00695c,color:#fff,stroke:#004d40,stroke-width:3px
    style C fill:#1565c0,color:#fff,stroke:#0d47a1
    style D fill:#6a1b9a,color:#fff,stroke:#4a148c
    style E fill:#e65100,color:#fff,stroke:#bf360c,stroke-width:3px
    style F fill:#c62828,color:#fff,stroke:#b71c1c,stroke-width:3px
    style KB fill:#f9a825,color:#000,stroke:#f57f17,stroke-width:3px
    style G fill:#37474f,color:#fff,stroke:#263238
    style A fill:#424242,color:#fff,stroke:#212121
```

### Key Innovation: Shared Knowledge Base

The `asq-intake` skill creates a **per-ASQ Google Drive workspace** that serves as a shared knowledge base for all downstream skills. Each skill in the lifecycle reads from and writes back to this workspace, building a cumulative context that gets richer over time:

| Lifecycle Phase | Reads from KB | Writes to KB |
|----------------|---------------|--------------|
| **Intake** | — | Creates CONTEXT doc (ASQ details, CAST, classification) + STATUS doc + folder structure |
| **Meeting Prep** | CONTEXT doc for engagement background, past session notes | — (read-only) |
| **Post-Meeting** | CONTEXT for context, STATUS for current phase | Session notes to sessions/, updated STATUS |
| **Close** | Full engagement history from CONTEXT + sessions/ | Final close notes, outcome summary |
| **Success Story** | CONTEXT + consumption data + session history | Published story draft to research/ |

This means every skill has full context without re-querying SFDC or Slack — and the knowledge base grows with every interaction. Google Drive IDs are stored in the CONTEXT doc so any agent can locate resources programmatically.

---

## Hackathon Deliverables

| Phase | Idea | Owner | Skill | Status | Description |
|-------|------|-------|-------|--------|-------------|
| 1 | **ASQ Auto-Triage** | Shidong Zhang | `asq-triage` | **Done** | Automates the full triage decision tree: UC stage validation, consumption checks, LLM scope scoring, competency-matrix assignment. Reduces 10-15 min/ASQ to seconds. |
| 2 | **ASQ Intake** | Aleksandra Stanojevic | `asq-intake` | **Done** | Extracts ASQ data from Salesforce, classifies the engagement, and creates a shared Knowledge Base (Google Drive workspace with CONTEXT and STATUS docs). |
| 3 | **Enhanced Meeting Prep** | Nadja Bulajic | `asq-refresher` | **Done** | Rewrites the refresher from a 4-step sequential flow to a 5-step parallel enrichment workflow with DBRA deep research, Logfood consumption metrics, Genie trends, and LLM synthesis into executive-ready briefs. ([PR #1](https://github.com/shdzhang/emea-sts-productivity-hackathon/pull/1)) |
| 4 | **Post-Meeting Actions** | TBD | `asq-update` | Planned | Extend with customer follow-up emails, structured action-item extraction, next-meeting scheduling, and UCO stage updates. |
| 5 | **Success Story Generator** | Nada El Atlassi | `success-story-generator` | **Done** | Adapted from [sts-success-stories](https://github.com/databricks-eng/plugin-marketplace/tree/main/experimental/teams/fe-sts/sts-success-stories) with improved scoring rubric, metric mappings, chart generation, and Google Docs publishing. |
| — | **ASQ Scheduler** | TBD | `asq-scheduler` | Planned | Scheduling infrastructure to automate skill invocation on a cadence (triage every 2h, daily meeting prep, weekly digest). |

> **Note:** `asq-triage` (Idea 1), `asq-refresher` (Idea 2), `success-story-generator` (Idea 4), and `asq-intake` (Idea 6) have been implemented. The other skills currently contain their original fe-sts v2.0.2 code and will be updated in-place once hackathon implementations are ready.

### What Already Existed (fe-sts v2.0.2)

| Skill | Purpose |
|-------|---------|
| `asq-onboarding` | Discover new ASQs, create Slack channels, invite AT, update SFDC |
| `asq-update` | Draft SFDC notes + CAST + Slack messages after meetings |
| `asq-refresher` | Meeting brief from SFDC, Slack, Calendar, Gmail, Obsidian |
| `asq-close` | Close ASQs with consumption analysis and STAR-format notes |
| `asq-local-cache` | Local YAML cache + user config + preferences management |

### What This Hackathon Adds

| Skill | What's New |
|-------|-----------|
| `asq-triage` | **Brand new** — full triage automation with 8-phase workflow, 5 reference docs, LLM scope scoring, competency-matrix assignment |
| `asq-refresher` | **Done** — rewritten with parallel DBRA + Logfood + Genie enrichment, LLM synthesis, brief template, graceful degradation ([PR #1](https://github.com/shdzhang/emea-sts-productivity-hackathon/pull/1)) |
| `asq-update` | Extended with follow-up emails, action-item extraction, meeting scheduling |
| `success-story-generator` | **Done** — adapted from [sts-success-stories](https://github.com/databricks-eng/plugin-marketplace/tree/main/experimental/teams/fe-sts/sts-success-stories) with improved scoring, metric mappings, chart generation, and Google Docs output |
| `asq-scheduler` | **Brand new** — scheduling infrastructure for automated skill invocation |
| `asq-intake` | **Done** — brand-new skill: SFDC extraction, engagement classification, Google Drive workspace creation with CONTEXT + STATUS docs |

---

## Improvements Over Original Code

Detailed comparison of hackathon deliverables against the [upstream fe-sts v2.0.2](https://github.com/databricks-field-eng/vibe/tree/main/plugins/fe-sts).

### Idea 1: ASQ Auto-Triage — `asq-triage` (Shidong Zhang) ✅

**Before:** No triage skill existed. Triage was entirely manual — the manager opened each new ASQ, checked UC stages in SFDC, verified consumption in Logfood, judged scope from the description, looked up the competency matrix spreadsheet, checked team workload, and posted Chatter comments one by one.

**After:** Brand-new 210-line SKILL.md with 8 automated phases and 5 reference docs:

| Capability | Before (manual) | After (asq-triage) |
|-----------|-----------------|---------------------|
| UC stage validation | Open each ASQ, navigate to UCO junction object, check stage manually | Batch SOQL query on `Approved_UseCase__c`, auto-apply U3+/U4+ rules |
| Consumption check | Log into Logfood/Genie, look up account, compare against threshold | Automated query with $1K threshold, LA-to-Core conversion detection |
| Scope scoring | Read description, make subjective judgment | LLM scores 1-10 using rubric in `triage-rules.md`, checks against cached service scope |
| Team assignment | Open competency matrix spreadsheet, check each person's workload in SFDC | 3-factor formula (skills 50% + workload 30% + experience 20%) from `competency-matrix.md` |
| Chatter comments | Copy/paste templates, manually tag users with SFDC IDs | 7 templates in `comment-templates.md`, auto-populated with ASQ-specific data |
| Under Review follow-up | Remember to go back and check stale ASQs | Phase 1b: batch query + 5-step re-triage process |
| Batch processing | One ASQ at a time | All new ASQs triaged together, grouped by action type for review |

**New files:** `SKILL.md`, `references/triage-rules.md`, `references/competency-matrix.md`, `references/comment-templates.md`, `references/sfdc-schema.md`, `references/cache-setup.md` (6 files, ~750 lines total)

---

### Idea 2: Enhanced Meeting Prep — `asq-refresher` (Nadja Bulajic) ✅

**Before (73 lines):** 4-step sequential workflow — gather from SFDC/Calendar/Gmail/Obsidian, fetch Slack history, fetch STS content, format a basic brief with raw field dumps.

**After (199 lines + 121-line template):** 5-step parallel enrichment workflow with LLM synthesis.

| Capability | Before (v2.0.2) | After (hackathon) |
|-----------|-----------------|-------------------|
| Data sources | 5 (SFDC, Calendar, Gmail, Slack, Obsidian) | 9 (+ DBRA, Logfood, Genie, Glean) |
| Enrichment model | Sequential — each step waits for the previous | Parallel — all 5 enrichment calls issued simultaneously |
| Consumption data | None | Logfood 30-day spend by product + 30d vs prior 30d growth trend (gated to LA/GA ASQs only) |
| Internal research | None | DBRA deep search: escalations, engineering blockers, internal discussions |
| Genie metrics | None | Account consumption summary from STS Genie Space |
| Output format | Raw field listing (ASQ Context, Action Items table) | LLM-synthesized executive brief with structured template |
| Brief template | None — hardcoded format in SKILL.md | Dedicated `references/brief-template.md` with 7 sections |
| New sections | — | Executive Summary, Meeting Timeline, Meeting Recap, Consumption Summary, Internal Context, Key Contacts |
| Source attribution | None | Every fact tagged with `[SFDC]`, `[Slack]`, `[Logfood]`, `[DBRA]`, etc. |
| Graceful degradation | "present what you have if a source errored" (1 line) | Each source fails independently with specific fallback messages |
| Output routing | Terminal only | Terminal (default) + Google Doc + Slack (on request) |
| Contradiction detection | None | Flags when sources disagree |

**Changed files:** `SKILL.md` (73 → 199 lines), new `references/brief-template.md` (121 lines)

---

### Idea 3: Post-Meeting Actions — `asq-update` (TBD) ⏳

**Before (119 lines):** 7-phase workflow — gather context, draft SFDC status note, check if CAST needed, draft Slack message, present for approval, apply updates, optional Obsidian sync.

**Planned improvements:**
- Customer follow-up emails via Gmail skill with templates by meeting type
- LLM extraction of structured action items with owners and deadlines from raw meeting notes
- Next-meeting scheduling via Google Calendar FreeBusy
- UCO stage progression suggestions based on meeting outcomes

---

### Idea 4: Success Story Generator — `success-story-generator` (Nada El Atlassi) ✅

**Before:** The [sts-success-stories](https://github.com/databricks-eng/plugin-marketplace/tree/main/experimental/teams/fe-sts/sts-success-stories) plugin existed in the experimental marketplace but was disconnected from the main ASQ lifecycle. Engineers had to manually invoke it separately and decide which ASQs were story-worthy.

**After:** Adapted and improved into a 350-line SKILL.md with 5-phase workflow, 3 reference docs, and a chart generation script (772 lines total):

| Capability | Before (manual) | After (success-story-generator) |
|-----------|-----------------|--------------------------------|
| Story-worthiness evaluation | Subjective gut feel | 4-criterion scoring rubric (max 10 points): Metric Relevance, Growth Magnitude, Temporal Correlation, Engagement Depth (`SCORING.md`) |
| Consumption data | Manually query Logfood/Genie | Automated queries against `gold_shared_asqrelativemetrics` with 30+ metric columns (`METRIC_MAPPINGS.md`) |
| Narrative generation | Write from scratch | LLM-generated 3-paragraph blurb (Situation/Action/Result) from ASQ context |
| Charts | Manual screenshot or no chart | `generate_chart.py` produces styled consumption PNGs per `CHART_SPEC.md` |
| Output | Email or Slack paste | Google Docs with formatted narrative + embedded charts |
| Red flag detection | None | Auto-skip if usage flat/declining, spike-only, or insufficient post-engagement data |

**New files:** `SKILL.md`, `references/SCORING.md`, `references/METRIC_MAPPINGS.md`, `references/CHART_SPEC.md`, `scripts/generate_chart.py` (5 files, ~772 lines total)

---

### Idea 5: ASQ Scheduler — `asq-scheduler` (TBD) ⏳

**Before:** No scheduling existed. Every skill had to be manually invoked by the user.

**Planned:** launchd-based scheduling infrastructure to automate skill invocation on a cadence (triage every 2h during business hours, daily meeting prep at 8 AM, weekly portfolio digest on Mondays).

---

### Idea 6: ASQ Intake — `asq-intake` (Aleksandra Stanojevic) ✅

**Before:** No intake skill existed. Engineers manually looked up ASQ details in Salesforce, created Google Drive folders by hand, and wrote CONTEXT/STATUS docs from scratch. Each skill operated in isolation with no shared state.

**After:** Brand-new 342-line SKILL.md with 6-phase workflow that introduces the **shared knowledge base** pattern — the most innovative part of the hackathon:

| Capability | Before (manual) | After (asq-intake) |
|-----------|-----------------|---------------------|
| ASQ lookup | Navigate SFDC, find the ASQ record | Direct lookup by AR number or customer name search with multi-match selection |
| Account data | Manually pull consumption, workspaces, contract info from account page | Automated extraction of DBU consumption (30d/60d), workspace list, consumption mode breakdown |
| Engagement classification | Subjective assessment | LLM classifies pillar, service type, engagement format, and estimated complexity |
| CAST framework | Write from scratch in a doc | Auto-populated from ASQ description with explicit "to be refined" markers for incomplete elements |
| Google Drive workspace | Manually create folder, subfolders, docs | Auto-creates `AR-XXXXX_CustomerName/` with research/, sessions/, code/, comms/ subfolders |
| CONTEXT + STATUS docs | Write from scratch | Templated Google Docs with ASQ details, CAST, account team, customer profile, classification |
| **Shared knowledge base** | **None — each skill queried SFDC independently** | **Google Drive IDs recorded in CONTEXT doc; all downstream skills read/write to this workspace, building cumulative context across the entire engagement lifecycle** |

**Why this matters:** In the original fe-sts, every skill starts from scratch — querying SFDC, searching Slack, re-gathering the same context. With `asq-intake`, the CONTEXT doc becomes the single source of truth. Meeting prep reads it, post-meeting actions update it, close reads the full history. The knowledge base grows with every interaction, eliminating redundant queries and ensuring no context is lost between sessions.

**New files:** `SKILL.md` (342 lines)

---

## How AI Improves Productivity

Each skill replaces manual, repetitive work with AI-driven automation:

| Manual Process | AI Automation | Time Saved |
|---------------|---------------|------------|
| Read ASQ description, check UC stage in SFDC, verify consumption, decide scope, find available team member, post Chatter comment | `asq-triage` runs all checks in parallel, scores with LLM, proposes assignment — human just approves | **10-15 min/ASQ** |
| Open 5 tabs (SFDC, Slack, Calendar, Gmail, Obsidian), read through history, write notes | `asq-refresher` aggregates all sources in one call, synthesizes an executive brief | **15-20 min/meeting** |
| Type meeting notes, copy to SFDC, rewrite for Slack, draft follow-up email, schedule next meeting | `asq-update` generates all artifacts from raw notes — SFDC, Slack, email, calendar | **10-15 min/meeting** |
| Query consumption data, compare before/after, write STAR notes, decide if story-worthy | `asq-close` + success story auto-analyzes impact, generates narrative with charts | **30-45 min/close** |
| Look up ASQ in SFDC, create Drive folders, write CONTEXT/STATUS docs from scratch | `asq-intake` extracts SFDC data, classifies engagement, creates full workspace in one command | **20-30 min/ASQ** |
| Manually invoke each skill, remember the cadence | `asq-scheduler` automates skill invocation on a schedule (triage, prep, digest) | **30 min/week** |

**Total estimated savings:** ~2-3 hours/week per STS engineer across the EMEA team.

---

## Architecture

All skills follow the same pattern:
- **SKILL.md** — Prompt-driven workflow (no traditional code)
- **references/** — Decision rules, templates, schemas
- **resources/** — Python CLI tools (`asq_tools.py`, `asq_cache.py`, `asq_config.py`)

Skills compose existing Vibe infrastructure: Salesforce CLI, Slack MCP, Google Workspace APIs, Databricks Genie Spaces, Logfood, Glean, and DBRA.

```
fe-sts/
├── .claude-plugin/plugin.json
├── commands/
│   ├── sts-help.md
│   └── sts-config.md
└── skills/
    ├── asq-triage/          ← NEW (Hackathon Idea 1)
    │   ├── SKILL.md
    │   └── references/
    │       ├── triage-rules.md
    │       ├── competency-matrix.md
    │       ├── comment-templates.md
    │       ├── sfdc-schema.md
    │       └── cache-setup.md
    ├── asq-onboarding/      (existing)
    ├── asq-refresher/       ← ENHANCE (Idea 2)
    ├── asq-update/          ← ENHANCE (Idea 3)
    ├── asq-close/           (existing)
    ├── success-story-generator/ ← NEW (Hackathon Idea 4)
    ├── asq-local-cache/     (existing)
    ├── asq-intake/          ← NEW (Hackathon Idea 6)
    └── asq-scheduler/       ← NEW (Idea 5, planned)
```

---

## Source

- fe-sts plugin: [databricks-field-eng/vibe/plugins/fe-sts](https://github.com/databricks-field-eng/vibe/tree/main/plugins/fe-sts)
- success-story-generator: [databricks-eng/plugin-marketplace/.../sts-success-stories](https://github.com/databricks-eng/plugin-marketplace/tree/main/experimental/teams/fe-sts/sts-success-stories)
- Hackathon planning doc: [STS EMEA - April FY26 Hackathon Pillar 3](https://docs.google.com/document/d/1hJRumsQso60yzBb39zToUTB6x4on8iS_4aLkPimgWrc/edit?tab=t.0)
