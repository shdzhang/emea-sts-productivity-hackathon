# CAST Integration Reference

This document describes how to format and post CAST (Customer Activity Sync Tool) updates to Salesforce from the asq-followup skill.

## CAST Format Structure

CAST comments follow a specific YAML-like structure for automated processing:

```yaml
---
meeting_date: YYYY-MM-DD
meeting_type: [Initial|Progress|Technical|Closing]
attendees:
  databricks: [list of attendees]
  customer: [list of attendees]
key_outcomes: |
  - Outcome 1
  - Outcome 2
action_items: |
  - [Owner] - [Task] - [Due: YYYY-MM-DD]
next_steps: |
  - Next step 1
  - Next step 2
uco_stage: [U0|U1|U2|U3|U4|U5]
sentiment: [Positive|Neutral|Concerned]
---
```

## Integration with asq-update

The asq-followup skill should coordinate with asq-update to avoid duplication:

### Check for Existing CAST

```python
def check_existing_cast(asq_id, meeting_date):
    """Check if CAST already exists for this meeting"""
    # Query SFDC for existing CAST comments from today
    # Return True if found, False otherwise
    pass
```

### Append vs New CAST

- If asq-update already created a CAST → Append additional info
- If no CAST exists → Create new CAST entry
- If multiple meetings same day → Create separate CAST entries with timestamps

## CAST Field Mappings

| CAST Field | Source | Format |
|------------|--------|--------|
| meeting_date | Parser output | YYYY-MM-DD |
| meeting_type | Parser classification | Enum value |
| attendees.databricks | Meeting notes | Comma-separated |
| attendees.customer | Meeting notes | Comma-separated |
| key_outcomes | Key decisions | Bullet list |
| action_items | Action items | [Owner] - [Task] - [Due: Date] |
| next_steps | Next topics | Bullet list |
| uco_stage | UCO indicators | U0-U5 |
| sentiment | Content analysis | Positive/Neutral/Concerned |

## Sentiment Analysis Rules

Determine sentiment based on meeting content:

| Sentiment | Indicators |
|-----------|------------|
| Positive | "approved", "happy", "excited", "great progress", "ahead of schedule" |
| Concerned | "blocked", "delayed", "issue", "problem", "concerned", "at risk" |
| Neutral | Default if no strong indicators |

## CAST Posting via SFDC API

```python
def post_cast_to_sfdc(asq_id, cast_content):
    """Post CAST-formatted comment to ASQ"""

    # Using salesforce-actions skill
    command = f"""
    /salesforce-actions add-comment
    --object ASQ__c
    --id {asq_id}
    --field CAST_Comments__c
    --value "{cast_content}"
    """

    return execute_skill(command)
```

## Enhanced CAST with Follow-up Info

The asq-followup skill adds additional context not in standard CAST:

```yaml
---
# Standard CAST fields...
follow_up_scheduled: YYYY-MM-DD HH:MM
follow_up_agenda: |
  - Review action items
  - Discuss progress
email_sent: true
email_recipients: [list]
customer_response_required: [list of items awaiting customer]
escalations: [list of escalated items]
---
```

## CAST Validation Rules

Before posting, validate:

1. **Required Fields**
   - meeting_date must be valid date
   - meeting_type must be valid enum
   - At least one outcome or action item

2. **Consistency Checks**
   - UCO stage should not regress
   - Due dates should be future dates
   - Attendees should match meeting notes

3. **Format Validation**
   - YAML structure must be valid
   - No special characters that break YAML
   - Proper indentation

## Error Recovery

If CAST posting fails:

```python
def handle_cast_failure(cast_content, error):
    """Handle CAST posting failures"""

    if "duplicate" in str(error).lower():
        # Append to existing CAST
        return append_to_cast(cast_content)

    elif "permission" in str(error).lower():
        # Store locally for manual posting
        return cache_for_manual_post(cast_content)

    elif "format" in str(error).lower():
        # Reformat and retry
        return reformat_and_retry(cast_content)

    else:
        # Log and notify user
        return notify_user_of_failure(error)
```

## CAST Template for asq-followup

```yaml
---
meeting_date: {meeting_date}
meeting_type: {meeting_type}
meeting_duration: {duration_minutes} minutes
attendees:
  databricks: {databricks_attendees}
  customer: {customer_attendees}

key_outcomes: |
{key_outcomes_formatted}

action_items: |
{action_items_formatted}

decisions_made: |
{decisions_formatted}

blockers_identified: |
{blockers_formatted}

next_steps: |
{next_steps_formatted}

uco_stage: {current_uco}
uco_progression: {uco_signal}
sentiment: {sentiment}

# Follow-up specific fields
follow_up_meeting:
  scheduled: {follow_up_date}
  agenda: {follow_up_agenda}
  attendees: {follow_up_attendees}

customer_deliverables:
{customer_deliverables_formatted}

internal_notes: |
  - Email sent: {email_sent_time}
  - Slack posted: {slack_posted}
  - Calendar invite: {calendar_created}

automation_metadata:
  generated_by: asq-followup
  timestamp: {current_timestamp}
  version: 1.0.0
---
```

## Integration with Other Systems

### Logfood Integration
```python
# Log CAST creation to Logfood
logfood_query = f"""
INSERT INTO cast_activities (
    asq_id,
    cast_content,
    created_by,
    created_at
) VALUES (
    '{asq_id}',
    '{cast_content}',
    'asq-followup',
    NOW()
)
"""
```

### Slack Notification
```python
# Notify in ASQ Slack channel
slack_message = f"""
📝 CAST Updated for ASQ {asq_id}
Meeting Type: {meeting_type}
Key Outcomes: {len(key_outcomes)} items
Action Items: {len(action_items)} items
Next Meeting: {follow_up_date}
"""
```

## Best Practices

1. **Keep CAST concise** - Focus on actionable information
2. **Use consistent formatting** - Enables automated parsing
3. **Include customer perspective** - Not just internal notes
4. **Update promptly** - Within 24 hours of meeting
5. **Link related CASTs** - Reference previous meetings
6. **Version control** - Track CAST schema changes