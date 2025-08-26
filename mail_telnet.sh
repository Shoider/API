#!/bin/sh

# --- Variables de Configuración ---
SMTP_SERVER="172.29.150.2"             # <--- IP de tu servidor SMTP
SMTP_PORT="25"                         # Puerto SMTP estándar sin cifrado
SENDER_EMAIL="requerimiento.seguridad06@conagua.gob.mx" # <--- Email del remitente
RECIPIENT_EMAIL="req.seguridad17@conagua.gob.mx" # <--- Email del destinatario
EMAIL_SUBJECT="Test Email script con pausas"
EMAIL_BODY="Este es un correo de prueba enviado desde un script en pfSense usando Telnet.
Ha sido enviado el $(date).
Saludos,
El Script de pfSense"

# --- Ejecución del Script ---
echo "Iniciando conexión Telnet a ${SMTP_SERVER}:${SMTP_PORT}..."
echo "Enviando correo..."

# Envía los comandos SMTP al servidor usando netcat
(
    printf "HELO pfsense\r\n"
    sleep 1
    
    printf "MAIL FROM:<%s>\r\n" "${SENDER_EMAIL}"
    sleep 1
    
    printf "RCPT TO:<%s>\r\n" "${RECIPIENT_EMAIL}"
    sleep 1
    
    printf "DATA\r\n"
    sleep 1
    
    # Encabezados y cuerpo del email (¡atención al formato!)
    printf "Subject: %s\r\n" "${EMAIL_SUBJECT}"
    printf "\r\n"  # Línea en blanco REQUERIDA entre headers y body
    printf "%s\r\n" "${EMAIL_BODY}"
    printf ".\r\n"  # Fin del mensaje
    sleep 2
    
    printf "QUIT\r\n"
    sleep 1
) | nc -w 15 -v "$SMTP_SERVER" "$SMTP_PORT" > "mail/smtp_log_$(date +%Y%m%d_%H%M%S).txt" 2>&1

# Verificación del resultado
if [ $? -eq 0 ]; then
    echo "Comandos SMTP enviados exitosamente. Verifica los logs del servidor y el archivo de log del script."
    LOG_FILE=$(ls -t mail/smtp_log_*.txt | head -1)
    echo "Log guardado en: $LOG_FILE"
    echo "Contenido del log:"
    cat "$LOG_FILE"
    exit 0
else
    echo "Error: Falló la conexión o el envío de comandos."
    LOG_FILE=$(ls -t mail/smtp_log_*.txt | head -1)
    [ -f "$LOG_FILE" ] && cat "$LOG_FILE"
    echo "Revisa la conectividad a ${SMTP_SERVER}:${SMTP_PORT}."
    exit 1
fi