FROM python:3.11-alpine

# Instalar dependências do sistema
RUN apk add --no-cache \
    gcc \
    musl-dev \
    curl

# Criar diretório de trabalho
WORKDIR /app

# Copiar requirements primeiro (para cache do Docker)
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Criar usuário não-root
RUN addgroup -g 1000 monitor && \
    adduser -D -s /bin/sh -u 1000 -G monitor monitor && \
    chown -R monitor:monitor /app

# Mudar para usuário não-root
USER monitor

# Healthcheck
HEALTHCHECK --interval=60s --timeout=10s --start-period=120s --retries=3 \
    CMD python -c "import requests; requests.get('http://zabbix-web:8080', timeout=5)" || exit 1

# Comando padrão
CMD ["python", "monitor.py"]