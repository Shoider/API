#!/bin/sh

# --- Variables ---
ASUNTO="TEST"
DESTINATARIO="req.seguridad17@conagua.gob.mx"

# --- Contenido del correo ---
CONTENIDO="HolaMundo"

# --- Envío del correo ---
echo "$CONTENIDO" | /usr/local/bin/send_mail.php -s="$ASUNTO" "$DESTINATARIO"
echo "Hola, esto es una prueba desde linea de comandos" | mail.php -s "comandos" "req.seguridad17@conagua.gob.mx"

# chmod +x email.sh