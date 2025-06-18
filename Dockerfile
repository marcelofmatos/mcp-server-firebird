# Dockerfile Ubuntu - Melhor suporte nativo para Firebird
FROM ubuntu:22.04

# Metadados da imagem
LABEL maintainer="marcelofmatos@gmail.com"
LABEL description="Servidor MCP para Firebird com Ubuntu (suporte nativo)"
LABEL version="1.0"

# Evitar prompts interativos
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=America/Sao_Paulo

# Configurar timezone
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Instalar Python 3.11 e dependências Firebird
RUN apt-get update && apt-get install -y \
    software-properties-common \
    curl \
    wget \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update \
    && apt-get install -y \
        python3.11 \
        python3.11-pip \
        python3.11-dev \
        firebird3.0-client \
        libfbclient2 \
        firebird-dev \
    && rm -rf /var/lib/apt/lists/*

# Criar links simbólicos para python3
RUN ln -sf /usr/bin/python3.11 /usr/bin/python3 \
    && ln -sf /usr/bin/python3.11 /usr/bin/python

# Instalar pip para Python 3.11
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11

# Configurar variáveis de ambiente Firebird
ENV FIREBIRD=/usr
ENV LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH

# Criar usuário não-root
RUN useradd -r -m -s /bin/bash -u 1001 mcp

# Diretórios de trabalho
RUN mkdir -p /app/mcp-server /var/log/mcp

# Copiar e instalar dependências Python
COPY requirements.txt /app/mcp-server/
RUN python3 -m pip install --no-cache-dir --upgrade pip \
    && python3 -m pip install --no-cache-dir -r /app/mcp-server/requirements.txt

# Copiar código do servidor
COPY server.py /app/mcp-server/

# Script para testar bibliotecas Firebird
RUN echo '#!/bin/bash\n\
echo "Testando bibliotecas Firebird..."\n\
echo "LD_LIBRARY_PATH: $LD_LIBRARY_PATH"\n\
echo "Procurando libfbclient..."\n\
find /usr -name "*fbclient*" 2>/dev/null\n\
echo "Testando Python FDB..."\n\
python3 -c "import fdb; print(f\"FDB version: {fdb.version}\")" 2>/dev/null && echo "✅ FDB OK" || echo "❌ FDB Error"\n\
' > /app/mcp-server/test-firebird.sh && chmod +x /app/mcp-server/test-firebird.sh

# Configurar permissões
RUN chown -R mcp:mcp /app/mcp-server /var/log/mcp

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

# Expor porta
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

# Comando de execução
CMD ["python3", "server.py"]