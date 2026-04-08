---
name: asq-onboarding
description: Onboard newly assigned ASQs — create Slack channels, invite the AT, post intro messages, add first SFDC status note, and update local cache. Triggers on 'new ASQs', 'onboard ASQs', 'assigned ASQs', 'bootstrap ASQs', 'set up new ASQs'.
---

# ASQ Onboarding Workflow

**Announce at start:** "Let me find your new ASQ assignments and get them set up."

**Script:**
```
ASQ_TOOLS=~/.claude/plugins/cache/fe-vibe/fe-sts/*/skills/asq-local-cache/resources/asq_tools.py
ASQ_CACHE=~/.claude/plugins/cache/fe-vibe/fe-sts/*/skills/asq-local-cache/resources/asq_cache.py
ASQ_CONFIG=~/.claude/plugins/cache/fe-vibe/fe-sts/*/skills/asq-local-cache/resources/asq_config.py
```

## Prerequisites

User config must exist at `~/asq-local-cache/user_config.yaml`. If any command returns `CONFIG_NOT_FOUND`, run the setup flow in asq-local-cache.

## Phase 1: Discover New ASQs

```bash
python3 $ASQ_TOOLS discover-new
```

Returns JSON with `count` and `asqs[]` — each has: `Id`, `Name`, `Account__r.Name`, `Request_Description__c`, `Support_Type__c`, `Start_Date__c`, `End_Date__c`, `CreatedBy.Name`, `CreatedById`, `_cached`.

Present the list. Flag any with future `Start_Date__c`.

## Phase 2: Prepare Per ASQ

### Get Calendar Availability
```bash
python3 $ASQ_TOOLS availability --days 5
```

### Slack Channel Name

Use the channel pattern from preferences:
```bash
python3 $ASQ_CONFIG preferences-show slack
python3 $ASQ_CONFIG preferences-show slugs
```

Default pattern: `ar-{number}-{account_slug}-{type_slug}`. Default slugs: ML & GenAI -> `ml-genai`, Data Engineering -> `data-eng`, Data Warehousing -> `data-wh`, Platform Administration -> `platform-admin`, Streaming -> `streaming`, Data Governance -> `data-gov`. All configurable.

### Intro Message

Use `slack.intro_template` preference. Default:
> Hey @{creator}, created this channel for the {support_type} ASQ for {account}. Could we set up a quick sync? Here are some times that work: {slots}

If `slack.detect_language` is true, check creator's recent messages for language.

### SFDC Status Note

Use `status_notes.format` preference. Default:
> YYYY-MM-DD: Created Slack channel (#channel-name) and reached out to AT. Internal sync to be scheduled.

**Multiple ASQs, same requestor:** Merge into shared channel using `slack.merged_channel_pattern` (default: `sts-support-{account_slug}`).

## Phase 3: Present Drafts for Approval

> **CRITICAL: NEVER create channels, send messages, or update SFDC without explicit approval.**

Show per ASQ: channel name, who to invite, intro message, SFDC note.

## Phase 4: Execute (After Approval)

### Create Slack Channel + Invite
```
mcp__slack__slack_write_api_call: conversations.create, {"name": "<channel_name>", "is_private": false}
mcp__slack__slack_write_api_call: conversations.setTopic, {"channel": "<id>", "topic": "<account> | <type> | AR-<number>"}
mcp__slack__slack_write_api_call: conversations.invite, {"channel": "<id>", "users": "<creator_slack_id>"}
mcp__slack__slack_write_api_call: chat.postMessage, {"channel": "<id>", "text": "<intro_message>"}
```

To find creator's Slack ID:
```
mcp__slack__slack_read_api_call: users.lookupByEmail, {"email": "<creator_email>"}
```

### Update SFDC
```bash
python3 -c "import json; json.dump({'Request_Status_Notes__c': '<note>'}, open('/tmp/asq_update.json','w'))"
python3 $ASQ_TOOLS sfdc-update <ASQ_ID> /tmp/asq_update.json
```

### Update Cache
```bash
python3 $ASQ_CACHE upsert --ar "AR-XXXXXX" \
  --field sfdc_id=<id> --field account_name="<name>" \
  --field slack_channel_id=<channel_id> --field slack_channel_name=<channel_name> \
  --field support_type="<type>" --field start_date=<start> --field end_date=<end>
```

## Phase 5: Obsidian (Optional)

Check `~/asq-local-cache/obsidian_preference.yaml`. If enabled, create ASQ page and link from account page.

## Phase 6: Summary

| ASQ | Account | Slack Channel | Creator Invited | SFDC Updated | Cache Updated |
|-----|---------|---------------|-----------------|--------------|---------------|
