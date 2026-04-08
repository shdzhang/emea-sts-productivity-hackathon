# STS Service → Metric Column Mappings

## Data Source

**Table:** `main.field_sts_metrics.gold_shared_asqrelativemetrics`
**Environment:** Logfood workspace (`adb-2548836972759138.18.azuredatabricks.net`, profile: `logfood`)

## Service Name Resolution

Map informal user input to canonical STS services and metric columns.

| User might say | Canonical STS Service | SQL Keywords (`support_type` / `additional_services`) | Primary Metric | Secondary Metric |
|---|---|---|---|---|
| Genie, AI/BI, dashboards, data citizen | AI/BI Data Citizen | `'%ai/bi%'`, `'%genie%'`, `'%data citizen%'` | `ai_bi_dollar_dbus` | `dbsql_dollar_dbus` |
| SQL, DBSQL, warehousing, warehouse | Data Warehousing | `'%warehousing%'`, `'%dbsql%'`, `'%sql%'` | `dbsql_dollar_dbus` | `dbsql_serverless_dollar_dbus` |
| Serverless SQL, serverless warehouse | Data Warehousing (Serverless) | `'%warehousing%'`, `'%serverless%'` | `dbsql_serverless_dollar_dbus` | — |
| ETL, pipelines, data engineering, jobs | Data Engineering | `'%engineering%'`, `'%etl%'`, `'%pipeline%'` | `automated_dollar_dbus` | `dlt_dollar_dbus` |
| DLT, Delta Live Tables, Lakeflow Pipelines | Lakeflow Pipelines | `'%lakeflow%'`, `'%dlt%'`, `'%delta live%'` | `lakeflow_pipeline_dollar_dbus` | `lakeflow_dollar_dbus` |
| Lakeflow Connect, ingestion, connectors | Lakeflow Connect | `'%lakeflow%'`, `'%connect%'`, `'%ingestion%'` | `lakeflow_connect_dollar_dbus` | — |
| ML, MLOps, model serving, GenAI | MLOps / Model Serving | `'%mlops%'`, `'%model serving%'`, `'%genai%'` | `genai_dbu_dollar_dbus` | `genai_gpu_model_serving_dollar_dbus` |
| FMAPI, foundation model, LLM | Foundation Model API | `'%foundation%'`, `'%fmapi%'`, `'%llm%'` | `genai_foundation_model_api_dollar_dbus` | — |
| UC, Unity Catalog, governance | Unity Catalog | `'%unity%'`, `'%uc%'`, `'%governance%'` | `uc_dollar_dbus` | — |
| Serverless, serverless migration | Serverless Migration | `'%serverless%'` | `serverless_dollar_dbus` | `serverless_jobs_dollar_dbus` |
| Serverless jobs | Serverless Jobs | `'%serverless%'`, `'%jobs%'` | `serverless_jobs_dollar_dbus` | — |
| Apps, Databricks Apps | Databricks Apps | `'%apps%'` | `apps_dollar_dbus` | — |
| Vector search, RAG, retrieval | Vector Search | `'%vector%'`, `'%rag%'`, `'%retrieval%'` | `vector_search_dollar_dbus` | — |
| Online tables, feature serving | Online Tables | `'%online%'`, `'%feature serving%'` | `online_tables_dollar_dbus` | — |
| AI Gateway, gateway | AI Gateway | `'%gateway%'` | `ai_gateway_dollar_dbus` | — |
| Agents, AgentBricks | AgentBricks | `'%agent%'` | `agentbricks_dollar_dbus` | — |
| Monitoring, lakehouse monitoring | Lakehouse Monitoring | `'%monitoring%'` | `lakehouse_monitoring_dollar_dbus` | — |
| Predictive optimization | Predictive Optimization | `'%predictive%'`, `'%optimization%'` | `predictive_optimization_dollar_dbus` | — |
| Training, model training, fine-tuning | Model Training | `'%training%'`, `'%fine-tun%'` | `model_training_dollar_dbus` | — |
| Delta, Delta Lake | Delta | `'%delta%'` | `delta_dollar_dbus` | — |
| DW migration, Lakebridge, Synapse, legacy mod | DW Migration | `'%migration%'`, `'%lakebridge%'` | `dbsql_dollar_dbus` | `total_dollar_consumption_month` |

## All Available Metric Columns

### Consumption ($DBU)
| Column | Feature |
|--------|---------|
| `total_dollar_consumption_month` | Total account $DBU |
| `total_dbu_consumption_month` | Total account DBU units |
| `ai_bi_dollar_dbus` | AI/BI (Genie + Dashboards) |
| `dbsql_dollar_dbus` | Databricks SQL |
| `dbsql_serverless_dollar_dbus` | Serverless SQL |
| `dlt_dollar_dbus` | Delta Live Tables |
| `lakeflow_dollar_dbus` | Lakeflow (all) |
| `lakeflow_connect_dollar_dbus` | Lakeflow Connect |
| `lakeflow_pipeline_dollar_dbus` | Lakeflow Pipelines |
| `automated_dollar_dbus` | Jobs / Workflows |
| `interactive_dollar_dbus` | Interactive clusters |
| `serverless_dollar_dbus` | All serverless SKUs |
| `serverless_jobs_dollar_dbus` | Serverless Jobs |
| `serverless_all_purpose_dollar_dbus` | Serverless All-Purpose |
| `genai_dbu_dollar_dbus` | GenAI aggregate |
| `genai_foundation_model_api_dollar_dbus` | Foundation Model API |
| `genai_gpu_model_serving_dollar_dbus` | GPU Model Serving |
| `genai_cpu_model_serving_dollar_dbus` | CPU Model Serving |
| `model_training_dollar_dbus` | Model Training |
| `vector_search_dollar_dbus` | Vector Search |
| `online_tables_dollar_dbus` | Online Tables |
| `apps_dollar_dbus` | Databricks Apps |
| `uc_dollar_dbus` | Unity Catalog |
| `agentbricks_dollar_dbus` | AgentBricks |
| `ai_gateway_dollar_dbus` | AI Gateway |
| `delta_dollar_dbus` | Delta |
| `lakehouse_monitoring_dollar_dbus` | Lakehouse Monitoring |
| `predictive_optimization_dollar_dbus` | Predictive Optimization |
| `sql_dollar_dbus` | SQL (broad) |
| `forecast_consumption_ds` | Demand Signal forecast |

### Cloud-Specific
| Column | Cloud |
|--------|-------|
| `aws_dollar_dbus` | AWS |
| `azure_dollar_dbus` | Azure |
| `gcp_dollar_dbus` | GCP |

## Resolution Rules

1. **Fuzzy match first.** "Genie" → AI/BI Data Citizen. "pipelines" → determine from context if Lakeflow or Data Engineering.
2. **Ask if ambiguous.** "serverless" could be SQL, jobs, or all-purpose — clarify with user.
3. **Search both columns.** Always check `support_type` AND `additional_services` since the service may appear in either.
4. **DW Migration special case.** For Lakebridge/migration ASQs, use DBSQL as primary metric (most migrations target SQL workloads) plus total consumption as secondary.

## Owner Name Lookup

Owner names may contain special characters (e.g., `Zuñiga`). Use partial match:
```sql
SELECT DISTINCT owner_name
FROM main.field_sts_metrics.gold_shared_asqrelativemetrics
WHERE LOWER(owner_name) LIKE '%partial_name%'
```
