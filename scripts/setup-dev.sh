#!/bin/bash
# Script para configurar ambiente de desenvolvimento do MCP Server Firebird

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_python() {
    log_info "Verificando Python..."
    
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 não encontrado. Instale Python 3.8+ primeiro."
        exit 1
    fi
    
    python_version=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
    log_success "Python $python_version encontrado"
    
    if [[ $(echo "$python_version < 3.8" | bc -l) -eq 1 ]]; then
        log_error "Python 3.8+ é necessário. Versão atual: $python_version"
        exit 1
    fi
}

setup_venv() {
    log_info "Configurando ambiente virtual..."
    
    if [ ! -d ".venv" ]; then
        python3 -m venv .venv
        log_success "Ambiente virtual criado"
    else
        log_info "Ambiente virtual já existe"
    fi
    
    # Ativar ambiente virtual
    source .venv/bin/activate
    
    # Atualizar pip
    python -m pip install --upgrade pip
    
    log_success "Ambiente virtual configurado"
}

install_dependencies() {
    log_info "Instalando dependências..."
    
    # Dependências principais
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        log_success "Dependências principais instaladas"
    fi
    
    # Dependências de desenvolvimento
    if [ -f "requirements-dev.txt" ]; then
        pip install -r requirements-dev.txt
        log_success "Dependências de desenvolvimento instaladas"
    fi
    
    # Instalar projeto em modo desenvolvimento
    pip install -e .
    log_success "Projeto instalado em modo desenvolvimento"
}

setup_pre_commit() {
    log_info "Configurando pre-commit hooks..."
    
    if command -v pre-commit &> /dev/null; then
        pre-commit install
        log_success "Pre-commit hooks instalados"
    else
        log_warning "pre-commit não encontrado, pule esta etapa"
    fi
}

create_directories() {
    log_info "Criando estrutura de diretórios..."
    
    mkdir -p {reports,logs,docs,scripts}
    mkdir -p tests/{unit,integration,fixtures}
    
    log_success "Estrutura de diretórios criada"
}

setup_configs() {
    log_info "Configurando arquivos de configuração..."
    
    # Criar .env se não existir
    if [ ! -f ".env" ] && [ -f ".env.example" ]; then
        cp .env.example .env
        log_success ".env criado a partir do exemplo"
        log_warning "Lembre-se de configurar as variáveis em .env"
    fi
    
    # Criar pytest.ini se não existir
    if [ ! -f "pytest.ini" ]; then
        cat > pytest.ini << EOF
[tool:pytest]
minversion = 7.0
addopts = 
    -ra
    --strict-markers
    --strict-config
    --cov=server
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-fail-under=80
testpaths = tests
markers =
    unit: marks tests as unit tests
    integration: marks tests as integration tests
    slow: marks tests as slow
    firebird: marks tests that require Firebird database
    docker: marks tests that require Docker
filterwarnings =
    error
    ignore::UserWarning
    ignore::DeprecationWarning
EOF
        log_success "pytest.ini criado"
    fi
}

check_docker() {
    log_info "Verificando Docker..."
    
    if command -v docker &> /dev/null; then
        log_success "Docker encontrado"
        
        if docker ps &> /dev/null; then
            log_success "Docker está rodando"
        else
            log_warning "Docker não está rodando ou sem permissões"
        fi
    else
        log_warning "Docker não encontrado - testes de integração não funcionarão"
    fi
}

run_initial_tests() {
    log_info "Executando testes iniciais..."
    
    # Teste simples de importação
    if python -c "import server; print('Import OK')" 2>/dev/null; then
        log_success "Módulo principal importado com sucesso"
    else
        log_error "Falha ao importar módulo principal"
        return 1
    fi
    
    # Executar testes unitários básicos
    if command -v pytest &> /dev/null; then
        log_info "Executando testes unitários básicos..."
        if pytest tests/unit -x -q --no-cov; then
            log_success "Testes unitários básicos passaram"
        else
            log_warning "Alguns testes unitários falharam"
        fi
    fi
}

show_next_steps() {
    log_success "Configuração do ambiente de desenvolvimento concluída!"
    echo ""
    echo -e "${BLUE}Próximos passos:${NC}"
    echo ""
    echo "1. Ativar o ambiente virtual:"
    echo "   source .venv/bin/activate"
    echo ""
    echo "2. Configurar variáveis de ambiente:"
    echo "   nano .env"
    echo ""
    echo "3. Executar testes:"
    echo "   ./scripts/run-tests.sh"
    echo ""
    echo "4. Iniciar desenvolvimento:"
    echo "   python server.py"
    echo ""
    echo -e "${BLUE}Comandos úteis:${NC}"
    echo "   ./scripts/run-tests.sh -t unit     # Testes unitários"
    echo "   ./scripts/run-tests.sh -f          # Testes rápidos"
    echo "   ./scripts/run-tests.sh --lint      # Verificações de código"
    echo "   make dev                           # Desenvolvimento completo"
    echo ""
    echo -e "${BLUE}Documentação:${NC}"
    echo "   - README.md: Documentação principal"
    echo "   - pyproject.toml: Configurações do projeto"
    echo "   - tests/: Exemplos de testes"
}

main() {
    echo -e "${BLUE}=== MCP Server Firebird - Setup Ambiente de Desenvolvimento ===${NC}"
    echo ""
    
    check_python
    setup_venv
    install_dependencies
    create_directories
    setup_configs
    setup_pre_commit
    check_docker
    run_initial_tests
    
    echo ""
    show_next_steps
}

# Executar se chamado diretamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
