#!/usr/bin/env python3
"""
MCP Server Simples para Firebird - Conexão Externa
Versão enxuta focada em conectividade com banco externo
"""

import json
import sys
import os
import logging
import ctypes.util
from typing import Dict, List, Any, Optional

# Configurar logging básico
logging.basicConfig(level=logging.WARNING, stream=sys.stderr)
logger = logging.getLogger(__name__)

def log(message: str):
    """Log simples para stderr"""
    print(f"[MCP-FIREBIRD] {message}", file=sys.stderr, flush=True)

# Importar FDB com tratamento robusto de erros
FDB_AVAILABLE = False
FDB_ERROR = None

try:
    import fdb
    FDB_AVAILABLE = True
    log("✅ FDB library loaded successfully")
    log(f"FDB version: {fdb.__version__}")
    
    # Verificar se consegue localizar as bibliotecas cliente
    try:
        import ctypes.util
        fbclient_path = ctypes.util.find_library('fbclient')
        if fbclient_path:
            log(f"✅ Firebird client library found at: {fbclient_path}")
        else:
            log("⚠️  Warning: libfbclient not found in system library path")
            log(f"LD_LIBRARY_PATH: {os.getenv('LD_LIBRARY_PATH', 'not set')}")
    except Exception as e:
        log(f"Library check failed: {e}")
        
except ImportError as e:
    FDB_AVAILABLE = False
    FDB_ERROR = str(e)
    log(f"❌ ERROR: Could not import fdb: {e}")
    log("💡 Server will start in fallback mode (database operations will fail)")
    log("To enable Firebird support:")
    log("  1. Install: apt-get install firebird3.0-client-core libfbclient2")
    log("  2. Or mount host libraries: -v /usr/lib/x86_64-linux-gnu:/usr/lib/x86_64-linux-gnu:ro")

# Configuração do banco externo
DB_CONFIG = {
    'host': os.getenv('FIREBIRD_HOST', 'localhost'),
    'port': int(os.getenv('FIREBIRD_PORT', 3050)),
    'database': os.getenv('FIREBIRD_DATABASE', '/path/to/database.fdb'),
    'user': os.getenv('FIREBIRD_USER', 'SYSDBA'),
    'password': os.getenv('FIREBIRD_PASSWORD', 'masterkey'),
    'charset': os.getenv('FIREBIRD_CHARSET', 'UTF8')
}

log(f"Connecting to: {DB_CONFIG['host']}:{DB_CONFIG['port']}")

class FirebirdMCPServer:
    def __init__(self):
        self.dsn = f"{DB_CONFIG['host']}/{DB_CONFIG['port']}:{DB_CONFIG['database']}"
        log(f"DSN: {self.dsn}")
        
    def test_connection(self):
        """Testar conexão com Firebird externo"""
        if not FDB_AVAILABLE:
            return {
                "connected": False, 
                "error": f"FDB library not available: {FDB_ERROR}",
                "solution": "Install Firebird client libraries: apt-get install firebird3.0-client-core libfbclient2"
            }
            
        try:
            log(f"Attempting connection to: {self.dsn}")
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
            log("✅ Connection successful!")
            return {"connected": True, "version": version.strip()}
        except Exception as e:
            log(f"❌ Connection failed: {e}")
            error_msg = str(e)
            
            # Diagnóstico específico para problemas comuns
            if "could not be determined" in error_msg.lower():
                error_msg += "\n\n💡 SOLUTION: Firebird client libraries not found. Try:\n"
                error_msg += "1. Install on host: apt-get install firebird3.0-client-core libfbclient2\n"
                error_msg += "2. Mount host libs: -v /usr/lib/x86_64-linux-gnu:/usr/lib/x86_64-linux-gnu:ro\n"
                error_msg += f"3. Current LD_LIBRARY_PATH: {os.getenv('LD_LIBRARY_PATH', 'not set')}"
            elif "network error" in error_msg.lower() or "connection refused" in error_msg.lower():
                error_msg += f"\n\n💡 SOLUTION: Check network connectivity to {DB_CONFIG['host']}:{DB_CONFIG['port']}"
            elif "login" in error_msg.lower() or "password" in error_msg.lower():
                error_msg += "\n\n💡 SOLUTION: Check username/password in environment variables"
            
            return {"connected": False, "error": error_msg}
    
    def execute_query(self, sql: str, params: Optional[List] = None):
        """Executar query SQL"""
        if not FDB_AVAILABLE:
            return {
                "success": False, 
                "error": f"FDB library not available: {FDB_ERROR}",
                "solution": "Install Firebird client libraries to enable database operations"
            }
            
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
            
            if sql.strip().upper().startswith('SELECT'):
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                rows = cursor.fetchall()
                data = [dict(zip(columns, row)) for row in rows]
                result = {"success": True, "data": data}
            else:
                affected = cursor.rowcount
                conn.commit()
                result = {"success": True, "affected_rows": affected}
                
            conn.close()
            return result
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_tables(self):
        """Listar tabelas"""
        if not FDB_AVAILABLE:
            return {"error": "FDB library not available"}
            
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
            return tables
        except Exception as e:
            log(f"Get tables failed: {e}")
            return {"error": str(e)}

# Instância do servidor Firebird
firebird_server = FirebirdMCPServer()

class MCPServer:
    def __init__(self):
        log("MCP Server initialized")
    
    def send_response(self, request_id: Any, result: Any):
        """Enviar resposta JSON-RPC"""
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }
        print(json.dumps(response), flush=True)
    
    def send_error(self, request_id: Any, code: int, message: str):
        """Enviar erro JSON-RPC"""
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": code, "message": message}
        }
        print(json.dumps(response), flush=True)
    
    def handle_initialize(self, request_id: Any, params: Dict):
        """Responder ao initialize"""
        result = {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {"listChanged": False}
            },
            "serverInfo": {
                "name": "firebird-mcp-server",
                "version": "1.0.0"
            }
        }
        self.send_response(request_id, result)
    
    def handle_tools_list(self, request_id: Any, params: Dict):
        """Listar ferramentas disponíveis"""
        tools = [
            {
                "name": "test_connection",
                "description": "Test connection to external Firebird database",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "execute_query",
                "description": "Execute SQL query on Firebird database",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "sql": {"type": "string", "description": "SQL query to execute"},
                        "params": {"type": "array", "description": "Optional parameters"}
                    },
                    "required": ["sql"]
                }
            },
            {
                "name": "list_tables",
                "description": "List all tables in the database",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "server_status",
                "description": "Get detailed server status and diagnostics",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]
        
        self.send_response(request_id, {"tools": tools})
    
    def handle_tools_call(self, request_id: Any, params: Dict):
        """Executar ferramenta"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        try:
            if tool_name == "test_connection":
                result_data = firebird_server.test_connection()
                content = [{
                    "type": "text",
                    "text": f"Connection test:\n```json\n{json.dumps(result_data, indent=2)}\n```"
                }]
            
            elif tool_name == "execute_query":
                sql = arguments.get("sql")
                if not sql:
                    raise ValueError("SQL query is required")
                
                params_list = arguments.get("params")
                result_data = firebird_server.execute_query(sql, params_list)
                content = [{
                    "type": "text",
                    "text": f"Query result:\n```json\n{json.dumps(result_data, indent=2)}\n```"
                }]
            
            elif tool_name == "list_tables":
                tables = firebird_server.get_tables()
                if isinstance(tables, dict) and "error" in tables:
                    # FDB não disponível ou erro
                    content = [{
                        "type": "text",
                        "text": f"Tables list failed:\n```json\n{json.dumps(tables, indent=2)}\n```"
                    }]
                else:
                    # Lista normal de tabelas
                    content = [{
                        "type": "text",
                        "text": f"Tables:\n```json\n{json.dumps(tables, indent=2)}\n```"
                    }]
            
            elif tool_name == "server_status":
                status = {
                    "fdb_available": FDB_AVAILABLE,
                    "fdb_error": FDB_ERROR if not FDB_AVAILABLE else None,
                    "database_config": {
                        "host": DB_CONFIG['host'],
                        "port": DB_CONFIG['port'],
                        "database": DB_CONFIG['database'],
                        "user": DB_CONFIG['user'],
                        "charset": DB_CONFIG['charset']
                    },
                    "dsn": firebird_server.dsn,
                    "environment": {
                        "LD_LIBRARY_PATH": os.getenv('LD_LIBRARY_PATH', 'not set'),
                        "FIREBIRD_HOME": os.getenv('FIREBIRD_HOME', 'not set')
                    },
                    "recommendations": []
                }
                
                # Adicionar recomendações baseadas no status
                if not FDB_AVAILABLE:
                    status["recommendations"].append(
                        "Install Firebird client: apt-get install firebird3.0-client-core libfbclient2"
                    )
                    status["recommendations"].append(
                        "Or mount host libraries: -v /usr/lib/x86_64-linux-gnu:/usr/lib/x86_64-linux-gnu:ro"
                    )
                
                content = [{
                    "type": "text",
                    "text": f"Server Status:\n```json\n{json.dumps(status, indent=2)}\n```"
                }]
            
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
            
            self.send_response(request_id, {
                "content": content,
                "isError": False
            })
            
        except Exception as e:
            error_content = [{
                "type": "text",
                "text": f"Error: {str(e)}"
            }]
            self.send_response(request_id, {
                "content": error_content,
                "isError": True
            })
    
    def handle_request(self, request: Dict):
        """Processar requisição JSON-RPC"""
        try:
            method = request.get("method")
            request_id = request.get("id")
            params = request.get("params", {})
            
            if method == "initialize":
                self.handle_initialize(request_id, params)
            elif method == "tools/list":
                self.handle_tools_list(request_id, params)
            elif method == "tools/call":
                self.handle_tools_call(request_id, params)
            elif method == "notifications/initialized":
                log("Received initialized notification")
            else:
                self.send_error(request_id, -32601, f"Method not found: {method}")
                
        except Exception as e:
            self.send_error(request.get("id"), -32603, str(e))
    
    def run(self):
        """Loop principal do servidor"""
        log("MCP Server ready - waiting for requests")
        
        try:
            for line in sys.stdin:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    request = json.loads(line)
                    self.handle_request(request)
                except json.JSONDecodeError as e:
                    log(f"Invalid JSON: {e}")
                except Exception as e:
                    log(f"Error processing request: {e}")
                    
        except KeyboardInterrupt:
            log("Server interrupted")
        except Exception as e:
            log(f"Server error: {e}")

def main():
    """Função principal"""
    log("🔥 MCP Firebird Server Starting...")
    log(f"📍 Host: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    log(f"🗄️  Database: {DB_CONFIG['database']}")
    log(f"👤 User: {DB_CONFIG['user']}")
    
    # Diagnóstico detalhado das bibliotecas
    log("🔍 Checking Firebird libraries...")
    if FDB_AVAILABLE:
        log("✅ FDB Python library available")
        
        # Verificar bibliotecas cliente
        try:
            import ctypes.util
            fbclient_path = ctypes.util.find_library('fbclient')
            if fbclient_path:
                log(f"✅ Firebird client found: {fbclient_path}")
            else:
                log("⚠️  Firebird client libraries not found")
                log("💡 Solutions:")
                log("  1. Install on host: apt-get install firebird3.0-client-core libfbclient2")
                log("  2. Mount host libs: -v /usr/lib/x86_64-linux-gnu:/usr/lib/x86_64-linux-gnu:ro")
                log("  3. Download manually and mount to /usr/local/lib")
        except Exception as e:
            log(f"⚠️  Could not check library paths: {e}")
        
        # Teste inicial de conexão (se bibliotecas disponíveis)
        log("🔌 Testing database connection...")
        try:
            result = firebird_server.test_connection()
            if result["connected"]:
                log(f"✅ Database connection OK - Firebird {result['version']}")
            else:
                log(f"❌ Database connection failed")
                # Mostrar apenas primeira linha do erro para não poluir o log
                error_lines = result['error'].split('\n')
                log(f"   Error: {error_lines[0]}")
                log("   (Use test_connection tool for detailed diagnosis)")
        except Exception as e:
            log(f"Connection test failed: {e}")
    else:
        log("❌ FDB Python library not available")
        log(f"   Error: {FDB_ERROR}")
        log("💡 To enable Firebird support:")
        log("   1. Install on host: apt-get install firebird3.0-client-core libfbclient2")
        log("   2. Mount libraries: -v /usr/lib/x86_64-linux-gnu:/usr/lib/x86_64-linux-gnu:ro")
    
    log("")
    log("🚀 Starting MCP server...")
    log("   (Server will work even if Firebird libraries are missing)")
    log("   (Use server_status tool to check detailed diagnostics)")
    log("")
    
    # Iniciar servidor MCP (sempre inicia, mesmo sem FDB)
    server = MCPServer()
    server.run()

if __name__ == "__main__":
    main()