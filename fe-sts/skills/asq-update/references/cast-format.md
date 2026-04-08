# CAST Chatter API Format

## Preferred Method: cast-post command

The `cast-post` command handles all formatting automatically. Manager CC is loaded from `user_config.yaml`.

```bash
ASQ_TOOLS=~/.claude/plugins/cache/fe-vibe/fe-sts/*/skills/asq-local-cache/resources/asq_tools.py

# Dry-run preview (default — safe):
python3 $ASQ_TOOLS cast-post <ASQ_ID> \
  --context "Context text" \
  --ask "Ask text" \
  --success "Success text" \
  --timeline "1 Discovery (completed)|2 Dev sessions|Follow-up as needed" \
  --cc "<REQUESTOR_SFDC_ID>"

# Post for real (only after user approval):
python3 $ASQ_TOOLS cast-post <ASQ_ID> \
  --context "..." --ask "..." --success "..." --timeline "..." \
  --cc "<REQUESTOR_SFDC_ID>" --confirm
```

- **Manager** is auto-CC'd (from `user_config.yaml`, configurable via `cast.auto_cc_manager` preference)
- **Additional CC**: the SA/AE who opened the request (`CreatedById`)
- Timeline bullets separated by `|`

## Low-Level API (for custom payloads)

### Endpoint
```
POST /services/data/v66.0/chatter/feed-elements
```

### Key Details
- Use `\u00a0` (non-breaking space) as blank line separator between sections
- Each paragraph needs `MarkupBegin`/`MarkupEnd` wrappers
- Bold text needs nested `MarkupBegin`/`MarkupEnd` within the paragraph
- C/C section uses `Mention` segments with SFDC user IDs

### Posting via CLI
```bash
sf api request rest --method POST "/services/data/v66.0/chatter/feed-elements" --body @/tmp/cast_payload.json
```
