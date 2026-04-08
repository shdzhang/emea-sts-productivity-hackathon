# Obsidian Integration Detection

All ASQ skills that include Obsidian steps must check availability before attempting any Obsidian MCP calls. The user's preference is stored in a YAML file so it persists across conversations.

## Preference File

Location: `~/asq-local-cache/obsidian_preference.yaml`

```yaml
obsidian_enabled: true       # true, false, or postponed
last_checked: 2026-03-23
```

## Detection Logic

```
1. Read ~/asq-local-cache/obsidian_preference.yaml
   ├── obsidian_enabled: true      → Proceed with Obsidian steps
   ├── obsidian_enabled: false     → Skip ALL Obsidian steps silently
   ├── obsidian_enabled: postponed → Skip silently for this run (re-ask next conversation)
   └── File does not exist         → Go to step 2

2. Test if Obsidian MCP is available:
   Call: obsidian_list_files_in_vault (lightweight probe)

3. Present THREE options:
   1. Yes — Enable (help with MCP setup if needed)
   2. Not now — Skip today, ask again next time
   3. No — Disable permanently (re-enable via shell command)
```

## Key Rules

- **Never fail an ASQ operation because Obsidian is unavailable**
- **Only prompt on first use or after "postponed"**
- **Skip silently when disabled** — don't mention Obsidian at all
- **Re-enable path**: `echo 'obsidian_enabled: true' > ~/asq-local-cache/obsidian_preference.yaml`
