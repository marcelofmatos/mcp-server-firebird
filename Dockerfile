# Dockerfile Corrigido - MCP Firebird com bibliotecas cliente
FROM python:3.11-slim

# Evitar prompts interativos
ENV DEBIAN_FRONTEND=noninteractive

# Instalar dependências básicas
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    libc6 \
    libstdc++6 \
    libncurses5 \
    libtinfo5 \
    && rm -rf /var/lib/apt/lists/*

# Baixar e instalar bibliotecas Firebird cliente
RUN cd /tmp && \
    # Baixar bibliotecas pré-compiladas do Firebird
    wget -q -O fbclient.tar.gz "https://github.com/FirebirdSQL/firebird/releases/download/v3.0.10/Firebird-3.0.10.33601-0.amd64.tar.gz" && \
    tar -xzf fbclient.tar.gz && \
    cd Firebird-* && \
    # Criar diretórios
    mkdir -p /opt/firebird/lib && \
    mkdir -p /usr/local/lib && \
    # Copiar bibliotecas cliente
    cp lib/libfbclient.so.2.5.9 /opt/firebird/lib/ && \
    cp lib/libfbclient.so.2.5.9 /usr/local/lib/libfbclient.so.2 && \
    # Criar links simbólicos
    ln -sf /usr/local/lib/libfbclient.so.2 /usr/local/lib/libfbclient.so && \
    ln -sf /opt/firebird/lib/libfbclient.so.2.5.9 /opt/firebird/lib/libfbclient.so.2 && \
    ln -sf /opt/firebird/lib/libfbclient.so.2 /opt/firebird/lib/libfbclient.so && \
    # Limpeza
    cd / && rm -rf /tmp/Firebird-* /tmp/fbclient.tar.gz

# Configurar variáveis de ambiente para Firebird
ENV FIREBIRD_HOME=/opt/firebird
ENV LD_LIBRARY_PATH=/opt/firebird/lib:/usr/local/lib:$LD_LIBRARY_PATH
ENV PATH=$FIREBIRD_HOME/bin:$PATH

# Atualizar cache das bibliotecas
RUN ldconfig

# Verificar se as bibliotecas foram instaladas
RUN echo "Verificando bibliotecas Firebird:" && \
    ls -la /opt/firebird/lib/ && \
    ls -la /usr/local/lib/libfbclient* && \
    ldconfig -p | grep fbclient

# Instalar FDB Python driver
RUN pip install --no-cache-dir fdb==2.0.2

# Testar importação do FDB
RUN python3 -c "import fdb; print('✅ FDB imported successfully')"

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
