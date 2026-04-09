# ASQ Triage Decision Rules

> This file contains only **decision logic** — rules, scoring rubrics, and patterns.
> For SFDC field names, query patterns, and stage codes, see `sfdc-schema.md`.
> For service scope details, see the cached `~/asq-local-cache/triage/sts_service_scope.md`.
> For assignment scoring, see `competency-matrix.md`.

## Use Case Stage Requirements

| Support Type | Minimum UC Stage |
|-------------|-----------------|
| Launch Accelerator (incl. "Growth Accelerator for PAYG") | U3+ |
| Lakebridge (Analyzer, Transpiler, Converter) | U3+ |
| Workspace Setup | U3+ |
| All other Support Types | U4+ |

If no use case is linked, or none meet the stage requirement → Under Review.

---

## Consumption Threshold (Launch Accelerator Only)

LA is for Hunter/Greenfield accounts only. High consumption signals the account is already active.

- **Threshold**: >$1K/month
- **Check period**: Current month AND previous month
- **Pass**: Both months < $1K → PASS
- **Fail**: Either month > $1K → FAIL — recommend Core Services instead

### LA-to-Core Conversion Signals
- Account DBU > $1K for 2+ months
- Customer explicitly wants only one narrow service (not full first-use-case program)
- Customer is doing a competitive evaluation (throwaway POC, not production MVP)

### Core-to-LA Conversion Signals
- Low or zero DBU consumption on a Core Services ASQ
- Single early-stage use case (U3 that could qualify for LA)
- Request is Workspace Setup or UC Setup for a greenfield account
- Description aligns with an LA track

### LA Tracks (for assignment and scoping)
| Track | Keywords / Signals |
|-------|-------------------|
| Unified Analytics BI | ETL, data warehousing, BI reporting, lakehouse, data pipeline, DLT |
| Predictive Analytics / DML | Predictive analytics, ML, machine learning, MLflow, model training |
| GenAI-Powered Solutions | Chatbots, GenAI, LLM, RAG, compound AI |
| Information Extraction | Document processing, information extraction, NLP |

---

## Scope Scoring Rubric (1-10)

Single score combining description quality (SAOR) and service alignment.

A good ASQ description follows the **SAOR** framework:
- **S — Situation**: Current customer state, existing setup, use case stage, industry
- **A — Ask**: What specific help is needed (name the service, describe the technical goal)
- **O — Outcome**: What success looks like (specific milestones, not vague aspirations)
- **R — Readiness**: Customer commitment, right stakeholders identified, prerequisites completed

Score against the **cached service scope** from the Slides deck. If cache is unavailable, use the keyword mapping below as a lightweight fallback.

| Score | Criteria |
|-------|----------|
| 1 | Empty/null description, or only unfilled template placeholders |
| 2 | Single word, "TBD", "N/A" |
| 3-4 | Vague one-liner with no SAOR elements, OR clearly out of scope (break-fix, training-only, hands-on) |
| 5-6 | Has Situation + Ask but missing Outcome/Readiness, OR partially aligned with STS services |
| 7-8 | Good SAOR coverage AND well-aligned with a specific STS service |
| 9-10 | Full SAOR with timeline/stakeholders AND perfect match to a specific STS service |

---

## Out-of-Scope Patterns

| Pattern | Redirect To | Resource / Channel | Example |
|---------|------------|-------------------|---------|
| Hands-on implementation ("build for us") | Professional Services or Partners | — | "Build a Delta Live Tables pipeline for our data" |
| Training, workshops, enablement, "learn about X" | Databricks Academy (free self-paced), DB Demos, Solutions Accelerators | academy.databricks.com | "Train our team of 20 on Databricks fundamentals" |
| L400+ deep architecture reviews, advanced perf tuning | Specialist Solution Architects (SSA) via ASQ | — | "Review our entire Spark cluster architecture" |
| Break-fix, production errors, bugs, outages | Databricks Support | — | "Workspace is giving 403 errors when users try to login" |
| Generic office hours / general Q&A | Not supported — STS does ASQ-specific engagements only | — | "Can we set up weekly office hours for our team?" |
| Full code reviews | Not supported | — | "Review all our notebooks for best practices" |
| DBR version migration | 1:many office hours only (monthly) — no ASQ needed | #dbr-migration-squad | "Migrate all our notebooks from DBR 13 to DBR 15" |

**Important**: Before flagging out-of-scope, always recommend free enablement resources first. STS ASQs should follow enablement, not replace it.

---

## Keyword-to-Service Mapping (Lightweight Fallback)

> Use this only if the cached service scope from the Slides deck is unavailable. The deck has richer detail on each service.

| Keywords / Signals | Service |
|-------------------|---------|
| Workspace, network, security, VPC, VNET, SSO, SCIM | Workspace Setup |
| Governance, UC, metastore, SCIM, catalog, permissions | UC Setup |
| HMS migration, UCX, Hive Metastore, federation | UC Migration |
| CI/CD, DABs, Git, Asset Bundles, Terraform, deployment automation | CI/CD |
| Costs, budgets, system tables, tagging, cluster policies | Observability — Cost & Budget |
| Data monitoring, profiling, SAT, drift detection, LHM | Observability — Data & Platform Health |
| Serverless, NCC, compute upgrade, serverless network | Serverless Upgrade |
| ETL, ingestion, pipelines, Lakeflow, DLT, Declarative Pipelines, CDC, orchestration | Lakeflow |
| Delta optimization, liquid clustering, ZORDER, VACUUM, partitioning, Photon | Delta Optimizations |
| Delta Sharing, JDBC, Power BI, Tableau, Clean Rooms, UniForm, Partner Connect | Data Sharing |
| SQL warehouse, DBSQL, query editor, admin controls, ACLs | DBSQL for Admin/Analyst |
| AI/BI, Genie, Genie space, dashboard, BI dashboard, MS Teams/Slack integration | AI/BI Data Citizen |
| Migration assessment, Lakebridge, workload analysis, Teradata/Snowflake/Redshift | Lakebridge Analyzer |
| Code conversion, transpiler, SQL migration, ETL migration | Lakebridge Transpiler |
| ML pipelines, model training, batch/streaming inference, model serving, AutoML | AI/ML Pipelines |
| GenAI, AI agent, RAG, chatbot, LLM, Vector Search, Agent Bricks, MCP, Lakebase | GenAI Apps |
| MLOps, LLMOps, model deployment automation, CI/CD for ML, MLflow | MLOps/LLMOps |

---

## Multi-Service Bundling Rules

| Type | Rule | Example |
|------|------|---------|
| **Bundleable** (one ASQ OK) | Related platform services that one engineer can deliver | Workspace Setup + UC Setup + CI/CD = Platform Setup Bundle |
| **Sequential** (separate ASQs, one at a time) | Services that depend on each other | Workspace Setup first → then Lakeflow later |
| **Independent** (separate ASQs, can be parallel) | Unrelated services needing different specialists | Lakeflow + GenAI Apps (different engineers) |

Flag bundling issues: "Consider splitting into separate ASQs for unrelated services."

---

## SLA Guidelines

| Urgency | Target to Start Engagement |
|---------|---------------------------|
| Low | 10+ business days |
| Normal | 5–10 business days |
| High / Urgent | < 5 business days |

Account teams should allow at least 5 business days between ASQ creation and desired engagement start date.

---

## Under Review Follow-Up Rules

### Gathering Context

For each Under Review ASQ, gather two pieces of context in parallel:

**Chatter history** — read the last 3 comments:
```bash
python3 $ASQ_TOOLS sfdc-chatter-read <ASQ_ID> --limit 3
```
Response format: each entry has `date`, `author`, and `text` fields. Look for:
- The most recent triage comment (usually from an STS team member)
- Any replies from the creator after that comment
- Whether any team member is already engaged/offering help

**UC stages** — batch query:
```bash
python3 $ASQ_TOOLS sfdc-query "SELECT Approval_Request__r.Name, Use_Case__r.Name, Use_Case__r.Stages__c, Stage__c FROM Approved_UseCase__c WHERE Approval_Request__r.Name IN ('AR-XXXXXX','AR-YYYYYY',...) ORDER BY Approval_Request__r.Name"
```

### Identifying the Original Issue

| Pattern in Chatter | Original Issue |
|-------------------|----------------|
| Mentions "U4 or later" or "use case stage" | UC stage too low |
| Mentions "$1K" or "consuming more than" | Consumption too high (LA) |
| Mentions "hands-on", "support case", "break-fix", "POC" | Scope / out-of-scope |
| Mentions "no request description" or "fill in Situation/Ask" | No description |
| No triage comment — only a forward or FYI | Untriaged (needs proper triage) |

### Checking Resolution

| Original Issue | How to Check |
|---------------|-------------|
| UC stage too low | Compare current `Use_Case__r.Stages__c` against requirement (U4+, or U3+ for LA, Lakebridge, and Workspace Setup). If UC shows "Lost", flag for rejection. |
| No description | Check `Request_Description__c` — is it still empty/template-only? |
| Consumption too high (LA) | Re-check consumption via logfood or Genie |
| Out of scope | Check if `Request_Description__c` was updated with new context since the triage comment date |
| Untriaged | Needs a triage comment — run through Phases 2-4 of the main workflow |

### Action Categories

| Action | Criteria |
|--------|----------|
| **Re-triage → Assign** | Blocking condition is resolved (e.g., UC stage updated to U4+). Run through Phase 5 assignment. |
| **Re-triage → check scope** | UC stage is now met but description may need review (e.g., was flagged as vague). |
| **Needs triage comment** | ASQ was never properly triaged — no triage comment exists. Run through Phases 2-4. |
| **Send reminder** | Blocked 5-15 business days, no creator response. Use Template 8 (follow-up reminder). |
| **Send final reminder** | Blocked 3-6 weeks, no response. Stale. |
| **Consider closing** | Blocked 6+ weeks, no response. Present to reviewer for closure decision. |
| **Consider rejecting** | UC shows "Lost" or account is no longer active. |
| **No action** | Correctly scoped out (e.g., break-fix, hands-on) and creator hasn't updated. |

### Presentation Format

Show one row per Under Review ASQ with full context:

| # | ASQ | Account | Type | Urgency | Start Date | Days UR | Original Issue | Current UC | Last Chatter | Action |
|---|-----|---------|------|---------|-----------|---------|----------------|------------|-------------|--------|

Then show a summary of actions:

| Action | Count | ASQs |
|--------|-------|------|
