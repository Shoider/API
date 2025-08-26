CREATE OR REPLACE VIEW public.inactive_rules_summary
AS SELECT r.rule_id,
    r.rule_label,
    mfir.month_start_date
   FROM rules r
     JOIN monthly_fully_inactive_rules mfir ON r.rule_id = mfir.rule_id;

-----------------------------------------------------------------------------------
-- USOS --

-- Ver todo
SELECT * FROM inactive_rules_summary;

-- Filtrar por fecha


-- Filtrar por rule_id y contar los registros
