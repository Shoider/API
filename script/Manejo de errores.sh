# --- Manejo final después del bucle de reintentos ---
if [ "$HTTP_STATUS" -ne 200 ]; then
    ERROR_DATE=$(date)
    ERROR_MESSAGE="Falló el envío de datos a la API después de ${MAX_RETRIES} intentos. Último código HTTP: ${HTTP_STATUS}"
    
    echo "$ERROR_DATE: $ERROR_MESSAGE"
    
    # Guardar la respuesta completa en el archivo de detalles de error (API_ERROR_DETAILS_FILE)
    # Esto sobrescribe el archivo con el último error
    echo "$ERROR_DATE - HTTP Status: ${HTTP_STATUS} - Response: ${API_RESPONSE}" > "$API_ERROR_DETAILS_FILE"
    echo "Detalles del último error guardados en: ${API_ERROR_DETAILS_FILE}"

    # --- Configuración para el Correo Electrónico ---
    RECIPIENT_EMAIL="tu_email@example.com" # <--- ¡CAMBIA ESTO A TU CORREO!
    SENDER_NAME="pfSense Alerts"
    SUBJECT="ALERTA: Error de API en pfSense - Fallo de script"
    
    # Cuerpo del correo
    EMAIL_BODY="Hola,\n\n"
    EMAIL_BODY+="El script de API en pfSense ha fallado.\n"
    EMAIL_BODY+="Fecha y Hora: $ERROR_DATE\n"
    EMAIL_BODY+="Mensaje de Error: $ERROR_MESSAGE\n"
    EMAIL_BODY+="Detalles del último error guardados en: $API_ERROR_DETAILS_FILE\n"
    EMAIL_BODY+="Respuesta completa de la API:\n"
    EMAIL_BODY+="$API_RESPONSE\n\n"
    EMAIL_BODY+="Por favor, revisa el firewall.\n"
    EMAIL_BODY+="Atentamente,\nEl Script de Alertas"

    # Enviar el correo electrónico
    # Usamos printf para manejar saltos de línea y formatear el cuerpo
    # La opción -s es para el asunto, y -r para el remitente (From)
    printf "%b" "$EMAIL_BODY" | mail -s "$SUBJECT" -r "$SENDER_NAME <no-reply@yourdomain.com>" "$RECIPIENT_EMAIL"
    echo "Alerta de correo electrónico enviada a $RECIPIENT_EMAIL"
    
    exit 1 # Indicar fallo del script
else
    echo "$(date): Proceso de envío de datos a la API completado exitosamente."
    exit 0 # Indicar éxito del script
fi