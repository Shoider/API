#!/bin/sh

# Configuracion de tu API
API_URL="http://172.29.206.227:8000/api/v1/data"
#API_URL="http://localhost:5001/api/v1/data"
#API_URL="http://192.168.137.149:8000/api/v1/data"

# Contenido de las estad  sticas de prueba como un JSON v  lido
# Las comillas simples encierran toda la cadena JSON.
# Las comillas dobles internas deben ser escapadas con \".
# Los saltos de l  nea se representan con \n.

# Lo que importa aqui es este dato 3 despues de id
ALL_USER_STATS='[
  "USER_RULE: PruebaHora id:50000005 0 0 0 0 0 0 0 0"
]'

# Archivo para guardar la respuesta de la API
API_RESPONSE_FILE="api_response_$(date +%Y%m%d_%H%M%S).txt"

# --- Realizar la llamada a la API usando curl ---
echo "Realizando llamada a la API en: ${API_URL}"

# El contenido del POST ser   el JSON v  lido de la variable ALL_USER_STATS
API_CALL_RESPONSE=$(echo "${ALL_USER_STATS}" | curl -s -X POST \
  -H "Content-Type: application/json" \
  -d @- \
  "${API_URL}")

# 3. Guardar la respuesta de la API en un archivo
echo "${API_CALL_RESPONSE}" > "${API_RESPONSE_FILE}"

# 4. Mostrar el resultado de la llamada a la API
if [ $? -eq 0 ]; then
    echo "Llamada a la API completada. Respuesta guardada en: ${API_RESPONSE_FILE}"
    echo "Contenido de la respuesta de la API:"
    cat "$API_RESPONSE_FILE"
else
    echo "Error en la llamada a la API. Consulta ${API_RESPONSE_FILE} para mas detalles."
fi