# Usa una imagen base de Ubuntu
FROM ubuntu:latest

# --- FASE DE PREPARACIÓN E INSTALACIÓN ---

# Actualiza la lista de paquetes e instala OpenSSH-server, curl y sudo
# Se usa `-y` para aceptar automáticamente las instalaciones
# `mkdir -p /var/run/sshd` es necesario para que el servicio SSH pueda iniciarse
RUN apt-get update && \
    apt-get install -y openssh-server curl sudo && \
    mkdir -p /var/run/sshd

COPY . /app

# --- CONFIGURACIÓN DE USUARIOS Y AUTENTICACIÓN ---

# 1. Configuración para el usuario ROOT:
# Establece una contraseña inicial para root (útil para acceso local dentro del contenedor si es necesario),
# pero el acceso SSH por contraseña será deshabilitado.
RUN echo 'root:rootpass' | chpasswd

# Modifica la configuración de SSH para deshabilitar el login de root con contraseña
# 'PermitRootLogin without-password' permite la autenticación solo con claves SSH para root.
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin without-password/' /etc/ssh/sshd_config

# 2. Configuración para el usuario ADMIN:
# Define una variable de entorno para la contraseña del usuario admin.
# Puedes pasarla durante el build con `--build-arg ADMIN_PASSWORD=tu_nueva_contraseña`.
ARG ADMIN_PASSWORD=pass

# Crea el usuario 'admin', le asigna un shell bash y lo añade al grupo sudo.
# Establece la contraseña para el usuario 'admin'.
RUN useradd -ms /bin/bash admin && \
    echo "admin:$ADMIN_PASSWORD" | chpasswd && \
    adduser admin sudo

# Asegura que la autenticación por contraseña esté habilitada globalmente para SSH.
# Esto es necesario para que el usuario 'admin' pueda usar contraseñas.
RUN sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config

# --- LIMPIEZA Y EJECUCIÓN ---

# Expone el puerto 22, el puerto estándar para SSH.
EXPOSE 22

# Comando por defecto para iniciar el servicio SSH en segundo plano
# `-D` mantiene sshd en primer plano, lo que es necesario para que el contenedor no se cierre.
CMD ["/usr/sbin/sshd", "-D"]
