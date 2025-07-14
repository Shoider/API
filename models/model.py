# model.py

import os
from datetime import datetime, timezone
from logger.logger import Logger
from sqlalchemy import create_engine, Column, Integer, BigInteger, String, DateTime, text, ForeignKey, Date
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.schema import Index

# Define la base declarativa
Base = declarative_base()

# Define tu modelo de tabla para 'rules'
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

# Define tu modelo de tabla para 'rule_metrics'
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
    
# Define tu modelo de tabla para 'inactive_rule_log'
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
    
# Define tu modelo de tabla para 'monthly_execution_counts'
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
    """Model class to connect to PostgreSQL and manage SQLAlchemy engine/sessions."""
    def __init__(self):
        self.engine = None
        self.Session = None
        self.logger = Logger()
        self.db_name = "test_db"

    def connect_to_database(self):
        """
        Function to connect to PostgreSQL and set up the SQLAlchemy engine.
        Also ensures the table schema is created if it doesn't exist.
        """
        db_user = os.environ.get("POSTGRES_USER", "api_user")
        db_password = os.environ.get("POSTGRES_PASSWORD", "pass")
        db_host = os.environ.get("POSTGRES_HOST", "localhost")
        db_port = os.environ.get("POSTGRES_PORT", "5002")

        if not all([db_user, db_password, db_host]):
            self.logger.critical("Database environment variables are required: POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST")
            raise ValueError("Set environment variables: POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST")

        DATABASE_URL = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{self.db_name}"

        self.logger.debug(f"URL: {DATABASE_URL}")

        try:
            self.engine = create_engine(DATABASE_URL)
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
                self.logger.info("Connected to PostgreSQL successfully.")
            
            # Crear las tablas si no existen (importante: Las tablas deben estar definidas)
            Base.metadata.create_all(self.engine)
            self.logger.info(f"Table '{Rule.__tablename__}' ensured to exist.")
            self.logger.info(f"Table '{RuleMetric.__tablename__}' ensured to exist.")
            self.logger.info(f"Table '{InactiveRuleLog.__tablename__}' ensured to exist.")
            self.logger.info(f"Table '{MonthlyExecutionCount.__tablename__}' ensured to exist.")

            self.Session = sessionmaker(bind=self.engine)

        except SQLAlchemyError as e:
            self.logger.critical(f"Error connecting to PostgreSQL or creating table: {e}")
            raise
        except Exception as e:
            self.logger.critical(f"An unexpected error occurred during DB connection: {e}")
            raise

    def close_connection(self):
        """Function to close the connection to PostgreSQL."""
        if self.engine:
            self.engine.dispose()
            self.logger.info("PostgreSQL engine disposed (connections closed).")

    def get_session(self):
        """Provides a new SQLAlchemy session."""
        if self.Session:
            return self.Session()
        else:
            self.logger.critical("Database session factory not initialized. Call connect_to_database first.")
            raise RuntimeError("Database not connected.")