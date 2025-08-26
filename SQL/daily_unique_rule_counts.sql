CREATE OR REPLACE VIEW public.daily_unique_rule_counts
AS SELECT date_trunc('day'::text, created_at)::date AS activity_date,
    count(DISTINCT rule_id) AS unique_rule_count
   FROM inactive_rule_log
  GROUP BY (date_trunc('day'::text, created_at)::date)
  ORDER BY (date_trunc('day'::text, created_at)::date) DESC;