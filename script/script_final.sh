#!/bin/sh

# Configuración del API
API_URL="http://172.29.206.227:8000/api/v1/data"
API_TOKEN="Mazapan"

# Rutas para los archivos de log
API_RESPONSE_LOG="/home/Operador5/pf/pf_sense_api_response.log"
# Archivo para guardar la última respuesta de la API cuando hay un error (se sobrescribe)
API_ERROR_DETAILS_FILE="/home/Operador5/pf/pf_sense_api_error_details.log"
# Ruta oara los logs de smtp
SMTP_LOG_DIR="/home/Operador5/pf/mail"

# Archivo temporal para la salida del cuerpo de la respuesta de curl
TEMP_CURL_OUTPUT="${SMTP_LOG_DIR}/curl_output_$$"

# Configuración del SMTP
SMTP_SERVER="172.29.150.2"                              # IP de tu servidor SMTP
SMTP_PORT="25"                                          # Puerto SMTP estándar sin cifrado
SENDER_EMAIL="requerimiento.seguridad06@conagua.gob.mx" # Email del remitente
RECIPIENT_EMAIL_ALERT="req.seguridad17@conagua.gob.mx"  # Email del destinatario

# Asegurarse de que los directorios existan
mkdir -p "$(dirname "$API_RESPONSE_LOG")"
mkdir -p "$(dirname "$API_ERROR_DETAILS_FILE")"
mkdir -p /home/Operador5/pf/mail

# Configuración de reintentos
MAX_RETRIES=1   # Intentos maximos
RETRY_DELAY=5  # Segundos entre intentos
RETRY_COUNT=0   # Contador inicializado en 0

# Función para limpiar archivos temporales al salir del script
cleanup() {
    rm -f "$TEMP_CURL_OUTPUT"
}
# Registrar la función cleanup para que se ejecute al salir del script (éxito o fallo)
trap cleanup EXIT

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

# --- Bucle de reintentos para la llamada a la API ---
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    echo "$(date): Intento $((RETRY_COUNT + 1)) de ${MAX_RETRIES} para enviar datos a la API..."

    # Captura el código HTTP y la respuesta del cuerpo en variables separadas
    # La salida del cuerpo de la respuesta va al archivo temporal
    HTTP_STATUS=$(curl -s -o "$TEMP_CURL_OUTPUT" -w "%{http_code}" \
      -X POST \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer ${API_TOKEN}" \
      -d "${JSON_PAYLOAD}" \
      "${API_URL}")

    # Leer la respuesta de la API desde el archivo temporal
    # El '2>/dev/null || echo ""' maneja el caso de que el archivo temporal no exista o esté vacío
    API_RESPONSE=$(cat "$TEMP_CURL_OUTPUT" 2>/dev/null || echo "")

    # Siempre guardar la respuesta en el log general (API_RESPONSE_LOG)
    # Se añade la fecha, el estado HTTP y la respuesta JSON en una sola línea
    echo "$(date) - HTTP Status: ${HTTP_STATUS} - Response: ${API_RESPONSE}" >> "$API_RESPONSE_LOG"
    echo "$(date): Respuesta de la API (HTTP Status: ${HTTP_STATUS}): ${API_RESPONSE}"

    # Evaluar el código de estado HTTP
    if [ "$HTTP_STATUS" -eq 200 ]; then
        echo "$(date): Datos enviados exitosamente. API respondió 200 OK."
        break # Salir del bucle de reintentos si fue exitoso
    else
        echo "$(date): API no respondió con 200 OK. Código: ${HTTP_STATUS}. Guardando detalles del error y reintentando en ${RETRY_DELAY} segundos..."

        RETRY_COUNT=$((RETRY_COUNT + 1))
        if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
            sleep $RETRY_DELAY # Esperar antes de reintentar
        fi
    fi
done

# --- Después del bucle de reintentos ---
if [ "$HTTP_STATUS" -ne 200 ]; then
    echo "$(date): Falló el envío a la API después de ${MAX_RETRIES} intentos. HTTP: ${HTTP_STATUS}"
    
    # Registrar error
    ERROR_DATE=$(date)
    ERROR_MESSAGE="API Error: $HTTP_STATUS - $API_RESPONSE"
    echo "$ERROR_DATE - $ERROR_MESSAGE" > "$API_ERROR_DETAILS_FILE"

    # Preparar correo
    ALERT_SUBJECT="ALERTA: Error de API en pfSense (HTTP $HTTP_STATUS)"
    ALERT_EMAIL_BODY=$(cat <<EOF
Hola,

Error en script pfSense:
- Fecha: $ERROR_DATE
- Codigo HTTP: $HTTP_STATUS
- Respuesta: ${API_RESPONSE}

Detalles completos en: $API_ERROR_DETAILS_FILE

Atentamente,
Sistema de Alertas de pfSense
EOF
    )

    # Enviar correo con verificación SMTP
    if nc -z -w 5 "$SMTP_SERVER" "$SMTP_PORT"; then
        {
            printf "HELO pfsense\r\n"; sleep 1
            printf "MAIL FROM:<%s>\r\n" "$SENDER_EMAIL"; sleep 1
            printf "RCPT TO:<%s>\r\n" "$RECIPIENT_EMAIL_ALERT"; sleep 1
            printf "DATA\r\n"; sleep 1
            printf "Subject: %s\r\n" "$ALERT_SUBJECT"
            printf "\r\n%s\r\n" "$ALERT_EMAIL_BODY"
            printf ".\r\n"; sleep 2
            printf "QUIT\r\n"; sleep 1
        } | /usr/bin/nc -w 20 -v "$SMTP_SERVER" "$SMTP_PORT" > "${SMTP_LOG_DIR}/smtp_alert_$(date +%Y%m%d_%H%M%S).log" 2>&1
    else
        echo "ERROR: No se pudo conectar al SMTP $SMTP_SERVER:$SMTP_PORT"
    fi
    exit 1
fi
