# Dockerfile Definitivo - MCP Firebird Server
# Versão completa e funcional para conectar a bancos Firebird externos
FROM ubuntu:22.04

# Definir variáveis de build
ARG APP_VERSION
ARG GIT_COMMIT
ENV APP_VERSION=${APP_VERSION}
ENV GIT_COMMIT=${GIT_COMMIT}

# Configuração básica
ENV DEBIAN_FRONTEND=noninteractive
LABEL maintainer="MCP Firebird Server"
LABEL description="MCP Server para Firebird com bibliotecas cliente completas"
LABEL version=${APP_VERSION}

# ==========================================
# FASE 1: INSTALAÇÃO DO SISTEMA BASE
# ==========================================

# Instalar Python e ferramentas essenciais
RUN apt-get update && apt-get install -y \
    # Python e desenvolvimento
    python3 \
    python3-pip \
    python3-dev \
    python3-venv \
    build-essential \
    gcc \
    g++ \
    make \
    # Ferramentas de sistema
    wget \
    curl \
    unzip \
    tar \
    dpkg-dev \
    ca-certificates \
    gnupg \
    lsb-release \
    # Bibliotecas de sistema necessárias
    libc6-dev \
    libstdc++6 \
    libgcc-s1 \
    && rm -rf /var/lib/apt/lists/*

# ==========================================
# FASE 2: DEPENDÊNCIAS ESPECÍFICAS DO FIREBIRD
# ==========================================

# Instalar todas as dependências que o Firebird precisa
RUN apt-get update && apt-get install -y \
    # Dependências matemáticas (CRÍTICAS para resolver libtommath.so.0)
    libtommath1 \
    libtommath-dev \
    libtomcrypt1 \
    libtomcrypt-dev \
    # Bibliotecas de internacionalização
    libicu70 \
    libicu-dev \
    # Bibliotecas de terminal e I/O
    libncurses5 \
    libncurses-dev \
    libedit2 \
    libedit-dev \
    # Bibliotecas de threading e atomic
    libatomic1 \
    # Outras dependências essenciais
    libssl3 \
    libssl-dev \
    zlib1g \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Criar links simbólicos para garantir que as bibliotecas sejam encontradas
RUN echo "🔗 Configurando bibliotecas matemáticas..." && \
    # Encontrar e configurar libtommath
    TOMMATH_LIB=$(find /usr/lib -name "libtommath.so*" | grep -v ".0" | head -1) && \
    if [ -n "$TOMMATH_LIB" ]; then \
        ln -sf "$TOMMATH_LIB" /usr/lib/libtommath.so.0 && \
        ln -sf "$TOMMATH_LIB" /usr/lib/libtommath.so && \
        echo "✅ libtommath configurado: $TOMMATH_LIB"; \
    fi && \
    # Encontrar e configurar libtomcrypt
    TOMCRYPT_LIB=$(find /usr/lib -name "libtomcrypt.so*" | grep -v ".0" | head -1) && \
    if [ -n "$TOMCRYPT_LIB" ]; then \
        ln -sf "$TOMCRYPT_LIB" /usr/lib/libtomcrypt.so.0 && \
        ln -sf "$TOMCRYPT_LIB" /usr/lib/libtomcrypt.so && \
        echo "✅ libtomcrypt configurado: $TOMCRYPT_LIB"; \
    fi && \
    # Atualizar cache do sistema
    ldconfig && \
    echo "📋 Bibliotecas matemáticas disponíveis:" && \
    ls -la /usr/lib/libtom* 2>/dev/null

# ==========================================
# FASE 3: INSTALAÇÃO DO FIREBIRD
# ==========================================

# Baixar e instalar Firebird extraindo buildroot diretamente
RUN echo "🔥 === INSTALAÇÃO FIREBIRD OFICIAL ===" && \
    cd /tmp && \
    echo "📦 Baixando Firebird 3.0.10 do GitHub..." && \
    wget -q https://github.com/FirebirdSQL/firebird/releases/download/v3.0.10/Firebird-3.0.10.33601-0.amd64.tar.gz && \
    echo "📂 Extraindo arquivo..." && \
    tar -xzf Firebird-3.0.10.33601-0.amd64.tar.gz && \
    cd Firebird-* && \
    echo "📋 Conteúdo do pacote Firebird:" && \
    ls -la && \
    echo "📦 Extraindo buildroot.tar.gz para /..." && \
    tar -xzf buildroot.tar.gz -C / && \
    echo "✅ Buildroot extraído para raiz do sistema" && \
    # Verificar se a extração funcionou
    if [ -d "/opt/firebird" ]; then \
        echo "✅ Diretório /opt/firebird criado com sucesso"; \
        ls -la /opt/firebird/; \
    else \
        echo "⚠️  /opt/firebird não encontrado, procurando bibliotecas..."; \
        find / -name "*fbclient*" -type f 2>/dev/null | head -5; \
    fi && \
    # Limpeza
    cd / && rm -rf /tmp/Firebird-*

# ==========================================
# FASE 4: CONFIGURAÇÃO DO AMBIENTE FIREBIRD
# ==========================================

# Configurar variáveis de ambiente do Firebird
ENV FIREBIRD=/opt/firebird
ENV FIREBIRD_HOME=/opt/firebird
ENV PATH=$FIREBIRD/bin:$PATH
ENV LD_LIBRARY_PATH=$FIREBIRD/lib:/opt/firebird/lib:/usr/lib:/usr/lib/x86_64-linux-gnu:/lib/x86_64-linux-gnu

# Criar configuração adicional de bibliotecas
RUN echo "🔧 Configurando ambiente Firebird..." && \
    # Criar arquivo de configuração ldconfig
    echo "/opt/firebird/lib" > /etc/ld.so.conf.d/firebird.conf && \
    echo "/usr/lib" >> /etc/ld.so.conf.d/firebird.conf && \
    echo "/usr/lib/x86_64-linux-gnu" >> /etc/ld.so.conf.d/firebird.conf && \
    # Atualizar cache de bibliotecas
    ldconfig && \
    # Verificar se bibliotecas fbclient estão acessíveis
    echo "📋 Verificando bibliotecas Firebird:" && \
    find /opt -name "*fbclient*" 2>/dev/null || echo "Nenhuma em /opt" && \
    find /usr/lib -name "*fbclient*" 2>/dev/null || echo "Nenhuma em /usr/lib" && \
    ldconfig -p | grep fbclient || echo "fbclient não encontrado no cache"

# Verificação pós-instalação e correção de dependências
RUN echo "🔍 === VERIFICAÇÃO FINAL FIREBIRD ===" && \
    # Verificar se libtommath.so.0 está disponível
    if ! ldconfig -p | grep -q "libtommath.so.0"; then \
        echo "🔗 Corrigindo libtommath.so.0..."; \
        TOMMATH=$(find /usr/lib -name "libtommath.so*" | grep -v ".0" | head -1); \
        if [ -n "$TOMMATH" ]; then \
            ln -sf "$TOMMATH" /usr/lib/libtommath.so.0; \
            echo "✅ Link criado: $TOMMATH -> libtommath.so.0"; \
        fi; \
    fi && \
    # Verificar se libtomcrypt.so.0 está disponível
    if ! ldconfig -p | grep -q "libtomcrypt.so.0"; then \
        echo "🔗 Corrigindo libtomcrypt.so.0..."; \
        TOMCRYPT=$(find /usr/lib -name "libtomcrypt.so*" | grep -v ".0" | head -1); \
        if [ -n "$TOMCRYPT" ]; then \
            ln -sf "$TOMCRYPT" /usr/lib/libtomcrypt.so.0; \
            echo "✅ Link criado: $TOMCRYPT -> libtomcrypt.so.0"; \
        fi; \
    fi && \
    # Atualizar ldconfig uma última vez
    ldconfig && \
    echo "📋 Status final das dependências:" && \
    ldconfig -p | grep -E "(fbclient|tommath|tomcrypt)"

# ==========================================
# FASE 5: INSTALAÇÃO DO PYTHON FDB
# ==========================================

# Atualizar pip e instalar FDB
COPY requirements.txt .
RUN echo "🐍 === INSTALAÇÃO FDB PYTHON ===" && \
    pip3 install --upgrade pip && \
    pip3 install --no-cache-dir -r requirements.txt

# ==========================================
# FASE 6: CONFIGURAÇÃO DA APLICAÇÃO
# ==========================================

# Criar usuário não-root para segurança
RUN groupadd -r mcp && useradd -r -g mcp -d /app -s /bin/bash mcp

# Configurar diretório da aplicação
WORKDIR /app

# Copiar código fonte completo
COPY server.py .
COPY src/ src/
COPY i18n/ i18n/
COPY pyproject.toml* .
COPY README.md* .

# Configurar permissões
RUN chown -R mcp:mcp /app
USER mcp

# ==========================================
# FASE 7: CONFIGURAÇÃO FINAL
# ==========================================

# Variáveis de ambiente para conexão com banco externo
ENV FIREBIRD_HOST=192.168.1.100
ENV FIREBIRD_PORT=3050
ENV FIREBIRD_DATABASE=/dados/sistema.fdb
ENV FIREBIRD_USER=SYSDBA
ENV FIREBIRD_PASSWORD=masterkey
ENV FIREBIRD_CHARSET=UTF8

# Configurações do MCP Server
ENV MCP_SERVER_NAME="firebird-mcp-server"
ENV MCP_SERVER_VERSION=${APP_VERSION}
ENV LOG_LEVEL=INFO
ENV MCP_SERVER_PORT=3000
ENV MCP_LOG_LEVEL=info
ENV MCP_DEFAULT_PROMPT_ENABLED=true
ENV MCP_DEFAULT_PROMPT=firebird_expert
ENV MCP_DEFAULT_OPERATION=query
ENV MCP_DEFAULT_COMPLEXITY=intermediate
ENV MCP_AUTO_APPLY_PROMPT=true

# Health check para verificar se o servidor está funcionando
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python3 -c "import fdb; print('OK')" || exit 1

# Comando de execução
CMD ["python3", "server.py"]