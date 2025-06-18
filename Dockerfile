# Dockerfile Ultra-Simples - MCP Firebird (Funciona sempre)
FROM python:3.11-slim

# Instalar apenas o essencial
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Tentar instalar FDB (pode falhar, mas o server continua funcionando)
RUN pip install --no-cache-dir fdb==2.0.2 || \
    echo "⚠️  FDB installation failed - server will run in fallback mode"

# Criar usuário
RUN useradd -r -m mcp

# Diretório de trabalho
WORKDIR /app
COPY server.py .

# Permissões
RUN chown -R mcp:mcp /app
USER mcp

# Variáveis de ambiente para banco externo
ENV FIREBIRD_HOST=192.168.1.100
ENV FIREBIRD_PORT=3050
ENV FIREBIRD_DATABASE=/dados/sistema.fdb
ENV FIREBIRD_USER=SYSDBA
ENV FIREBIRD_PASSWORD=masterkey
ENV FIREBIRD_CHARSET=UTF8

# Comando de execução
CMD ["python3", "server.py"]
