# Gemini Meeting Notes Parser

This document describes how to retrieve and parse Google Gemini meeting notes from Gmail or directly via URL for the asq-followup skill.

## Gemini Email Structure

Gemini meeting notes typically arrive with these characteristics:

### Email Headers
- **From:** meet-recordings-noreply@google.com or similar Gemini address
- **Subject:** Usually contains:
  - Meeting title
  - Date/time
  - "Meeting notes" or "Meeting summary"
  - Sometimes participant names
- **Arrival Time:** Usually within 10-30 minutes after meeting ends

### Email Body Structure
```
Meeting: [Meeting Title]
Date: [Date and Time]
Participants: [List of attendees]
Duration: [Meeting length]

Summary:
[AI-generated meeting summary]

Key Topics Discussed:
• [Topic 1]
• [Topic 2]
• [Topic 3]

Action Items:
• [Action 1]
• [Action 2]

Next Steps:
[Suggested follow-ups]

Full Transcript:
[Optional - complete meeting transcript]
```

## URL-Based Retrieval

### Supported URL Patterns

```python
GEMINI_URL_PATTERNS = {
    'meet_recording': r'https://meet\.google\.com/recording/([a-zA-Z0-9\-]+)',
    'drive_recording': r'https://drive\.google\.com/file/d/([a-zA-Z0-9\-_]+)',
    'meet_transcript': r'https://meet\.google\.com/.*[?&]transcript=([a-zA-Z0-9\-_]+)',
    'calendar_event': r'https://calendar\.google\.com/.*[?&]eid=([a-zA-Z0-9]+)',
}
```

### Extract Meeting ID from URL

```python
def extract_meeting_id_from_url(url):
    """Extract meeting ID from various Google Meet/Drive URLs"""

    for pattern_name, pattern in GEMINI_URL_PATTERNS.items():
        match = re.search(pattern, url)
        if match:
            return {
                'type': pattern_name,
                'id': match.group(1),
                'url': url
            }

    return None
```

### Fetch Notes via URL

```python
def fetch_gemini_notes_from_url(url):
    """Fetch Gemini meeting notes using provided URL"""

    meeting_info = extract_meeting_id_from_url(url)

    if not meeting_info:
        raise ValueError(f"Unrecognized URL format: {url}")

    if meeting_info['type'] == 'meet_recording':
        # Try to find associated email using meeting ID
        return search_gmail_by_meeting_id(meeting_info['id'])

    elif meeting_info['type'] == 'drive_recording':
        # Fetch from Google Drive
        return fetch_from_drive(meeting_info['id'])

    elif meeting_info['type'] == 'meet_transcript':
        # Direct transcript access
        return fetch_transcript_directly(meeting_info['id'])

    elif meeting_info['type'] == 'calendar_event':
        # Find via calendar event
        return fetch_via_calendar(meeting_info['id'])
```

### Search Gmail by Meeting ID

```python
def search_gmail_by_meeting_id(meeting_id):
    """Search Gmail for Gemini notes using meeting ID from URL"""

    # Build search query using meeting ID
    query = f'from:meet-recordings-noreply@google.com "{meeting_id}"'

    # Execute search
    results = mcp__google__gmail_message_list(
        q=query,
        max_results=5
    )

    if results:
        # Get the most recent match
        return get_gemini_email_content(results[0]['id'])

    # If not in Gmail, try alternative retrieval
    return fetch_from_meet_directly(meeting_id)
```

### Direct Meet API Access

```python
def fetch_from_meet_directly(meeting_id):
    """Attempt to fetch notes directly from Meet API"""

    # Note: This might require additional OAuth scopes
    try:
        # Use Google Meet API if available
        meet_api_url = f"https://meet.googleapis.com/v1/recordings/{meeting_id}/transcript"

        # Would need proper API client setup
        # This is pseudocode for the approach
        response = google_api_client.get(meet_api_url)

        return parse_meet_api_response(response)
    except:
        # Fall back to web scraping or manual input
        return None
```

### Fetch from Google Drive

```python
def fetch_from_drive(file_id):
    """Fetch meeting notes from Google Drive"""

    try:
        # Export the document as text
        content = mcp__google__drive_file_export(
            file_id=file_id,
            mime_type='text/plain'
        )

        return content
    except Exception as e:
        print(f"Error fetching from Drive: {e}")
        return None
```

## Gmail Search Implementation

### Search for Gemini Notes

```python
def search_gemini_notes(customer_name=None, meeting_date=None, asq_id=None):
    """Search Gmail for Gemini meeting notes"""

    # Build search query
    query_parts = [
        'from:(meet-recordings-noreply@google.com OR gemini-noreply@google.com)',
        'subject:("meeting notes" OR "meeting summary" OR "meeting recap")'
    ]

    if customer_name:
        query_parts.append(f'subject:"{customer_name}"')

    if meeting_date:
        # Format: after:2024/4/7 before:2024/4/9
        date_str = meeting_date.strftime('%Y/%m/%d')
        next_day = (meeting_date + timedelta(days=1)).strftime('%Y/%m/%d')
        query_parts.append(f'after:{date_str} before:{next_day}')
    else:
        # Default to last 48 hours
        query_parts.append('newer_than:2d')

    if asq_id:
        # Try to find ASQ ID in email body or subject
        query_parts.append(f'("{asq_id}" OR "ASQ-{asq_id}")')

    gmail_query = ' '.join(query_parts)

    # Execute search using Google MCP
    results = mcp__google__gmail_message_list(
        q=gmail_query,
        max_results=10
    )

    return results
```

### Retrieve Full Email Content

```python
def get_gemini_email_content(message_id):
    """Retrieve full Gemini email content"""

    # Get full message with body
    message = mcp__google__gmail_message_get(
        message_id=message_id,
        format='full'
    )

    # Extract and decode body
    body = extract_email_body(message)

    return body
```

## Parsing Gemini Notes Format

### Extract Sections from Gemini Email

```python
def parse_gemini_notes(email_body):
    """Parse structured Gemini meeting notes"""

    sections = {
        'meeting_title': '',
        'date': '',
        'participants': [],
        'duration': '',
        'summary': '',
        'topics': [],
        'action_items': [],
        'next_steps': [],
        'transcript': ''
    }

    # Use regex patterns to extract sections
    patterns = {
        'meeting_title': r'Meeting:\s*(.+?)(?:\n|$)',
        'date': r'Date:\s*(.+?)(?:\n|$)',
        'participants': r'Participants:\s*(.+?)(?:\n\n|$)',
        'duration': r'Duration:\s*(.+?)(?:\n|$)',
        'summary': r'Summary:\s*(.+?)(?:Key Topics|Action Items|\n\n)',
        'topics': r'Key Topics.*?:\s*(.+?)(?:Action Items|Next Steps|\n\n)',
        'action_items': r'Action Items:\s*(.+?)(?:Next Steps|Full Transcript|\n\n|$)',
        'next_steps': r'Next Steps:\s*(.+?)(?:Full Transcript|\n\n|$)',
        'transcript': r'Full Transcript:\s*(.+?)$'
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, email_body, re.DOTALL | re.IGNORECASE)
        if match:
            content = match.group(1).strip()

            # Parse lists for certain fields
            if key in ['topics', 'action_items']:
                # Split by bullet points or newlines
                items = re.findall(r'[•\-\*]\s*(.+?)(?:\n|$)', content)
                sections[key] = items
            elif key == 'participants':
                # Split by commas or newlines
                sections[key] = [p.strip() for p in re.split(r'[,\n]', content)]
            else:
                sections[key] = content

    return sections
```

## Integration with ASQ Lookup

### Match Gemini Notes to ASQ

```python
def match_notes_to_asq(gemini_notes, asq_id=None):
    """Match Gemini notes to specific ASQ"""

    if asq_id:
        # Direct match provided
        return asq_id

    # Try to extract from participants or meeting title
    participants = gemini_notes.get('participants', [])
    meeting_title = gemini_notes.get('meeting_title', '')

    # Look for customer company name in participants
    customer_domains = extract_domains(participants)

    # Query SFDC for matching ASQ
    sfdc_query = f"""
    SELECT Id, Account_Name__c, Primary_Contact__c
    FROM ASQ__c
    WHERE Status__c = 'Active'
    AND (
        Account_Domain__c IN ({','.join(customer_domains)})
        OR Account_Name__c LIKE '%{extract_company_name(meeting_title)}%'
    )
    ORDER BY LastModifiedDate DESC
    LIMIT 5
    """

    matches = salesforce_query(sfdc_query)

    if len(matches) == 1:
        return matches[0]['Id']
    elif len(matches) > 1:
        # Present options to user
        return prompt_user_selection(matches)
    else:
        # No match found, prompt for ASQ ID
        return prompt_for_asq_id()
```

## Enhanced Action Item Extraction

Gemini typically provides action items in a cleaner format:

```python
def extract_gemini_action_items(action_items_text):
    """Extract structured action items from Gemini format"""

    items = []

    # Gemini patterns:
    # "John to send proposal by Friday"
    # "Sarah will review documentation (by April 15)"
    # "Customer to confirm budget approval"

    patterns = [
        r'([A-Z][a-z]+ ?[A-Z]?[a-z]*) (?:to|will) (.+?)(?:\(by (.+?)\))?$',
        r'([A-Z][a-z]+ ?[A-Z]?[a-z]*): (.+?)(?:by (.+?))?$',
    ]

    for item_text in action_items_text:
        for pattern in patterns:
            match = re.match(pattern, item_text.strip())
            if match:
                owner = match.group(1)
                task = match.group(2)
                due = match.group(3) if len(match.groups()) > 2 else 'TBD'

                # Normalize owner
                if owner.lower() in ['customer', 'client']:
                    owner = 'Customer Team'

                items.append({
                    'owner': owner,
                    'task': task.strip(),
                    'due_date': parse_date(due) if due else 'TBD'
                })
                break

    return items
```

## Workflow Integration

### Complete Gemini-based Workflow

```python
def process_gemini_meeting_notes(url=None, customer_name=None, meeting_date=None, asq_id=None):
    """Main workflow for processing Gemini notes"""

    # Step 0: If URL provided, try direct retrieval first
    if url:
        try:
            email_content = fetch_gemini_notes_from_url(url)
            if email_content:
                gemini_data = parse_gemini_notes(email_content)
                return process_extracted_data(gemini_data, asq_id)
        except Exception as e:
            print(f"URL retrieval failed: {e}, falling back to email search")

    # Step 1: Search for Gemini emails
    emails = search_gemini_notes(customer_name, meeting_date, asq_id)

    if not emails:
        return fallback_to_manual_input()

    # Step 2: Select email (if multiple)
    if len(emails) > 1:
        selected_email = prompt_email_selection(emails)
    else:
        selected_email = emails[0]

    # Step 3: Retrieve full content
    email_content = get_gemini_email_content(selected_email['id'])

    # Step 4: Parse Gemini structure
    gemini_data = parse_gemini_notes(email_content)

    # Step 5: Match to ASQ
    matched_asq_id = match_notes_to_asq(gemini_data, asq_id)

    # Step 6: Extract structured data
    structured_data = {
        'meeting_type': classify_meeting_type(gemini_data),
        'attendees': gemini_data['participants'],
        'meeting_date': parse_date(gemini_data['date']),
        'action_items': extract_gemini_action_items(gemini_data['action_items']),
        'key_decisions': gemini_data['topics'],
        'next_topics': parse_next_steps(gemini_data['next_steps']),
        'raw_notes': gemini_data['summary'] + '\n\n' + gemini_data.get('transcript', '')
    }

    return structured_data, matched_asq_id
```

## User Prompts for Gemini Workflow

### Initial Prompt
```
I'll help you process your meeting follow-up.

How would you like to identify the meeting?
1. Provide Gemini/Meet recording URL
2. Search by customer name
3. Search by date
4. Provide ASQ ID
5. Show recent Gemini notes
6. Paste notes manually

Choice:
```

### URL Input Prompt
```
Please provide the Google Meet recording or Gemini notes URL:

User: https://meet.google.com/recording/abc-defg-hij

Agent: Retrieving meeting notes from the provided URL...

Found meeting: "Acme Corp - Technical Review"
Date: April 8, 2024
Processing the transcript...
```

### Multiple Matches Prompt
```
I found multiple Gemini meeting notes:

1. [Meeting: Acme Corp Technical Review - Apr 8, 2024]
   Participants: John Smith, Sarah Jones, Mike Wilson

2. [Meeting: Acme Corp Budget Discussion - Apr 8, 2024]
   Participants: John Smith, Lisa Chen

Which meeting would you like to process?
```

### Confirmation Prompt
```
I've retrieved the Gemini notes for:
Meeting: {meeting_title}
Date: {date}
Participants: {participants}

Found {len(action_items)} action items and {len(decisions)} key decisions.

Proceed with follow-up generation? (yes/no)
```

## Error Handling

| Scenario | Handling |
|----------|----------|
| No Gemini emails found | Offer to search different date range or manual input |
| Multiple customers same day | Present list for selection |
| Gemini format changed | Fall back to generic parsing |
| Email access denied | Request Gmail permissions |
| Partial Gemini data | Supplement with manual input |

## Configuration Options

```yaml
gemini_settings:
  search_window_hours: 48  # How far back to search
  auto_match_confidence: 0.85  # Confidence for auto-matching to ASQ
  include_transcript: false  # Whether to include full transcript
  sender_addresses:  # Possible Gemini sender addresses
    - meet-recordings-noreply@google.com
    - gemini-noreply@google.com
    - meeting-notes@google.com
```