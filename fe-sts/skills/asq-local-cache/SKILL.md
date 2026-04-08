---
name: asq-local-cache
description: Local cache of stable ASQ metadata and user configuration. Auto-setup on first use detects SFDC identity and manager. All ASQ skills read from and write to this cache. Triggers automatically when any ASQ operation begins.
user-invocable: true
---

# ASQ Local Cache & Configuration

Local YAML cache at `~/asq-local-cache/` storing stable ASQ metadata and user configuration. Eliminates repeated SFDC/Slack/Calendar searches across all ASQ skills.

**Scripts:**
```
ASQ_TOOLS=~/.claude/plugins/cache/fe-vibe/fe-sts/*/skills/asq-local-cache/resources/asq_tools.py
ASQ_CACHE=~/.claude/plugins/cache/fe-vibe/fe-sts/*/skills/asq-local-cache/resources/asq_cache.py
ASQ_CONFIG=~/.claude/plugins/cache/fe-vibe/fe-sts/*/skills/asq-local-cache/resources/asq_config.py
```

## First-Time Setup (Config)

All ASQ skills require `~/asq-local-cache/user_config.yaml`. On first use, if a command returns `CONFIG_NOT_FOUND`, run the auto-setup flow:

### Step 1: Auto-detect identity
```bash
python3 $ASQ_CONFIG detect-identity
```
Returns JSON with auto-detected values: `sfdc_user_id`, `user_name`, `sfdc_username`, `manager_sfdc_id`, `manager_name`.

### Step 2: Confirm with the user
Present the detected values. Ask: "Does this look right? Is {manager_name} your current manager?"

### Step 3: Save config
```bash
python3 $ASQ_CONFIG setup \
  --user-id "<sfdc_user_id>" \
  --username "<sfdc_username>" \
  --user-name "<user_name>" \
  --manager-id "<manager_sfdc_id>" \
  --manager-name "<manager_name>"
```

### Optional: Set Obsidian vault path
```bash
python3 $ASQ_CONFIG set obsidian_vault_path "~/Obsidian-Vault"
```

### View or update config
```bash
python3 $ASQ_CONFIG show
python3 $ASQ_CONFIG set <key> <value>
python3 $ASQ_CONFIG get <key>
```

## Customizing Preferences

All opinionated behaviors (templates, tone, naming conventions) have sensible defaults that can be overridden without editing skill files. Preferences are stored in `~/asq-local-cache/preferences.yaml`.

### View all preferences
```bash
python3 $ASQ_CONFIG preferences-show
# Filter by category:
python3 $ASQ_CONFIG preferences-show tone
python3 $ASQ_CONFIG preferences-show slack
python3 $ASQ_CONFIG preferences-show close_notes
```

### Override a preference
```bash
python3 $ASQ_CONFIG preferences-set tone.slack "professional"
python3 $ASQ_CONFIG preferences-set cast.auto_cc_manager false
python3 $ASQ_CONFIG preferences-set status_notes.language "pt-br"
```

### Reset to default
```bash
python3 $ASQ_CONFIG preferences-reset tone.slack
```

### Preference categories
| Category | What it controls |
|---|---|
| `status_notes.*` | Date format, language, session numbering, internal sync labels |
| `cast.*` | Auto-CC manager, CAST section names, extra CC IDs |
| `close_notes.*` | Close notes format (STAR), template, separator, partial tag |
| `tone.*` | SFDC tone (professional), Slack tone (friendly), descriptions |
| `slack.*` | Channel naming pattern, intro/closing message templates, language detection |
| `slugs.*` | Support type -> channel name slug mapping |
| `obsidian.*` | Vault directory paths for active/archive ASQs |

## Cache Location

- Directory: `~/asq-local-cache/`
- One file per ASQ: `AR-XXXXXX.yaml`
- Index file: `~/asq-local-cache/index.yaml` (alias -> AR number mapping)
- Config file: `~/asq-local-cache/user_config.yaml`
- Preferences: `~/asq-local-cache/preferences.yaml` (optional overrides)

## Cache File Schema

```yaml
ar_number: AR-000107402
account_name: Acme Corp
known_aliases:
  - acme
sfdc_id: aEJVp000001KRujOAG
slack_channel_id: C0AALHVN1FB
slack_channel_name: ar-000107402-acme-ml-genai
slack_channel_language: en-us
known_calendar_events:
  - event_id: 401rhhvl2dkl5lplnchfe4mnpt
    summary: "Acme - ML - Databricks"
    recurrence: weekly
support_type: "ML & GenAI"
created_by_name: Jane Smith
created_by_sfdc_id: "005Vp000003mdoXIAQ"
start_date: "2026-01-29"
end_date: "2026-03-27"
last_updated: "2026-03-20"
```

## Operations

### Lookup
```bash
python3 $ASQ_CACHE lookup "<query>"
```
Searches AR numbers, account names, and aliases. Fuzzy matching.

### Create / Update
```bash
python3 $ASQ_CACHE upsert --ar "AR-000107402" --field key=value [--field key=value ...]
```

### Add Alias
```bash
python3 $ASQ_CACHE add-alias --ar "AR-000107402" --alias "Acme"
```

### List All / Rebuild Index
```bash
python3 $ASQ_CACHE list
python3 $ASQ_CACHE rebuild-index
```

## Obsidian Integration (Optional)

Stored at `~/asq-local-cache/obsidian_preference.yaml`. See `references/obsidian-detection.md` for the first-use prompt logic. Teammates without Obsidian pick "No" once and never see it again.

## Integration with Other ASQ Skills

**All ASQ skills MUST:**
1. **On start**: Run `lookup` before searching SFDC/Slack/Calendar
2. **If cache hit**: Use cached IDs directly — skip searching
3. **If cache miss**: Search normally, then `upsert` discovered metadata
4. **On new discovery**: Update the cache immediately
