---
name: asq-update
description: Update ASQ (Account Specialist Request) tickets on Salesforce with meeting notes, post updates to Slack, and write CAST comments. Use when the user shares meeting results, asks to update an ASQ, write a CAST, or check status. Triggers on 'meeting notes', 'ASQ', 'status update', 'CAST'. For closing ASQs, use asq-close instead.
---

# ASQ Update Workflow

**Script:**
```
ASQ_TOOLS=~/.claude/plugins/cache/fe-vibe/fe-sts/*/skills/asq-local-cache/resources/asq_tools.py
ASQ_CACHE=~/.claude/plugins/cache/fe-vibe/fe-sts/*/skills/asq-local-cache/resources/asq_cache.py
```

## Prerequisites

User config must exist at `~/asq-local-cache/user_config.yaml`. If any command returns `CONFIG_NOT_FOUND`, run the setup flow described in the asq-local-cache skill.

## Phase 1: Gather Context (single Bash call)

```bash
python3 $ASQ_TOOLS gather "<customer name or alias>"
```

Returns JSON with: `cache`, `sfdc` (full ASQ record + UCOs), `calendar`, `obsidian`, `sts_content` (index of searchable page titles), `slack` (metadata), `flags`, `preferences`.

Key fields from `sfdc.asqs[0]`: `Id`, `Name`, `Status__c`, `Support_Type__c`, `Request_Status_Notes__c`, `Request_Description__c`, `CreatedBy.Name`, `CreatedById`, `End_Date__c`.

### Fetch STS Service Content (if needed)

The `sts_content` field contains an index with `pages` (titles) and `search_query`. To get fresh content:
1. **Preferred:** Search Glean with the `search_query`
2. **Alternative:** Use Obsidian MCP or Confluence with the page titles

### Slack History (if needed)
```
mcp__slack__slack_read_api_call: conversations.history, {"channel": "<slack.channel_id>", "limit": 20}
```

## Phase 2: Draft SFDC Status Note (LLM)

The `gather` output includes a `preferences` object. Use these to format correctly:

- **Format**: Use `preferences.status_notes.format` (default: `YYYY-MM-DD: (Meeting Type) <content>`)
- **Order**: `preferences.status_notes.order` (default: newest first)
- **Session numbering**: If `preferences.status_notes.session_numbering` is true, number customer sessions (1st Meeting, 2nd Meeting)
- **Discovery**: If `preferences.status_notes.discovery_is_numbered` is false, don't number discovery sessions
- **Internal syncs**: Label using `preferences.status_notes.internal_sync_label`
- **Language**: Write in `preferences.status_notes.language`, even if user provides notes in another language
- **Tone**: Follow `preferences.tone.sfdc` / `preferences.tone.sfdc_description`

## Phase 3: Determine if CAST is Needed (LLM)

**Only after Discovery with the customer — NEVER after just an Internal Sync.**

If no CAST exists and Discovery has occurred, draft one using `references/cast-format.md`.

To check existing CASTs:
```bash
python3 $ASQ_TOOLS sfdc-chatter-read <ASQ_ID> --limit 3
```

**CAST Structure**: Use sections from `preferences.cast.sections` (default: Context, Ask, Success, Timeline) + C/C section
- **Success** should reference STS service outcomes (fetch from index if needed)
- CC behavior: If `preferences.cast.auto_cc_manager` is true, manager is auto-CC'd. Always CC the SA/AE who created the request (`CreatedById`).

## Phase 4: Draft Slack Message (LLM)

- If `preferences.slack.detect_language` is true, use `slack.language` from gather output
- Tone: Follow `preferences.tone.slack` / `preferences.tone.slack_description`
- Not a verbatim copy of SFDC note — match conversational style of the channel

## Phase 5: Present ALL Drafts for Review

> **CRITICAL: NEVER post to SFDC or Slack without explicit user approval.**

Present SFDC note, CAST (if applicable), and Slack message together. Wait for approval.

## Phase 6: Apply Updates

### SFDC Status Notes
```bash
python3 -c "import json; json.dump({'Request_Status_Notes__c': '<FULL_NOTES>'}, open('/tmp/asq_update.json','w'))"
python3 $ASQ_TOOLS sfdc-update <ASQ_ID> /tmp/asq_update.json
```

### CAST (Chatter Comment)
```bash
# Dry-run preview (default — safe):
python3 $ASQ_TOOLS cast-post <ASQ_ID> \
  --context "<text>" --ask "<text>" --success "<text>" \
  --timeline "item1|item2|item3" --cc "<REQUESTOR_SFDC_ID>"

# Post for real (only after approval):
python3 $ASQ_TOOLS cast-post <ASQ_ID> \
  --context "<text>" --ask "<text>" --success "<text>" \
  --timeline "..." --cc "<REQUESTOR_SFDC_ID>" --confirm
```
Manager is auto-CC'd from config. Timeline bullets separated by `|`.

### Slack
```
mcp__slack__slack_write_api_call: chat.postMessage, {"channel": "<channel_id>", "text": "<message>"}
```

### Cache Update
```bash
python3 $ASQ_CACHE upsert --ar "AR-XXXXXX" --field key=value
```

## Phase 7: Obsidian (Optional)

Check `~/asq-local-cache/obsidian_preference.yaml`. If enabled:
```bash
python3 $ASQ_TOOLS obsidian-patch <AR_NUMBER> "Session Log" "<content>" --account "<AccountName>"
```

## Resources
- `references/cast-format.md`: Chatter API payload template and cast-post usage
