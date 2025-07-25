#!/bin/bash
# Build script para MCP Server Firebird
# Constrói imagem Docker com tag ghcr.io/marcelofmatos/mcp-server-firebird:latest

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

IMAGE_NAME="ghcr.io/marcelofmatos/mcp-server-firebird"
TAG="latest"
FULL_TAG="${IMAGE_NAME}:${TAG}"

CLEAN_BUILD=false
PUSH_IMAGE=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --clean)
            CLEAN_BUILD=true
            shift
            ;;
        --push)
            PUSH_IMAGE=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            echo "Uso: $0 [opções]"
            echo "Opções:"
            echo "  --clean     Build sem cache"
            echo "  --push      Push para registry após build"
            echo "  --verbose   Output detalhado"
            echo "  --help      Mostra esta ajuda"
            exit 0
            ;;
        *)
            echo "Opção desconhecida: $1"
            exit 1
            ;;
    esac
done

log() {
    echo "🔨 [$(date '+%H:%M:%S')] $*"
}

error() {
    echo "❌ [$(date '+%H:%M:%S')] ERROR: $*" >&2
    exit 1
}

check_prerequisites() {
    log "Verificando pré-requisitos..."
    
    if ! command -v docker &> /dev/null; then
        error "Docker não encontrado. Instale o Docker primeiro."
    fi
    
    if ! docker info &> /dev/null; then
        error "Docker daemon não está rodando"
    fi
    
    if [[ ! -f "Dockerfile" ]]; then
        error "Dockerfile não encontrado no diretório atual"
    fi
    
    log "✅ Pré-requisitos verificados"
}

get_build_info() {
    APP_VERSION="latest"
    GIT_COMMIT="unknown"
    
    if command -v git &> /dev/null && git rev-parse --git-dir &> /dev/null; then
        GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
        
        if git describe --tags --exact-match HEAD &> /dev/null; then
            APP_VERSION=$(git describe --tags --exact-match HEAD)
        elif git describe --tags &> /dev/null; then
            APP_VERSION=$(git describe --tags)
        fi
    fi
    
    log "Versão: $APP_VERSION"
    log "Commit: $GIT_COMMIT"
}

build_image() {
    log "Construindo imagem: $FULL_TAG"
    
    DOCKER_ARGS=(
        "build"
        "-t" "$FULL_TAG"
        "--build-arg" "APP_VERSION=$APP_VERSION"
        "--build-arg" "GIT_COMMIT=$GIT_COMMIT"
        "--label" "org.opencontainers.image.source=https://github.com/marcelofmatos/mcp-server-firebird"
        "--label" "org.opencontainers.image.version=$APP_VERSION"
        "--label" "org.opencontainers.image.revision=$GIT_COMMIT"
        "--label" "org.opencontainers.image.created=$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
    )
    
    if [[ "$CLEAN_BUILD" == true ]]; then
        log "Build limpo (sem cache)"
        DOCKER_ARGS+=("--no-cache")
    fi
    
    if [[ "$VERBOSE" == true ]]; then
        DOCKER_ARGS+=("--progress=plain")
    fi
    
    DOCKER_ARGS+=(".")
    
    if ! docker "${DOCKER_ARGS[@]}"; then
        error "Falha no build da imagem"
    fi
    
    log "✅ Imagem construída com sucesso"
}

validate_image() {
    log "Validando imagem..."
    
    if ! docker image inspect "$FULL_TAG" &> /dev/null; then
        error "Imagem não encontrada após build"
    fi
    
    local size=$(docker image inspect "$FULL_TAG" --format='{{.Size}}' | awk '{printf "%.1f MB", $1/1024/1024}')
    log "Tamanho da imagem: $size"
    
    log "Testando execução básica..."
    if ! timeout 30 docker run --rm "$FULL_TAG" python3 -c "import fdb; print('FDB OK')" &> /dev/null; then
        log "⚠️  Teste básico falhou, mas imagem foi construída"
    else
        log "✅ Teste básico passou"
    fi
}

push_image() {
    if [[ "$PUSH_IMAGE" == true ]]; then
        log "Fazendo push da imagem para registry..."
        
        if ! docker push "$FULL_TAG"; then
            error "Falha no push da imagem"
        fi
        
        log "✅ Push concluído com sucesso"
    fi
}

cleanup_on_error() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        log "Build falhou, removendo artefatos..."
        docker rmi "$FULL_TAG" 2>/dev/null || true
    fi
    exit $exit_code
}

main() {
    trap cleanup_on_error EXIT
    
    log "Iniciando build do MCP Server Firebird"
    log "Imagem: $FULL_TAG"
    
    check_prerequisites
    get_build_info
    build_image
    validate_image
    push_image
    
    log "🎉 Build concluído com sucesso!"
    log "Para executar: docker run -d --name mcp-firebird $FULL_TAG"
    
    trap - EXIT
}

main "$@"
