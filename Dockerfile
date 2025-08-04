FROM python:3.14.0rc1-alpine3.22

WORKDIR /app

# Crear grupo y usuario 'app'
RUN addgroup -g 1000 app && adduser -D -u 1000 -G app app

# Copiar archivos y cambiar propietario
COPY --chown=app . .

RUN mkdir -p /app/logs && \
    chown -R app:app /app/logs && \
    chmod -R 775 /app/logs

# Instalar dependencias del sistema
RUN apk update && \
    apk add --no-cache tzdata curl && \
    rm -rf /var/cache/apk/*

RUN pip install --no-cache-dir --upgrade pip && pip install -r requirements.txt

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 CMD curl --fail http://localhost:8000/api/v1/healthcheck || exit 1

USER app

ENTRYPOINT ["gunicorn", "--bind", "0.0.0.0:8000", "-w 1", "app:app"]