# EMEA STS Productivity Hackathon — Pillar 3

Clone of [fe-sts](https://github.com/databricks-field-eng/vibe/tree/main/plugins/fe-sts) from the Vibe plugin marketplace.

**Goal:** Extend the fe-sts plugin to cover the complete STS engagement lifecycle — from triage to success story — with AI-driven automation at every step.

**Team:** 5 people | **Duration:** 1 day | **Platform:** [go/vibe](https://github.com/databricks-field-eng/vibe) Claude Code plugins

---

## ASQ Lifecycle — AI Automation Map

```mermaid
flowchart LR
    subgraph TRIAGE["Phase 1: Triage"]
        T1[New ASQ arrives]
        T2[Validate UC Stage]
        T3[Check Consumption]
        T4[Score Scope via LLM]
        T5[Auto-Assign via\nCompetency Matrix]
        T1 --> T2 --> T3 --> T4 --> T5
    end

    subgraph ONBOARD["Phase 2: Onboarding"]
        O1[Create Slack Channel]
        O2[Invite AT + Post Intro]
        O3[Update SFDC + Cache]
        O1 --> O2 --> O3
    end

    subgraph ENGAGE["Phase 3: Engagement Loop"]
        direction TB
        E1[Meeting Prep\n+ DBRA Research]
        E2[Customer Meeting]
        E3[Post-Meeting Actions\nSFDC + Slack + Email]
        E1 --> E2 --> E3
        E3 -.->|next meeting| E1
    end

    subgraph CLOSE["Phase 4: Close"]
        C1[Consumption Analysis\nvia Genie Room]
        C2[Generate Close Notes\nSTAR format]
        C3[Update SFDC + Slack]
        C1 --> C2 --> C3
    end

    subgraph STORY["Phase 5: Success Story"]
        S1[Score Story-Worthiness]
        S2[Generate Narrative\n+ Charts]
        S3[Publish to\nGoogle Docs + Slack]
        S1 --> S2 --> S3
    end

    subgraph SCHED["Scheduling Layer"]
        SC1[Weekly Digest]
        SC2[Auto-Triage every 2h]
        SC3[Daily Meeting Prep]
    end

    T5 ==> O1
    O3 ==> E1
    E3 ==> C1
    C3 ==> S1
    SCHED -.->|automates| TRIAGE
    SCHED -.->|automates| ENGAGE
    SCHED -.->|automates| CLOSE

    style TRIAGE fill:#2e7d32,color:#fff,stroke:#1b5e20
    style ONBOARD fill:#1565c0,color:#fff,stroke:#0d47a1
    style ENGAGE fill:#6a1b9a,color:#fff,stroke:#4a148c
    style CLOSE fill:#e65100,color:#fff,stroke:#bf360c
    style STORY fill:#c62828,color:#fff,stroke:#b71c1c
    style SCHED fill:#37474f,color:#fff,stroke:#263238
```

---

## Hackathon Deliverables

| # | Idea | Owner | Skill | Status | Description |
|---|------|-------|-------|--------|-------------|
| 1 | **ASQ Auto-Triage** | Person 1 | `asq-triage` | **Done** | Automates the full triage decision tree: UC stage validation, consumption checks, LLM scope scoring, competency-matrix assignment. Reduces 10-15 min/ASQ to seconds. |
| 2 | **Enhanced Meeting Prep** | Person 2 | `asq-refresher` | Planned | Upgrade refresher with DBRA deep research, Logfood consumption trends, and Genie Space metrics. Add LLM synthesis for executive-ready briefs. |
| 3 | **Post-Meeting Actions** | Person 3 | `asq-update` | Planned | Extend with customer follow-up emails, structured action-item extraction, next-meeting scheduling, and UCO stage updates. |
| 4 | **Success Story Generator** | Person 4 | `asq-close` | Planned | Hook into close flow: score story-worthiness (4-criterion rubric), auto-generate narrative with consumption charts, publish to Google Docs. |
| 5 | **Scheduling + Weekly Digest** | Person 5 | `asq-digest` | Planned | launchd-based scheduling for all skills + weekly portfolio digest with health scores, risk alerts, and suggested actions. |

> **Note:** Only `asq-triage` (Idea 1) has been implemented so far. The other skills currently contain their original fe-sts v2.0.2 code and will be updated in-place once hackathon implementations are ready.

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
| `asq-refresher` | Enhanced with DBRA + Logfood + Genie parallel agents and LLM synthesis |
| `asq-update` | Extended with follow-up emails, action-item extraction, meeting scheduling |
| `asq-close` | Integrated success-story scoring and generation |
| `asq-digest` | **Brand new** — weekly portfolio digest with scheduling infrastructure |

---

## How AI Improves Productivity

Each skill replaces manual, repetitive work with AI-driven automation:

| Manual Process | AI Automation | Time Saved |
|---------------|---------------|------------|
| Read ASQ description, check UC stage in SFDC, verify consumption, decide scope, find available team member, post Chatter comment | `asq-triage` runs all checks in parallel, scores with LLM, proposes assignment — human just approves | **10-15 min/ASQ** |
| Open 5 tabs (SFDC, Slack, Calendar, Gmail, Obsidian), read through history, write notes | `asq-refresher` aggregates all sources in one call, synthesizes an executive brief | **15-20 min/meeting** |
| Type meeting notes, copy to SFDC, rewrite for Slack, draft follow-up email, schedule next meeting | `asq-update` generates all artifacts from raw notes — SFDC, Slack, email, calendar | **10-15 min/meeting** |
| Query consumption data, compare before/after, write STAR notes, decide if story-worthy | `asq-close` + success story auto-analyzes impact, generates narrative with charts | **30-45 min/close** |
| Manually review each ASQ status, check for overdue items, compile portfolio view | `asq-digest` runs weekly, surfaces risks and suggests actions proactively | **30 min/week** |

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
    ├── asq-close/           ← ENHANCE (Idea 4)
    ├── asq-local-cache/     (existing)
    └── asq-digest/          ← NEW (Idea 5, planned)
```

---

## Source

Cloned from [databricks-field-eng/vibe/plugins/fe-sts](https://github.com/databricks-field-eng/vibe/tree/main/plugins/fe-sts).

Hackathon planning doc: [STS EMEA - April FY26 Hackathon Pillar 3](https://docs.google.com/document/d/1hJRumsQso60yzBb39zToUTB6x4on8iS_4aLkPimgWrc/edit?tab=t.0).
