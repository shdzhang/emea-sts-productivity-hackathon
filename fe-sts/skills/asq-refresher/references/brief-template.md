# Meeting Brief Template

Use this template for the LLM synthesis step. Fill every section from gathered data. If a data source was unavailable, note it inline and skip that section's content.

---

## Template

```
# Meeting Brief: {account_name} — {ar_number}

**Meeting:** {title}
**When:** {date/time} ({days_until} days from now)
**Platform:** {platform}
**Attendees:**
- **Databricks:** {databricks_attendees}
- **Customer/External:** {external_attendees}

**ASQ:** {ar_number} | **Type:** {support_type} | **Status:** {status} | **Start:** {start_date} | **End:** {end_date}

---

## Executive Summary

{2-3 sentences max: What is this ASQ about and what is its current state. Keep it short — a quick orientation, not a deep dive. Synthesize across sources, do not repeat SFDC fields.}

---

## Meeting Timeline

{Build from Calendar events and SFDC status notes. ONLY include meetings where the current user was an attendee. Bold the row for the meeting this refresher was triggered for.}

| Date | Meeting | Notes |
|------|---------|-------|
| **{date}** | **{current_meeting_title}** | **{details}** [{source}] |
| {date} | {next_meeting_title} | {time, platform} [{source}] |

---

## Meeting Recap

{What was discussed or covered in this meeting. Source content in priority order:
1. **Meeting notes** — Obsidian session logs, Slack thread summaries, or Gmail follow-ups
2. **DBRA** — internal Slack discussions, Confluence pages, support tickets related to this customer/engagement
3. **SFDC status notes** — Request_Status_Notes field (often has per-meeting entries)
4. **SFDC description** — the ASQ ask as a fallback baseline

Cross-reference across sources. Organize into numbered topics with what was discussed/decided.}

### 1. {Topic}
{Summary from notes/SFDC} [{source}]

### 2. {Topic}
{Summary from notes/SFDC} [{source}]

---

## Next Steps & Open Risks

**Next meeting:** {next_meeting_title} | {next_meeting_date_time}

{Merge open items, risks, and next meeting agenda into a single table. Each row is an actionable item with a Notes column for additional context (agenda details, blockers, follow-ups). Source from ALL sources: SFDC, Slack, Gmail, Obsidian, DBRA, flags. Deduplicate. Order by risk (High first). Only include topics directly tied to the ASQ scope. Do NOT add "Create Slack channel" unless explicitly requested in SFDC or Slack. Do NOT infer items from contextual observations (e.g., language) unless in the ASQ description.}

---

## Consumption Summary

{ONLY include this section if the ASQ support_type is "Growth Accelerator for PAYG" or "Launch Accelerator". For all other ASQ types, skip this section entirely.}

{If included: Combine Logfood (30-day) and Genie (historical) into a single distilled view. Lead with a headline, show only ASQ-relevant products, connect data to the engagement.}

**~${total_30d}/month** — {trend vs historical} [Logfood, Genie]

| Product | Current 30d | Trend | Relevance to this ASQ |
|---------|-------------|-------|-----------------------|
| {product relevant to ASQ} | ${amount} | {↑/↓ %} | {Why this matters} [{source}] |

{If Logfood/Genie unavailable, note it and move on.}

---

## Internal Context

{From DBRA, Glean, Obsidian — include whichever are available:}

- **Escalations:** {open ES tickets, severity} [DBRA]
- **Engineering blockers:** {active blockers, workarounds} [DBRA]
- **Strategic notes:** {account plans, leadership discussions} [DBRA]
- **Internal discussions:** {relevant Slack threads, Confluence pages} [DBRA/Glean]

{If DBRA unavailable: "Internal context: DBRA unavailable — install with `isaac plugin add dbra@experimental`."}
{If no internal context found from any source: "No additional internal context found."}

| Item | Owner | Status | Risk | Notes |
|------|-------|--------|------|-------|
| {item} | {owner} | {status} | {High/Med/Low} | {Additional context: what to discuss, why it matters, blockers} [{source}] |

---

## Notes

{Any contextual observations: short engagement window, language preferences, On Hold reasons, cultural considerations, etc.}

---

*Sources: {list sources that contributed, e.g. SFDC, Calendar, Gmail, Slack, Obsidian, Glean, Logfood, Genie, DBRA — mark unavailable ones}*
*Generated: {timestamp}*
```

## Synthesis Rules

When filling the template, follow these rules:

1. **Cross-reference and deduplicate** — the same fact from SFDC + Slack should appear once
2. **Lead with actionable items** — what matters for today's meeting comes first
3. **Consumption data from Logfood/Genie supersedes estimates** — if you have real numbers, use them over any cached or approximate figures
4. **Integrate DBRA context** — weave internal context into relevant sections (e.g., an escalation goes into Open Items & Risks, not just the Internal Context dump)
5. **Tag facts with source** — use [SFDC], [Slack], [Gmail], [Logfood], [Genie], [DBRA], [Glean], [Calendar], [Obsidian]
6. **Flag contradictions** — if sources disagree (e.g., Slack says "data is ready" but SFDC says "waiting for data"), call it out explicitly
7. **No inferred context** — do not add language preferences, cultural notes, or Slack channel creation unless explicitly mentioned in the ASQ description or requested by the user
