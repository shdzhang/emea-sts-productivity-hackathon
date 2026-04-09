# ASQ Follow-up Email Templates

This file contains email templates for different meeting types in the ASQ lifecycle.

## Template Variables

All templates support the following variables:
- `{ACCOUNT_NAME}` - Customer account name
- `{MEETING_DATE}` - Date of the meeting
- `{ATTENDEES}` - List of meeting attendees
- `{KEY_DECISIONS}` - Bullet list of decisions made
- `{ACTION_ITEMS}` - Formatted table of action items
- `{NEXT_STEPS}` - Bullet list of next steps
- `{NEXT_MEETING_DATE}` - Proposed follow-up date (if available)
- `{NEXT_MEETING_TIME}` - Proposed follow-up time (if available)
- `{AVAILABILITY_REQUEST}` - Availability request section (when no meeting scheduled)
- `{YOUR_NAME}` - Sender's name
- `{YOUR_TITLE}` - Sender's title

## Initial Meeting Follow-up

**Subject:** Follow-up: {ACCOUNT_NAME} - Initial Technical Discussion - {MEETING_DATE}

**Body:**
```
Dear Team,

Thank you for taking the time to meet with us today to discuss your data and AI initiatives. It was great to learn more about your goals and how Databricks can help accelerate your journey.

## Meeting Summary

**Key Decisions:**
{KEY_DECISIONS}

**Action Items:**
{ACTION_ITEMS}

## Next Steps
{NEXT_STEPS}

## Proposed Follow-up
{AVAILABILITY_REQUEST}

Looking forward to our continued collaboration.

Best regards,
{YOUR_NAME}
{YOUR_TITLE}
Databricks
```

## Progress Check-in Follow-up

**Subject:** Follow-up: {ACCOUNT_NAME} - Progress Update - {MEETING_DATE}

**Body:**
```
Hi Team,

Thank you for the productive progress review today. I'm pleased to see the momentum we're building together.

## Progress Highlights
{KEY_DECISIONS}

## Updated Action Items
{ACTION_ITEMS}

## Next Milestones
{NEXT_STEPS}

## Upcoming Meeting
{AVAILABILITY_REQUEST}

Best regards,
{YOUR_NAME}
{YOUR_TITLE}
Databricks
```

## Technical Deep Dive Follow-up

**Subject:** Follow-up: {ACCOUNT_NAME} - Technical Deep Dive - {MEETING_DATE}

**Body:**
```
Team,

Thank you for the engaging technical discussion today. I appreciate the detailed questions and the opportunity to explore how Databricks can address your specific requirements.

## Technical Decisions
{KEY_DECISIONS}

## Technical Action Items
{ACTION_ITEMS}

## Documentation and Resources
As discussed, I'll be sharing the following:
{NEXT_STEPS}

## Next Technical Session
{AVAILABILITY_REQUEST}

Please let me know if you need any clarification on the topics we covered.

Best regards,
{YOUR_NAME}
{YOUR_TITLE}
Databricks
```

## Blocker Resolution Follow-up

**Subject:** Follow-up: {ACCOUNT_NAME} - Blocker Resolution Discussion - {MEETING_DATE}

**Body:**
```
Team,

Thank you for the open discussion today about the challenges you're facing. I'm confident we can work together to resolve these blockers and keep the project moving forward.

## Identified Blockers and Resolutions
{KEY_DECISIONS}

## Immediate Actions Required
{ACTION_ITEMS}

## Mitigation Steps
{NEXT_STEPS}

## Follow-up Check-in
{AVAILABILITY_REQUEST}

If any urgent issues arise before then, please don't hesitate to reach out.

Best regards,
{YOUR_NAME}
{YOUR_TITLE}
Databricks
```

## Closing Meeting Follow-up

**Subject:** Follow-up: {ACCOUNT_NAME} - Project Closure & Next Steps - {MEETING_DATE}

**Body:**
```
Team,

Congratulations on reaching this milestone! It's been a pleasure working with you throughout this engagement.

## Project Achievements
{KEY_DECISIONS}

## Handover Items
{ACTION_ITEMS}

## Post-Project Support
{NEXT_STEPS}

## Future Collaboration
While this phase is complete, I remain available for any questions or future initiatives.

{AVAILABILITY_REQUEST}

Thank you for the opportunity to partner with you on this journey.

Best regards,
{YOUR_NAME}
{YOUR_TITLE}
Databricks
```

## Email Template Selection Logic

The skill should select templates based on keywords and context from the meeting notes:

| Keywords/Context | Template |
|-----------------|----------|
| "initial", "kickoff", "introduction", "first meeting" | Initial Meeting |
| "progress", "update", "status", "check-in" | Progress Check-in |
| "technical", "architecture", "deep dive", "POC" | Technical Deep Dive |
| "blocker", "issue", "problem", "challenge" | Blocker Resolution |
| "closing", "completion", "handover", "final" | Closing Meeting |
| Default (if no match) | Progress Check-in |

## Availability Request Templates

The `{AVAILABILITY_REQUEST}` variable is populated based on whether follow-up meeting details were found in the notes:

### When Follow-up Meeting is Scheduled
If the meeting notes contain a specific follow-up date/time:
```
Our next meeting is scheduled for {NEXT_MEETING_DATE} at {NEXT_MEETING_TIME} to review progress on the action items and discuss next steps.

Please let me know if this time still works for everyone or if we need to reschedule.
```

### When No Follow-up Meeting is Scheduled
If no follow-up meeting details were found in the notes:
```
I'd like to schedule our next discussion to review progress on the action items and plan our next steps. Based on calendar availability, I've identified the following potential slots:

• Option 1: {AVAILABILITY_SLOT_1}
• Option 2: {AVAILABILITY_SLOT_2}
• Option 3: {AVAILABILITY_SLOT_3}

Please let me know which time works best for you, or suggest an alternative if none of these fit your schedule. Once confirmed, I'll send a calendar invitation with the meeting details and agenda.
```

## Availability Slot Generation

The skill will generate availability slots by:
1. Running availability scan for next 2 weeks
2. Finding 3 non-conflicting slots during business hours
3. Formatting as: "Day, Month Date at Time (Timezone)"
4. Example: "Tuesday, April 15 at 2:00 PM (PT)"

## Customization Notes

1. **Tone Adjustment**: Templates can be made more formal/informal based on customer preference
2. **Length**: Templates can be condensed for executives or expanded for technical teams
3. **Formatting**: HTML formatting can be applied for better visual structure
4. **Attachments**: References to attachments can be added in the resources section
5. **Signatures**: Company signatures and legal disclaimers can be appended
6. **Availability Windows**: Default 2 weeks, can be adjusted based on urgency
7. **Time Zones**: Auto-detect customer timezone from attendee domains