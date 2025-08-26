CREATE OR REPLACE PROCEDURE analyze_monthly_inactive_rules(
    p_year INT,
    p_month INT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_month_start_date DATE;
    v_month_end_date DATE;
    v_expected_executions INT;
    v_total_monthly_detections INT;
BEGIN
    -- 1. Calcular el rango de fechas para el mes
    v_month_start_date := MAKE_DATE(p_year, p_month, 1);
    v_month_end_date := (v_month_start_date + INTERVAL '1 month' - INTERVAL '1 day')::DATE;
    
    RAISE NOTICE 'Analizando inactividad para el mes: %-% (del % al %).', p_year, p_month, v_month_start_date, v_month_end_date;

    -- 2. Obtener el número total de ejecuciones de la API para este mes
    SELECT execution_count
    INTO v_expected_executions
    FROM monthly_execution_counts
    WHERE month_start_date = v_month_start_date;

    -- Si no hay registro de ejecuciones para el mes, no hay reglas que hayan estado inactivas todo el mes
    IF v_expected_executions IS NULL OR v_expected_executions = 0 THEN
        RAISE NOTICE 'No se encontraron registros de ejecuciones de la API para el mes %-%s. No se identificarán reglas totalmente inactivas.', p_year, p_month;
        v_expected_executions := 0;
    ELSE
        RAISE NOTICE 'Total de ejecuciones de la API esperadas para el mes: %', v_expected_executions;
    END IF;

    -- 3. Identificar reglas que estuvieron inactivas TODOS los días del mes (en TODAS las ejecuciones)
    -- Solo si hubo ejecuciones de la API para ese mes
    IF v_expected_executions > 0 THEN
        INSERT INTO monthly_fully_inactive_rules (rule_id, month_start_date)
        SELECT
            irl.rule_id,
            v_month_start_date
        FROM
            inactive_rule_log irl
        WHERE
            irl.created_at::DATE >= v_month_start_date
            AND irl.created_at::DATE <= v_month_end_date
        GROUP BY
            irl.rule_id
        -- Conteo de registros de inactividad para la regla debe ser igual al total de ejecuciones de la API
        HAVING
            COUNT(irl.log_id) = v_expected_executions
        ON CONFLICT (rule_id, month_start_date) DO NOTHING;

        GET DIAGNOSTICS v_total_monthly_detections = ROW_COUNT;
        RAISE NOTICE 'Reglas totalmente inactivas insertadas/actualizadas: %', v_total_monthly_detections;
    ELSE
        RAISE NOTICE 'No se identificaron reglas totalmente inactivas debido a la falta de ejecuciones de la API.';
    END IF;


    -- 4. Calcular el conteo total de detecciones de inactividad para el mes
    SELECT COUNT(log_id)
    INTO v_total_monthly_detections
    FROM inactive_rule_log
    WHERE created_at::DATE >= v_month_start_date
      AND created_at::DATE <= v_month_end_date;

    -- 5. Insertar/Actualizar el conteo mensual en monthly_inactive_detection_counts
    INSERT INTO monthly_inactive_detection_counts (total_detections, inactive_month)
    VALUES (v_total_monthly_detections, v_month_start_date)
    ON CONFLICT (inactive_month) DO UPDATE SET
        total_detections = EXCLUDED.total_detections,
        created_at = NOW();

    RAISE NOTICE 'Conteo mensual de detecciones de inactividad (%s) registrado para %s.', v_total_monthly_detections, v_month_start_date;

END;
$$;