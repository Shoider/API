-- init_db.sql

-- Crear la base de datos de test
CREATE DATABASE test_db;
-- Produccion
CREATE DATABASE pf_sense;
-- Reporte
CREATE DATABASE pf_sense_report;
-- Conectarse a la base de datos test_db para crear objetos dentro de ella
\c test_db;
\c pf_sense_report;

-- 1. Usuario Administrador para test_db
CREATE USER admin WITH ENCRYPTED PASSWORD 'pass';
ALTER USER admin WITH SUPERUSER;
GRANT ALL PRIVILEGES ON DATABASE test_db TO admin;

-- 2. Usuario para la API
CREATE USER api_user WITH ENCRYPTED PASSWORD 'pass';
ALTER USER api_user WITH PASSWORD 'nct44YFPvyHIc8/I9YjI3w==';
GRANT CONNECT ON DATABASE test_db TO api_user;
GRANT CONNECT ON DATABASE pf_sense TO api_user;

-- 3. Usuario para procedimiento almacenado
CREATE USER proccess_user WITH ENCRYPTED PASSWORD '2Sj4jMRz/TZZbsW/03lC/Q==';
GRANT CONNECT ON DATABASE test_db TO proccess_user;
GRANT CONNECT ON DATABASE pf_sense TO proccess_user;

-- 4. Privilegios default en el esquema
-- ALTER DEFAULT PRIVILEGES IN SCHEMA public;

GRANT CONNECT ON DATABASE pf_sense_report TO api_user;
GRANT CONNECT ON DATABASE pf_sense_report TO proccess_user;