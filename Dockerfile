# Dockerfile Mínimo - Garantido para funcionar
FROM python:3.11-slim

# Instalar apenas o essencial
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Criar usuário
RUN useradd -r -m mcp

# Criar diretório
RUN mkdir -p /app/mcp-server
WORKDIR /app/mcp-server

# Instalar FDB (sem bibliotecas por enquanto - para testar protocolo MCP)
RUN pip3 install --no-cache-dir fdb==2.0.2

# Copiar server.py
COPY server.py .

# Configurar permissões
RUN chown -R mcp:mcp /app/mcp-server
USER mcp

# Variáveis de ambiente
ENV FIREBIRD_HOST=localhost
ENV FIREBIRD_PORT=3050
ENV FIREBIRD_DATABASE=/path/to/database.fdb
ENV FIREBIRD_USER=SYSDBA
ENV FIREBIRD_PASSWORD=masterkey
ENV FIREBIRD_CHARSET=UTF8

# Comando de execução
CMD ["python3", "server.py"]