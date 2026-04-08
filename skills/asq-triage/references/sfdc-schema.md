# Salesforce Schema Reference for ASQ Triage

## EMEA STS Queue

- **Queue Name**: `Technical_Onboarding_Services_EMEA`
- **Queue ID (OwnerId)**: `00G8Y000006CaluUAC`
- **Type**: Salesforce Queue (Group object, NOT a User)

> **Important**: Filter by `OwnerId = '00G8Y000006CaluUAC'`, NOT `Owner.Name`. The `Owner.Name` filter silently returns empty results for queues.

## ApprovalRequest__c (ASQ)

**RecordType**: `'Shared Technical Services'` (NOT `'Technical Services'`)

> No `RecordType.Name` filter is needed when filtering by OwnerId — the queue only contains STS ASQs.

### Key Fields

| Field | Description |
|-------|-------------|
| `Id` | Salesforce record ID |
| `Name` | ASQ number (e.g., AR-000115163) |
| `Support_Type__c` | Platform Administration, Data Engineering, Data Warehousing, ML & GenAI, Launch Accelerator, Growth Accelerator for PAYG, DWH Lakebridge Migration Foundation, AI/BI Migration |
| `Additional_Services__c` | Specific services requested (semicolon-separated) |
| `Request_Description__c` | Free-text description |
| `CreatedBy.Name` / `CreatedById` | Creator info (use `CreatedById` for Chatter @mentions) |
| `Account_Name__c` | Account name |
| `Status__c` | New, Under Review, On Hold, In Progress, Complete, Rejected, Cancelled |
| `Urgency__c` | Picklist: `Low: 10+ Days`, `Normal: 5-10 Days`, `High: Less than 5 Days (...)`, `Critical: Less than 48 Hrs (...)` |
| `Start_Date__c` | Requested start date (compare against today to flag overdue) |
| `LastModifiedDate` | Last modification timestamp |
| `CreatedDate` | Creation timestamp |

### Fields NOT to rely on

| Field | Why |
|-------|-----|
| `Use_Case_defined__c` | Boolean, unreliable. Always use the junction object instead. |
| `Use_Case__c`, `Use_case_2__c`, `Use_case_3__c` | Lookup fields, also unreliable. Use junction. |

### Support Type Aliases

| Value in SFDC | Treat As |
|--------------|----------|
| `Growth Accelerator for PAYG` | Launch Accelerator |
| `DWH Lakebridge Migration Foundation` | Data Warehousing (Lakebridge) |
| `AI/BI Migration` | Data Warehousing (AI/BI) |

## Approved_UseCase__c (Junction — Use Case Stages)

> **ALWAYS** use this junction object for use case stage checks. Never use the lookup fields on the ASQ.

### Query Pattern

```sql
SELECT
  Approval_Request__r.Name,
  Approval_Request__r.Account_Name__c,
  Use_Case__r.Name,
  Use_Case__r.Stages__c,
  Stage__c,
  Use_Case_Type__c
FROM Approved_UseCase__c
WHERE Approval_Request__r.Name IN ('AR-XXXXXX', ...)
ORDER BY Approval_Request__r.Name
```

### Stage Values

| Code | Display Name | Numeric Order |
|------|-------------|--------------|
| U1 | Identifying | 1 |
| U2 | Scoping | 2 |
| U3 | Evaluating | 3 |
| U4 | Confirming | 4 |
| U5 | Onboarding | 5 |
| U6 | Live | 6 |
| Lost | Lost | — (flag for rejection) |

- `Use_Case__r.Stages__c` — stage code (U3, U4, etc.)
- `Stage__c` — display name (e.g., "3-Evaluating")

## Chatter

### Reading Comments

```bash
python3 $ASQ_TOOLS sfdc-chatter-read <ASQ_ID> --limit 3
```

Response format: array of objects with `date`, `author`, `text` fields.

### Posting Comments

See `references/comment-templates.md` for payload structure and templates.

## User Object

Query team member SFDC IDs for Chatter @mentions:

```sql
SELECT Id, Name, Email
FROM User
WHERE Name IN ('Name1', 'Name2', ...)
AND IsActive = true
```

> Some team members may have multiple User records (old/new). Use the most recent active one.

## Workload Query

> **CRITICAL: Do NOT use a single `Owner.Name IN (...)` query.** Names with Unicode characters (e.g., "Jovan Višnjić", "Gergelj Kiš") silently return 0 results in a bulk IN clause via the `sf` CLI. Query each team member separately.

For each team member from the cached competency matrix (row 0):

```sql
SELECT Owner.Name, Status__c, Support_Type__c, COUNT(Id) cnt
FROM ApprovalRequest__c
WHERE Owner.Name = '<INDIVIDUAL_NAME>'
AND Status__c IN ('In Progress', 'On Hold')
GROUP BY Owner.Name, Status__c, Support_Type__c
```

No `RecordType.Name` filter is needed — individual owner queries naturally scope to their ASQs.

Extract team member names dynamically from the cached competency matrix (row 0). Do NOT hardcode names.
