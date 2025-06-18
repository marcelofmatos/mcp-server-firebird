# Dockerfile Mínimo - Foco apenas em funcionar
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=America/Sao_Paulo

# Configurar timezone
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Instalar apenas o essencial que sabemos que existe
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    curl \
    wget \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Tentar instalar Firebird (pode ou não funcionar)
RUN apt-get update && \
    (apt-get install -y libfbclient2 || echo "libfbclient2 not available") && \
    (apt-get install -y firebird3.0-common || echo "firebird3.0-common not available") && \
    (apt-get install -y firebird3.0-utils || echo "firebird3.0-utils not available") && \
    rm -rf /var/lib/apt/lists/*

# Se os pacotes não funcionaram, instalar manualmente
RUN if [ ! -f /usr/lib/x86_64-linux-gnu/libfbclient.so ]; then \
    echo "Instalando bibliotecas Firebird manualmente..." && \
    mkdir -p /tmp/fb && cd /tmp/fb && \
    wget -q https://github.com/FirebirdSQL/firebird/releases/download/v5.0.0/Firebird-5.0.0.1306-0.amd64.tar.xz && \
    tar -xf Firebird-5.0.0.1306-0.amd64.tar.xz && \
    cd Firebird-5.0.0.1306-0.amd64 && \
    cp lib/libfbclient.so* /usr/lib/x86_64-linux-gnu/ 2>/dev/null || \
    cp lib/libfbclient.so* /usr/lib/ 2>/dev/null || \
    echo "Erro ao copiar bibliotecas" && \
    ldconfig && \
    cd / && rm -rf /tmp/fb; \
    fi

# Configurar ambiente
ENV LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:/usr/lib:$LD_LIBRARY_PATH
ENV FIREBIRD=/usr

# Criar usuário
RUN useradd -r -m mcp
RUN mkdir -p /app/mcp-server
WORKDIR /app/mcp-server

# Instalar dependências Python
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copiar código
COPY server.py .
RUN chown -R mcp:mcp /app/mcp-server

# Configurar usuário
USER mcp

# Variáveis de ambiente
ENV MCP_SERVER_PORT=3000
ENV MCP_LOG_LEVEL=info
ENV FIREBIRD_HOST=firebird-server
ENV FIREBIRD_PORT=3050
ENV FIREBIRD_DATABASE=/path/to/database.fdb
ENV FIREBIRD_USER=SYSDBA
ENV FIREBIRD_PASSWORD=masterkey
ENV FIREBIRD_CHARSET=UTF8

EXPOSE 3000

# Comando simples
CMD ["python3", "server.py"]