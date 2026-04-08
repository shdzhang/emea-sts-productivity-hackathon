# STS Content Index — Fetch-on-Demand Reference

Instead of reading local files (which risk going stale), this index maps support types to searchable page titles and search queries. Fetch fresh content from Glean, Confluence, or Obsidian MCP at the time you need it.

## Programmatic Access

```bash
ASQ_TOOLS=~/.claude/plugins/cache/fe-vibe/fe-sts/*/skills/asq-local-cache/resources/asq_tools.py

# Get index for a specific support type
python3 $ASQ_TOOLS sts-index "ML & GenAI"

# Get the full index
python3 $ASQ_TOOLS sts-index
```

## Support Type Index

| Support Type | Page Titles | Search Query |
|---|---|---|
| Platform Administration | STS Workspace Setup, STS Delivery and Resources, STS FAQ | `STS Content Repo Workspace Setup` |
| Data Governance | STS Data Governance, STS UC FAQ, STS UC Learning Sessions | `STS Content Repo Data Governance Unity Catalog` |
| Data Engineering | STS Data Engineering | `STS Content Repo Data Engineering` |
| Data Warehousing | STS Data Warehousing, STS Courses Recommendation | `STS Content Repo Data Warehousing` |
| ML & GenAI | STS ML & GenAI | `STS Content Repo ML GenAI` |
| Launch Accelerator | STS Launch Accelerator, STS LA Execution Guide, STS LA FAQ, STS LA Red Flags | `STS Content Repo Launch Accelerator` |

## Cross-Cutting Resources

| Resource | Search Query |
|---|---|
| Email Templates | `STS Email Templates` |
| Service Expertise Definitions | `STS Service Expertise Definitions` |
| Overview (go/sts) | `STS Overview go-sts` |
