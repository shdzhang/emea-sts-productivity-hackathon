---
name: asq-refresher
description: Prepare a meeting brief with outstanding topics, action items, and commitments by researching SFDC, Slack, Gmail, and Calendar. Auto-triggers on upcoming meeting, what to discuss, meeting context, meeting prep. Triggers on 'next meeting', 'upcoming meeting', 'what do I discuss', 'meeting prep', 'refresh me on', 'prep me for'.
---

# ASQ Meeting Refresher

**Announce at start:** "Let me pull together a meeting brief for you."

**Script:**
```
ASQ_TOOLS=~/.claude/plugins/cache/fe-vibe/fe-sts/*/skills/asq-local-cache/resources/asq_tools.py
ASQ_CACHE=~/.claude/plugins/cache/fe-vibe/fe-sts/*/skills/asq-local-cache/resources/asq_cache.py
```

## Prerequisites

User config must exist at `~/asq-local-cache/user_config.yaml`. If any command returns `CONFIG_NOT_FOUND`, run the setup flow in asq-local-cache.

## Workflow

### Step 1: Gather all context (single Bash call)

```bash
python3 $ASQ_TOOLS gather "<customer name or alias>" [--domain customer-email.com]
```

Returns JSON with: `cache`, `sfdc` (ASQ + UCOs), `calendar`, `gmail`, `obsidian`, `sts_content` (index), `slack` (metadata), `flags`, `hints`, `preferences`.

If `cache_hit` is false, upsert discovered metadata afterward:
```bash
python3 $ASQ_CACHE upsert --ar "AR-XXXXXX" --field key=value
```

### Step 2: Slack channel history (1 MCP call)

If `slack.channel_id` is present:
```
mcp__slack__slack_read_api_call: conversations.history, {"channel": "<id>", "limit": 30}
```

### Step 3: Fetch STS service context (if relevant)

If `sts_content` is present, use the `search_query` to fetch fresh content about expected milestones and deliverables:
1. **Preferred:** Search Glean with the `search_query`
2. **Alternative:** Obsidian MCP or Confluence with page titles

### Step 4: Format the meeting brief

**Meeting:** {title} | **When:** {date/time} | **Attendees:** {list}

## Open Topics for Today
### 1. {Most urgent topic}
{Context from SFDC/Slack/Gmail/Obsidian}

## ASQ Context
- **ASQ:** {name} | Status: {status} | **Target end: {date}** {flag if <2 weeks}
- **UCO:** {stage} | Go-live: {date}
- **Service expectations:** {from STS content, if fetched}
- {Any flags from script output}

## Action Items Tracker
| Item | Owner | Source | Status |

## Recent Correspondence
{Summary if gmail data available}

## Rules
- **Read-only** — no SFDC writes, no Slack posts, no emails
- Speed over completeness — present what you have if a source errored
- Deduplicate across sources
- Note if Slack channel is in a non-English language
