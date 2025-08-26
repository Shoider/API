# Primero se le dan permisos
chmod +x /home/script.sh 

# Luego abrimos cron
crontab -e

# Modo insersion con "i"
# Salir con "esc" + ":wq" + "enter"

# Despues le decimos que ejecute cada minuto
*/1 * * * * /home/script.sh
*/5 * * * * /home/script_final.sh

# Cada hora
0 * * * * /home/script.sh

# Verificar que se va a ejecutar
crontab -l

# Si actualizas pfSense o reinstalas el sistema, 
# se debe verificar que cron no se haya desconfigurado