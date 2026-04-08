---
name: asq-close
description: Close ASQ tickets with automated consumption/impact analysis. Queries Genie Rooms for metrics, compares outcomes against STS service expectations, and generates close notes. Triggers on 'close ASQ', 'close ticket', 'partially complete', 'closing notes', 'wrap up ASQ'.
---

# ASQ Closing Workflow

**Script:**
```
ASQ_TOOLS=~/.claude/plugins/cache/fe-vibe/fe-sts/*/skills/asq-local-cache/resources/asq_tools.py
ASQ_CACHE=~/.claude/plugins/cache/fe-vibe/fe-sts/*/skills/asq-local-cache/resources/asq_cache.py
```

## Prerequisites

User config must exist at `~/asq-local-cache/user_config.yaml`. If any command returns `CONFIG_NOT_FOUND`, run the setup flow in asq-local-cache.

## Phase 1: Prepare Closing Payload

```bash
python3 $ASQ_TOOLS close "<customer name or alias>" [--partial]
```

Returns JSON with: `ar_number`, `sfdc_id`, `support_type`, `payload`, `missing_fields`, `genie_room_id`, `sts_content_index`, `closing_instructions`.

If `missing_fields` is non-empty, prompt the user to choose values (e.g., Platform Admin closures require connectivity/configuration options).

## Phase 2: Gather Context

```bash
python3 $ASQ_TOOLS gather "<customer name or alias>"
```

Use the returned `sfdc` data and Slack history to reconstruct what was done.

## Phase 3: Consumption & Impact Analysis

### 3a: Query Genie Room for Metrics

Use the `genie_room_id` from Phase 1 with the `genie-rooms` skill to query:
- Account consumption trends (before vs. after engagement)
- Feature adoption tied to the support type
- Measurable impact indicators

### 3b: Fetch STS Service Expectations

The `sts_content_index` from Phase 1 has page titles and a search query. Fetch **fresh** content:
1. **Preferred:** Search Glean with the `search_query`
2. **Alternative:** Obsidian MCP or Confluence

Extract: standard deliverables, expected timeline, success criteria.

### 3c: Compare Outcome vs. Expectations

- What was the service supposed to deliver? (STS content)
- What was actually delivered? (status notes, Slack, Obsidian)
- Consumption impact? (Genie metrics)
- If partial: what was not completed and why?

## Phase 4: Draft Close Notes

The `gather` output includes `preferences.close_notes`. Use these:

- **Format**: `preferences.close_notes.format` (default: STAR)
- **Separator**: `preferences.close_notes.separator`
- **Partial tag**: `preferences.close_notes.partial_tag`
- **Template**: `preferences.close_notes.template` — placeholders: `{partial_tag}`, `{sep}`, `{situation}`, `{task}`, `{action}`, `{result}`

Default STAR template:
```
{partial_tag}
{sep}
SITUATION
{sep}
<Context: customer, account, why the ASQ was opened>
{sep}
TASK
{sep}
<What was scoped — reference STS service deliverables>
{sep}
ACTION
{sep}
<What was done — sessions, activities, artifacts>
{sep}
RESULT
{sep}
<Outcome — consumption impact, feature adoption, customer state>
```

## Phase 5: Draft Slack Closing Message

- Use `preferences.slack.closing_template` as base
- Language: Check `slack.language` if `preferences.slack.detect_language` is true
- Tone: Follow `preferences.tone.slack`

## Phase 6: Present ALL Drafts for Review

> **CRITICAL: NEVER post to SFDC or Slack without explicit user approval.**

Present: close notes, Slack message, and any missing field selections.

## Phase 7: Apply Updates

### SFDC Close
```bash
python3 -c "import json; json.dump({...payload...}, open('/tmp/asq_close.json','w'))"
python3 $ASQ_TOOLS sfdc-update <ASQ_ID> /tmp/asq_close.json
```

Fields: `Status__c: Complete`, `Actual_Completion_Date__c: YYYY-MM-DD`, `Request_Closure_Note__c: <notes>`, optionally `PartiallyComplete__c: true` and support-type-specific fields.

### Retroactive CAST (if missing)
```bash
python3 $ASQ_TOOLS sfdc-chatter-read <ASQ_ID> --limit 3
```
If no CAST found, draft one using the asq-update skill's CAST workflow.

### Slack + Cache
```
mcp__slack__slack_write_api_call: chat.postMessage, {"channel": "<id>", "text": "<closing_message>"}
```
```bash
python3 $ASQ_CACHE upsert --ar "AR-XXXXXX" --field status=Complete
```

## Closing Checklist

- [ ] Status Notes up-to-date
- [ ] CAST exists (retroactive if needed)
- [ ] Genie consumption analysis completed
- [ ] Outcome compared against STS expectations
- [ ] SFDC fields set (Status, Date, Close Notes, extras)
- [ ] Slack closing message posted
- [ ] Cache updated
- [ ] Obsidian archived (if enabled)
