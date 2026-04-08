# Chart Generation Specification

## JSON Input Schema

```json
{
  "account_name": "string (required)",
  "asq_name": "string (required) — e.g., AR-000106066",
  "support_type": "string (required) — e.g., Data Warehousing",
  "metric_label": "string (required) — e.g., DBSQL $DBUs",
  "engagement_start_month": "int (required) — months_after_creation when ASQ started (usually 0)",
  "engagement_end_month": "int (required) — months_after_creation when ASQ ended",
  "data": [
    {"month": -6, "value": 5800.00},
    {"month": -5, "value": 5900.00},
    {"month": 0, "value": 8200.00},
    {"month": 1, "value": 10500.00}
  ],
  "secondary_data": "(optional) same format as data, for overlay metric",
  "secondary_metric_label": "string (optional) — label for secondary line"
}
```

## Preparing Data from Step 2a Results

1. **Group rows** by `months_after_creation` for the selected ASQ
2. **Pick primary metric column** using `METRIC_MAPPINGS.md` — resolve `support_type` + `additional_services` to the correct column name
3. **Set engagement period**: `engagement_start_month = 0` (ASQ creation), `engagement_end_month = DATEDIFF(month, start_date, end_date)`
4. **Build JSON**: map each row → `{"month": months_after_creation, "value": <primary_metric_value>}`
5. **Optional secondary**: add `secondary_data` with `total_dollar_consumption_month` for account-level context

## Running the Script

```bash
python3 scripts/generate_chart.py --input /tmp/chart_data.json --output /tmp/chart_AR-000106066.png
```

Or pipe via stdin:
```bash
echo '<json>' | python3 scripts/generate_chart.py --output /tmp/chart.png
```

### Arguments

| Flag | Required | Description |
|------|----------|-------------|
| `--input <path>` | No | JSON input file (default: stdin) |
| `--output <path>` | Yes | Output PNG path |
| `--title <string>` | No | Override chart title |
| `--secondary-metric <key>` | No | Enable secondary metric overlay |

## Chart Styling

- **Line color**: `#FF3621` (Databricks red)
- **Engagement band**: `#FFB300` at 25% opacity (amber)
- **Background**: `#F5F0E8` (warm cream)
- **Pre-avg line**: `#888888` dashed
- **Post-avg line**: `#FF3621` dashed
- **Dimensions**: 10x5 inches at 150 DPI
- **Growth annotation**: Bold percentage in a rounded box near post-avg line

## Embedding in Output

### Google Slides
1. Upload PNG to Google Drive via `google-drive-upload` skill
2. Insert image into slide body (Option B area) via Google Slides API
3. Position: centered, max width 80% of slide

### Google Doc
1. Upload PNG to Google Drive
2. Insert inline image after the "Post-Engagement Impact" section
3. Add caption: `Figure: {metric_label} consumption trend — {account_name} ({asq_name})`

### Markdown Fallback
Reference the local file path:
```markdown
![Consumption Chart](/tmp/chart_AR-000106066.png)
```

## Fallback (No matplotlib)

If matplotlib is unavailable, generate a text-based table:

```
Month | DBSQL $DBUs | Trend
------|-------------|------
  -6  |    $5,800   |
  -5  |    $5,900   | →
  ...
   0  |    $8,200   | ↑ STS START
   1  |   $10,500   | ↑↑
   2  |   $13,300   | ↑↑↑

Pre-avg: $5,850/mo → Post-avg: $11,900/mo (+103%)
```
