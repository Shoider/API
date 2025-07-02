from flask import Flask
from logger.logger import Logger
from schemas.schema import Schema
from schemas.schemaDate import DateRangeSchema
from routes.route import PFRoute  
from services.service import Service
from models.model import BDModel

#ESTO se comenta
from flask_cors import CORS

app = Flask(__name__)

#ESTO se comenta DEBUG
CORS(app)

logger = Logger()

# Schema
schema_date = DateRangeSchema()

# Model
db_model = BDModel()
db_model.connect_to_database()

# Service
#service = Service(db_conn)
# Inicializa tu servicio de métricas de reglas, pasándole el db_model
rule_metric_service = Service(db_model)

# Routes
#routes = FileGeneratorRoute(service, form_schemaVPNMayo, form_schemaTel, form_schemaRFC, form_schemaInter, form_schemaFolio, form_schemaCampo)
routes = PFRoute(Schema, schema_date, rule_metric_service)

#Blueprint
app.register_blueprint(routes)

if __name__ == "__main__":
    try:
        #app.run(host="0.0.0.0", debug=False)
        app.run(host="0.0.0.0", port=5001, debug=True)
        logger.info("Application started")
    finally:
        #db_conn.close_connection()
        logger.info("Application closed")
        logger.info("Postgres connection closed")