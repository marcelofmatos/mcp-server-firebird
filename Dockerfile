# Dockerfile Simples - Servidor MCP Nativo
FROM python:3.11-slim

# Metadados da imagem
LABEL maintainer="seu-email@exemplo.com"
LABEL description="Servidor MCP Nativo para Firebird"
LABEL version="1.0"

# Evitar prompts interativos
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=America/Sao_Paulo

# Instalar dependências mínimas e bibliotecas Firebird
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Baixar e instalar bibliotecas Firebird manualmente
RUN mkdir -p /tmp/firebird && \
    cd /tmp/firebird && \
    wget -q https://github.com/FirebirdSQL/firebird/releases/download/v5.0.0/Firebird-5.0.0.1306-0.amd64.tar.xz && \
    tar -xf Firebird-5.0.0.1306-0.amd64.tar.xz && \
    cd Firebird-5.0.0.1306-0.amd64 && \
    # Copiar apenas bibliotecas cliente necessárias
    mkdir -p /usr/lib/firebird && \
    cp lib/libfbclient.so.2.5.9 /usr/lib/x86_64-linux-gnu/ && \
    cp lib/libib_util.so /usr/lib/x86_64-linux-gnu/ && \
    # Criar links simbólicos
    ln -sf /usr/lib/x86_64-linux-gnu/libfbclient.so.2.5.9 /usr/lib/x86_64-linux-gnu/libfbclient.so.2 && \
    ln -sf /usr/lib/x86_64-linux-gnu/libfbclient.so.2 /usr/lib/x86_64-linux-gnu/libfbclient.so && \
    # Atualizar cache de bibliotecas
    ldconfig && \
    # Limpar arquivos temporários
    cd / && rm -rf /tmp/firebird

# Configurar variáveis de ambiente para Firebird
ENV FIREBIRD=/usr
ENV LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH

# Criar usuário não-root
RUN useradd -r -m -s /bin/bash -u 1001 mcp

# Criar diretórios
RUN mkdir -p /app/mcp-server /var/log/mcp

# Instalar dependências Python (apenas FDB agora)
COPY requirements.txt /app/mcp-server/
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir -r /app/mcp-server/requirements.txt

# Copiar código do servidor (apenas server.py principal)
COPY server.py /app/mcp-server/

# Configurar permissões
RUN chown -R mcp:mcp /app/mcp-server /var/log/mcp && \
    chmod +x /app/mcp-server/*.py

# Configurar usuário
USER mcp
WORKDIR /app/mcp-server

# Variáveis de ambiente
ENV FIREBIRD_HOST=firebird-server
ENV FIREBIRD_PORT=3050
ENV FIREBIRD_DATABASE=/path/to/database.fdb
ENV FIREBIRD_USER=SYSDBA
ENV FIREBIRD_PASSWORD=masterkey
ENV FIREBIRD_CHARSET=UTF8

# Comando de execução (servidor MCP nativo)
CMD ["python3", "server.py"]