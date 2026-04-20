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

Team member SFDC User IDs are pre-resolved and cached in `~/asq-local-cache/triage/team_member_ids.json` (refreshed with the competency matrix on a 7-day TTL). Use this cache for Chatter @mentions, OwnerId assignment, and workload queries.

If a name is not in the cache (e.g., ad-hoc assignment), fall back to SOQL with internal-user filters:

```sql
SELECT Id, Name, Email
FROM User
WHERE Name = '<name>'
AND UserType = 'Standard'
AND IsActive = true
```

> **CRITICAL: Always include `UserType = 'Standard'`** to exclude portal/customer community users. Salesforce can have multiple users with the same name — omitting this filter risks resolving a customer contact instead of the Databricks employee.

## Workload Query

Use the cached `team_member_ids.json` to get all team member SFDC User IDs, then run a **single bulk query** using `OwnerId IN (...)`:

```sql
SELECT OwnerId, Owner.Name, Status__c, Support_Type__c, COUNT(Id) cnt
FROM ApprovalRequest__c
WHERE OwnerId IN ('005Vp...', '005Vp...', ...)
AND Status__c IN ('In Progress', 'On Hold')
GROUP BY OwnerId, Owner.Name, Status__c, Support_Type__c
```

> **Why `OwnerId` instead of `Owner.Name`**: Using IDs avoids two problems: (1) Unicode characters (e.g., š, ć, í) silently returning 0 results in `Owner.Name IN (...)` via the `sf` CLI, and (2) the need for N individual queries. A single `OwnerId IN (...)` query handles all team members reliably.

No `RecordType.Name` filter is needed — the OwnerId filter naturally scopes to team member ASQs.

Extract team member IDs from `~/asq-local-cache/triage/team_member_ids.json`. Do NOT hardcode IDs.
