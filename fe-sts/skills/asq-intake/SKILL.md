---
name: asq-intake
description: Onboard a new ASQ engagement — extract Salesforce data, create Google Drive workspace, build CONTEXT and STATUS docs
user-invocable: true  # Allow /asq-intake invocation
---

# ASQ Intake

Extracts ASQ information from Salesforce, performs initial customer discovery, classifies the engagement, and creates a structured Google Drive workspace with master context and status documents.

## Prerequisites
- Authenticated with Salesforce (ASQ read access)
- Google Drive access (create folders and Google Docs)
- ASQ exists in SFDC with a valid ASQ number (e.g., `AR-123456`)

## Workflow

### Phase 1: Retrieve ASQ Data from Salesforce
Input: ASQ number (e.g., `AR-123456`), or customer name / search term
Process:
1. If ASQ number provided:
   - Fetch ASQ record directly from Salesforce using sf CLI:
   ```bash
   sf data query --query "SELECT Id, Name, Status__c, Support_Type__c, Additional_Services__c, Request_Description__c, Account__c, Account__r.Name, CreatedDate, Start_Date__c, End_Date__c, CreatedBy.Name, LastModifiedDate, Request_Status_Notes__c FROM ApprovalRequest__c WHERE Name = 'AR-XXXXXX'" --json
   ```
   **NOTE:** Do NOT use `Last_SA_Engaged__r` — this relationship is not valid on ApprovalRequest__c. Fetch account owner separately in Phase 2.
2. If customer name or search term provided:
   - Search Salesforce for matching ASQs:
   ```bash
   sf data query --query "SELECT Id, Name, Status__c, Support_Type__c, Account__r.Name FROM ApprovalRequest__c WHERE Account__r.Name LIKE '%CUSTOMER_NAME%' AND Status__c IN ('In Progress', 'On Hold', 'New')" --json
   ```
   - If multiple matches, present list for user selection
3. Extract from the ASQ record:
   - **ASQ metadata:** number, status, creation date, requested start/end dates, additional services (service type)
   - **Request description:** the full description of what's being asked
   - **Customer type:** cloud provider (AWS, Azure, GCP) — infer from description or account data
   - **Related use cases:** any linked use cases on the account
4. If ASQ description is vague or incomplete, flag this explicitly — it signals a scoping call is needed
Output: Structured ASQ metadata

### Phase 1b: Retrieve Account Team
```bash
sf data query --query "SELECT Id, Name, OwnerId, Owner.Name, Owner.Email FROM Account WHERE Id = 'ACCOUNT_ID'" --json
```
Extract: Account owner (AE), plus the ASQ creator from Phase 1.

### Phase 2: Retrieve Account Data
Input: Account ID from Phase 1
Process:
1. Fetch account page from Salesforce
2. Extract:
   - **Account name and basic info**
   - **Consumption summary:** Total DBUs (1-30 days, 31-60 days), consumption mode breakdown (Interactive, Automated, SQL)
   - **Workspace info:** workspace names and IDs
   - **Contract info:** if visible, general contract stage
Output: Structured account profile

### Phase 3: Classify the Engagement
Input: ASQ description and account data from Phases 1-2
Process:
Based on the ASQ description, classify:
- **STS Pillar:** Platform / Data Engineering & Warehousing / ML & GenAI
- **Service type:** the specific service from the STS catalog (e.g., "Unity Catalog Setup", "Lakeflow", "GenAI Apps", "CI/CD", etc.)
- **Engagement format:** Launch Accelerator (multi-week) or Core Service (focused sessions)
- **Estimated complexity:** Simple (1-2 sessions) / Medium (3-4 sessions) / Complex (5+ sessions, Launch Accelerator)
Output: Classification labels

### Phase 4: Present Extracted Data for Review

**CRITICAL: Do NOT create the Google Drive workspace until the user has reviewed and approved the extracted data.**

Display all extracted and classified data in formatted output:
1. ASQ metadata table
2. CAST framework (Context, Ask, Success, Timeline) — note that Success and Timeline may be incomplete at intake
3. Account team
4. Customer profile
5. Classification

Prompt: "Review the above. Type 'approve' to create the Google Drive workspace, or specify what to modify."

### Phase 5: Create Google Drive Workspace
Input: Approved data from Phase 4
Process:

#### 5.1 Locate or Create the ASQs Root Folder
```python
# Search for existing ASQs folder
results = mcp__google__drive_search(
    query="ASQs",
    file_types=["folder"],
    max_results=5
)

# If not found, create it
if not found:
    asqs_folder = mcp__google__drive_file_create(
        name="ASQs",
        mime_type="application/vnd.google-apps.folder"
    )
```

#### 5.2 Create the Engagement Folder
```python
engagement_folder = mcp__google__drive_file_create(
    name=f"AR-{asq_number}_{customer_name}",
    mime_type="application/vnd.google-apps.folder",
    parents=[asqs_folder_id]
)
```

#### 5.3 Create Subfolders
```python
for subfolder_name in ["research", "sessions", "code", "comms"]:
    mcp__google__drive_file_create(
        name=subfolder_name,
        mime_type="application/vnd.google-apps.folder",
        parents=[engagement_folder_id]
    )
```

#### 5.4 Create the CONTEXT Google Doc

**IMPORTANT:** `mcp__google__docs_document_create_from_markdown` requires a file path, not inline content. Write the markdown to a temp file first, then create the doc from the file.

```python
# Step 1: Write markdown to temp file (use the Write tool)
# Write to /tmp/context_{ar_number}.md with the CONTEXT template content
# Include Google Drive References section with all folder/doc IDs from steps 5.1-5.3

# Step 2: Create Google Doc from the temp file
context_doc = mcp__google__docs_document_create_from_markdown(
    title="CONTEXT",
    markdown_file_path="/tmp/context_{ar_number}.md"
)

# Step 3: Move into engagement folder
mcp__google__drive_file_update(
    file_id=context_doc_id,
    add_parents=[engagement_folder_id]
)
```

#### 5.5 Create the STATUS Google Doc

```python
# Step 1: Write markdown to temp file
# Write to /tmp/status_{ar_number}.md with the STATUS template content

# Step 2: Create Google Doc from the temp file
status_doc = mcp__google__docs_document_create_from_markdown(
    title="STATUS",
    markdown_file_path="/tmp/status_{ar_number}.md"
)

# Step 3: Move into engagement folder
mcp__google__drive_file_update(
    file_id=status_doc_id,
    add_parents=[engagement_folder_id]
)
```

#### 5.6 Update CONTEXT doc with document IDs

Now that both docs are created, update the Google Drive References table in the CONTEXT doc with the actual CONTEXT and STATUS document IDs (which weren't known at write time).

Output: Engagement folder with CONTEXT doc, STATUS doc, and all subfolders created in Google Drive

### Phase 6: Confirm Completion
Display summary with links:
1. Engagement folder link (Google Drive)
2. CONTEXT doc link
3. STATUS doc link
4. All subfolder links
5. Classification summary
6. Any flags (vague description, incomplete CAST, etc.)

```
✅ Engagement workspace created: AR-XXXXX — Customer Name
   📁 Folder:  <Google Drive link>
   📄 CONTEXT: <Google Doc link>
   📄 STATUS:  <Google Doc link>
   📂 research/, sessions/, code/, comms/ created
   ⚠️  CAST incomplete — scoping call needed to refine Success and Timeline
```

## Document Templates

### CONTEXT Doc Template

```markdown
# AR-XXXXX: Customer Name

## ASQ Details
| Field | Value |
|-------|-------|
| ASQ Number | AR-XXXXX |
| Status | On Hold / In Progress |
| Service Type | <from Additional Services> |
| STS Pillar | Platform / DE & Warehousing / ML & GenAI |
| Created | YYYY-MM-DD |
| Requested Start | YYYY-MM-DD |
| Requested End | YYYY-MM-DD |

## CAST
| Element | Details |
|---------|---------|
| **Context** | <what we know about the customer situation> |
| **Ask** | <what is required from STS> |
| **Success** | <what does done look like — to be refined after scoping> |
| **Timeline** | <target dates and session cadence — to be refined after scoping> |

## Account Team
| Role | Name |
|------|------|
| AE | |
| SA/SE | |
| Other | |

## Customer Profile
| Field | Value |
|-------|-------|
| Cloud | AWS / Azure / GCP |
| DBU (30d) | |
| DBU (60d) | |
| Workspaces | <list> |
| Consumption Pattern | <Interactive / Automated / SQL breakdown> |

## Request Description
<full ASQ description>

## Related Use Cases
<from Salesforce>

## Classification
- **Pillar:** ...
- **Service:** ...
- **Format:** ...
- **Estimated Complexity:** ...

## Scoping Notes
<to be filled after scoping call>

## Google Drive References
| Resource | Google Drive ID |
|----------|----------------|
| Engagement Folder | <folder ID> |
| CONTEXT Doc | <document ID> |
| STATUS Doc | <document ID> |
| research/ | <folder ID> |
| sessions/ | <folder ID> |
| code/ | <folder ID> |
| comms/ | <folder ID> |
```

### STATUS Doc Template

```markdown
# Engagement Status: AR-XXXXX — Customer Name

## Current Phase: INTAKE_COMPLETE
## Last Updated: YYYY-MM-DD

## Phase History
- YYYY-MM-DD: Intake complete. Engagement folder created in Google Drive. Ready for scoping.
```

## Error Handling

| Scenario | Handling |
|----------|----------|
| ASQ not found in Salesforce | Prompt user to verify the ASQ number or search by customer name |
| Account data incomplete | Create workspace with available data, flag missing fields |
| Google Drive folder already exists for this ASQ | Warn user, offer to open existing folder or create a new one |
| Google Drive API failure | Retry once, then report error with details |
| ASQ description is vague | Flag explicitly in CONTEXT doc and completion summary — scoping call needed |
| CAST elements unclear from description | Leave as "to be refined after scoping" — do not guess |

## Rules

1. **Extract, don't interpret.** Pull the information from Salesforce as-is. Don't make assumptions about the engagement.
2. **CAST may be incomplete at intake.** The Success and Timeline elements are often refined during the scoping call. Leave them as "to be refined after scoping" if not clear from the ASQ description.
3. **Never create the workspace without user approval.** Always present extracted data for review first.
4. **Create all subfolders** (research/, sessions/, code/, comms/) even if empty. They'll be used by other agents.
5. **Always use Google Drive MCP tools** for creating folders and documents. Never write to the local filesystem.
6. **Always record Google Drive References** in the CONTEXT doc so downstream agents can locate resources.

## Example Usage

### Standard Workflow

```
/asq-intake AR-123456

Agent: Retrieving ASQ AR-123456 from Salesforce...

Found ASQ: AR-123456
Account: Acme Corp
Service Type: Unity Catalog Setup
Status: In Progress

Extracted Data:
┌─────────────────┬──────────────────────────────────┐
│ Field           │ Value                            │
├─────────────────┼──────────────────────────────────┤
│ ASQ Number      │ AR-123456                        │
│ Status          │ In Progress                      │
│ Service Type    │ Unity Catalog Setup              │
│ STS Pillar      │ Platform                         │
│ Created         │ 2026-04-01                       │
│ Requested Start │ 2026-04-15                       │
│ Requested End   │ 2026-05-15                       │
└─────────────────┴──────────────────────────────────┘

CAST:
- Context: Acme Corp migrating from Hive to Unity Catalog across 3 workspaces
- Ask: Guide UC setup, migration plan, and best practices
- Success: to be refined after scoping
- Timeline: to be refined after scoping

Classification:
- Pillar: Platform
- Service: Unity Catalog Setup
- Format: Core Service
- Complexity: Medium (3-4 sessions)

⚠️  CAST incomplete — Success and Timeline need scoping call

Review the above. Type 'approve' to create the Google Drive workspace, or specify what to modify.
```

### Search by Customer Name

```
/asq-intake --customer "Acme Corp"

Agent: Searching Salesforce for ASQs matching "Acme Corp"...

Found 2 matching ASQs:
1. AR-123456 — Unity Catalog Setup (In Progress)
2. AR-123400 — Lakeflow Setup (Closed)

Which ASQ would you like to onboard?
```

## Command Options

```bash
/asq-intake <ASQ_NUMBER>           # Direct ASQ lookup
/asq-intake --customer <NAME>      # Search by customer name
/asq-intake                        # Interactive mode — prompts for input
```

## Dependencies

- Salesforce access (ASQ read, account read)
- Google Drive MCP (`mcp__google__drive_file_create`, `mcp__google__drive_file_update`, `mcp__google__drive_search`)
- Google Docs MCP (`mcp__google__docs_document_create_from_markdown`, `mcp__google__docs_document_batch_update`)
