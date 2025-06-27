from datetime import datetime
from flask import jsonify
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, and_, text
from sqlalchemy.dialects import postgresql
from models.model import RuleMetric
from logger.logger import Logger

class Service:
    """Service class to that implements the logic of the CRUD operations for tickets"""

    def __init__(self, db_model):
        self.logger = Logger()
        self.db_model = db_model

    def add_rule_metrics(self, rule_metrics_list: list[dict]) -> bool:
        """
        Adds a list of parsed rule metrics to the database.
        This method handles the business logic for saving rule metrics.

        Args:
            rule_metrics_list: A list of dictionaries, where each dictionary
                               represents a parsed pfctl rule metric.
        Returns:
            bool: True if insertion was successful, False otherwise.
        """
        session = None
        try:
            session = self.db_model.get_session() # Obtiene la sesión de la capa de modelo
            for metric_data in rule_metrics_list:
                metric = RuleMetric(
                    rule_id=metric_data['id'],
                    rule_label=metric_data['label'],
                    evaluations=metric_data['evaluations'],
                    packets_matched=metric_data['packets_matched'],
                    bytes_matched=metric_data['bytes_matched'],
                    states_created=metric_data['states_created'],
                    state_packets=metric_data['state_packets'],
                    state_bytes=metric_data['state_bytes'],
                    last_field=metric_data.get('last_field')
                )
                session.add(metric)
            session.commit()
            self.logger.info(f"Successfully added {len(rule_metrics_list)} rule metrics to DB.")
            return True
        except SQLAlchemyError as e:
            if session:
                session.rollback()
            self.logger.critical(f"Database error while adding rule metrics: {e}")
            return False
        except Exception as e:
            self.logger.critical(f"An unexpected error occurred in service layer while adding rule metrics: {e}")
            return False
        finally:
            if session:
                session.close()

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