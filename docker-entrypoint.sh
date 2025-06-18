#!/bin/bash
set -e

# Função para log
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

log "Iniciando servidor MCP Firebird..."

# Configurar timezone
ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Inicializar Firebird se for primeira execução
if [ ! -f "$FIREBIRD_DATABASE" ]; then
    log "Banco de dados não encontrado. Criando novo banco..."
    /usr/local/bin/init-database.sh
fi

# Aguardar Firebird estar pronto
log "Verificando se Firebird está pronto..."
until /opt/firebird/bin/isql -user "$FIREBIRD_USER" -password "$FIREBIRD_PASSWORD" "$FIREBIRD_DATABASE" -q -o /dev/null <<< "SELECT 1 FROM RDB\$DATABASE;" 2>/dev/null; do
    log "Aguardando Firebird ficar disponível..."
    sleep 2
done

log "Firebird está pronto!"

# Iniciar supervisor
log "Iniciando supervisor..."
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf