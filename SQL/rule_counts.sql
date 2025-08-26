CREATE OR REPLACE VIEW rule_counts AS
SELECT
    DATE_TRUNC('day', irl.created_at)::date AS activity_date,
    COUNT(DISTINCT irl.rule_id) AS inactive_rule_count,
    COUNT(DISTINCT rm.rule_id) AS total_rules_count
FROM
    public.inactive_rule_log irl
LEFT JOIN
    public.rule_metrics rm ON DATE_TRUNC('day', irl.created_at)::date = DATE_TRUNC('day', rm."timestamp")::date
GROUP BY
    activity_date
ORDER BY
    activity_date ASC;