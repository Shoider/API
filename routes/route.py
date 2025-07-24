from flask import Blueprint, request, jsonify
from logger.logger import Logger
from marshmallow import ValidationError
from datetime import datetime, time
import re

class PFRoute(Blueprint):
    """Class to handle the routes"""

    def __init__(self, schema_class, schema_date, service):
        super().__init__("pf_routes", __name__)
        self.logger = Logger()
        self.schema_class = schema_class
        self.schema_date = schema_date
        self.service = service
        self.register_routes()

    def register_routes(self):
        """Function to register the routes"""
        self.route("/api/v1/data", methods=["POST"])(self.update)
        self.route("/api/v1/healthcheck", methods=["GET"])(self.healthcheck)

    def fetch_request_data(self):
        """Function to fetch the request data"""
        try:
            request_data = request.json
            if not request_data:
                return 400, "Invalid data", None
            return 200, None, request_data
        except Exception as e:
            self.logger.error(f"Error fetching request data: {e}")
            return 500, "Error fetching request data", None
        
    def parse_pfctl_line(self, line: str) -> dict:
        """Parses a single pfctl statistics line."""
        pattern = re.compile(
            r'^(USER_RULE:?\s*(.*?))\s+id:(\d+)\s+'  # USER_RULE prefix, label, id
            r'(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)' # 7 numeric counters
        )
        
        match = pattern.match(line)
        
        if match:
            full_label_prefix = match.group(1)
            label = match.group(2).strip()

            evaluations = int(match.group(4))
            packets_matched = int(match.group(5))
            bytes_matched = int(match.group(6))
            states_created = int(match.group(7))
            state_packets = int(match.group(8))
            state_bytes = int(match.group(9))
            input_output = int(match.group(10))
            rule_id = int(match.group(3))
            
            return {
                "label": label,
                "id": rule_id,
                "evaluations": evaluations,
                "packets_matched": packets_matched,
                "bytes_matched": bytes_matched,
                "states_created": states_created,
                "state_packets": state_packets,
                "state_bytes": state_bytes,
                "input_output": input_output
            }
        else:
            print(f"WARNING: Could not parse line: {line}")
            return None

    def merge_duplicate_rules(self, rules) -> dict:
        """Merge the duplicated rules registered"""
        merged = {}
        for rule in rules:
            rule_id = rule['id']
            if rule_id in merged:
                # Suma los valores numéricos
                merged[rule_id]['evaluations'] += rule['evaluations']
                merged[rule_id]['packets_matched'] += rule['packets_matched']
                merged[rule_id]['bytes_matched'] += rule['bytes_matched']
                merged[rule_id]['states_created'] += rule['states_created']
                merged[rule_id]['state_packets'] += rule['state_packets']
                merged[rule_id]['state_bytes'] += rule['state_bytes']
                merged[rule_id]['input_output'] += rule['input_output']
            else:
                merged[rule_id] = rule.copy()
        return list(merged.values())

    def update(self):
        """
        Esta ruta debera de recibir datos y mostrarlos
        Args:
            data: Un diccionario.

        Returns:
            validated_data: Datos registrados en la base de datos
        """
        try:
            # Traer datos
            raw_lines = request.get_json()
            if not raw_lines:
                self.logger.error(f"No se recibierón datos")
                return jsonify({"error": "No se recibieron datos"}), 400
            
            self.logger.debug(f"Datos recibidos: {raw_lines}")

            # Se crea el diccionario
            parsed_data = []
            for line in raw_lines:
                parsed_rule = self.parse_pfctl_line(line)
                if parsed_rule:
                    parsed_data.append(parsed_rule)

            # Revisar si hay datos duplicados para sumarlos y guardarlos juntos
            filtered_data = self.merge_duplicate_rules(parsed_data)

            # Validacion con Marshmallow
            schema_instance = self.schema_class(many=True)
            validated_data = schema_instance.load(filtered_data)
            self.logger.debug(f"Datos validados correctamente: {validated_data}")

            # Se le llama al servicio para guardar los datos
            result = self.service.add_metrics(validated_data)

            if (result == True):
                self.logger.info("Registro exitoso")
                return jsonify({"message": "Registro exitoso", "data": validated_data, "time": datetime.now().isoformat()}), 200
            else:
                self.logger.info("Ocurrio un error al guardar la informacion en la base de datos")
                return jsonify({"message": "Ocurrio un error al guardar la informacion en la base de datos", "data": validated_data, "time": datetime.now().isoformat()}), 400
            
        except ValidationError as err:
            messages = err.messages
            self.logger.warning("Ocurrieron errores de validación")
            self.logger.info(f"Errores de validación completos: {messages}")
            
            # Otro error de validacion
            return jsonify({"error": "Datos invalidos", "time": datetime.now().isoformat()}), 422
        except Exception as e:
            self.logger.critical(f"Error critico: {e}")
            return jsonify({"error": "Error interno", "time": datetime.now().isoformat()}), 500
        finally:
            # Eliminar el directorio temporal
            self.logger.info("Función finalizada")

    def InactiveRules(self):
        """
        Endpoint para buscar reglas sin uso comparando "bytes_matched".
        Espera 'start_date' y 'end_date' como parametros en formato YYYY-MM-DD.
        """
        try:
            # Validacion de datos recibidos
            query_params = {
                "fechaInicio": request.args.get('fechaInicio'),
                "fechaFin": request.args.get('fechaFin')
            }
            
            self.logger.debug(f"Datos recibidos: {query_params}")

            validated_data = self.schema_date.load(query_params)

            # Las fechas ya son objetos datetime.date gracias a fields.Date
            start_date_obj = validated_data['fechaInicio']
            end_date_obj = validated_data['fechaFin']

            # Convierte datetime.date a datetime.datetime y establece la hora
            # Para start_date, queremos el inicio del día
            start_date = datetime.combine(start_date_obj, time.min) # 00:00:00.000000

            # Para end_date, queremos el final del día
            end_date = datetime.combine(end_date_obj, time.max) # 23:59:59.999999

            # Llama al servicio para obtener las reglas inactivas
            inactive_rules = self.service.get_inactive_rules(start_date, end_date)

            return jsonify({"status": "success", "inactive_rules": inactive_rules}), 200

        except ValidationError as err:
            messages = err.messages
            self.logger.warning("Ocurrieron errores de validación")
            self.logger.info(f"Errores de validación completos: {messages}")
            return jsonify({"error": "Datos invalidos"}), 422
        except Exception as e:
            self.logger.critical(f"Error critico: {e}")
            return jsonify({"error": "Error interno"}), 500
        
    def Zero(self, data):
        """
        Endpoint para actualizar la tabla que contiene los registros con 0 bytes usados.
        """
        self.logger.debug("Llamada iniciada")
        try:
            self.logger.debug(f"Datos recibidos en Zero {data}")

            self.logger.debug("Llamando al servicio")

            result = self.service.dasdasd

            self.logger.debug("Tabla de reglas sin uso actualizada")

            self.logger.info(f"Datos agregados a tabla sin uso {data}")

            # Las fechas ya son objetos datetime.date gracias a fields.Date

            # Convierte datetime.date a datetime.datetime y establece la hora
            # Para start_date, queremos el inicio del día

            if (result == True):
                return result
            else:
                return result

        except Exception as e:
            self.logger.critical(f"Error critico: {e}")
            return False

    def healthcheck(self):
        """Function to check the health of the services API inside the docker container"""
        return jsonify({"status": "Up"}), 200