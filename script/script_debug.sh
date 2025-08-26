#!/bin/sh

# Configuración de tu API
API_URL="http://172.29.206.227:8000/api/v1/data"

# Nombre del archivo de salida donde se guardará el contenido que se enviaría a la API
# Para debug estan bien, pero API_RESPONSE_FILE podria reducirse para para ahorrar espacio,
# ademas, OUTPUT_FILE es 100% de debug, hay que eliminarlo despues
OUTPUT_FILE="/home/pf/data/pfctl_api_raw_payload_$(date +%Y%m%d_%H%M%S).txt"
API_RESPONSE_FILE="/home/pf/response/api_response_$(date +%Y%m%d_%H%M%S).txt"

# Configuración de reintentos
MAX_RETRIES=5   # Intentos maximos
RETRY_DELAY=60  # Segundos entre intentos
RETRY_COUNT=0   # Contador inicializado en 0

# --- Lógica principal del script ---
echo "Recopilando estadísticas de pfSense..."

# Obtener las líneas de estadísticas de reglas de usuario.
# Usamos `awk` para filtrar solo las líneas que contienen los contadores numéricos al final.
PF_STATS_RAW=$(pfctl -s all | awk '/^USER_RULE:/')

# Verificar si se encontraron estadísticas
if [ -z "$PF_STATS_RAW" ]; then
    echo "No se encontraron líneas de estadísticas de USER_RULE: con contadores. No se generará archivo."
    exit 0
fi

# Convertir las líneas de PF_STATS_RAW a un array JSON usando jq
# Cada línea se convierte en un elemento de un array JSON
JSON_PAYLOAD=$(echo "$PF_STATS_RAW" | jq -R . | jq -s .)

# Guardar datos que se van a enviar para revisarlos
echo "Generando archivo con el payload JSON en: ${OUTPUT_FILE}"
echo "${JSON_PAYLOAD}" > "${OUTPUT_FILE}"

# Confirmación de la generación del archivo de datos
if [ -f "$OUTPUT_FILE" ]; then
    echo "Archivo generado exitosamente. Contenido:"
    cat "$OUTPUT_FILE" # Muestra el contenido del archivo generado
else
    echo "Error: No se pudo generar el archivo de payload."
fi

# --- Bucle de reintentos para la llamada a la API ---
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    echo "$(date): Intento $((RETRY_COUNT + 1)) de ${MAX_RETRIES} para enviar datos a la API..."

    # Captura el código HTTP y la respuesta del cuerpo en variables separadas
    HTTP_STATUS=$(curl -s -o "${API_RESPONSE_FILE}.tmp" -w "%{http_code}" \
      -X POST \
      -H "Content-Type: application/json" \
      -d "${JSON_PAYLOAD}" \
      "${API_URL}")

    # Mueve el contenido temporal al archivo final de respuesta si la llamada de curl tuvo éxito
    if [ $? -eq 0 ]; then
        mv "${API_RESPONSE_FILE}.tmp" "${API_RESPONSE_FILE}"
    else
        echo "$(date): Error de Curl. No se pudo completar la petición HTTP. Reintentando..."
        RETRY_COUNT=$((RETRY_COUNT + 1))
        if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
            sleep $RETRY_DELAY
        fi
        continue # Ir al siguiente intento del bucle
    fi

    # Leer la respuesta de la API que ahora está en el archivo
    API_RESPONSE=$(cat "${API_RESPONSE_FILE}")

    echo "$(date): Respuesta de la API (HTTP Status: ${HTTP_STATUS}): ${API_RESPONSE}"

    if [ "$HTTP_STATUS" -eq 200 ]; then
        echo "$(date): Datos enviados exitosamente. API respondió 200 OK."
        break # Salir del bucle de reintentos
    else
        echo "$(date): API no respondió con 200 OK. Código: ${HTTP_STATUS}. Reintentando en ${RETRY_DELAY} segundos..."
        RETRY_COUNT=$((RETRY_COUNT + 1))
        if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
            sleep $RETRY_DELAY
        fi
    fi
done

# --- Manejo final después del bucle de reintentos ---
if [ "$HTTP_STATUS" -ne 200 ]; then
    echo "$(date): Falló el envío de datos a la API después de ${MAX_RETRIES} intentos. Último código HTTP: ${HTTP_STATUS}"
    
    # Aqui podemos pensar como avisar si hubo un error.
    # Quiza un correo, una alerta, algo para comunicar que no se ejecuto correctamente

    exit 1 # Indicar fallo
else
    echo "$(date): Proceso de envío de datos a la API completado exitosamente."
    exit 0 # Indicar éxito
fi