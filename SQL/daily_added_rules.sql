CREATE OR REPLACE VIEW daily_added_rules AS
SELECT
    DATE_TRUNC('day', created_at)::date AS added_date,
    COUNT(rule_id) AS rules_added_count
FROM
    public.rules
GROUP BY
    added_date
ORDER BY
    added_date ASC;