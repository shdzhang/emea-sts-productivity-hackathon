# STS Plugin — Configuration

View and manage your STS plugin preferences.

## Usage

```
/sts-config
```

## Task

1. **Show all current preferences:**
   ```bash
   python3 ~/.claude/plugins/cache/fe-vibe/fe-sts/*/skills/asq-local-cache/resources/asq_config.py preferences-show 2>/dev/null
   ```

2. **Show user identity:**
   ```bash
   python3 ~/.claude/plugins/cache/fe-vibe/fe-sts/*/skills/asq-local-cache/resources/asq_config.py show 2>/dev/null
   ```

3. **Present a formatted summary** grouped by category:
   - **User** — language
   - **Status Notes** — format, language, ordering, session numbering
   - **CAST** — CC rules, sections, timeline format
   - **Closing Notes** — format, template, partial tag
   - **Tone** — SFDC vs Slack tone
   - **Slack** — channel naming, templates, language detection
   - **Obsidian** — vault paths

   Mark overridden values with a badge so the user can see what they've customized vs defaults.

4. **Ask what they'd like to change.** When the user requests a change, apply it:
   ```bash
   python3 ~/.claude/plugins/cache/fe-vibe/fe-sts/*/skills/asq-local-cache/resources/asq_config.py preferences-set <key> <value>
   ```

   Common requests and their keys:
   - "Change my language" → `user.language`
   - "Change SFDC notes language" → `status_notes.language`
   - "Don't CC the requestor on CASTs" → `cast.cc_requestor false`
   - "Change Slack tone" → `tone.slack`
   - "Change channel naming" → `slack.channel_pattern`
