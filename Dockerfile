# Dockerfile Simples e Funcional - MCP Firebird
FROM ubuntu:22.04

# Evitar prompts interativos
ENV DEBIAN_FRONTEND=noninteractive

# Instalar Python e dependências básicas
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    build-essential \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar cliente Firebird do repositório Ubuntu
RUN apt-get update && apt-get install -y \
    firebird3.0-client-core \
    libfbclient2 \
    && rm -rf /var/lib/apt/lists/*

# Configurar bibliotecas
RUN ldconfig

# Instalar biblioteca Python para Firebird
RUN pip3 install --no-cache-dir fdb==2.0.2

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