# GCP Analytics Queries (Funnel)

Этот файл — быстрые шаблоны запросов для Cloud Logging / BigQuery по событиям воронки.

## 1) Cloud Logging (Logs Explorer)

Базовый фильтр по событиям:

```text
resource.type="cloud_run_revision"
resource.labels.service_name="edtonai-backend"
textPayload:"ANALYTICS_EVENT"
```

Фильтр по конкретному событию:

```text
resource.type="cloud_run_revision"
resource.labels.service_name="edtonai-backend"
textPayload:"ANALYTICS_EVENT"
textPayload:"\"event_name\": \"analysis_finished\""
```

События воронки:
- `resume_uploaded`
- `vacancy_added`
- `analysis_started`
- `analysis_finished`
- `export_clicked`
- `feedback_submitted`

## 2) BigQuery (после Logging Sink)

Ожидаем таблицу с колонкой payload (raw log строка). Далее можно выделять поля JSON.

Пример (псевдо-шаблон):

```sql
WITH events AS (
  SELECT
    JSON_VALUE(payload, '$.event_name') AS event_name,
    JSON_VALUE(payload, '$.session_id') AS session_id,
    TIMESTAMP(JSON_VALUE(payload, '$.occurred_at')) AS occurred_at
  FROM `project.dataset.analytics_logs`
  WHERE JSON_VALUE(payload, '$.event_name') IS NOT NULL
)
SELECT
  event_name,
  COUNT(DISTINCT session_id) AS sessions
FROM events
GROUP BY event_name
ORDER BY sessions DESC;
```

Конверсия шага A->B:

```sql
WITH events AS (
  SELECT
    JSON_VALUE(payload, '$.event_name') AS event_name,
    JSON_VALUE(payload, '$.session_id') AS session_id
  FROM `project.dataset.analytics_logs`
),
step_a AS (
  SELECT DISTINCT session_id FROM events WHERE event_name = 'analysis_finished'
),
step_b AS (
  SELECT DISTINCT session_id FROM events WHERE event_name = 'export_clicked'
)
SELECT
  (SELECT COUNT(*) FROM step_a) AS sessions_a,
  (SELECT COUNT(*) FROM step_b) AS sessions_b,
  SAFE_DIVIDE((SELECT COUNT(*) FROM step_b), (SELECT COUNT(*) FROM step_a)) * 100 AS conversion_percent;
```
