#!/bin/bash
# Teste da estrutura do container

echo "🔍 Testando estrutura do container..."

# Build da imagem
docker build -t mcp-firebird-test . || exit 1

# Verificar estrutura de arquivos
echo "📁 Verificando estrutura de arquivos no container:"
docker run --rm mcp-firebird-test find /app -type f -name "*.py" | head -10

# Testar imports
echo "🐍 Testando imports Python:"
docker run --rm mcp-firebird-test python3 -c "
import sys
sys.path.insert(0, '/app')
try:
    from src import I18n, FirebirdMCPServer
    print('✅ Imports funcionando')
except ImportError as e:
    print(f'❌ Erro de import: {e}')
"
