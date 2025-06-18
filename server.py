#!/usr/bin/env python3
"""
Servidor MCP para Firebird Externo
Permite que modelos de IA interajam com banco de dados Firebird externo
"""

import os
import asyncio
import logging
from typing import Dict, List, Any, Optional
import firebird.driver as fb_driver
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import uvicorn
from contextlib import asynccontextmanager

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configurações do banco externo
DB_CONFIG = {
    'host': os.getenv('FIREBIRD_HOST', 'localhost'),
    'port': int(os.getenv('FIREBIRD_PORT', 3050)),
    'database': os.getenv('FIREBIRD_DATABASE', '/path/to/database.fdb'),
    'user': os.getenv('FIREBIRD_USER', 'SYSDBA'),
    'password': os.getenv('FIREBIRD_PASSWORD', 'masterkey'),
    'charset': os.getenv('FIREBIRD_CHARSET', 'UTF8')
}

# Modelos Pydantic
class QueryRequest(BaseModel):
    sql: str
    params: Optional[List[Any]] = None

class QueryResponse(BaseModel):
    success: bool
    data: Optional[List[Dict[str, Any]]] = None
    affected_rows: Optional[int] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None

class DatabaseInfo(BaseModel):
    tables: List[str]
    version: str
    database_path: str
    server_info: Dict[str, Any]

class TableSchema(BaseModel):
    table_name: str
    fields: List[Dict[str, Any]]

class ConnectionStatus(BaseModel):
    connected: bool
    server_version: Optional[str] = None
    database: Optional[str] = None
    error: Optional[str] = None

class MCPFirebirdServer:
    def __init__(self):
        self.connection_string = self._build_connection_string()
        logger.info(f"Configurado para conectar em: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
        
    def _build_connection_string(self) -> str:
        """Construir string de conexão para Firebird"""
        return f"{DB_CONFIG['host']}/{DB_CONFIG['port']}:{DB_CONFIG['database']}"
    
    async def test_connection(self) -> ConnectionStatus:
        """Testar conexão com o banco Firebird"""
        try:
            with fb_driver.connect(
                self.connection_string,
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                charset=DB_CONFIG['charset']
            ) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT RDB$GET_CONTEXT('SYSTEM', 'ENGINE_VERSION') FROM RDB$DATABASE")
                version = cursor.fetchone()[0]
                
                return ConnectionStatus(
                    connected=True,
                    server_version=version,
                    database=DB_CONFIG['database']
                )
                
        except Exception as e:
            logger.error(f"Erro ao testar conexão: {e}")
            return ConnectionStatus(
                connected=False,
                error=str(e)
            )
    
    async def execute_query(self, sql: str, params: List[Any] = None) -> QueryResponse:
        """Executar query SQL no Firebird"""
        import time
        start_time = time.time()
        
        try:
            with fb_driver.connect(
                self.connection_string,
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                charset=DB_CONFIG['charset']
            ) as conn:
                cursor = conn.cursor()
                
                if params:
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)
                
                execution_time = time.time() - start_time
                
                # Verificar se é SELECT
                sql_upper = sql.strip().upper()
                if sql_upper.startswith('SELECT') or sql_upper.startswith('WITH'):
                    columns = [desc[0] for desc in cursor.description] if cursor.description else []
                    rows = cursor.fetchall()
                    
                    # Converter dados para formato JSON-serializável
                    data = []
                    for row in rows:
                        row_dict = {}
                        for i, value in enumerate(row):
                            # Tratar tipos especiais do Firebird
                            if hasattr(value, 'isoformat'):  # datetime objects
                                row_dict[columns[i]] = value.isoformat()
                            elif isinstance(value, bytes):  # BLOB data
                                try:
                                    row_dict[columns[i]] = value.decode('utf-8')
                                except:
                                    row_dict[columns[i]] = f"<BLOB: {len(value)} bytes>"
                            else:
                                row_dict[columns[i]] = value
                        data.append(row_dict)
                    
                    return QueryResponse(
                        success=True,
                        data=data,
                        execution_time=round(execution_time, 4)
                    )
                else:
                    # Para INSERT, UPDATE, DELETE
                    affected_rows = cursor.rowcount if hasattr(cursor, 'rowcount') else 0
                    conn.commit()
                    
                    return QueryResponse(
                        success=True,
                        affected_rows=affected_rows,
                        execution_time=round(execution_time, 4)
                    )
                    
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Erro ao executar query: {e}")
            return QueryResponse(
                success=False,
                error=str(e),
                execution_time=round(execution_time, 4)
            )
    
    async def get_database_info(self) -> DatabaseInfo:
        """Obter informações do banco de dados"""
        try:
            with fb_driver.connect(
                self.connection_string,
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                charset=DB_CONFIG['charset']
            ) as conn:
                cursor = conn.cursor()
                
                # Obter lista de tabelas
                cursor.execute("""
                    SELECT TRIM(RDB$RELATION_NAME) as TABLE_NAME
                    FROM RDB$RELATIONS 
                    WHERE RDB$VIEW_BLR IS NULL 
                    AND (RDB$SYSTEM_FLAG IS NULL OR RDB$SYSTEM_FLAG = 0)
                    ORDER BY RDB$RELATION_NAME
                """)
                tables = [row[0] for row in cursor.fetchall()]
                
                # Obter versão do Firebird
                cursor.execute("SELECT RDB$GET_CONTEXT('SYSTEM', 'ENGINE_VERSION') FROM RDB$DATABASE")
                version = cursor.fetchone()[0]
                
                # Informações adicionais do servidor
                cursor.execute("""
                    SELECT 
                        RDB$GET_CONTEXT('SYSTEM', 'DB_NAME') as DB_NAME,
                        RDB$GET_CONTEXT('SYSTEM', 'NETWORK_PROTOCOL') as PROTOCOL,
                        RDB$GET_CONTEXT('SYSTEM', 'CLIENT_ADDRESS') as CLIENT_ADDR
                    FROM RDB$DATABASE
                """)
                server_row = cursor.fetchone()
                server_info = {
                    'database_name': server_row[0],
                    'protocol': server_row[1],
                    'client_address': server_row[2],
                    'tables_count': len(tables)
                }
                
                return DatabaseInfo(
                    tables=tables,
                    version=version,
                    database_path=DB_CONFIG['database'],
                    server_info=server_info
                )
                
        except Exception as e:
            logger.error(f"Erro ao obter informações do banco: {e}")
            raise HTTPException(status_code=500, detail=f"Erro ao conectar com banco: {str(e)}")

    async def get_table_schema(self, table_name: str) -> TableSchema:
        """Obter schema detalhado de uma tabela"""
        try:
            with fb_driver.connect(
                self.connection_string,
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                charset=DB_CONFIG['charset']
            ) as conn:
                cursor = conn.cursor()
                
                sql = """
                SELECT 
                    TRIM(rf.RDB$FIELD_NAME) as FIELD_NAME,
                    CASE f.RDB$FIELD_TYPE
                        WHEN 261 THEN 'BLOB'
                        WHEN 14 THEN 'CHAR'
                        WHEN 40 THEN 'CSTRING'
                        WHEN 11 THEN 'D_FLOAT'
                        WHEN 27 THEN 'DOUBLE'
                        WHEN 10 THEN 'FLOAT'
                        WHEN 16 THEN 'BIGINT'
                        WHEN 8 THEN 'INTEGER'
                        WHEN 9 THEN 'QUAD'
                        WHEN 7 THEN 'SMALLINT'
                        WHEN 12 THEN 'DATE'
                        WHEN 13 THEN 'TIME'
                        WHEN 35 THEN 'TIMESTAMP'
                        WHEN 37 THEN 'VARCHAR'
                        ELSE 'UNKNOWN'
                    END as DATA_TYPE,
                    f.RDB$FIELD_LENGTH as FIELD_LENGTH,
                    f.RDB$FIELD_SCALE as FIELD_SCALE,
                    rf.RDB$NULL_FLAG as NOT_NULL,
                    rf.RDB$DEFAULT_SOURCE as DEFAULT_VALUE,
                    rf.RDB$FIELD_POSITION as POSITION
                FROM RDB$RELATION_FIELDS rf
                JOIN RDB$FIELDS f ON rf.RDB$FIELD_SOURCE = f.RDB$FIELD_NAME
                WHERE rf.RDB$RELATION_NAME = ?
                ORDER BY rf.RDB$FIELD_POSITION
                """
                
                cursor.execute(sql, [table_name.upper()])
                fields = []
                
                for row in cursor.fetchall():
                    field_info = {
                        'name': row[0],
                        'type': row[1],
                        'length': row[2],
                        'scale': row[3],
                        'not_null': bool(row[4]),
                        'default': row[5].strip() if row[5] else None,
                        'position': row[6]
                    }
                    fields.append(field_info)
                
                return TableSchema(
                    table_name=table_name,
                    fields=fields
                )
                
        except Exception as e:
            logger.error(f"Erro ao obter schema da tabela {table_name}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

# Instância do servidor MCP
mcp_server = MCPFirebirdServer()

# Criar aplicação FastAPI
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando servidor MCP Firebird...")
    # Testar conexão na inicialização
    status = await mcp_server.test_connection()
    if status.connected:
        logger.info(f"Conectado ao Firebird {status.server_version}")
    else:
        logger.warning(f"Não foi possível conectar ao banco: {status.error}")
    yield
    logger.info("Encerrando servidor MCP Firebird...")

app = FastAPI(
    title="MCP Firebird Server",
    description="Servidor MCP para integração com Firebird externo",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    """Verificação de saúde do servidor e conexão com banco"""
    status = await mcp_server.test_connection()
    if status.connected:
        return {
            "status": "healthy", 
            "database": "connected",
            "server_version": status.server_version,
            "database_path": status.database
        }
    else:
        return {
            "status": "unhealthy", 
            "database": "disconnected",
            "error": status.error
        }

@app.get("/info", response_model=DatabaseInfo)
async def get_info():
    """Obter informações completas do banco de dados"""
    return await mcp_server.get_database_info()

@app.post("/query", response_model=QueryResponse)
async def execute_query(request: QueryRequest):
    """Executar query SQL no banco"""
    return await mcp_server.execute_query(request.sql, request.params)

@app.get("/tables", response_model=List[str])
async def list_tables():
    """Listar todas as tabelas do banco"""
    info = await mcp_server.get_database_info()
    return info.tables

@app.get("/tables/{table_name}/schema", response_model=TableSchema)
async def get_table_schema(table_name: str):
    """Obter schema detalhado de uma tabela"""
    return await mcp_server.get_table_schema(table_name)

@app.get("/connection/test")
async def test_connection():
    """Testar conexão com o banco"""
    return await mcp_server.test_connection()

if __name__ == "__main__":
    port = int(os.getenv('MCP_SERVER_PORT', 3000))
    logger.info(f"Iniciando servidor MCP na porta {port}")
    logger.info(f"Banco configurado: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=port,
        log_level=os.getenv('MCP_LOG_LEVEL', 'info').lower(),
        reload=False
    )