# Meeting Notes Parser Reference

This document defines the LLM prompts and parsing logic for extracting structured information from meeting notes, with special handling for Gemini-formatted notes from Gmail.

## Input Source Detection

```python
def detect_input_source(meeting_notes):
    """Detect if notes are from Gemini or manual input"""

    gemini_indicators = [
        'Meeting:',
        'Participants:',
        'Key Topics Discussed:',
        'Action Items:',
        'Full Transcript:'
    ]

    gemini_score = sum(1 for indicator in gemini_indicators if indicator in meeting_notes)

    if gemini_score >= 3:
        return 'gemini'
    else:
        return 'manual'
```

## Primary Extraction Prompt

```
You are an expert at analyzing meeting notes and extracting structured information. Please analyze the following meeting notes and extract:

1. **Action Items** - Format each as: [Owner Name] - [Task Description] - [Due Date]
   - If no due date mentioned, use "TBD"
   - If owner unclear, use "Team"

2. **Key Decisions** - List important decisions or agreements made
   - Focus on concrete outcomes, not discussions
   - Include any approved proposals or confirmed directions

3. **Open Questions/Blockers** - List unresolved items
   - Include any dependencies mentioned
   - Note any risks or concerns raised

4. **Next Meeting Topics** - Suggested agenda items for follow-up
   - Based on action items and open questions
   - Include any explicitly mentioned future discussions

5. **Follow-up Meeting Details** - Extract scheduled follow-up meeting info
   - Look for phrases like "next meeting on", "follow up on", "meet again on", "reconvene"
   - Extract date patterns like "next Tuesday", "April 15", "4/15 at 2pm"
   - Include time and timezone if mentioned
   - Mark as "NOT_FOUND" if no specific meeting scheduled

6. **UCO Stage Indicators** - Identify progression signals
   - Look for phrases like: "approved", "ready to proceed", "confirmed", "signed off"
   - Note any milestone completions
   - Identify readiness for next phase

7. **Meeting Type Classification** - Categorize the meeting
   - Options: Initial/Kickoff, Progress Update, Technical Deep Dive, Blocker Resolution, Closing
   - Base on content and discussion topics

Meeting Notes:
{MEETING_NOTES}

Please provide the extracted information in a structured JSON format.
```

## Expected JSON Output Schema

```json
{
  "meeting_type": "Progress Update",
  "attendees": ["John Smith", "Sarah Jones", "Mike Wilson"],
  "meeting_date": "2024-04-08",
  "account_name": "Acme Corporation",

  "action_items": [
    {
      "owner": "John Smith",
      "task": "Review and approve the technical architecture document",
      "due_date": "2024-04-15",
      "priority": "high"
    },
    {
      "owner": "Sarah Jones",
      "task": "Send API documentation to the customer team",
      "due_date": "2024-04-12",
      "priority": "medium"
    }
  ],

  "key_decisions": [
    "Approved Phase 1 implementation plan",
    "Confirmed Q2 timeline for production deployment",
    "Agreed on weekly status meetings"
  ],

  "open_questions": [
    "Budget approval pending from finance team",
    "Integration approach with legacy system needs review",
    "Security audit requirements to be confirmed"
  ],

  "next_topics": [
    "Review Phase 1 implementation progress",
    "Discuss integration architecture",
    "Plan user training sessions"
  ],

  "follow_up_meeting": {
    "scheduled": true,
    "date": "2024-04-15",
    "time": "14:00",
    "timezone": "PT",
    "raw_text": "next Tuesday at 2pm PT",
    "confidence": 0.9
  },

  "uco_indicators": {
    "current_stage": "U2",
    "suggested_stage": "U3",
    "progression_signals": [
      "Customer confirmed readiness to proceed",
      "Technical POC approved",
      "Budget allocation discussed"
    ],
    "confidence": 0.85
  }
}
```

## Parsing Patterns

### Action Item Patterns

Common patterns to identify action items:
- "will [action]" → Future commitment
- "to do:" → Explicit task marker
- "action:" → Explicit action marker
- "needs to [action]" → Required task
- "follow up on" → Follow-up task
- "send/share/provide" → Delivery task
- "review/approve/confirm" → Decision task

### Owner Extraction

Rules for identifying task owners:
1. Name mentioned before the action verb
2. "I will" → Meeting organizer
3. "We will" → Team or multiple owners
4. "Customer will" → Customer team
5. No owner mentioned → Assign to "Team"

### Due Date Extraction

Patterns for extracting deadlines:
- "by [date]" → Explicit deadline
- "next [day]" → Relative date
- "end of [period]" → Period end
- "ASAP" → Within 2 business days
- "before [event]" → Event-based deadline
- No date → "TBD"

### Follow-up Meeting Extraction

Patterns for identifying scheduled follow-up meetings:
- "next meeting on [date]" → Explicit meeting date
- "follow up on [date] at [time]" → Date and time
- "reconvene next [day]" → Relative date
- "meet again [date] [time] [timezone]" → Full details
- "schedule for [date]" → Proposed date
- "calendar invite for [date]" → Confirmed meeting
- "sync up on [day]" → Informal meeting
- "check in [timeframe]" → Regular cadence

Time patterns:
- "2pm", "14:00", "2:00 PM" → Time formats
- "PT", "PST", "Pacific" → Timezone indicators
- "morning", "afternoon" → General time

Date patterns:
- "April 15", "4/15", "15th April" → Specific dates
- "next Tuesday", "tomorrow", "next week" → Relative dates
- "in 2 weeks", "end of month" → Period-based

### UCO Stage Mapping

| Stage | Indicators |
|-------|------------|
| U0→U1 | "initial meeting", "introduction", "exploring options" |
| U1→U2 | "requirements gathered", "use case defined", "POC requested" |
| U2→U3 | "POC successful", "technical validation complete", "proceeding with implementation" |
| U3→U4 | "in production", "deployment started", "going live" |
| U4→U5 | "expanding usage", "additional use cases", "scaling up" |

## Follow-up Meeting Extraction Implementation

```python
def extract_follow_up_meeting(meeting_notes):
    """Extract follow-up meeting details from meeting notes"""

    follow_up_patterns = [
        r'next meeting (?:on |is )?([^,\.\n]+)',
        r'follow[- ]?up (?:on |meeting |call )([^,\.\n]+)',
        r'reconvene (?:on |next )?([^,\.\n]+)',
        r'meet again (?:on )?([^,\.\n]+)',
        r'schedule(?:d)? for ([^,\.\n]+)',
        r'calendar invite for ([^,\.\n]+)',
        r'sync up (?:on |next )?([^,\.\n]+)',
        r'check[- ]?in (?:on |scheduled for )?([^,\.\n]+)'
    ]

    for pattern in follow_up_patterns:
        match = re.search(pattern, meeting_notes, re.IGNORECASE)
        if match:
            raw_text = match.group(1).strip()
            parsed = parse_meeting_datetime(raw_text)
            if parsed:
                return {
                    "scheduled": True,
                    "date": parsed.get("date"),
                    "time": parsed.get("time"),
                    "timezone": parsed.get("timezone", "PT"),
                    "raw_text": raw_text,
                    "confidence": 0.85
                }

    return {
        "scheduled": False,
        "date": None,
        "time": None,
        "timezone": None,
        "raw_text": None,
        "confidence": 0
    }

def parse_meeting_datetime(text):
    """Parse date and time from extracted text"""

    # Extract time
    time_pattern = r'(\d{1,2}):?(\d{2})?\s*(am|pm|AM|PM)?|\b(\d{1,2})\s*(am|pm|AM|PM)'
    time_match = re.search(time_pattern, text)

    # Extract timezone
    tz_pattern = r'\b(PT|PST|PDT|ET|EST|EDT|CT|CST|CDT|MT|MST|MDT|GMT|UTC)\b'
    tz_match = re.search(tz_pattern, text, re.IGNORECASE)

    # Extract date (simplified - would use dateutil in production)
    date_patterns = [
        r'(\d{1,2})[/-](\d{1,2})[/-]?(\d{2,4})?',  # MM/DD or MM/DD/YYYY
        r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{1,2})',  # Month DD
        r'next\s+(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*',  # Next weekday
        r'tomorrow',
        r'next\s+week'
    ]

    result = {}

    if time_match:
        result["time"] = format_time(time_match)

    if tz_match:
        result["timezone"] = tz_match.group(1).upper()

    for pattern in date_patterns:
        date_match = re.search(pattern, text, re.IGNORECASE)
        if date_match:
            result["date"] = format_date(date_match)
            break

    return result if result else None
```

## Fallback Extraction

If LLM extraction fails or returns incomplete data:

```python
def fallback_extraction(meeting_notes):
    """Manual pattern-based extraction as fallback"""

    action_items = []

    # Look for bullet points with action verbs
    action_verbs = ['send', 'share', 'review', 'create', 'setup',
                   'schedule', 'provide', 'prepare', 'confirm']

    lines = meeting_notes.split('\n')
    for line in lines:
        for verb in action_verbs:
            if verb in line.lower():
                action_items.append({
                    'owner': 'Team',
                    'task': line.strip('- •*').strip(),
                    'due_date': 'TBD'
                })

    return {
        'action_items': action_items,
        'key_decisions': [],
        'open_questions': [],
        'next_topics': [],
        'meeting_type': 'Progress Update'
    }
```

## Quality Validation

After extraction, validate the results:

1. **Action Items Check**
   - At least one action item should be present
   - Each action should have an owner (even if "Team")
   - Due dates should be realistic (not in the past)

2. **Decision Validation**
   - Decisions should be concrete, not vague
   - Should represent actual outcomes

3. **UCO Stage Logic**
   - Suggested stage should not regress
   - Confidence should reflect signal strength
   - Only suggest progression with clear indicators

## Error Handling

| Error Type | Handling |
|-----------|----------|
| No content extracted | Prompt user for manual input |
| Invalid JSON from LLM | Use fallback extraction |
| Missing critical fields | Request user clarification |
| Conflicting information | Present options to user |

## Example Meeting Notes Input

### Example 1: With Explicit Follow-up Meeting
```
Meeting with Acme Corp - April 8, 2024

Attendees: John Smith (Databricks), Sarah Jones (Databricks), Mike Wilson (Acme), Lisa Chen (Acme)

Discussion:
- Reviewed the POC results from last week
- Customer very happy with performance improvements (10x faster queries)
- Mike confirmed they want to proceed with Phase 1 implementation
- Budget approval expected by end of week

Action Items:
- John to send the implementation plan by April 15
- Sarah to provide API documentation by April 12
- Mike to get final budget approval by April 10
- Schedule technical deep dive for next week

Next Steps:
- Begin environment setup once budget approved
- Plan training sessions for Acme team
- Review security requirements

We agreed to meet again next Tuesday April 15 at 2:00 PM PT to review the implementation plan.
The customer is ready to move forward pending budget approval.
```

### Example 2: Without Specific Follow-up Meeting
```
Meeting with Beta Corp - April 8, 2024

Attendees: John Smith (Databricks), Sarah Jones (Databricks), Alex Johnson (Beta)

Discussion:
- Discussed initial requirements for data platform
- Customer interested in real-time analytics capabilities
- Need to evaluate current infrastructure

Action Items:
- John to prepare technical assessment by April 12
- Sarah to share case studies by April 10
- Alex to gather current system documentation

Next Steps:
- Review technical requirements
- Schedule architecture session
- Prepare cost estimates

The customer will review internally and get back to us with next steps.
We should follow up once they've had time to review the materials.
```

## Improvement Patterns

The parser should learn from corrections:
1. Store user corrections to extraction
2. Build pattern library from successful extractions
3. Adjust confidence thresholds based on feedback
4. Maintain customer-specific parsing rules