# Chatter Comment Templates for ASQ Triage

## Chatter Payload Construction

All Chatter comments are posted via `sfdc-chatter` using a JSON payload. @mentions must use Salesforce User IDs.

### Payload Structure

```json
{
  "feedElementType": "FeedItem",
  "subjectId": "<ASQ_RECORD_ID>",
  "body": {
    "messageSegments": [
      {"type": "Text", "text": "Hi "},
      {"type": "Mention", "id": "<USER_ID>"},
      {"type": "Text", "text": ", <message text>"}
    ]
  }
}
```

### How to Get User IDs

- **Creator**: Use `CreatedById` from the ASQ record (already available from Phase 1 query)
- **Assignee**: Query the User object if needed:
  ```bash
  python3 $ASQ_TOOLS sfdc-query "SELECT Id, Name, Email FROM User WHERE Name = '<assignee name>'"
  ```

### Posting a Comment

```bash
python3 -c "import json; json.dump(<payload_dict>, open('/tmp/asq_chatter_<AR>.json', 'w'))"
python3 $ASQ_TOOLS sfdc-chatter /tmp/asq_chatter_<AR>.json
```

---

## Template 1: Under Review — UC Stage Not Met (non-Launch Accelerator)

**When to use**: Support Type is NOT Launch Accelerator, and no linked Use Case meets U4+.

**Message segments**:
```json
[
  {"type": "Text", "text": "Hi "},
  {"type": "Mention", "id": "<CREATOR_USER_ID>"},
  {"type": "Text", "text": ", We engage in U4 or later for activated accounts. Can you confirm if the tech win is achieved for the use case? If yes, can you please move the use-case case object to the confirming/onboarding stage? or attach the right use case to the ASQ (top right drop-down --> link use case)"}
]
```

---

## Template 2: Under Review — UC Stage Not Met (Launch Accelerator)

**When to use**: Support Type is Launch Accelerator, and no linked Use Case meets U3+.

**Message segments**:
```json
[
  {"type": "Text", "text": "Hi "},
  {"type": "Mention", "id": "<CREATOR_USER_ID>"},
  {"type": "Text", "text": ", We engage in U3 or later for Launch Accelerator accounts. Can you confirm the use case will be in stage 3? If yes, can you please move the use-case case object to the confirming/onboarding stage? or attach the right use case to the ASQ (top right drop-down --> link use case)"}
]
```

---

## Template 3: Under Review — LA Consumption Too High

**When to use**: Support Type is Launch Accelerator and account consumption exceeds $1K/month.

**Message segments**:
```json
[
  {"type": "Text", "text": "Hi "},
  {"type": "Mention", "id": "<CREATOR_USER_ID>"},
  {"type": "Text", "text": ", We do not support Launch Accelerator for accounts consuming more than 1K dollars. We could support independent traditional services such as [SUGGESTED_SERVICES]. More info in go/sts."}
]
```

**Note**: Replace `[SUGGESTED_SERVICES]` with the specific Core Services that match the request description (e.g., "Workspace Setup", "Lakeflow", "UC Setup"). Use the keyword-to-service mapping in `triage-rules.md` to identify the right services.

---

## Template 4: Under Review — No Description

**When to use**: The `Request_Description__c` field is empty or null.

**Message segments**:
```json
[
  {"type": "Text", "text": "Hi "},
  {"type": "Mention", "id": "<CREATOR_USER_ID>"},
  {"type": "Text", "text": ", the ASQ has no request description. Could you please fill in the Situation, Ask, and Desired Outcome so we can assess scope and assign appropriately?"}
]
```

---

## Template 5: Under Review — Out of Scope (Break-fix)

**When to use**: Request describes break-fix issues (DNS, auth errors, connectivity troubleshooting).

**Message segments** (customize `[describe specific issue]`):
```json
[
  {"type": "Text", "text": "Hi "},
  {"type": "Mention", "id": "<CREATOR_USER_ID>"},
  {"type": "Text", "text": ", [describe specific issue] are break-fix scenarios better handled by the Support team. Please consider filing a support ticket. If there's a broader platform setup need, please update the description."}
]
```

**Note**: Replace `[describe specific issue]` with the specific break-fix issue identified in the description (e.g., "DNS resolution failures and 403 authentication errors").

---

## Template 6: Under Review — Out of Scope (L400+ / SSA Redirect)

**When to use**: Request describes L400+ deep architecture reviews or advanced performance tuning.

**Message segments**:
```json
[
  {"type": "Text", "text": "Hi "},
  {"type": "Mention", "id": "<CREATOR_USER_ID>"},
  {"type": "Text", "text": ", this request appears to require L400+ deep architecture review or advanced performance tuning, which is best handled by a Specialist Solution Architect (SSA). Please consider filing an SSA ASQ instead. If part of this request aligns with STS services (e.g., [alternative in-scope service]), please update the description with more context."}
]
```

**Note**: Replace `[alternative in-scope service]` with the closest in-scope service (e.g., "Delta Optimizations & Maintenance" or "Lakeflow setup").

---

## Template 6b: Under Review — Out of Scope (Enablement / Training)

**When to use**: Request describes training, workshops, or "learn about X" scenarios.

**Message segments**:
```json
[
  {"type": "Text", "text": "Hi "},
  {"type": "Mention", "id": "<CREATOR_USER_ID>"},
  {"type": "Text", "text": ", STS provides outcome-based coaching on feature activation, not training or enablement workshops. We recommend starting with free self-paced resources: Databricks Academy (academy.databricks.com), DB Demos, and Solutions Accelerators. Once the customer has completed enablement and has a specific activation goal, feel free to file a new ASQ with the technical milestone you'd like to achieve."}
]
```

---

## Template 6c: Under Review — Out of Scope (DBR Migration)

**When to use**: Request is specifically about DBR version migration.

**Message segments**:
```json
[
  {"type": "Text", "text": "Hi "},
  {"type": "Mention", "id": "<CREATOR_USER_ID>"},
  {"type": "Text", "text": ", DBR version migrations are supported through 1:many monthly office hours only (no ASQ needed). Please direct the customer to the #dbr-migration-squad Slack channel and the monthly 'Databricks Office Hours: DBR Migration' sessions."}
]
```

---

## Template 7: Assign — On Hold

**When to use**: ASQ passes all checks and is being assigned to a team member.

**Message segments**:
```json
[
  {"type": "Text", "text": "Hi "},
  {"type": "Mention", "id": "<CREATOR_USER_ID>"},
  {"type": "Text", "text": ", I've assigned the ASQ to "},
  {"type": "Mention", "id": "<ASSIGNEE_USER_ID>"},
  {"type": "Text", "text": ", please align with them on scope and timelines."}
]
```

---

## Template 8: Under Review — Follow-Up Reminder

**When to use**: ASQ has been Under Review for 5+ business days with no response from the creator.

**Message segments**:
```json
[
  {"type": "Text", "text": "Hi "},
  {"type": "Mention", "id": "<CREATOR_USER_ID>"},
  {"type": "Text", "text": ", friendly reminder — this ASQ has been Under Review since [DATE]. Could you please update [the use case stage / the description / etc.] so we can proceed with triage?"}
]
```

**Note**: Replace `[DATE]` with the date the ASQ was put Under Review, and `[the use case stage / the description / etc.]` with the specific blocker.

---

## Template 9: Under Review — Resolved, Now Assigning

**When to use**: A previously Under Review ASQ now passes triage checks (e.g., UC stage was updated, description was filled in) and is being assigned.

**Message segments**:
```json
[
  {"type": "Text", "text": "Hi "},
  {"type": "Mention", "id": "<CREATOR_USER_ID>"},
  {"type": "Text", "text": ", thanks for updating the [use case stage / description]. I've now assigned the ASQ to "},
  {"type": "Mention", "id": "<ASSIGNEE_USER_ID>"},
  {"type": "Text", "text": ", please align with them on scope and timelines."}
]
```

**Note**: Replace `[use case stage / description]` with what was resolved.

---

## Combining Multiple Issues in One Message

When an ASQ has multiple issues (e.g., UC stage fail + no description + possible break-fix), combine them into a **single Chatter comment** with numbered items. Do NOT post separate comments for each issue.

**Pattern:**
```json
[
  {"type": "Text", "text": "Hi "},
  {"type": "Mention", "id": "<CREATOR_USER_ID>"},
  {"type": "Text", "text": ", a few items on this ASQ: (1) [first issue + action needed] (2) [second issue + action needed] (3) [third issue + action needed]"}
]
```

**Example** (UC fail + short description + possible break-fix):
> Hi @[CREATOR], a few items on this ASQ: (1) We engage in U4 or later — can you please move the use case to the confirming/onboarding stage, or attach the right use case? (2) The description is very brief — could you fill in the Situation, Ask, and Desired Outcome so we can assess scope? (3) The setup errors described may be better handled by Support — if there's a broader platform need beyond the errors, please clarify in the description.
