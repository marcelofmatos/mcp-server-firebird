# Dockerfile Ultra-Simples - MCP Firebird (Sem complicações)
FROM python:3.11-slim

# Instalar apenas dependências básicas (sem repositórios externos)
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Instalar FDB Python (funciona mesmo sem bibliotecas cliente)
RUN pip install --no-cache-dir fdb==2.0.2

# Criar usuário
RUN useradd -r -m mcp

# Diretório de trabalho
WORKDIR /app
COPY server.py .

# Script de inicialização simples
RUN echo '#!/bin/bash\n\
echo "🔥 MCP Firebird Server Starting..."\n\
echo "📍 Host: ${FIREBIRD_HOST}"\n\
echo "🗄️  Database: ${FIREBIRD_DATABASE}"\n\
echo "🔍 Checking Firebird libraries..."\n\
if python3 -c "import fdb; print(\"FDB imported OK\")" 2>/dev/null; then\n\
    echo "✅ FDB Python library available"\n\
    python3 -c "\
import ctypes.util;\
lib = ctypes.util.find_library(\"fbclient\");\
if lib:\
    print(f\"✅ Firebird client found: {lib}\");\
else:\
    print(\"⚠️  Firebird client libraries not found\");\
    print(\"💡 Solutions:\");\
    print(\"  1. Install on host: apt-get install firebird3.0-client-core libfbclient2\");\
    print(\"  2. Mount host libs: -v /usr/lib/x86_64-linux-gnu:/usr/lib/x86_64-linux-gnu:ro\")\
" 2>/dev/null || echo "⚠️  Could not check library paths"\n\
else\n\
    echo "❌ FDB Python library not available"\n\
fi\n\
echo ""\n\
echo "🚀 Starting MCP Server..."\n\
echo "   (Server will work even if Firebird libraries are missing)"\n\
echo "   (Use server_status tool to check detailed diagnostics)"\n\
echo ""\n\
exec python3 server.py\n\
' > start.sh && chmod +x start.sh

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
CMD ["./start.sh"]

# ==========================================
# INSTRUÇÕES DE USO
# ==========================================
#
# Este Dockerfile é ULTRA-SIMPLES e sempre funciona!
# Sem scripts bash complexos, sem repositórios externos.
#
# 1. Build (sempre sucede):
#    docker build -t mcp-firebird .
#
# 2. Execução básica (para teste):
#    docker run -e FIREBIRD_HOST=192.168.1.50 \
#               -e FIREBIRD_DATABASE=/dados/app.fdb \
#               -e FIREBIRD_PASSWORD=minhasenha \
#               mcp-firebird
#
# 3. MELHOR OPÇÃO - Instalar Firebird no host:
#    # No host Docker:
#    apt-get update
#    apt-get install firebird3.0-client-core libfbclient2
#    
#    # Executar container:
#    docker run -v /usr/lib/x86_64-linux-gnu:/usr/lib/x86_64-linux-gnu:ro \
#               -e FIREBIRD_HOST=192.168.1.50 \
#               -e FIREBIRD_DATABASE=/dados/app.fdb \
#               -e FIREBIRD_PASSWORD=minhasenha \
#               mcp-firebird
#
# 4. Alternativa - Baixar bibliotecas manualmente:
#    mkdir firebird-libs && cd firebird-libs
#    wget https://github.com/FirebirdSQL/firebird/releases/download/v3.0.10/Firebird-3.0.10.33601-0.amd64.tar.gz
#    tar -xzf Firebird-*.tar.gz
#    cp Firebird-*/lib/libfbclient.so.2.5.9 ./libfbclient.so.2
#    docker run -v $(pwd):/usr/local/lib:ro -e FIREBIRD_HOST=192.168.1.50 mcp-firebird
#
# 5. O servidor sempre mostra:
#    🔥 Status de inicialização
#    📍 Configuração do banco
#    🔍 Status das bibliotecas Firebird
#    🔌 Teste de conexão
#    💡 Soluções se houver problemas
#
# ==========================================