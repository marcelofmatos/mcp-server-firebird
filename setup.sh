#!/bin/bash
# Script para configurar estrutura do projeto MCP Firebird

set -e

echo "🚀 Configurando projeto MCP Firebird Server..."
echo "============================================="

# Verificar se estamos na pasta correta
if [ ! -f "Dockerfile" ]; then
    echo "❌ Dockerfile não encontrado!"
    echo "📍 Execute este script na pasta onde você salvou os arquivos do projeto"
    exit 1
fi

# Criar pastas necessárias
echo "📂 Criando estrutura de pastas..."
mkdir -p logs

# Verificar arquivos obrigatórios
echo "🔍 Verificando arquivos obrigatórios..."

REQUIRED_FILES=("Dockerfile" "requirements.txt" "server.py")
MISSING_FILES=()

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        MISSING_FILES+=("$file")
    fi
done

if [ ${#MISSING_FILES[@]} -gt 0 ]; then
    echo "❌ Arquivos obrigatórios não encontrados:"
    for file in "${MISSING_FILES[@]}"; do
        echo "   - $file"
    done
    echo ""
    echo "📋 Você precisa criar/copiar estes arquivos dos artefatos:"
    echo "   - server.py: Copie o conteúdo do artefato 'server.py - Servidor MCP para Firebird Externo'"
    echo "   - requirements.txt: Copie o conteúdo do artefato 'requirements.txt'"
    echo "   - Dockerfile: Copie o conteúdo do artefato 'Dockerfile'"
    exit 1
fi

# Configurar arquivo .env
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "📝 Criando arquivo .env a partir do exemplo..."
        cp .env.example .env
        echo "✅ Arquivo .env criado!"
        echo "⚠️  IMPORTANTE: Edite o arquivo .env com os dados do seu banco Firebird"
    else
        echo "📝 Criando arquivo .env básico..."
        cat > .env << EOF
# Configurações do Banco Firebird Externo
FIREBIRD_HOST=localhost
FIREBIRD_PORT=3050
FIREBIRD_DATABASE=/caminho/para/seu/banco.fdb
FIREBIRD_USER=SYSDBA
FIREBIRD_PASSWORD=masterkey
FIREBIRD_CHARSET=UTF8

# Configurações do Servidor MCP
MCP_SERVER_PORT=3000
MCP_LOG_LEVEL=info

# Configurações Gerais
TZ=America/Sao_Paulo
EOF
        echo "✅ Arquivo .env criado com configurações básicas!"
        echo "⚠️  IMPORTANTE: Edite o arquivo .env com os dados do seu banco Firebird"
    fi
else
    echo "✅ Arquivo .env já existe"
fi

# Verificar se Docker está disponível
if command -v docker >/dev/null 2>&1; then
    echo "🐳 Docker encontrado"
    
    # Testar build
    echo "🔨 Testando build da imagem..."
    if docker build -t mcp-firebird-server:test . >/dev/null 2>&1; then
        echo "✅ Build da imagem funcionou!"
        docker rmi mcp-firebird-server:test >/dev/null 2>&1 || true
    else
        echo "❌ Erro no build da imagem"
        echo "🔍 Execute manualmente para ver os erros: docker build -t mcp-firebird-server ."
        exit 1
    fi
else
    echo "⚠️  Docker não encontrado, pule para a instalação quando estiver pronto"
fi

# Verificar Docker Compose
if command -v docker-compose >/dev/null 2>&1; then
    echo "🐙 Docker Compose encontrado"
else
    echo "⚠️  Docker Compose não encontrado (opcional)"
fi

# Verificar Python para testes
if command -v python3 >/dev/null 2>&1; then
    echo "🐍 Python3 encontrado (para scripts de teste)"
else
    echo "⚠️  Python3 não encontrado (opcional, apenas para scripts de teste)"
fi

echo ""
echo "🎉 Configuração concluída com sucesso!"
echo "============================================="
echo ""
echo "📋 Próximos passos:"
echo "1. ✏️  Edite o arquivo .env com os dados do seu banco Firebird:"
echo "   nano .env"
echo ""
echo "2. 🚀 Construa e execute o servidor:"
echo "   docker build -t mcp-firebird-server ."
echo "   docker-compose up -d"
echo ""
echo "3. 🧪 Teste o servidor:"
echo "   curl http://localhost:3000/health"
echo ""
echo "📚 Para mais comandos, consulte o README.md ou execute:"
echo "   make help  (se tiver make instalado)"
echo ""
echo "⚠️  LEMBRE-SE: Configure o arquivo .env antes de executar!"

# Mostrar conteúdo atual do .env
echo ""
echo "📄 Configuração atual do .env:"
echo "=============================="
cat .env