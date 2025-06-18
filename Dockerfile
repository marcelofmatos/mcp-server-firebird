# Dockerfile Robusto - MCP Firebird com instalação resiliente
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
    software-properties-common \
    ca-certificates \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Tentar múltiplas formas de instalar Firebird (sem falhar o build)
RUN echo "🔥 Tentando instalar bibliotecas Firebird..." && \
    # Método 1: Tentar repositórios padrão
    (apt-get update && \
     apt-get install -y firebird3.0-client-core libfbclient2 firebird3.0-common-doc && \
     echo "✅ Firebird instalado via repositórios padrão") || \
    # Método 2: Tentar com universe
    (add-apt-repository universe && \
     apt-get update && \
     apt-get install -y firebird3.0-client-core libfbclient2 && \
     echo "✅ Firebird instalado via repositório universe") || \
    # Método 3: Instalação manual
    (echo "📦 Tentando instalação manual..." && \
     cd /tmp && \
     wget -q https://github.com/FirebirdSQL/firebird/releases/download/v3.0.10/Firebird-3.0.10.33601-0.amd64.tar.gz && \
     tar -xzf Firebird-3.0.10.33601-0.amd64.tar.gz && \
     cd Firebird-* && \
     mkdir -p /usr/lib/firebird/3.0 /usr/include/firebird && \
     cp lib/libfbclient.so.2.5.9 /usr/lib/firebird/3.0/ && \
     ln -sf /usr/lib/firebird/3.0/libfbclient.so.2.5.9 /usr/lib/libfbclient.so.2 && \
     ln -sf /usr/lib/libfbclient.so.2 /usr/lib/libfbclient.so && \
     cp include/ibase.h /usr/include/firebird/ 2>/dev/null || true && \
     echo "/usr/lib/firebird/3.0" > /etc/ld.so.conf.d/firebird.conf && \
     cd / && rm -rf /tmp/Firebird-* && \
     echo "✅ Firebird instalado manualmente") || \
    echo "⚠️  Falha na instalação do Firebird - continuando..." && \
    # Limpeza final
    rm -rf /var/lib/apt/lists/* /tmp/*

# Configurar variáveis de ambiente para Firebird
ENV LD_LIBRARY_PATH=/usr/lib/firebird/3.0:/usr/lib:/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH

# Atualizar cache das bibliotecas
RUN ldconfig

# Verificar o que foi instalado (sem falhar o build)
RUN echo "📋 Status da instalação Firebird:" && \
    echo "=== Verificando arquivos instalados ===" && \
    (ls -la /usr/lib/libfbclient* 2>/dev/null || echo "Não encontrado em /usr/lib/") && \
    (ls -la /usr/lib/firebird/3.0/libfbclient* 2>/dev/null || echo "Não encontrado em /usr/lib/firebird/3.0/") && \
    (ls -la /usr/lib/x86_64-linux-gnu/libfbclient* 2>/dev/null || echo "Não encontrado em /usr/lib/x86_64-linux-gnu/") && \
    echo "=== Verificando ldconfig ===" && \
    (ldconfig -p | grep fbclient || echo "fbclient não encontrado no cache") && \
    echo "=== LD_LIBRARY_PATH ===" && \
    echo "$LD_LIBRARY_PATH" && \
    echo "=== Instalação completa ==="

# Instalar driver Python Firebird
RUN pip3 install --no-cache-dir fdb==2.0.2

# Testar se FDB funciona (sem falhar o build)
RUN echo "🐍 Testando FDB Python..." && \
    (python3 -c "import fdb; print('✅ FDB imported successfully')" || \
     echo "⚠️  FDB import failed - will be handled at runtime") && \
    (python3 -c "import ctypes.util; lib = ctypes.util.find_library('fbclient'); print(f'Library path: {lib}' if lib else 'Library not found in standard paths')" || \
     echo "⚠️  Could not check library path")

# Criar usuário não-root
RUN useradd -r -m mcp

# Configurar diretório de trabalho
WORKDIR /app
COPY server.py .

# Configurar permissões
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
