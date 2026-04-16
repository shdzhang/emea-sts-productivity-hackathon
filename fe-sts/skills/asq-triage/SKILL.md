---
name: asq-triage
description: Triage the ASQ queue — validate UC stages, check consumption, score scope, and assign to team members. Also follows up on Under Review ASQs. Automates the full EMEA STS triage decision tree. Triggers on 'triage ASQs', 'triage queue', 'new ASQ queue', 'assign ASQs', 'review new ASQs', 'follow up ASQs', 'under review ASQs'.
---

# ASQ Triage Workflow

**Announce at start:** "Let me pull unassigned ASQs and run triage checks."

**Script:**
```
ASQ_TOOLS=~/.claude/plugins/cache/fe-vibe/fe-sts/*/skills/asq-local-cache/resources/asq_tools.py
GOOGLE_AUTH=~/.claude/plugins/cache/fe-vibe/fe-google-tools/*/skills/google-auth/resources/google_auth.py
```

**References** (read as needed, not all upfront):
- `references/sfdc-schema.md` — Queue ID, field names, SOQL patterns, gotchas
- `references/triage-rules.md` — UC stage rules, consumption thresholds, scope rubric, out-of-scope patterns, conversion signals, Under Review follow-up rules
- `references/competency-matrix.md` — Assignment scoring formula, rating weights, service-to-type mapping
- `references/comment-templates.md` — All Chatter templates, payload structure, combining multiple issues
- `references/cache-setup.md` — How to fetch/refresh the cached service scope and competency matrix

> **SFDC data is always live** — never cache ASQ queries. Reference data (service scope, competency matrix) is cached locally with a 7-day TTL.

## Prerequisites

User config must exist at `~/asq-local-cache/user_config.yaml`. If any command returns `CONFIG_NOT_FOUND`, run the setup flow in asq-local-cache.

## Phase 0: Load Reference Data (Cached)

Follow `references/cache-setup.md` to check freshness and fetch if stale:
1. Check `~/asq-local-cache/triage/cache_meta.yaml` for timestamps
2. If `sts_service_scope.md` is missing or >7 days old → fetch from Google Slides
3. If `competency_matrix.json` is missing or >7 days old → fetch from Google Sheets
4. If fresh → read directly from cache

If the user says "refresh" or "force refresh", re-fetch both regardless of age.

## Phase 1: Pull Unassigned ASQs

Query SFDC for new ASQs in the EMEA queue. See `references/sfdc-schema.md` for the queue ID, field names, and query pattern.

```bash
python3 $ASQ_TOOLS sfdc-query "SELECT Id, Name, Support_Type__c, Additional_Services__c, Request_Description__c, CreatedBy.Name, CreatedById, Account_Name__c, Status__c, CreatedDate, LastModifiedDate, Urgency__c, Start_Date__c FROM ApprovalRequest__c WHERE OwnerId = '00G8Y000006CaluUAC' AND Status__c = 'New' ORDER BY CreatedDate ASC"
```

If no new ASQs, proceed to Phase 1b.

### Phase 1b: Follow Up on Under Review ASQs

```bash
python3 $ASQ_TOOLS sfdc-query "SELECT Id, Name, Support_Type__c, Additional_Services__c, Request_Description__c, Account_Name__c, CreatedBy.Name, CreatedById, Status__c, LastModifiedDate, Use_Case_defined__c, Urgency__c, Start_Date__c FROM ApprovalRequest__c WHERE OwnerId = '00G8Y000006CaluUAC' AND Status__c = 'Under Review' ORDER BY LastModifiedDate DESC"
```

Follow the 5-step process in `references/triage-rules.md` (Under Review Follow-Up Rules section):
1. Gather Chatter history + batch UC stages
2. Identify each ASQ's original triage issue from the Chatter text
3. Check if the blocking condition is now resolved
4. Categorize into an action (re-triage, reminder, close, no action, etc.)
5. Present the follow-up table with full context

## Phase 2: Validate Use Case Stage

> **CRITICAL: Query the `Approved_UseCase__c` junction object, NOT the lookup fields. See `references/sfdc-schema.md`.**

```bash
python3 $ASQ_TOOLS sfdc-query "SELECT Approval_Request__r.Name, Approval_Request__r.Account_Name__c, Use_Case__r.Name, Use_Case__r.Stages__c, Stage__c, Use_Case_Type__c FROM Approved_UseCase__c WHERE Approval_Request__r.Name IN ('AR-XXXXXX',...) ORDER BY Approval_Request__r.Name"
```

Apply stage requirements from `references/triage-rules.md`:
- **Launch Accelerator** (including "Growth Accelerator for PAYG"): U3+
- **Lakebridge** (Analyzer, Transpiler, Converter): U3+
- **Workspace Setup**: U3+
- **All other Support Types**: U4+

If fail → status "Under Review", post Chatter from `references/comment-templates.md` (Template 1 or 2). **STOP.**

## Phase 3: Check Consumption & Track Fit (Launch Accelerator Only)

Skip for non-LA types. Apply rules from `references/triage-rules.md` (Consumption Threshold section).

Check via logfood-querier or STS Genie Space. If >$1K → "Under Review" + Template 3.

Also check for LA-to-Core and Core-to-LA conversion signals (see triage-rules.md).

## Phase 4: Score Scope (LLM Assessment)

> **CRITICAL: Use LLM judgment, NOT keyword matching.** Read the full description in context. Examples of false positives to avoid:
> - "customer wants to learn best practices for UC Setup" → IS in scope (coaching)
> - "architecture review of their workspace" → IS in scope if L200 guidance
> - "SSA helped previously, now need STS for CI/CD" → IS in scope
> - "Need an SSA to help with Lakeflow setup" → IS in scope (creator used "SSA" generically — actual ask is Lakeflow enablement)
>
> **SSA Mention Rule**: When a description mentions "SSA", do NOT auto-redirect. Check the actual ask against STS services and UC stage. See `references/triage-rules.md` (SSA Mention Handling section). If in scope → assign with a note. If genuinely L400+ → Under Review + Template 6.

### 4a: Scope Score (1-10)

Apply the rubric from `references/triage-rules.md` (Scope Scoring Rubric section). Single score combining SAOR description quality and service alignment.

Compare against the **cached service scope** at `~/asq-local-cache/triage/sts_service_scope.md`. If unavailable, use the keyword mapping fallback in triage-rules.md.

- **Score 1-2** → "Under Review" + Template 4 (No Description). **STOP.**
- **Score 3-4** → "Under Review" + appropriate out-of-scope template. Only flag if the **primary ask** is clearly outside STS scope (see out-of-scope patterns in triage-rules.md). **STOP.**
- **Score 5+** → proceed to Phase 5.

### 4b: Multi-Service & Prerequisites Check

Apply bundling rules from `references/triage-rules.md`. Flag but don't block.

Check prerequisites against the cached service scope. Flag as informational for assignee.

### 4c: Core-to-LA Conversion Check

Check conversion signals from `references/triage-rules.md`. Flag as recommendation, not a block.

## Phase 4d: Check Team Calendar for PTO

Query the EMEA STS team calendar for PTO and public holidays covering the assignment period (this week + next 2 weeks):

```bash
CALENDAR_ID="c_ongptofm03eu3c2dq6r9mr7idc%40group.calendar.google.com"
TOKEN=$(python3 $GOOGLE_AUTH token)
curl -s "https://www.googleapis.com/calendar/v3/calendars/${CALENDAR_ID}/events?timeMin=<TODAY>T00:00:00%2B02:00&timeMax=<TODAY+14>T23:59:59%2B02:00&singleEvents=true&orderBy=startTime&maxResults=50" \
  -H "Authorization: Bearer $TOKEN" \
  -H "x-goog-user-project: gcp-sandbox-field-eng"
```

Use PTO data as a constraint in Phase 6 assignment — do not assign ASQs to team members who are on PTO during the requested start date window. Flag overdue ASQs that would be further delayed by PTO.

## Phase 5: Get Team Workload

> **This phase MUST run before assignment** — workload is a key input to the scoring formula.

Extract team names from the cached competency matrix, then query **each member individually** to handle names with special characters (e.g., diacritics like š, ć, í).

> **CRITICAL: Do NOT use a single `Owner.Name IN (...)` query.** Names with Unicode characters (e.g., "Jovan Višnjić", "Gergelj Kiš") silently return 0 results in a bulk IN clause via the `sf` CLI. Query each team member separately.

```bash
# For EACH team member name from the matrix:
python3 $ASQ_TOOLS sfdc-query "SELECT Owner.Name, Status__c, Support_Type__c, COUNT(Id) cnt FROM ApprovalRequest__c WHERE Owner.Name = '<TEAM_MEMBER_NAME>' AND Status__c IN ('In Progress','On Hold') GROUP BY Owner.Name, Status__c, Support_Type__c"
```

> **Note**: No `RecordType.Name` filter is needed — when querying by individual owner name, the results naturally scope to their ASQs.

**Weighted workload** = `IP_regular×1 + IP_LA×2 + OH_regular×0.5 + OH_LA×1.0`

LA identified by `Support_Type__c` containing "Accelerator". See `references/competency-matrix.md` for the full formula.

## Phase 6: Assign ASQ

Apply the 3-factor scoring formula from `references/competency-matrix.md`:

1. **Skills Match (50%)** — map Support Type to matrix services, score ratings
2. **Workload (30%)** — use weighted load from Phase 5
3. **Experience (20%)** — prefer Experienced for complex ASQs, tenure as tiebreaker

> **CRITICAL: The Assignee must be a specific team member's full name from the competency matrix (e.g., "Anna Sviridova"), NEVER a skill name, service name, or role description.** The output must make clear which person is assigned to which ASQ.

Set status "On Hold", post Chatter Template 7.

## Phase 7: Present All Actions for Review

> **CRITICAL: NEVER update SFDC or post Chatter without explicit user approval.**

### Under Review ASQs

**Group by Chatter template** — show the message once per group, then a table of ASQs.

Typical groups:
- **UC Stage Not Met — non-LA** → Template 1 (same for all)
- **UC Stage Not Met — LA** → Template 2
- **Out of Scope** — Templates 5/6/6b/6c (may need per-ASQ customization)
- **No Description** → Template 4
- **Multiple Issues** → combined numbered message (see comment-templates.md)

Format per group:
```
#### [Group Name] (N ASQs)

Chatter:
> [The exact message, shown once]

| # | ASQ | Account | Type | Urgency | Start Date | [group-specific columns] |
```

### Assign → On Hold ASQs

Chatter is Template 7 for all — show once, then the table:

| # | ASQ | Account | Type | Scope | Urgency | Start Date | Assignee | Weighted Load | Notes |
|---|-----|---------|------|-------|---------|-----------|----------|--------------|-------|

Flag overdue ASQs (Start Date in the past). Shorten urgency: Low/Normal/High/Critical.

### Under Review Follow-Ups

Use the table format from `references/triage-rules.md` (Presentation Format section):

| # | ASQ | Account | Type | Urgency | Start Date | Days UR | Original Issue | Current UC | Last Chatter | Action |

Then the action summary.

### Workload After Assignments

| Team Member | IP | IP-LA | OH | OH-LA | Before (weighted) | +New | After |
|---|---|---|---|---|---|---|---|

## Phase 8: Execute (After Approval)

### Update ASQ Statuses
```bash
python3 -c "import json; json.dump({'Status__c': '<Under Review or On Hold>'}, open('/tmp/asq_triage_<AR>.json','w'))"
python3 $ASQ_TOOLS sfdc-update <ASQ_ID> /tmp/asq_triage_<AR>.json
```

For batch: `python3 $ASQ_TOOLS sfdc-batch-update /tmp/asq_triage_batch.json`

### Post Chatter Comments

Construct payloads per `references/comment-templates.md`, then post:
```bash
python3 $ASQ_TOOLS sfdc-chatter /tmp/asq_chatter_<AR>.json
```

## Summary

| ASQ | Account | Decision | Status Updated | Comment Posted |
|-----|---------|----------|---------------|----------------|
