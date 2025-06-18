#!/bin/bash
# Script helper para testes do MCP Firebird Server

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}=================================================${NC}"
    echo -e "${BLUE} $1${NC}"
    echo -e "${BLUE}=================================================${NC}"
}

print_section() {
    echo -e "\n${YELLOW}>>> $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

show_help() {
    print_header "MCP Firebird Server - Test Helper"
    echo ""
    echo "Uso: $0 [comando] [opções]"
    echo ""
    echo "Comandos disponíveis:"
    echo "  diagnostics     - Executar diagnóstico completo do sistema"
    echo "  test-fdb       - Testar apenas biblioteca FDB"
    echo "  test-server    - Testar servidor MCP (requer servidor rodando)"
    echo "  test-direct    - Testar conexão direta com Firebird"
    echo "  test-all       - Executar todos os testes"
    echo "  env            - Mostrar variáveis de ambiente"
    echo "  libs           - Procurar bibliotecas Firebird"
    echo "  help           - Mostrar esta ajuda"
    echo ""
    echo "Exemplos:"
    echo "  $0 diagnostics"
    echo "  $0 test-server"
    echo "  $0 test-direct --host 192.168.1.100 --database /path/banco.fdb --user SYSDBA --password masterkey"
    echo ""
}

test_fdb() {
    print_section "Testando biblioteca FDB"
    
    python3 -c "
import fdb
fdb_version = getattr(fdb, '__version__', 'Unknown')
print('✅ FDB import OK - Version:', fdb_version)

try:
    # Teste de conexão que deve falhar mas mostrar se bibliotecas estão OK
    conn = fdb.connect(dsn='localhost/3050:/tmp/nonexistent.fdb', user='test', password='test')
except Exception as e:
    error_msg = str(e)
    if 'could not be determined' in error_msg:
        print('❌ Bibliotecas cliente não encontradas')
        exit(1)
    elif 'network' in error_msg.lower() or 'connection' in error_msg.lower() or 'shutdown' in error_msg.lower():
        print('✅ Bibliotecas OK (erro de conexão esperado)')
    else:
        print('⚠️  Erro inesperado:', error_msg)
"
}

test_server() {
    print_section "Testando servidor MCP"
    
    if command -v python3 >/dev/null 2>&1; then
        python3 /app/mcp-server/test-connection.py --url http://localhost:3000
    else
        print_error "Python3 não encontrado"
        return 1
    fi
}

test_direct() {
    print_section "Testando conexão direta"
    
    # Usar variáveis de ambiente ou parâmetros
    local host="${FIREBIRD_HOST:-localhost}"
    local database="${FIREBIRD_DATABASE:-/tmp/test.fdb}"
    local user="${FIREBIRD_USER:-SYSDBA}"
    local password="${FIREBIRD_PASSWORD:-masterkey}"
    
    # Parse de argumentos básico
    while [[ $# -gt 0 ]]; do
        case $1 in
            --host)
                host="$2"
                shift 2
                ;;
            --database)
                database="$2"
                shift 2
                ;;
            --user)
                user="$2"
                shift 2
                ;;
            --password)
                password="$2"
                shift 2
                ;;
            *)
                shift
                ;;
        esac
    done
    
    print_info "Host: $host"
    print_info "Database: $database"
    print_info "User: $user"
    
    python3 /app/mcp-server/test-connection.py --direct \
        --host "$host" \
        --database "$database" \
        --user "$user" \
        --password "$password"
}

show_env() {
    print_section "Variáveis de Ambiente"
    
    echo "Configuração Firebird:"
    echo "  FIREBIRD_HOST: ${FIREBIRD_HOST:-'Not set'}"
    echo "  FIREBIRD_PORT: ${FIREBIRD_PORT:-'Not set'}"
    echo "  FIREBIRD_DATABASE: ${FIREBIRD_DATABASE:-'Not set'}"
    echo "  FIREBIRD_USER: ${FIREBIRD_USER:-'Not set'}"
    echo "  FIREBIRD_PASSWORD: ${FIREBIRD_PASSWORD:-'Not set'}"
    echo "  FIREBIRD_CHARSET: ${FIREBIRD_CHARSET:-'Not set'}"
    echo ""
    echo "Configuração Sistema:"
    echo "  LD_LIBRARY_PATH: ${LD_LIBRARY_PATH:-'Not set'}"
    echo "  FIREBIRD: ${FIREBIRD:-'Not set'}"
    echo "  PATH: ${PATH:-'Not set'}"
}

find_libs() {
    print_section "Procurando bibliotecas Firebird"
    
    echo "Procurando em locais comuns..."
    find /usr -name "*fbclient*" 2>/dev/null || echo "Nenhuma biblioteca fbclient encontrada"
    find /usr -name "*firebird*" 2>/dev/null || echo "Nenhuma biblioteca firebird encontrada"
    
    echo ""
    echo "Verificando cache ldconfig..."
    ldconfig -p | grep -i firebird || echo "Nenhuma entrada firebird no cache"
    ldconfig -p | grep -i fbclient || echo "Nenhuma entrada fbclient no cache"
}

run_diagnostics() {
    print_section "Executando diagnóstico completo"
    
    if [[ -f /app/mcp-server/firebird-diagnostics.py ]]; then
        python3 /app/mcp-server/firebird-diagnostics.py
    else
        print_error "Script firebird-diagnostics.py não encontrado"
        return 1
    fi
}

test_all() {
    print_header "Executando Todos os Testes"
    
    print_section "1. Variáveis de Ambiente"
    show_env
    
    print_section "2. Bibliotecas"
    find_libs
    
    print_section "3. FDB"
    test_fdb
    
    print_section "4. Diagnóstico Completo"
    run_diagnostics
    
    print_section "5. Servidor MCP (se rodando)"
    test_server || print_info "Servidor não está rodando ou não acessível"
    
    print_success "Todos os testes concluídos!"
}

# Main
case "${1:-help}" in
    diagnostics)
        run_diagnostics
        ;;
    test-fdb)
        test_fdb
        ;;
    test-server)
        test_server
        ;;
    test-direct)
        shift
        test_direct "$@"
        ;;
    test-all)
        test_all
        ;;
    env)
        show_env
        ;;
    libs)
        find_libs
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Comando desconhecido: $1"
        echo ""
        show_help
        exit 1
        ;;
esac