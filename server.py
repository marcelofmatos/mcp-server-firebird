#!/usr/bin/env python3
"""
Servidor MCP para Firebird Externo
Permite que modelos de IA interajam com banco de dados Firebird externo
Usando biblioteca FDB (mais estável)
"""

import os
import asyncio
import logging
from typing import Dict, List, Any, Optional
import datetime
import decimal

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Verificar e importar FDB com diagnóstico melhorado
try:
    import fdb
    logger.info(f"FDB library loaded successfully - Version: {fdb.version}")
except ImportError as e:
    logger.error(f"Failed to import FDB library: {e}")
    logger.error("Please install FDB: pip install fdb")
    raise
except Exception as e:
    logger.error(f"Unexpected error importing FDB: {e}")
    # Diagnóstico adicional
    import sys
    logger.error(f"Python version: {sys.version}")
    logger.error(f"LD_LIBRARY_PATH: {os.environ.get('LD_LIBRARY_PATH', 'Not set')}")
    logger.error(f"FIREBIRD env: {os.environ.get('FIREBIRD', 'Not set')}")
    
    # Tentar procurar bibliotecas
    import glob
    lib_paths = ['/usr/lib', '/usr/lib/x86_64-linux-gnu', '/usr/local/lib']
    found_libs = []
    for path in lib_paths:
        pattern = os.path.join(path, '*fbclient*')
        found_libs.extend(glob.glob(pattern))
    
    if found_libs:
        logger.info(f"Found Firebird libraries: {found_libs}")
    else:
        logger.error("No Firebird client libraries found in common locations")
        logger.error("Please install: apt-get install libfbclient2 firebird-dev")
    
    raise

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import uvicorn
from contextlib import asynccontextmanager

# Configurações do banco externo
DB_CONFIG = {
    'host': os.getenv('FIREBIRD_HOST', 'localhost'),
    'port': int(os.getenv('FIREBIRD_PORT', 3050)),
    'database': os.getenv('FIREBIRD_DATABASE', '/path/to/database.fdb'),
    'user': os.getenv('FIREBIRD_USER', 'SYSDBA'),
    'password': os.getenv('FIREBIRD_PASSWORD', 'masterkey'),
    'charset': os.getenv('FIREBIRD_CHARSET', 'UTF8')
}

# Log da configuração (sem senha)
config_log = DB_CONFIG.copy()
config_log['password'] = '***'
logger.info(f"Database configuration: {config_log}")

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

def serialize_value(value):
    """Serializar valores para JSON"""
    if value is None:
        return None
    elif isinstance(value, (datetime.datetime, datetime.date)):
        return value.isoformat()
    elif isinstance(value, datetime.time):
        return value.strftime('%H:%M:%S')
    elif isinstance(value, decimal.Decimal):
        return float(value)
    elif isinstance(value, bytes):
        try:
            return value.decode('utf-8')
        except:
            return f"<BLOB: {len(value)} bytes>"
    else:
        return value

class MCPFirebirdServer:
    def __init__(self):
        self.dsn = self._build_dsn()
        logger.info(f"Configurado para conectar em: {self.dsn}")
        
    def _build_dsn(self) -> str:
        """Construir DSN para Firebird usando FDB"""
        if DB_CONFIG['host'].lower() in ['localhost', '127.0.0.1']:
            # Conexão local
            return f"{DB_CONFIG['host']}/{DB_CONFIG['port']}:{DB_CONFIG['database']}"
        else:
            # Conexão remota
            return f"{DB_CONFIG['host']}/{DB_CONFIG['port']}:{DB_CONFIG['database']}"
    
    async def test_connection(self) -> ConnectionStatus:
        """Testar conexão com o banco Firebird"""
        try:
            logger.debug(f"Testando conexão com DSN: {self.dsn}")
            conn = fdb.connect(
                dsn=self.dsn,
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                charset=DB_CONFIG['charset']
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT RDB$GET_CONTEXT('SYSTEM', 'ENGINE_VERSION') FROM RDB$DATABASE")
            version = cursor.fetchone()[0]
            
            conn.close()
            logger.info("Conexão com Firebird estabelecida com sucesso")
            
            return ConnectionStatus(
                connected=True,
                server_version=version.strip() if version else 'Unknown',
                database=DB_CONFIG['database']
            )
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Erro ao testar conexão: {error_msg}")
            
            # Diagnóstico específico para problemas comuns
            if "could not be determined" in error_msg:
                logger.error("DIAGNÓSTICO: Bibliotecas cliente Firebird não encontradas")
                logger.error("SOLUÇÃO: Instalar libfbclient2 e firebird-dev")
                logger.error("COMANDO: apt-get install libfbclient2 firebird-dev")
            elif "network" in error_msg.lower():
                logger.error("DIAGNÓSTICO: Problema de rede/conectividade")
                logger.error(f"SOLUÇÃO: Verificar se {DB_CONFIG['host']}:{DB_CONFIG['port']} está acessível")
            elif "login" in error_msg.lower() or "authentication" in error_msg.lower():
                logger.error("DIAGNÓSTICO: Problema de autenticação")
                logger.error("SOLUÇÃO: Verificar usuário e senha do banco")
            elif "database" in error_msg.lower() and "not found" in error_msg.lower():
                logger.error("DIAGNÓSTICO: Arquivo de banco não encontrado")
                logger.error(f"SOLUÇÃO: Verificar se existe o arquivo {DB_CONFIG['database']}")
            
            return ConnectionStatus(
                connected=False,
                error=error_msg
            )
    
    async def execute_query(self, sql: str, params: List[Any] = None) -> QueryResponse:
        """Executar query SQL no Firebird"""
        import time
        start_time = time.time()
        
        conn = None
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
                        row_dict[columns[i]] = serialize_value(value)
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
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
            logger.error(f"Erro ao executar query: {e}")
            return QueryResponse(
                success=False,
                error=str(e),
                execution_time=round(execution_time, 4)
            )
        finally:
            if conn:
                try:
                    conn.close()
                except:
                    pass
    
    async def get_database_info(self) -> DatabaseInfo:
        """Obter informações do banco de dados"""
        conn = None
        try:
            conn = fdb.connect(
                dsn=self.dsn,
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                charset=DB_CONFIG['charset']
            )
            
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
            version_row = cursor.fetchone()
            version = version_row[0].strip() if version_row and version_row[0] else 'Unknown'
            
            # Informações adicionais do servidor
            try:
                cursor.execute("""
                    SELECT 
                        RDB$GET_CONTEXT('SYSTEM', 'DB_NAME') as DB_NAME,
                        RDB$GET_CONTEXT('SYSTEM', 'NETWORK_PROTOCOL') as PROTOCOL,
                        RDB$GET_CONTEXT('SYSTEM', 'CLIENT_ADDRESS') as CLIENT_ADDR
                    FROM RDB$DATABASE
                """)
                server_row = cursor.fetchone()
                server_info = {
                    'database_name': server_row[0] if server_row[0] else 'Unknown',
                    'protocol': server_row[1] if server_row[1] else 'Unknown',
                    'client_address': server_row[2] if server_row[2] else 'Unknown',
                    'tables_count': len(tables)
                }
            except:
                server_info = {
                    'database_name': 'Unknown',
                    'protocol': 'Unknown',
                    'client_address': 'Unknown',
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
        finally:
            if conn:
                try:
                    conn.close()
                except:
                    pass

    async def get_table_schema(self, table_name: str) -> TableSchema:
        """Obter schema detalhado de uma tabela"""
        conn = None
        try:
            conn = fdb.connect(
                dsn=self.dsn,
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                charset=DB_CONFIG['charset']
            )
            
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
        finally:
            if conn:
                try:
                    conn.close()
                except:
                    pass

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
        logger.warning("Servidor iniciado, mas sem conexão com banco")
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
            "error": status.error,
            "fdb_version": fdb.version,
            "config": {
                "host": DB_CONFIG['host'],
                "port": DB_CONFIG['port'],
                "database": DB_CONFIG['database'],
                "user": DB_CONFIG['user']
            }
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

@app.get("/diagnostics")
async def diagnostics():
    """Informações de diagnóstico do sistema"""
    import sys
    import glob
    
    # Procurar bibliotecas Firebird
    lib_paths = ['/usr/lib', '/usr/lib/x86_64-linux-gnu', '/usr/local/lib']
    found_libs = []
    for path in lib_paths:
        if os.path.exists(path):
            pattern = os.path.join(path, '*fbclient*')
            found_libs.extend(glob.glob(pattern))
    
    return {
        "python_version": sys.version,
        "fdb_version": fdb.version,
        "environment": {
            "LD_LIBRARY_PATH": os.environ.get('LD_LIBRARY_PATH', 'Not set'),
            "FIREBIRD": os.environ.get('FIREBIRD', 'Not set'),
            "PATH": os.environ.get('PATH', 'Not set')
        },
        "firebird_libraries": found_libs,
        "database_config": {
            "host": DB_CONFIG['host'],
            "port": DB_CONFIG['port'],
            "database": DB_CONFIG['database'],
            "user": DB_CONFIG['user'],
            "charset": DB_CONFIG['charset']
        }
    }

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

def serialize_value(value):
    """Serializar valores para JSON"""
    if value is None:
        return None
    elif isinstance(value, (datetime.datetime, datetime.date)):
        return value.isoformat()
    elif isinstance(value, datetime.time):
        return value.strftime('%H:%M:%S')
    elif isinstance(value, decimal.Decimal):
        return float(value)
    elif isinstance(value, bytes):
        try:
            return value.decode('utf-8')
        except:
            return f"<BLOB: {len(value)} bytes>"
    else:
        return value

class MCPFirebirdServer:
    def __init__(self):
        self.dsn = self._build_dsn()
        logger.info(f"Configurado para conectar em: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
        
    def _build_dsn(self) -> str:
        """Construir DSN para Firebird usando FDB"""
        if DB_CONFIG['host'].lower() in ['localhost', '127.0.0.1']:
            # Conexão local
            return f"{DB_CONFIG['host']}/{DB_CONFIG['port']}:{DB_CONFIG['database']}"
        else:
            # Conexão remota
            return f"{DB_CONFIG['host']}/{DB_CONFIG['port']}:{DB_CONFIG['database']}"
    
    async def test_connection(self) -> ConnectionStatus:
        """Testar conexão com o banco Firebird"""
        try:
            conn = fdb.connect(
                dsn=self.dsn,
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                charset=DB_CONFIG['charset']
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT RDB$GET_CONTEXT('SYSTEM', 'ENGINE_VERSION') FROM RDB$DATABASE")
            version = cursor.fetchone()[0]
            
            conn.close()
            
            return ConnectionStatus(
                connected=True,
                server_version=version.strip() if version else 'Unknown',
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
        
        conn = None
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
                        row_dict[columns[i]] = serialize_value(value)
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
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
            logger.error(f"Erro ao executar query: {e}")
            return QueryResponse(
                success=False,
                error=str(e),
                execution_time=round(execution_time, 4)
            )
        finally:
            if conn:
                try:
                    conn.close()
                except:
                    pass
    
    async def get_database_info(self) -> DatabaseInfo:
        """Obter informações do banco de dados"""
        conn = None
        try:
            conn = fdb.connect(
                dsn=self.dsn,
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                charset=DB_CONFIG['charset']
            )
            
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
            version_row = cursor.fetchone()
            version = version_row[0].strip() if version_row and version_row[0] else 'Unknown'
            
            # Informações adicionais do servidor
            try:
                cursor.execute("""
                    SELECT 
                        RDB$GET_CONTEXT('SYSTEM', 'DB_NAME') as DB_NAME,
                        RDB$GET_CONTEXT('SYSTEM', 'NETWORK_PROTOCOL') as PROTOCOL,
                        RDB$GET_CONTEXT('SYSTEM', 'CLIENT_ADDRESS') as CLIENT_ADDR
                    FROM RDB$DATABASE
                """)
                server_row = cursor.fetchone()
                server_info = {
                    'database_name': server_row[0] if server_row[0] else 'Unknown',
                    'protocol': server_row[1] if server_row[1] else 'Unknown',
                    'client_address': server_row[2] if server_row[2] else 'Unknown',
                    'tables_count': len(tables)
                }
            except:
                server_info = {
                    'database_name': 'Unknown',
                    'protocol': 'Unknown',
                    'client_address': 'Unknown',
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
        finally:
            if conn:
                try:
                    conn.close()
                except:
                    pass

    async def get_table_schema(self, table_name: str) -> TableSchema:
        """Obter schema detalhado de uma tabela"""
        conn = None
        try:
            conn = fdb.connect(
                dsn=self.dsn,
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                charset=DB_CONFIG['charset']
            )
            
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
        finally:
            if conn:
                try:
                    conn.close()
                except:
                    pass

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