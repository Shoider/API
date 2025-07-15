# model.py

import os
from datetime import datetime, timezone
from logger.logger import Logger
from sqlalchemy import create_engine, Column, Integer, BigInteger, String, DateTime, text, ForeignKey, Date
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.schema import Index

Base = declarative_base()

class Rule(Base):
    __tablename__ = 'rules'

    rule_id = Column(BigInteger, primary_key=True)
    rule_label = Column(String(255), nullable=False)
    rule_description = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index('idx_rules_rule_label', 'rule_label'),
    )

    def __repr__(self):
        return f"<Rule(rule_id={self.rule_id}, rule_label='{self.rule_label}', created_at='{self.created_at}')>"

class RuleMetric(Base):
    __tablename__ = 'rule_metrics'

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
    rule_id = Column(BigInteger, ForeignKey('rules.rule_id', ondelete='RESTRICT'), nullable=False)
    evaluations = Column(BigInteger, nullable=False)
    packets_matched = Column(BigInteger, nullable=False)
    bytes_matched = Column(BigInteger, nullable=False)
    states_created = Column(BigInteger, nullable=False)
    state_packets = Column(BigInteger, nullable=False)
    state_bytes = Column(BigInteger, nullable=False)
    input_output = Column(BigInteger, nullable=True)

    __table_args__ = (
        Index('idx_rule_metrics_rule_id', 'rule_id'),
        Index('idx_rule_metrics_timestamp', 'timestamp'),
        Index('idx_rule_metrics_rule_id_timestamp', 'rule_id', 'timestamp', unique=False),
    )

    def __repr__(self):
        return f"<RuleMetric(id={self.id}, rule_id={self.rule_id}, timestamp='{self.timestamp}')>"
    
class InactiveRuleLog(Base):
    __tablename__ = 'inactive_rule_log'

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    rule_id = Column(BigInteger, ForeignKey('rules.rule_id', ondelete='RESTRICT'), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index('idx_inactive_rule_log_rule_id', 'rule_id'),
        Index('idx_inactive_rule_log_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<InactiveRuleLog(id={self.log_id}, rule_id='{self.rule_id}', created_at='{self.created_at}')>"
    
class MonthlyExecutionCount(Base):
    __tablename__ = 'monthly_execution_counts'

    count_id = Column(Integer, primary_key=True, autoincrement=True)
    month_start_date = Column(Date, nullable=False, unique=True) # Unique constraint a nivel de columna
    execution_count = Column(Integer, nullable=False, default=0)
    last_updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        # No se necesita Index explícito si month_start_date ya es UNIQUE
        # Index('idx_monthly_execution_counts_month', 'month_start_date'),
    )

    def __repr__(self):
        return f"<MonthlyExecutionCount(month={self.month_start_date}, count={self.execution_count})>"


class BDModel:
    """Clase para conectarse a PostgreSQL y gestionar SQLAlchemy engine/sessions."""
    def __init__(self):
        self.engine = None
        self.Session = None
        self.logger = Logger()
        self.db_name = "pf_sense"

    def connect_to_database(self):
        """Funcion para conectarse a PostgreSQL y iniciar SQLAlchemy engine."""
        db_user = os.environ.get("POSTGRES_USER", "api_user")
        db_password = os.environ.get("POSTGRES_PASSWORD", "pass")
        db_host = os.environ.get("POSTGRES_HOST", "localhost")
        db_port = os.environ.get("POSTGRES_PORT", "5000")

        if not all([db_user, db_password, db_host]):
            self.logger.critical("No se agregaron las variables de entorno de la Base de Datos: POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST")
            raise ValueError("Agrega las variables: POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST")

        DATABASE_URL = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{self.db_name}"

        self.logger.debug(f"URL: {DATABASE_URL}")

        try:
            self.engine = create_engine(DATABASE_URL)
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
                self.logger.info("Conectado a PostgreSQL exitosamente.")
            
            # Crear las tablas si no existen (importante: Las tablas deben estar definidas)
            Base.metadata.create_all(self.engine)
            self.logger.debug(f"Table '{Rule.__tablename__}' asegurate que exista.")
            self.logger.debug(f"Table '{RuleMetric.__tablename__}' asegurate que exista.")
            self.logger.debug(f"Table '{InactiveRuleLog.__tablename__}' asegurate que exista.")
            self.logger.debug(f"Table '{MonthlyExecutionCount.__tablename__}' asegurate que exista.")

            self.Session = sessionmaker(bind=self.engine)

        except SQLAlchemyError as e:
            self.logger.critical(f"Error conectando a PostgreSQL o creando tabla: {e}")
            raise
        except Exception as e:
            self.logger.critical(f"Ocurrio un error durante la conexion a PostgreSQL: {e}")
            raise

    def close_connection(self):
        """Funcion para cerrar la conexion a PostgreSQL."""
        if self.engine:
            self.engine.dispose()
            self.logger.info("PostgreSQL engine detenido (conexiones cerradas).")

    def get_session(self):
        """Crea una nueva SQLAlchemy session."""
        if self.Session:
            return self.Session()
        else:
            self.logger.critical("No se ha iniciado la sesion. Usa connect_to_database primero.")
            raise RuntimeError("Base de datos no conectada.")