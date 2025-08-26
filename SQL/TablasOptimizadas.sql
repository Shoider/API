-- Tabla Maestra de Reglas
CREATE TABLE rules (
    rule_id BIGINT PRIMARY KEY,
    rule_label VARCHAR(255) NOT NULL,
    rule_description VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-----------------------------------------------------------------------------------

-- Tabla de metricas historicas
CREATE TABLE rule_metrics (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    rule_id BIGINT NOT NULL,
    evaluations BIGINT NOT NULL,
    packets_matched BIGINT NOT NULL,
    bytes_matched BIGINT NOT NULL,
    states_created BIGINT NOT NULL,
    state_packets BIGINT NOT NULL,
    state_bytes BIGINT NOT NULL,
    input_output BIGINT,
    -- Clave foránea a la tabla 'rules'
    CONSTRAINT fk_rule_metrics_rule_id FOREIGN KEY (rule_id) REFERENCES rules (rule_id) ON DELETE RESTRICT
);

-----------------------------------------------------------------------------------

-- Tabla para registrar reglas inactivas
CREATE TABLE inactive_rule_log (
    log_id SERIAL PRIMARY KEY,
    rule_id BIGINT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    -- Clave foránea a la tabla 'rules'
    CONSTRAINT fk_inactive_rule_log_rule_id FOREIGN KEY (rule_id) REFERENCES rules (rule_id) ON DELETE RESTRICT
);

-----------------------------------------------------------------------------------

-- Tabla para registrar reglas inactivas de un mes (Reglas que estuvieron inactivas TODO el mes)
CREATE TABLE monthly_fully_inactive_rules (
    monthly_log_id SERIAL PRIMARY KEY,
    rule_id BIGINT NOT NULL,
    month_start_date DATE NOT NULL, -- La fecha de inicio del mes analizado (ej. '2025-06-01')
    -- Clave foránea a la tabla 'rules'
    CONSTRAINT fk_monthly_fully_inactive_rules_rule_id FOREIGN KEY (rule_id) REFERENCES rules (rule_id) ON DELETE RESTRICT,
    -- Restricción de unicidad para evitar duplicar la misma regla para el mismo mes
    CONSTRAINT uq_monthly_fully_inactive UNIQUE (rule_id, month_start_date)
);

-----------------------------------------------------------------------------------

-- Tabla para registrar la cantidad total de detecciones de reglas inactivas por mes
CREATE TABLE monthly_inactive_detection_counts (
    count_id SERIAL PRIMARY KEY,
    total_detections INT NOT NULL,
    inactive_month DATE NOT NULL, -- La fecha de inicio del mes analizado (ej. '2025-06-01')
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,

    -- Restricción de unicidad para asegurar un solo conteo por mes
    CONSTRAINT uq_monthly_inactive_count UNIQUE (inactive_month)
);

-----------------------------------------------------------------------------------

-- Tabla para registrar la cantidad total de ejecuciones de la API por mes
CREATE TABLE monthly_execution_counts (
    count_id SERIAL PRIMARY KEY,
    month_start_date DATE NOT NULL, -- La fecha de inicio del mes analizado (ej. '2025-06-01')
    execution_count INT NOT NULL DEFAULT 0, -- Contador de cuántas veces se ha ejecutado la API en ese mes
    last_updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,

    -- Restricción de unicidad para asegurar un solo conteo por mes
    CONSTRAINT uq_monthly_execution_count UNIQUE (month_start_date)
);

-----------------------------------------------------------------------------------

-- Índices para buscar por rule_id o por fecha
CREATE INDEX idx_rule_metrics_rule_id ON rule_metrics (rule_id);
CREATE INDEX idx_rule_metrics_timestamp ON rule_metrics (timestamp);
-- Este índice compuesto para rangos de fechas por reglas
CREATE INDEX idx_rule_metrics_rule_id_timestamp ON rule_metrics (rule_id, timestamp DESC);
-- Índice en rule_label para buscar reglas por su nombre
CREATE INDEX idx_rules_rule_label ON rules (rule_label);
-- Índices
CREATE INDEX idx_monthly_inactive_detection_counts_month ON monthly_inactive_detection_counts (inactive_month);
-- Índices
CREATE INDEX idx_inactive_rule_log_rule_id ON inactive_rule_log (rule_id);
CREATE INDEX idx_inactive_rule_log_created_at ON inactive_rule_log (created_at DESC);
-- Índices
CREATE INDEX idx_monthly_fully_inactive_rules_rule_id ON monthly_fully_inactive_rules (rule_id);
CREATE INDEX idx_monthly_fully_inactive_rules_month_start_date ON monthly_fully_inactive_rules (month_start_date);
-- Índice para búsquedas eficientes por mes
CREATE INDEX idx_monthly_execution_counts_month ON monthly_execution_counts (month_start_date);

-----------------------------------------------------------------------------------

-- Permisos al API
GRANT SELECT, INSERT, UPDATE ON rules TO api_user;
GRANT SELECT, INSERT ON rule_metrics TO api_user;
GRANT SELECT, INSERT ON inactive_rule_log TO api_user;
GRANT SELECT, INSERT, UPDATE ON monthly_execution_counts TO api_user;

-- Permisos para usar los numeros secuenciales
GRANT USAGE ON SEQUENCE rule_metrics_id_seq TO api_user;
GRANT USAGE ON SEQUENCE inactive_rule_log_log_id_seq TO api_user;
GRANT USAGE ON SEQUENCE monthly_execution_counts_count_id_seq TO api_user;

-----------------------------------------------------------------------------------

-- Estos permisos son para el usuario que ejecuta los procedimientos
-- Debo crear un nuevo usuario

-- Permisos para las nuevas tablas
GRANT SELECT, INSERT ON monthly_fully_inactive_rules TO proccess_user;
GRANT SELECT, INSERT, UPDATE ON monthly_inactive_detection_counts TO proccess_user;
GRANT SELECT ON monthly_execution_counts TO proccess_user;
GRANT SELECT ON rule_metrics TO proccess_user;

-- Permisos para las secuencias de las nuevas tablas
GRANT USAGE ON SEQUENCE monthly_fully_inactive_rules_monthly_log_id_seq TO proccess_user;
GRANT USAGE ON SEQUENCE monthly_inactive_detection_counts_count_id_seq TO proccess_user;
