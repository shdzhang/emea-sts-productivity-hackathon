# Competency Matrix — Scoring Logic

> **Team member names, skills ratings, and tenure come from the live Google Sheet**, cached at `~/asq-local-cache/triage/competency_matrix.json` (7-day TTL).
>
> **Sheet ID**: `1vn6LmBVBlthTvyNDJpJLIryIfSy1pU6mN7wFXYobaWE`
> **Tab**: `EMEA SME`
> **Range**: `A1:Z50` (Row 1 = names, Rows 4-26 = service ratings, Rows 29-31 = tenure)
>
> This file contains only the **scoring formulas and mappings** — no copied data.

## Rating Weights

| Rating | Weight |
|--------|--------|
| Experienced | 3 |
| Intermediate | 2 |
| Beginner | 1 |
| No Experience | 0 |

## Service-to-Support-Type Mapping

Maps the service rows in the Google Sheet to ASQ Support Types. Use this to determine which matrix rows to score for a given ASQ.

| Service Row in Sheet | Support Type(s) |
|---------------------|----------------|
| Workspace Setup (Azure/AWS/GCP) | Platform Administration |
| UC Setup - Option 1/2 | Platform Administration |
| UC Migration | Platform Administration |
| CI/CD Setup | Platform Administration |
| Observability | Platform Administration |
| Serverless Upgrade | Platform Administration |
| Lakeflow | Data Engineering |
| Delta Optimizations & Maintenance | Data Engineering |
| Data Sharing to External Systems | Data Engineering |
| DBSQL for Admin / Analysts | Data Warehousing, AI/BI Migration |
| AI/BI Data Citizen | Data Warehousing, AI/BI Migration |
| Lakebridge Analyzer | Data Warehousing, DWH Lakebridge Migration Foundation |
| Lakebridge Converter | Data Warehousing, DWH Lakebridge Migration Foundation |
| AI/ML Pipelines | ML & GenAI |
| GenAI Apps | ML & GenAI |
| MLOps | ML & GenAI |
| Launch Accelerator | Growth Accelerator for PAYG |

> **"Launch Accelerator" vs "Growth Accelerator for PAYG"**: In the SFDC UI the picklist label is "Launch Accelerator", but the API value stored on records is `Growth Accelerator for PAYG`. Always use the API value in SOQL queries.

### Migration Support Types

**AI/BI Migration** and **DWH Lakebridge Migration Foundation** are migration-focused Support Types whose `Additional_Services__c` values specify the **source platform** being migrated from:

| Support Type | Additional Services (source platforms) | Score Using Sheet Rows |
|---|---|---|
| AI/BI Migration | PowerBI, Tableau, Other | AI/BI Data Citizen, DBSQL for Admin / Analysts |
| DWH Lakebridge Migration Foundation | Snowflake, SQLServer, Synapse, Other | Lakebridge Analyzer, Lakebridge Converter |

## Assignment Scoring Formula

**Total Score = (0.50 × Skills Match) + (0.30 × Workload Score) + (0.20 × Experience Score)**

### Skills Match (50% weight)
1. Map the ASQ's Support Type to the relevant service rows using the table above
2. If `Additional_Services__c` names specific services, also include those rows
3. For each team member, average their ratings (using weights above) across matched rows
4. Normalize to 0-10 scale: `(avg_weight / 3.0) × 10`

### Workload Score (30% weight)
Based on **weighted workload** with LA multiplier:

`weighted = IP_regular×1 + IP_LA×2 + OH_regular×0.5 + OH_LA×1.0`

- On Hold counts at 50% (awaiting customer action)
- Launch Accelerator counts at 200% (6-week program, 12+ sessions)
- LA On Hold = 2.0 × 0.5 = 1.0×

Lower weighted load = higher score. Normalize inversely against the team's range.

### Experience Score (20% weight)
For complex ASQs (description scope score > 7, multiple services):
- Prefer team members with more "Experienced" ratings in the relevant services
- Use tenure as tiebreaker (longer tenure = higher score, from sheet rows 29-31)

For straightforward ASQs:
- "Intermediate" ratings are acceptable
- Distribute to less-loaded team members even if slightly less experienced
