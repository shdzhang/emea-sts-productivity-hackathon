# Success Story Scoring Rubric

## 4-Criterion Scoring (Max 10 Points)

### Criterion 1: Metric Relevance (0-3)

Did the **relevant feature metric** (mapped from ASQ service type) grow post-ASQ?

| Score | Criteria |
|-------|----------|
| 3 | Relevant metric grew AND (was zero before OR post/pre > 1.5x) |
| 2 | Relevant metric post > pre |
| 1 | Any post-ASQ consumption in relevant metric |
| 0 | No consumption in relevant metric |

### Criterion 2: Growth Magnitude (0-3)

Overall **account-level** consumption growth (all product types):

| Score | Criteria |
|-------|----------|
| 3 | > 50% growth |
| 2 | 20-50% growth |
| 1 | 0-20% growth |
| 0 | Decline (check cost-optimization exception) |

**Cost-optimization exception:** If the ASQ closure note indicates cost reduction was the goal, declining consumption is the intended outcome. Score based on whether the stated objective was achieved.

### Criterion 3: Temporal Correlation (0-2)

Compare ASQ completion month to prior month:

| Score | Criteria |
|-------|----------|
| 2 | Step-up > 15% in ASQ month or new account from zero |
| 1 | Any step-up |
| 0 | No step-up |

### Criterion 4: Engagement Depth (0-2)

Based on estimated session count: `sessions = round(effort_days * 4)`. For multi-ASQ accounts, sum effort across all ASQs.

| Score | Criteria |
|-------|----------|
| 2 | Estimated sessions >= 6 (effort >= 1.5 days) OR multiple ASQs for same account |
| 1 | Estimated sessions >= 2 (effort >= 0.5 days) |
| 0 | Single session (effort <= 0.25 days) |

## What Makes a Good Success Story

| Signal | Criteria |
|--------|----------|
| **Strong growth** | `growth_multiplier` >= 2x (feature consumption at least doubled) |
| **Sustained adoption** | After-period usage stays elevated across multiple months, not a one-time spike |
| **Low baseline** | Near-zero before usage that becomes meaningful after — indicates net-new adoption |
| **Upward trend** | Later months (5, 6, 7+) higher than early months (1, 2) — organic growth |
| **Sufficient data** | At least 3+ months of post-engagement data to confirm a pattern |

## Red Flags (Not a Success Story)

- Usage was already high before and stayed flat or declined
- Spike only during month 0, then drop back to baseline
- Only 1 month of post-engagement data (too early to tell)
- Null values in the after period (customer may have churned or stopped the feature)

## Before/After SQL Template

```sql
SELECT
  asq_name, account_name,
  ROUND(AVG(CASE WHEN months_after_creation < 0 THEN <METRIC_COLUMN> END), 2) AS avg_before,
  ROUND(AVG(CASE WHEN months_after_creation > 0 THEN <METRIC_COLUMN> END), 2) AS avg_after,
  ROUND(
    AVG(CASE WHEN months_after_creation > 0 THEN <METRIC_COLUMN> END) /
    NULLIF(AVG(CASE WHEN months_after_creation < 0 THEN <METRIC_COLUMN> END), 0),
    2
  ) AS growth_multiplier
FROM main.field_sts_metrics.gold_shared_asqrelativemetrics
WHERE asq_name IN ('<ASQ_1>', '<ASQ_2>')
  AND <METRIC_COLUMN> IS NOT NULL
GROUP BY asq_name, account_name
ORDER BY growth_multiplier DESC
```

## Existing Stories Slide Deck

**Check before documenting:** [STS Success Stories](https://docs.google.com/presentation/d/1PakD1ZHUX6rL4D80BEJzpjfgBkeuqdrWgunLx_QKif8/edit#slide=id.p)

Search for the account name. If the same service/ASQ is already documented, inform the user and skip.

## UCO Relevance Filtering

For each account, filter UCOs to those relevant to the ASQ category:
- Match UCO `Name` or `Use_Case_Type__c` against keywords for the ASQ service type
- For Growth Accelerator ASQs: no filtering — return top UCOs by `Monthly_DBUs__c`
- Take top 5 per account by `Monthly_DBUs__c` descending
- Build Lightning URLs: `https://databricks.lightning.force.com/lightning/r/UseCase__c/{{uco_id}}/view/`
