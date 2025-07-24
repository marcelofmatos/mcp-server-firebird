#!/bin/bash
# Script para executar testes do MCP Server Firebird
# Uso: ./scripts/run-tests.sh [opcoes]

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configurações padrão
PYTHON_ENV=${PYTHON_ENV:-"python3"}
TEST_TYPE=${TEST_TYPE:-"all"}
COVERAGE=${COVERAGE:-"true"}
PARALLEL=${PARALLEL:-"true"}
VERBOSE=${VERBOSE:-"false"}

# Funções auxiliares
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

show_help() {
    cat << EOF
Uso: $0 [OPÇÕES]

OPÇÕES:
    -h, --help              Mostra esta ajuda
    -t, --type TYPE         Tipo de teste: unit, integration, performance, all (padrão: all)
    -c, --coverage BOOL     Gerar relatório de cobertura (padrão: true)
    -p, --parallel BOOL     Executar testes em paralelo (padrão: true)
    -v, --verbose           Output verboso
    -f, --fast              Execução rápida (pula testes lentos)
    -m, --marker MARKER     Executar apenas testes com marcador específico
    --no-cov                Desabilitar cobertura
    --html                  Gerar relatório HTML
    --xml                   Gerar relatório XML
    --clean                 Limpar cache e artefatos antes
    --install-deps          Instalar dependências de desenvolvimento

EXEMPLOS:
    $0                      # Executar todos os testes
    $0 -t unit              # Apenas testes unitários
    $0 -t integration -v    # Testes de integração com output verboso
    $0 -f                   # Execução rápida (sem testes lentos)
    $0 -m firebird          # Apenas testes marcados com 'firebird'
    $0 --clean --install-deps  # Limpar e instalar deps

VARIÁVEIS DE AMBIENTE:
    PYTHON_ENV             Comando Python (padrão: python3)
    TEST_TYPE              Tipo de teste (unit/integration/performance/all)
    COVERAGE               Habilitar cobertura (true/false)
    PARALLEL               Executar em paralelo (true/false)
    PYTEST_ARGS           Argumentos adicionais para pytest

EOF
}

check_dependencies() {
    log_info "Verificando dependências..."
    
    # Verificar se Python está disponível
    if ! command -v $PYTHON_ENV &> /dev/null; then
        log_error "Python não encontrado: $PYTHON_ENV"
        exit 1
    fi
    
    # Verificar se pytest está instalado
    if ! $PYTHON_ENV -c "import pytest" &> /dev/null; then
        log_warning "pytest não encontrado. Use --install-deps para instalar."
        return 1
    fi
    
    # Verificar se requirements-dev.txt existe
    if [ ! -f "requirements-dev.txt" ]; then
        log_error "requirements-dev.txt não encontrado"
        exit 1
    fi
    
    log_success "Dependências verificadas"
    return 0
}

install_dependencies() {
    log_info "Instalando dependências de desenvolvimento..."
    
    $PYTHON_ENV -m pip install --upgrade pip
    $PYTHON_ENV -m pip install -r requirements-dev.txt
    
    log_success "Dependências instaladas"
}

clean_artifacts() {
    log_info "Limpando artefatos de teste..."
    
    # Remover cache
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
    
    # Remover relatórios anteriores
    rm -rf htmlcov/ coverage.xml .coverage reports/
    
    # Remover arquivos temporários
    find . -name "*.pyc" -delete 2>/dev/null || true
    find . -name "*.pyo" -delete 2>/dev/null || true
    
    log_success "Artefatos limpos"
}

build_pytest_args() {
    local args=""
    
    # Diretório de testes baseado no tipo
    case $TEST_TYPE in
        "unit")
            args="$args tests/unit"
            ;;
        "integration")
            args="$args tests/integration"
            ;;
        "performance")
            args="$args -m 'slow or performance'"
            ;;
        "all")
            args="$args tests/"
            ;;
        *)
            log_error "Tipo de teste inválido: $TEST_TYPE"
            exit 1
            ;;
    esac
    
    # Cobertura
    if [ "$COVERAGE" = "true" ]; then
        args="$args --cov=server --cov=src"
        args="$args --cov-report=term-missing"
        
        if [ "$GENERATE_HTML" = "true" ]; then
            args="$args --cov-report=html:htmlcov"
        fi
        
        if [ "$GENERATE_XML" = "true" ]; then
            args="$args --cov-report=xml"
        fi
        
        args="$args --cov-fail-under=80"
    fi
    
    # Paralelização
    if [ "$PARALLEL" = "true" ] && [ "$TEST_TYPE" != "integration" ]; then
        # Detectar número de cores
        if command -v nproc &> /dev/null; then
            cores=$(nproc)
        else
            cores=2
        fi
        args="$args -n $cores"
    fi
    
    # Verbosidade
    if [ "$VERBOSE" = "true" ]; then
        args="$args -v"
    else
        args="$args -q"
    fi
    
    # Execução rápida
    if [ "$FAST_MODE" = "true" ]; then
        args="$args -m 'not slow'"
    fi
    
    # Marcador específico
    if [ -n "$MARKER" ]; then
        args="$args -m '$MARKER'"
    fi
    
    # Relatórios
    if [ "$GENERATE_HTML" = "true" ]; then
        mkdir -p reports
        args="$args --html=reports/pytest-report.html --self-contained-html"
    fi
    
    # Argumentos adicionais do usuário
    if [ -n "$PYTEST_ARGS" ]; then
        args="$args $PYTEST_ARGS"
    fi
    
    echo "$args"
}

run_linting() {
    log_info "Executando verificações de qualidade de código..."
    
    # Ruff
    if command -v ruff &> /dev/null; then
        log_info "Executando ruff..."
        ruff check . || log_warning "Ruff encontrou problemas"
    fi
    
    # Black
    if command -v black &> /dev/null; then
        log_info "Verificando formatação com black..."
        black --check . || log_warning "Black encontrou problemas de formatação"
    fi
    
    # MyPy
    if command -v mypy &> /dev/null; then
        log_info "Executando verificação de tipos..."
        mypy . || log_warning "MyPy encontrou problemas de tipos"
    fi
    
    # Bandit
    if command -v bandit &> /dev/null; then
        log_info "Executando verificação de segurança..."
        bandit -r server.py src/ || log_warning "Bandit encontrou problemas de segurança"
    fi
}

run_tests() {
    log_info "Executando testes: $TEST_TYPE"
    
    local pytest_args=$(build_pytest_args)
    
    log_info "Comando: $PYTHON_ENV -m pytest $pytest_args"
    
    # Criar diretório de relatórios
    mkdir -p reports
    
    # Executar testes
    if $PYTHON_ENV -m pytest $pytest_args; then
        log_success "Todos os testes passaram!"
        return 0
    else
        log_error "Alguns testes falharam!"
        return 1
    fi
}

show_results() {
    log_info "Resultados dos testes:"
    
    # Mostrar cobertura se disponível
    if [ "$COVERAGE" = "true" ] && [ -f ".coverage" ]; then
        echo ""
        log_info "Relatório de cobertura:"
        $PYTHON_ENV -m coverage report --show-missing
    fi
    
    # Mostrar localização dos relatórios
    if [ "$GENERATE_HTML" = "true" ]; then
        echo ""
        log_info "Relatórios HTML gerados:"
        if [ -d "htmlcov" ]; then
            echo "  - Cobertura: htmlcov/index.html"
        fi
        if [ -f "reports/pytest-report.html" ]; then
            echo "  - Testes: reports/pytest-report.html"
        fi
    fi
    
    # Mostrar relatórios XML
    if [ "$GENERATE_XML" = "true" ]; then
        echo ""
        log_info "Relatórios XML gerados:"
        if [ -f "coverage.xml" ]; then
            echo "  - Cobertura: coverage.xml"
        fi
    fi
}

# Parse argumentos da linha de comando
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -t|--type)
            TEST_TYPE="$2"
            shift 2
            ;;
        -c|--coverage)
            COVERAGE="$2"
            shift 2
            ;;
        -p|--parallel)
            PARALLEL="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE="true"
            shift
            ;;
        -f|--fast)
            FAST_MODE="true"
            shift
            ;;
        -m|--marker)
            MARKER="$2"
            shift 2
            ;;
        --no-cov)
            COVERAGE="false"
            shift
            ;;
        --html)
            GENERATE_HTML="true"
            shift
            ;;
        --xml)
            GENERATE_XML="true"
            shift
            ;;
        --clean)
            CLEAN="true"
            shift
            ;;
        --install-deps)
            INSTALL_DEPS="true"
            shift
            ;;
        --lint)
            LINT_ONLY="true"
            shift
            ;;
        *)
            log_error "Opção desconhecida: $1"
            show_help
            exit 1
            ;;
    esac
done

# Executar ações baseadas nos argumentos
main() {
    log_info "MCP Server Firebird - Test Runner"
    log_info "Tipo de teste: $TEST_TYPE"
    
    # Limpar se solicitado
    if [ "$CLEAN" = "true" ]; then
        clean_artifacts
    fi
    
    # Instalar dependências se solicitado
    if [ "$INSTALL_DEPS" = "true" ]; then
        install_dependencies
    fi
    
    # Verificar dependências
    if ! check_dependencies; then
        log_error "Dependências não atendidas. Use --install-deps para instalar."
        exit 1
    fi
    
    # Apenas linting
    if [ "$LINT_ONLY" = "true" ]; then
        run_linting
        exit $?
    fi
    
    # Executar linting antes dos testes (opcional)
    if [ "$TEST_TYPE" = "all" ] || [ "$VERBOSE" = "true" ]; then
        run_linting
    fi
    
    # Executar testes
    if run_tests; then
        show_results
        log_success "✅ Execução de testes concluída com sucesso!"
        exit 0
    else
        show_results
        log_error "❌ Execução de testes falhou!"
        exit 1
    fi
}

# Verificar se está sendo executado diretamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
