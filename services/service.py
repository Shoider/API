from datetime import datetime, timezone
from flask import jsonify
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, and_, text
from sqlalchemy.dialects import postgresql
from models.model import RuleMetric, Rule, InactiveRuleLog, MonthlyExecutionCount
from logger.logger import Logger

class Service:
    """Service class to that implements the logic"""

    def __init__(self, db_model):
        self.logger = Logger()
        self.db_model = db_model

    def _upsert_monthly_execution_count(self, session) -> None:
        """
        Increments the execution count for the current month.
        Inserts if the month does not exist, updates if it does.
        """
        # Calcular el primer día del mes actual en UTC
        today_utc = datetime.now(timezone.utc)
        current_month_start_date = today_utc.replace(day=1, hour=0, minute=0, second=0, microsecond=0).date()

        # Usar INSERT ... ON CONFLICT DO UPDATE
        insert_stmt = postgresql.insert(MonthlyExecutionCount).values(
            month_start_date=current_month_start_date,
            execution_count=1, # Si es una nueva entrada, el conteo inicial es 1
            last_updated_at=today_utc
        )
        on_conflict_stmt = insert_stmt.on_conflict_do_update(
            index_elements=['month_start_date'], # La columna con la restricción UNIQUE
            set_={
                'execution_count': MonthlyExecutionCount.execution_count + 1, # Incrementa el conteo
                'last_updated_at': today_utc # Actualiza la marca de tiempo
            }
        )
        session.execute(on_conflict_stmt)
        self.logger.debug(f"Contador mensual de ejecuciones actualizado {current_month_start_date}.")

    def add_metrics(self, rule_metrics_list: list[dict]) -> bool:
        """
        Adds a list of parsed to the database.
        This method handles the business logic for saving rule metrics.

        Args:
            rule_metrics_list: A list of dictionaries, where each dictionary
                               represents a parsed pfctl rule metric.
        Returns:
            bool: True if insertion was successful, False otherwise.
        """
        self.logger.debug(f"Datos recibidos en add_metrics: {rule_metrics_list}")
        session = None
        try:
            session = self.db_model.get_session()

            # Añadir a rules
            self.logger.debug("Añadiendo/Actualizando datos en la tabla 'rules'")
            self._upsert_rules(session, rule_metrics_list)

            # Añadir rule metrics
            self.logger.debug("Añadiendo datos en la tabla 'rule_metrics'")
            self._add_rule_metrics(session, rule_metrics_list)

            # Añadir inactive rule logs
            self.logger.debug("Añadiendo datos en la tabla 'inactive_rule_log'")
            # Logica para encontrar reglas sin uso
            inactive_rules = self.get_inactive_rules_from_this_batch(rule_metrics_list)
            self.logger.debug(f"Lista de reglas inactivas: {inactive_rules}")
            self._add_inactive_rules_log(session, inactive_rules)

            # Incrementar el contador de ejecuciones mensuales
            self.logger.debug("Incrementando el contador de ejecuciones mensuales.")
            self._upsert_monthly_execution_count(session) # Llamada a la nueva función

            session.commit()
            self.logger.info(f"Batch de métricas procesado y guardado exitosamente. Reglas: {len(rule_metrics_list)}")
            return True
        except SQLAlchemyError as e:
            if session:
                session.rollback()
                self.logger.debug("Rollback")
            self.logger.critical(f"Error en la base de datos durante la insercion: {e}")
            return False
        except Exception as e:
            self.logger.critical(f"Ocurrio un error inesperado en el servicio durante la insercion: {e}")
            return False
        finally:
            if session:
                session.close()
                self.logger.debug("Sesion cerrada")

    def _upsert_rules(self, session, rule_metrics_list: list[dict]):
        """Internal method to add/update rules using ON CONFLICT for efficiency."""
        # Prepara los valores para la inserción en lote
        rule_values = []
        for data in rule_metrics_list:
            rule_values.append({
                'rule_id': data['id'],
                'rule_label': data['label']
            })

        # Construye la declaración de inserción con ON CONFLICT DO UPDATE
        insert_stmt = postgresql.insert(Rule).values(rule_values)
        on_conflict_stmt = insert_stmt.on_conflict_do_update(
            index_elements=['rule_id'], # El campo que define la unicidad
            set_={'rule_label': insert_stmt.excluded.rule_label} # Actualiza el label si cambia
        )
        session.execute(on_conflict_stmt)
        self.logger.debug(f"{len(rule_values)} reglas actualizadas en batch.")
    
    def _add_rule_metrics(self, session, rule_metrics_list: list[dict]):
        """Internal method to add rule metrics in batch."""
        metric_objects = []
        for metric_data in rule_metrics_list:
            metric_objects.append(RuleMetric(
                rule_id=metric_data['id'],
                evaluations=metric_data['evaluations'],
                packets_matched=metric_data['packets_matched'],
                bytes_matched=metric_data['bytes_matched'],
                states_created=metric_data['states_created'],
                state_packets=metric_data['state_packets'],
                state_bytes=metric_data['state_bytes'],
                input_output=metric_data('input_output')
            ))
        session.add_all(metric_objects) # Mejorar rendimiento: agregar todos a la vez
        self.logger.debug(f"{len(metric_objects)} rule metrics agregadas en batch.")

    def _add_inactive_rules_log(self, session, inactive_rules_data: list[dict]):
        """Internal method to add inactive rule logs in batch."""
        log_objects = []
        for logs_data in inactive_rules_data:
            log_objects.append(InactiveRuleLog(
                rule_id=logs_data['rule_id'],
            ))
        session.add_all(log_objects) # Agregar todos a la vez
        self.logger.debug(f"{len(log_objects)} inactive rule logs agregadas en batch.")

    def get_inactive_rules_from_this_batch(self, rule_metrics_list: list[dict]) -> list[dict]:
        """
        Filters the given list of rule metrics to identify rules with 0 bytes_matched.
        These are considered "inactive" for the purpose of logging in inactive_rule_log.

        Args:
            rule_metrics_list: A list of dictionaries, where each dictionary
                               represents a parsed pfctl rule metric from the current batch.

        Returns:
            list[dict]: A list of dictionaries, containing only the rule_id and rule_label
                        for rules that had 0 bytes_matched in this batch.
        """
        inactive_rules = []
        for metric_data in rule_metrics_list:
            if metric_data.get('bytes_matched', 0) == 0:
                # Solo necesitamos el id y el label para el log de inactividad
                inactive_rules.append({
                    'rule_id': metric_data['id'],
                    'rule_label': metric_data['label']
                })
        self.logger.info(f"Se detectaron {len(inactive_rules)} reglas inactivas en batch.")
        return inactive_rules
    
    def get_inactive_rules(self, start_date: datetime, end_date: datetime) -> list[dict]:
        session = None
        inactive_rules = []
        try:
            session = self.db_model.get_session()
            
            # --- Consulta SQL para identificar reglas inactivas con funciones de ventana ---
            # SQLAlchemy puede construir esto, pero a veces es más claro y fácil
            # usar text() para consultas complejas con funciones de ventana,
            # especialmente al principio.

            # Tolerancia como una constante o parámetro
            BYTES_TOLERANCE = 100

            # Nota: Los placeholders ':start_date' y ':end_date' son para seguridad (prevención de SQL Injection)
            sql_query = text(f"""
                SELECT DISTINCT
                    subquery.rule_id,
                    subquery.rule_label
                FROM (
                    SELECT
                        rm.rule_id,
                        rm.rule_label,
                        FIRST_VALUE(rm.bytes_matched) OVER (PARTITION BY rm.rule_id ORDER BY rm.timestamp ASC) AS first_bytes_matched,
                        LAST_VALUE(rm.bytes_matched) OVER (PARTITION BY rm.rule_id ORDER BY rm.timestamp ASC RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS last_bytes_matched
                    FROM
                        rule_metrics rm
                    WHERE
                        rm.timestamp >= :start_date AND rm.timestamp <= :end_date
                ) AS subquery
                WHERE
                    ABS(subquery.last_bytes_matched - subquery.first_bytes_matched) < :tolerance; -- Condición de inactividad con tolerancia
            """)
            
            # Ejecutar la consulta con parámetros
            result = session.execute(
                sql_query,
                {"start_date": start_date, "end_date": end_date, "tolerance": BYTES_TOLERANCE}
            ).fetchall()

            self.logger.debug(f"Resultados: {result}")

            # Convertir los resultados a una lista de diccionarios
            for row in result:
                inactive_rules.append({"rule_id": row.rule_id, "rule_label": row.rule_label})

            self.logger.info(f"Found {len(inactive_rules)} inactive rules between {start_date} and {end_date}.")
            return inactive_rules

        except SQLAlchemyError as e:
            self.logger.critical(f"Database error during inactive rules analysis: {e}")
            return []
        except Exception as e:
            self.logger.critical(f"An unexpected error occurred during inactive rules analysis: {e}")
            return []
        finally:
            if session:
                session.close()