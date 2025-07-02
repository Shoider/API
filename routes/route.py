from flask import Blueprint, request, jsonify, send_file
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
        self.route("/api/v1/shell", methods=["POST"])(self.actualizacion)
        self.route("/api/v1/data", methods=["POST"])(self.token)
        self.route("/api/v1/inactive", methods=["GET"])(self.InactiveRules)
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
        
    # --- Define your parsing function here or import it ---
    def parse_pfctl_line(self, line: str) -> dict:
        """
        Parses a single pfctl statistics line.
        """
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
            last_field = int(match.group(10))

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
                "last_field": last_field
            }
        else:
            print(f"WARNING: Could not parse line: {line}")
            return None

    def token(self):
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
                return jsonify({"error": "No data sent"}), 400
            
            self.logger.debug(f"Datos recibidos: {raw_lines}")

            # Se crea el diccionario
            parsed_data = []
            for line in raw_lines:
                parsed_rule = self.parse_pfctl_line(line)
                if parsed_rule:
                    parsed_data.append(parsed_rule)

            # Validacion con Marshmallow
            schema_instance = self.schema_class(many=True)

            validated_data = schema_instance.load(parsed_data)
            self.logger.info(f"Datos validados correctamente: {validated_data}")

            # Se le llama al servicio para guardar los datos
            result = self.service.add_metrics(validated_data)

            if (result == True):
                return jsonify({"message": "Registro exitoso", "data": validated_data}), 200
            else:
                return jsonify({"message": "Ocurrio un error al guardar la informacion en la base de datos", "data": validated_data}), 400
            
        except ValidationError as err:
            messages = err.messages
            self.logger.warning("Ocurrieron errores de validación")
            self.logger.info(f"Errores de validación completos: {messages}")
            
            # Otro error de validacion
            return jsonify({"error": "Datos invalidos"}), 422
        except Exception as e:
            self.logger.critical(f"Error critico: {e}")
            return jsonify({"error": "Error interno"}), 500
        finally:
            # Eliminar el directorio temporal
            self.logger.info("Función finalizada")

    def actualizacion(self):
        """
        Esta ruta debera de recibir datos y guardarlos en una base de datos

        Args:
            data: Un diccionario.

        Returns:
            No se
        """
        try:

            # Validacion de datos recibidos
            data = request.get_json()
            if not data:
                return jsonify({"error": "No se enviaron datos"}), 400
            
            self.logger.debug(f"Datos recibidos: {data}")

            # Validacion de los datos en schema
            #self.schema.load(data)
            self.logger.debug("Ya se validaron los datos correctamente")
            self.logger.debug(data)

            # Guardar en base de datos
            # Llamar al servicio
            #vpnmayo_registro, status_code = self.service.add_VPNMayo(datosProcesados)

            """
            if status_code == 201:
                noformato = vpnmayo_registro.get('_id')
                epoch = vpnmayo_registro.get('epoch')
                self.logger.info(f"Registro VPN Mayo agregado con ID: {noformato}")

                # Enviar informacion al frontend
                return jsonify({"message": "Generando PDF", "id": noformato, "epoch": epoch}), 200
            else:
                self.logger.error(f"Error agregando el registro a la base de datos")
                # Enviar informacion al frontend
                return jsonify({"error": "Error agregando el registro a la base de datos"}), 500 """
            
            return jsonify({"message": "Registrado correctamente"}), 200
            
        except ValidationError as err:
            messages = err.messages
            self.logger.warning("Ocurrieron errores de validación")
            self.logger.info(f"Errores de validación completos: {messages}")
            
            # Otro error de validacion
            return jsonify({"error": "Datos invalidos"}), 422
        except Exception as e:
            self.logger.critical(f"Error critico: {e}")
            return jsonify({"error": "Error interno"}), 500
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