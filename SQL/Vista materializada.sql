-- Crea la vista materializada con la consulta optimizada
CREATE MATERIALIZED VIEW rule_counts_materialized AS
WITH inactive_counts AS (
    SELECT
        date_trunc('day', created_at)::date AS activity_date,
        count(DISTINCT rule_id) AS inactive_rule_count
    FROM
        inactive_rule_log
    GROUP BY
        activity_date
),
total_counts AS (
    SELECT
        date_trunc('day', "timestamp")::date AS activity_date,
        count(DISTINCT rule_id) AS total_rules_count
    FROM
        rule_metrics
    GROUP BY
        activity_date
)
SELECT
    COALESCE(tc.activity_date, ic.activity_date) AS activity_date,
    COALESCE(ic.inactive_rule_count, 0) AS inactive_rule_count,
    COALESCE(tc.total_rules_count, 0) AS total_rules_count,
    COALESCE(tc.total_rules_count, 0) - COALESCE(ic.inactive_rule_count, 0) AS active_rules_count
FROM
    total_counts tc
FULL OUTER JOIN inactive_counts ic ON tc.activity_date = ic.activity_date
ORDER BY
    activity_date;

-- Comando para actualizar los datos (ejecútalo periódicamente)
REFRESH MATERIALIZED VIEW rule_counts_materialized;