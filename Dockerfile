FROM python:latest

WORKDIR /app

# Crear grupo y usuario 'app'
RUN groupadd -g 1000 app && \
    useradd -m -u 1000 -g app app

# Copiar archivos y cambiar propietario
COPY . .

RUN mkdir -p /app/logs && \
    chown -R app:app /app/logs && \
    chmod -R 775 /app/logs

RUN mkdir -p /app/data && \
    chown -R app:app /app/data && \
    chmod -R 777 /app/data

# Instalar dependencias del sistema
RUN apt-get update && \
    apt-get install -y tzdata curl faketime && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip && pip install -r requirements.txt

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 CMD curl --fail http://localhost:8000/api/v1/healthcheck || exit 1

USER app

ENTRYPOINT ["gunicorn", "--bind", "0.0.0.0:8000", "-w 4", "app:app"]