---
name: asq-followup
description: Automate post-meeting actions including follow-up emails, SFDC updates, and calendar scheduling
user-invocable: true  # Allow /asq-followup invocation
---

# ASQ Post-Meeting Follow-up

Completes the post-meeting lifecycle with customer emails, action extraction, and scheduling.

## Prerequisites
- Gmail access with Gemini meeting notes arriving
- Authenticated with Salesforce and Google Workspace
- ASQ exists in SFDC
- Optional: Slack authentication for team notifications

## Workflow

### Phase 1: Retrieve Gemini Meeting Notes
Input: URL to Gemini notes, ASQ ID, or meeting date/customer name
Process:
1. If URL provided (e.g., https://meet.google.com/recording/...):
   - Extract meeting ID from URL
   - Fetch meeting notes directly via Google API
   - Or search Gmail for related Gemini email using meeting ID
2. Otherwise, search Gmail for Gemini meeting notes using filters:
   - From: meet-recordings-noreply@google.com or Gemini sender
   - Subject contains: customer name or meeting title
   - Date range: last 24-48 hours
3. Parse email/page to extract meeting transcript/summary
4. If multiple matches, present list for user selection
5. If not found, fall back to manual input
Output: Raw meeting text from Gemini

### Phase 2: Extract Structured Data
Use LLM with this prompt:
"From these meeting notes, extract:
- Action items with format: [Owner] - [Task] - [Due Date]
- Key decisions made
- Open questions or blockers
- Suggested next meeting topics
- UCO progression indicators (phrases like 'ready to proceed', 'approved', etc.)"

### Phase 3: Draft Follow-up Email
Template structure:
- Subject: Follow-up: {Account Name} - {Meeting Date}
- Greeting
- Thank you for time
- Summary of key decisions
- Action items table
- Next steps
- Proposed next meeting: {date from availability}
- Sign-off

### Phase 4: Draft SFDC Status Note
Generate CAST-formatted status note for Salesforce:
```yaml
---
meeting_date: {date}
meeting_type: {type: Initial|Progress|Technical|Closing}
attendees:
  databricks: {list}
  customer: {list}
key_outcomes: |
  - {decisions from Phase 2}
action_items: |
  - {formatted action items}
next_steps: |
  - {next steps}
uco_stage: {current_stage}
uco_progression: {if detected}
sentiment: {Positive|Neutral|Concerned}
follow_up_meeting: {date/time if scheduled}
---
```
Display formatted CAST note for review and copying to SFDC

### Phase 5: Handle Follow-up Meeting Scheduling
Process:
1. Check if meeting notes contain follow-up meeting details:
   - Look for phrases like "next meeting on", "follow up on", "reconvene on"
   - Extract date/time if present
2. If follow-up meeting details found:
   - Create calendar event with extracted date/time
   - Title: {Account Name} - Follow-up
   - Attendees from original meeting
   - Agenda from next steps
   - Location/Meet link
3. If NO follow-up meeting details found:
   - Skip calendar creation
   - Add availability request to email draft:
     * Run availability scan for next 2 weeks
     * Include 3 time slot options in email
     * Request customer to confirm preferred slot

### Phase 6: Apply Updates

**CRITICAL: NEVER execute without explicit user approval.**

After user approves drafts, execute in this order:

#### 6.1 Send Follow-up Email
```python
# Create Gmail draft (do not auto-send)
draft = mcp__google__gmail_draft_create(
    to=customer_emails,
    subject=f"Follow-up: {account_name} - {meeting_date}",
    body=email_body
)
print(f"✅ Email draft created: {draft['id']}")
```

#### 6.2 Update SFDC Status Notes
```python
# Fetch existing status notes
existing_notes = get_asq_field(asq_id, 'Request_Status_Notes__c')

# Prepare separator
separator = "\n\n" + "="*60 + "\n"

# Prepend new CAST note to existing notes
if existing_notes:
    full_notes = f"{cast_note}{separator}{existing_notes}"
else:
    full_notes = cast_note

# Write combined notes to temp file and update SFDC
import json
update_data = {'Request_Status_Notes__c': full_notes}
with open('/tmp/asq_update.json', 'w') as f:
    json.dump(update_data, f)

# Update SFDC with combined notes
subprocess.run(['python3', os.environ['ASQ_TOOLS'], 'sfdc-update', asq_id, '/tmp/asq_update.json'])
print(f"✅ SFDC status notes updated with new CAST note prepended")
```

#### 6.3 Post CAST (if applicable)
Only if new CAST needed:
```bash
# Preview first (dry-run is default)
python3 $ASQ_TOOLS cast-post <ASQ_ID> \
  --context "<context>" --ask "<ask>" --success "<success>" \
  --timeline "item1|item2|item3" --cc "<REQUESTOR_SFDC_ID>"

# After user confirms preview, post for real
python3 $ASQ_TOOLS cast-post <ASQ_ID> \
  --context "<context>" --ask "<ask>" --success "<success>" \
  --timeline "item1|item2|item3" --cc "<REQUESTOR_SFDC_ID>" --confirm
```

#### 6.4 Create Calendar Event (if scheduled)
```python
if follow_up_meeting['scheduled']:
    event = mcp__google__calendar_event_create(
        summary=f"{account_name} - Follow-up",
        start={'dateTime': meeting_datetime},
        end={'dateTime': meeting_end},
        attendees=attendee_list,
        add_google_meet=True
    )
    print(f"✅ Calendar event created: {event['htmlLink']}")
```

#### 6.5 Post to Slack (Optional)
```python
# Only post to Slack if channel is configured for the ASQ
if slack_channel_id:
    slack_message = f"""📝 Meeting Summary - {account_name}
**Key Decisions:** {key_decisions}
**Action Items:** {action_items}
**Next Meeting:** {follow_up_date if scheduled else 'TBD'}
cc: {attendee_mentions}"""

    result = mcp__slack__slack_write_api_call(
        endpoint="chat.postMessage",
        params={
            "channel": slack_channel_id,
            "text": slack_message
        }
    )
    print(f"✅ Slack message posted to #{slack_channel_name}")
else:
    print("ℹ️ No Slack channel configured, skipping Slack notification")
```

### Phase 7: Present for Review
Display all drafts in formatted output:
1. Email draft (full text)
2. SFDC CAST status note (YAML format for copying)
3. Calendar event (if follow-up meeting scheduled)
4. Slack message (if channel configured)

Prompt: "Review the above drafts. Type 'approve' to execute all actions, or specify which to modify."

### Phase 8: Service Goals Alignment Assessment

Compare meeting activities against the specific service goals and outcomes to identify progress and gaps:

#### 8.1 Load Service Definition
```python
def load_service_definition(asq_data):
    """Load the specific service definition based on ASQ support type"""

    # Map ASQ support types to service paths
    service_mapping = {
        'ML & GenAI': 'ml-genai/gen-ai-apps',
        'Data Engineering': 'data-engineering/lakeflow',
        'Data Warehousing': 'data-warehousing/genie-foundation',
        'Platform Administration': 'platform/workspace-setup',
        'Streaming': 'data-engineering/lakeflow',
        'Data Governance': 'platform/unity-catalog-setup',
        'Migration': 'migration/lakebridge-analyzer'
    }

    support_type = asq_data.get('support_type', 'Platform Administration')
    service_path = service_mapping.get(support_type, 'platform/workspace-setup')

    # Load service definition
    service_file = f'/plugins/fe-sts/sts-services/{service_path}/README.md'

    try:
        with open(service_file, 'r') as f:
            service_def = parse_service_definition(f.read())
        return service_def
    except:
        return get_default_service_definition()
```

#### 8.2 Compare Activities to Service Goals
```python
def assess_service_alignment(meeting_data, service_def):
    """Compare meeting activities to service goals and deliverables"""

    assessment = {
        'covered_activities': [],
        'missing_activities': [],
        'progress_toward_deliverables': [],
        'gaps_in_deliverables': [],
        'alignment_score': 0
    }

    # Extract meeting activities
    meeting_activities = extract_meeting_activities(meeting_data)

    # Compare against Key Activities from service definition
    for key_activity in service_def['key_activities']:
        if activity_was_discussed(key_activity, meeting_activities):
            assessment['covered_activities'].append({
                'activity': key_activity,
                'evidence': find_evidence(key_activity, meeting_data)
            })
        else:
            assessment['missing_activities'].append(key_activity)

    # Check progress toward Deliverables
    for deliverable in service_def['deliverables']:
        progress = check_deliverable_progress(deliverable, meeting_data)
        if progress['status'] != 'not_started':
            assessment['progress_toward_deliverables'].append({
                'deliverable': deliverable,
                'status': progress['status'],
                'evidence': progress['evidence']
            })
        else:
            assessment['gaps_in_deliverables'].append(deliverable)

    # Calculate alignment score
    total_goals = len(service_def['key_activities']) + len(service_def['deliverables'])
    covered_goals = len(assessment['covered_activities']) + len(assessment['progress_toward_deliverables'])
    assessment['alignment_score'] = int((covered_goals / total_goals) * 100) if total_goals > 0 else 0

    return assessment
```

#### 8.3 Extract Meeting Activities
```python
def extract_meeting_activities(meeting_data):
    """Extract concrete activities discussed in the meeting"""

    activities = []

    # From key decisions
    for decision in meeting_data.get('key_decisions', []):
        activities.append({
            'type': 'decision',
            'content': decision,
            'keywords': extract_keywords(decision)
        })

    # From action items
    for action in meeting_data.get('action_items', []):
        activities.append({
            'type': 'action',
            'content': action.get('task', ''),
            'owner': action.get('owner', ''),
            'keywords': extract_keywords(action.get('task', ''))
        })

    # From discussion topics (if available)
    for topic in meeting_data.get('discussion_topics', []):
        activities.append({
            'type': 'discussion',
            'content': topic,
            'keywords': extract_keywords(topic)
        })

    return activities
```

#### 8.4 Generate Targeted Recommendations
```python
def generate_service_recommendations(assessment, service_def):
    """Generate recommendations based on service goal gaps"""

    recommendations = {
        'next_meeting_agenda': [],
        'immediate_actions': [],
        'resources_to_share': []
    }

    # Focus next meeting on missing key activities
    if assessment['missing_activities']:
        recommendations['next_meeting_agenda'] = [
            f"Review: {activity}" for activity in assessment['missing_activities'][:3]
        ]

    # Generate actions to close deliverable gaps
    for gap in assessment['gaps_in_deliverables']:
        if 'documentation' in gap.lower():
            recommendations['immediate_actions'].append(
                "Share relevant documentation templates and examples"
            )
        elif 'configuration' in gap.lower() or 'setup' in gap.lower():
            recommendations['immediate_actions'].append(
                f"Schedule hands-on session for {gap}"
            )
        elif 'training' in gap.lower():
            recommendations['resources_to_share'].append(
                "Training catalog and certification paths"
            )

    # Add service-specific recommendations
    if service_def.get('service_type') == 'ML & GenAI':
        if 'model' not in str(assessment['covered_activities']).lower():
            recommendations['immediate_actions'].append(
                "Discuss model requirements and evaluation criteria"
            )
    elif service_def.get('service_type') == 'Data Engineering':
        if 'pipeline' not in str(assessment['covered_activities']).lower():
            recommendations['immediate_actions'].append(
                "Review data pipeline architecture and SLAs"
            )

    return recommendations
```

#### 8.5 Display Service Alignment Report
```python
# After Phase 7 review, show service alignment
print("\n" + "="*60)
print(f"📊 SERVICE GOALS ALIGNMENT: {service_def['name']}")
print("="*60)

print(f"\n📋 Service Overview:")
print(f"   {service_def['overview']}")

print(f"\n🎯 Key Activities Coverage ({len(assessment['covered_activities'])}/{len(service_def['key_activities'])}):")
if assessment['covered_activities']:
    print("✅ Discussed:")
    for item in assessment['covered_activities']:
        print(f"  • {item['activity']}")
        if item['evidence']:
            print(f"    Evidence: {item['evidence'][:100]}...")

if assessment['missing_activities']:
    print("\n❌ Not Yet Covered:")
    for activity in assessment['missing_activities']:
        print(f"  • {activity}")

print(f"\n📦 Deliverables Progress ({len(assessment['progress_toward_deliverables'])}/{len(service_def['deliverables'])}):")
if assessment['progress_toward_deliverables']:
    print("✅ In Progress:")
    for item in assessment['progress_toward_deliverables']:
        status_icon = "🟢" if item['status'] == 'completed' else "🟡"
        print(f"  {status_icon} {item['deliverable']} - {item['status']}")

if assessment['gaps_in_deliverables']:
    print("\n⏳ Not Started:")
    for deliverable in assessment['gaps_in_deliverables']:
        print(f"  • {deliverable}")

# Alignment Score
print(f"\n📈 Service Alignment Score: {assessment['alignment_score']}%")
if assessment['alignment_score'] < 30:
    print("   ⚠️ Early stage - focus on foundational activities")
elif assessment['alignment_score'] < 70:
    print("   📊 Making progress - maintain momentum on key activities")
else:
    print("   ✅ Strong alignment - approaching service completion")

# Recommendations
print("\n" + "="*60)
print("🎯 RECOMMENDATIONS FOR SERVICE SUCCESS")
print("="*60)

if recommendations['next_meeting_agenda']:
    print("\n📅 Next Meeting Focus Areas:")
    for item in recommendations['next_meeting_agenda']:
        print(f"  • {item}")

if recommendations['immediate_actions']:
    print("\n⚡ Immediate Actions:")
    for action in recommendations['immediate_actions']:
        print(f"  • {action}")

if recommendations['resources_to_share']:
    print("\n📚 Resources to Share:")
    for resource in recommendations['resources_to_share']:
        print(f"  • {resource}")

# Success Criteria Check
print(f"\n✨ Success Metrics Target:")
for metric in service_def.get('success_metrics', []):
    print(f"  • {metric}")
```

## Implementation Approach

The skill will use the following patterns:

1. **Zero-approval pattern**: No automatic execution without explicit user consent
2. **Graceful error handling**: Continue with other actions if one fails
3. **Cached updates**: Store failed updates locally for retry
4. **Multiple time options**: Show 3 calendar slots for flexibility

## Integration Points

### Gmail Integration for Gemini Notes
```python
# Search for Gemini meeting notes
mcp__google__gmail_message_list(
    q='from:meet-recordings-noreply@google.com subject:"meeting notes" newer_than:2d',
    max_results=10
)

# Retrieve specific Gemini email
mcp__google__gmail_message_get(
    message_id='{MESSAGE_ID}',
    format='full'
)

# Draft follow-up email
mcp__google__gmail_draft_create(
    to='{RECIPIENTS}',
    subject='Follow-up: {ACCOUNT_NAME} - {MEETING_DATE}',
    body='{EMAIL_BODY}'
)
```

### Salesforce Integration
```python
# Draft CAST status note for manual posting
cast_note = f"""
---
meeting_date: {meeting_date}
meeting_type: {meeting_type}
attendees:
  databricks: {databricks_attendees}
  customer: {customer_attendees}
key_outcomes: |
{formatted_outcomes}
action_items: |
{formatted_actions}
next_steps: |
{formatted_next_steps}
uco_stage: {current_stage}
sentiment: {sentiment}
---
"""
# Display for user to copy to SFDC
```

### Calendar Integration
```bash
# Using google-calendar skill
/google-calendar create-event --title {TITLE} --attendees {LIST} --time {SLOT}
```

### Slack Integration (Optional)
```python
# Check if Slack channel is configured
if asq.slack_channel_id:
    # Post to Slack using MCP
    mcp__slack__slack_write_api_call(
        channel=asq.slack_channel_id,
        text=slack_message
    )
else:
    # Skip Slack posting - no error
    print("No Slack channel configured, skipping...")
```

## Error Handling

| Scenario | Handling |
|----------|----------|
| No meeting notes provided | Prompt user for input |
| LLM extraction fails | Provide manual override form |
| SFDC connection issue | Display CAST note for manual copy |
| No calendar availability | Suggest async follow-up |
| Slack channel not found | Skip silently (optional feature) |

## Success Metrics

- Extracts ≥90% of action items from meeting notes
- Generates professional email suitable for customers
- Produces properly formatted CAST note for SFDC
- Creates valid calendar events with correct attendees (when scheduled)
- Posts formatted Slack summary (when channel available)
- Completes full workflow in <30 seconds

## Example Usage

### URL-Based Workflow (Fastest)

```
/asq-followup --url https://meet.google.com/recording/abc-defg-hij

Agent: Retrieving meeting notes from the provided URL...

Found meeting: "Acme Corp - Technical Review"
Date: April 8, 2024, 2:00 PM
Participants: John Smith, Sarah Jones, Mike Wilson (Acme)

Extracted:
- 3 action items
- 4 key decisions
- Next meeting proposed for April 15

[Continues with draft generation...]
```

### Standard Search Workflow

```
/asq-followup

Agent: I'll help you process your meeting follow-up.

How would you like to identify the meeting?
1. Provide Gemini/Meet recording URL
2. Search by customer name
3. Search by date (today/yesterday)
4. Provide ASQ ID
5. Show recent Gemini notes

User: 2

Agent: Please enter the customer name:

User: Acme Corp

Agent: I found a Gemini meeting note:
- Meeting: "Acme Corp - Technical Review"
- Date: April 8, 2024, 2:00 PM
- Participants: John Smith, Sarah Jones, Mike Wilson (Acme)

Retrieving and processing the notes...
```

### Manual Input Fallback

```
/asq-followup --manual

Agent: Please provide your meeting notes (paste directly):

User: [pastes meeting notes]

Agent: I've extracted the following from your meeting notes:

**Action Items:**
- John Smith - Review pricing proposal - April 15
- Sarah Jones - Send technical documentation - April 12
- Customer - Confirm budget approval - April 20

**Key Decisions:**
- Proceeding with Phase 1 implementation
- Weekly check-ins agreed upon
- Technical POC approved

**Next Steps:**
- Schedule technical deep-dive
- Prepare implementation plan
- Set up staging environment

I've prepared the following actions:

1. **Follow-up Email** [Draft shown]
2. **SFDC CAST Note** [YAML format shown - ready to copy]
3. **Calendar Event** [Details shown - if meeting scheduled]
4. **Slack Summary** [Preview shown - if channel configured]

Type 'approve' to execute all actions, or specify which to modify.
```

## Command Options

The skill supports several command-line options:

```bash
/asq-followup                    # Interactive mode
/asq-followup --url <URL>        # Direct URL to Gemini notes
/asq-followup --asq <ASQ_ID>     # Specific ASQ ID
/asq-followup --customer <NAME>   # Search by customer name
/asq-followup --date <DATE>      # Search by meeting date
/asq-followup --manual           # Skip search, manual input
```

## Dependencies

- fe-sts plugin v2.0.2+
- salesforce-actions skill (for ASQ lookup)
- gmail skill (with Gemini email access)
- google-calendar skill
- google-drive skill (for URL-based retrieval)
- slack MCP connection (optional)
- asq_tools.py availability subcommand

## Notes

- This skill is designed as a companion to asq-update, not a replacement
- Focus on customer-facing outputs (email) vs internal (SFDC notes)
- Maintains zero-approval pattern for safety
- Compatible with existing asq-update workflow