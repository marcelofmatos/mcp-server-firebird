# Dockerfile para Servidor MCP Firebird (conecta a banco externo)
FROM python:3.11-slim

# Metadados da imagem
LABEL maintainer="seu-email@exemplo.com"
LABEL description="Servidor MCP para conexão com Firebird externo"
LABEL version="1.0"

# Evitar prompts interativos durante instalação
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=America/Sao_Paulo

# Instalar dependências do sistema necessárias para firebird-driver
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    gcc \
    libc6-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Criar usuário não-root para o servidor MCP
RUN useradd -r -m -s /bin/bash -u 1001 mcp

# Diretórios de trabalho
RUN mkdir -p /app/mcp-server /var/log/mcp

# Instalar dependências Python primeiro
COPY requirements.txt /app/mcp-server/
RUN pip3 install --no-cache-dir --upgrade pip \
    && pip3 install --no-cache-dir -r /app/mcp-server/requirements.txt

# Copiar código do servidor MCP
COPY server.py /app/mcp-server/

# Configurar permissões
RUN chown -R mcp:mcp /app/mcp-server /var/log/mcp
RUN chmod +x /app/mcp-server/*.py

# Configurar usuário de trabalho
USER mcp
WORKDIR /app/mcp-server

# Variáveis de ambiente padrão
ENV MCP_SERVER_PORT=3000
ENV MCP_LOG_LEVEL=info
ENV FIREBIRD_HOST=firebird-server
ENV FIREBIRD_PORT=3050
ENV FIREBIRD_DATABASE=/path/to/database.fdb
ENV FIREBIRD_USER=SYSDBA
ENV FIREBIRD_PASSWORD=masterkey
ENV FIREBIRD_CHARSET=UTF8

# Expor porta do servidor MCP
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

# Comando de execução
CMD ["python3", "server.py"]