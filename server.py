#!/usr/bin/env python3
"""
Servidor MCP para Firebird - Versão Ultra-Rápida
Otimizado para inicialização instantânea e sem timeouts
"""

import os
import sys
import logging
from typing import Dict, List, Any, Optional

# Configuração de logging otimizada
logging.basicConfig(level=logging.WARNING)  # Reduzir logs desnecessários
logger = logging.getLogger(__name__)

def stderr_log(message: str):
    """Log crítico para stderr - aparece no Claude Desktop"""
    print(f"[MCP] {message}", file=sys.stderr, flush=True)

# Importações críticas primeiro
stderr_log("Starting MCP Firebird Server...")

try:
    import fdb
    stderr_log("FDB imported successfully")
except Exception as e:
    stderr_log(f"FDB import failed: {e}")
    sys.exit(1)

# Importações FastAPI depois (pode causar delay)
try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    import uvicorn
    stderr_log("FastAPI imported successfully")
except Exception as e:
    stderr_log(f"FastAPI import failed: {e}")
    sys.exit(1)

# Configurações do banco (sem validação pesada)
DB_CONFIG = {
    'host': os.getenv('FIREBIRD_HOST', 'localhost'),
    'port': int(os.getenv('FIREBIRD_PORT', 3050)),
    'database': os.getenv('FIREBIRD_DATABASE', '/path/to/database.fdb'),
    'user': os.getenv('FIREBIRD_USER', 'SYSDBA'),
    'password': os.getenv('FIREBIRD_PASSWORD', 'masterkey'),
    'charset': os.getenv('FIREBIRD_CHARSET', 'UTF8')
}

stderr_log(f"Database configured: {DB_CONFIG['host']}:{DB_CONFIG['port']}")

# Modelos mínimos
class QueryRequest(BaseModel):
    sql: str
    params: Optional[List[Any]] = None

class QueryResponse(BaseModel):
    success: bool
    data: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None

# Servidor MCP simplificado
class MCPFirebirdServer:
    def __init__(self):
        self.dsn = f"{DB_CONFIG['host']}/{DB_CONFIG['port']}:{DB_CONFIG['database']}"
        stderr_log(f"DSN configured: {self.dsn}")
    
    def test_connection(self):
        """Teste de conexão síncrono e rápido"""
        try:
            conn = fdb.connect(
                dsn=self.dsn,
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                charset=DB_CONFIG['charset']
            )
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM RDB$DATABASE")
            cursor.fetchone()
            conn.close()
            stderr_log("Connection test: SUCCESS")
            return {"status": "healthy", "database": "connected"}
        except Exception as e:
            error_msg = str(e)
            stderr_log(f"Connection test: FAILED - {error_msg}")
            
            # Diagnóstico rápido
            if "902" in error_msg or "shutdown" in error_msg.lower():
                stderr_log("DIAGNOSIS: SQLCODE -902 - Check Firebird server and firewall")
            elif "network" in error_msg.lower():
                stderr_log("DIAGNOSIS: Network issue - Check host/port accessibility")
            elif "login" in error_msg.lower():
                stderr_log("DIAGNOSIS: Authentication - Check username/password")
                
            return {"status": "unhealthy", "error": error_msg}
    
    def execute_query(self, sql: str, params: List[Any] = None):
        """Execução de query simplificada"""
        try:
            conn = fdb.connect(
                dsn=self.dsn,
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                charset=DB_CONFIG['charset']
            )
            cursor = conn.cursor()
            
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            
            # SELECT
            if sql.strip().upper().startswith('SELECT'):
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                rows = cursor.fetchall()
                data = [dict(zip(columns, row)) for row in rows]
                conn.close()
                stderr_log(f"Query executed: {len(data)} rows")
                return QueryResponse(success=True, data=data)
            else:
                # INSERT/UPDATE/DELETE
                conn.commit()
                conn.close()
                stderr_log("Query executed: modification successful")
                return QueryResponse(success=True)
                
        except Exception as e:
            stderr_log(f"Query failed: {e}")
            return QueryResponse(success=False, error=str(e))
    
    def get_tables(self):
        """Listar tabelas rapidamente"""
        try:
            conn = fdb.connect(
                dsn=self.dsn,
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                charset=DB_CONFIG['charset']
            )
            cursor = conn.cursor()
            cursor.execute("""
                SELECT TRIM(RDB$RELATION_NAME) 
                FROM RDB$RELATIONS 
                WHERE RDB$VIEW_BLR IS NULL 
                AND (RDB$SYSTEM_FLAG IS NULL OR RDB$SYSTEM_FLAG = 0)
                ORDER BY RDB$RELATION_NAME
            """)
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()
            stderr_log(f"Tables retrieved: {len(tables)}")
            return tables
        except Exception as e:
            stderr_log(f"Get tables failed: {e}")
            return []

# Criar instância
mcp_server = MCPFirebirdServer()

# FastAPI app mínima
app = FastAPI(
    title="MCP Firebird",
    description="Fast MCP Firebird Server",
    version="1.0"
)

# Endpoints essenciais apenas
@app.get("/health")
def health_check():
    """Health check rápido"""
    stderr_log("Health check requested")
    return mcp_server.test_connection()

@app.post("/query")
def execute_query(request: QueryRequest):
    """Executar query"""
    stderr_log(f"Query: {request.sql[:50]}...")
    return mcp_server.execute_query(request.sql, request.params)

@app.get("/tables")
def list_tables():
    """Listar tabelas"""
    stderr_log("Tables requested")
    return mcp_server.get_tables()

@app.get("/info")
def get_info():
    """Informações básicas"""
    stderr_log("Info requested")
    tables = mcp_server.get_tables()
    return {
        "tables": tables,
        "database_path": DB_CONFIG['database'],
        "tables_count": len(tables)
    }

# Endpoint de diagnóstico
@app.get("/diagnostics")
def diagnostics():
    """Diagnóstico mínimo"""
    stderr_log("Diagnostics requested")
    import glob
    found_libs = []
    for path in ['/usr/lib', '/usr/lib/x86_64-linux-gnu']:
        if os.path.exists(path):
            found_libs.extend(glob.glob(os.path.join(path, '*fbclient*')))
    
    return {
        "database_config": {
            "host": DB_CONFIG['host'],
            "port": DB_CONFIG['port'],
            "database": DB_CONFIG['database'],
            "user": DB_CONFIG['user']
        },
        "firebird_libraries": found_libs,
        "python_version": sys.version
    }

# Interceptar erros globais
@app.exception_handler(Exception)
def global_exception_handler(request, exc):
    stderr_log(f"Unhandled error: {exc}")
    return {"error": str(exc)}

if __name__ == "__main__":
    port = int(os.getenv('MCP_SERVER_PORT', 3000))
    
    stderr_log(f"Starting server on port {port}")
    stderr_log("Server ready for connections")
    
    # Configuração uvicorn otimizada para velocidade
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=port,
        log_level="warning",  # Menos logs
        access_log=False,     # Sem access logs
        reload=False,
        workers=1            # Apenas 1 worker
    )