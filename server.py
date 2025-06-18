#!/usr/bin/env python3
"""
MCP Server Robusto para Firebird - Conexão Externa
Versão que detecta bibliotecas em runtime e oferece soluções
Funciona mesmo se a instalação automática falhar
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

# Importar FDB com detecção robusta
FDB_AVAILABLE = False
FDB_ERROR = None
FIREBIRD_CLIENT_AVAILABLE = False

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
            FIREBIRD_CLIENT_AVAILABLE = True
            log(f"✅ Firebird client library found at: {fbclient_path}")
        else:
            log("⚠️  Firebird client libraries not found in standard paths")
            log(f"LD_LIBRARY_PATH: {os.getenv('LD_LIBRARY_PATH', 'not set')}")
            # Tentar caminhos alternativos
            possible_paths = [
                "/usr/lib/libfbclient.so.2",
                "/usr/lib/firebird/3.0/libfbclient.so.2.5.9",
                "/usr/lib/x86_64-linux-gnu/libfbclient.so.2"
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    FIREBIRD_CLIENT_AVAILABLE = True
                    log(f"✅ Found Firebird client at: {path}")
                    break
            
            if not FIREBIRD_CLIENT_AVAILABLE:
                log("❌ No Firebird client libraries found")
                
    except Exception as e:
        log(f"Library check failed: {e}")
        
except ImportError as e:
    FDB_AVAILABLE = False
    FDB_ERROR = str(e)
    log(f"❌ Could not import fdb: {e}")
    log("💡 FDB library not available - database operations will show instructions")

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
                "solution": "pip install fdb==2.0.2 (this should be installed in the container)"
            }
            
        if not FIREBIRD_CLIENT_AVAILABLE:
            return {
                "connected": False,
                "error": "Firebird client libraries not found",
                "solution": "Install Firebird client libraries. Options:\n" +
                           "1. Host install: apt-get install firebird3.0-client-core libfbclient2\n" +
                           "2. Mount host libs: -v /usr/lib/x86_64-linux-gnu:/usr/lib/x86_64-linux-gnu:ro\n" +
                           "3. Container should have auto-installed them - try rebuilding image"
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
                error_msg += "\n\n💡 FIREBIRD CLIENT ISSUE: Client libraries not properly configured"
                error_msg += "\n• Try: docker run -v /usr/lib/x86_64-linux-gnu:/usr/lib/x86_64-linux-gnu:ro ..."
                error_msg += "\n• Or install on host: apt-get install firebird3.0-client-core libfbclient2"
            elif "network error" in error_msg.lower() or "connection refused" in error_msg.lower():
                error_msg += f"\n\n💡 NETWORK ISSUE: Cannot reach {DB_CONFIG['host']}:{DB_CONFIG['port']}"
                error_msg += "\n• Check if Firebird server is running"
                error_msg += "\n• Check firewall rules"
                error_msg += "\n• Verify host and port are correct"
            elif "login" in error_msg.lower() or "password" in error_msg.lower() or "authentication" in error_msg.lower():
                error_msg += "\n\n💡 AUTHENTICATION ISSUE: Invalid credentials"
                error_msg += f"\n• Check username: {DB_CONFIG['user']}"
                error_msg += "\n• Check password in FIREBIRD_PASSWORD"
                error_msg += "\n• Verify user exists in Firebird security database"
            elif "database" in error_msg.lower() and "not found" in error_msg.lower():
                error_msg += f"\n\n💡 DATABASE ISSUE: Database file not found"
                error_msg += f"\n• Check database path: {DB_CONFIG['database']}"
                error_msg += "\n• Verify database file exists on Firebird server"
                error_msg += "\n• Check file permissions"
            
            return {"connected": False, "error": error_msg}
    
    def execute_query(self, sql: str, params: Optional[List] = None):
        """Executar query SQL"""
        if not FDB_AVAILABLE:
            return {
                "success": False,
                "error": f"FDB library not available: {FDB_ERROR}",
                "solution": "FDB Python library not installed - this should be available in the container"
            }
            
        if not FIREBIRD_CLIENT_AVAILABLE:
            return {
                "success": False,
                "error": "Firebird client libraries not available",
                "solution": "Install client libraries:\n" +
                           "1. Host: apt-get install firebird3.0-client-core libfbclient2\n" +
                           "2. Mount: -v /usr/lib/x86_64-linux-gnu:/usr/lib/x86_64-linux-gnu:ro"
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
                result = {"success": True, "data": data, "row_count": len(data)}
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
            return {
                "success": False,
                "error": "FDB library not available",
                "solution": "FDB Python library not installed"
            }
            
        if not FIREBIRD_CLIENT_AVAILABLE:
            return {
                "success": False,
                "error": "Firebird client libraries not available",
                "solution": "Install Firebird client libraries on host or mount them"
            }
            
        try:
            conn = fdb.connect(
                dsn=self.dsn,
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                charset=DB_CONFIG['charset']
            )
            cursor = conn.cursor()
            cursor.execute("""
                SELECT TRIM(RDB$RELATION_NAME) as TABLE_NAME
                FROM RDB$RELATIONS 
                WHERE RDB$VIEW_BLR IS NULL 
                AND (RDB$SYSTEM_FLAG IS NULL OR RDB$SYSTEM_FLAG = 0)
                ORDER BY RDB$RELATION_NAME
            """)
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()
            return {"success": True, "tables": tables, "count": len(tables)}
        except Exception as e:
            log(f"Get tables failed: {e}")
            return {"success": False, "error": str(e)}

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
                "description": "Test connection to external Firebird database and show detailed diagnostics",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "execute_query",
                "description": "Execute SQL query on external Firebird database (SELECT, INSERT, UPDATE, DELETE)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "sql": {"type": "string", "description": "SQL query to execute"},
                        "params": {"type": "array", "description": "Optional parameters for parameterized queries"}
                    },
                    "required": ["sql"]
                }
            },
            {
                "name": "list_tables",
                "description": "List all user tables in the external Firebird database",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "server_status",
                "description": "Get complete server status, library information, and connection diagnostics",
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
                result = firebird_server.get_tables()
                content = [{
                    "type": "text",
                    "text": f"Tables result:\n```json\n{json.dumps(result, indent=2)}\n```"
                }]
            
            elif tool_name == "server_status":
                # Verificar status da conexão atual se possível
                connection_test = None
                if FDB_AVAILABLE and FIREBIRD_CLIENT_AVAILABLE:
                    connection_test = firebird_server.test_connection()
                
                status = {
                    "fdb_python_library": {
                        "available": FDB_AVAILABLE,
                        "version": fdb.__version__ if FDB_AVAILABLE else None,
                        "error": FDB_ERROR if not FDB_AVAILABLE else None
                    },
                    "firebird_client_libraries": {
                        "available": FIREBIRD_CLIENT_AVAILABLE,
                        "path": None,
                        "status": "✅ Found" if FIREBIRD_CLIENT_AVAILABLE else "❌ Not found"
                    },
                    "database_config": {
                        "host": DB_CONFIG['host'],
                        "port": DB_CONFIG['port'],
                        "database": DB_CONFIG['database'],
                        "user": DB_CONFIG['user'],
                        "charset": DB_CONFIG['charset']
                    },
                    "dsn": firebird_server.dsn,
                    "connection_test": connection_test,
                    "environment": {
                        "LD_LIBRARY_PATH": os.getenv('LD_LIBRARY_PATH', 'not set')
                    },
                    "recommendations": []
                }
                
                # Verificar localização da biblioteca cliente
                if FDB_AVAILABLE:
                    try:
                        import ctypes.util
                        fbclient_path = ctypes.util.find_library('fbclient')
                        status["firebird_client_libraries"]["path"] = fbclient_path
                    except:
                        status["firebird_client_libraries"]["path"] = "Could not check"
                
                # Adicionar recomendações baseadas no status
                if not FDB_AVAILABLE:
                    status["recommendations"].append("Install FDB: pip install fdb==2.0.2")
                
                if not FIREBIRD_CLIENT_AVAILABLE:
                    status["recommendations"].extend([
                        "Install on host: apt-get install firebird3.0-client-core libfbclient2",
                        "Mount host libs: -v /usr/lib/x86_64-linux-gnu:/usr/lib/x86_64-linux-gnu:ro",
                        "Or rebuild container - auto-install may have failed"
                    ])
                
                content = [{
                    "type": "text",
                    "text": f"Complete Server Status:\n```json\n{json.dumps(status, indent=2)}\n```"
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
    
    # Status das bibliotecas
    log("🔍 Checking Firebird components...")
    
    if FDB_AVAILABLE:
        log("✅ FDB Python library: Available")
    else:
        log("❌ FDB Python library: Not available")
        log(f"   Error: {FDB_ERROR}")
    
    if FIREBIRD_CLIENT_AVAILABLE:
        log("✅ Firebird client libraries: Available")
        try:
            import ctypes.util
            fbclient_path = ctypes.util.find_library('fbclient')
            if fbclient_path:
                log(f"📚 Client library location: {fbclient_path}")
        except:
            pass
    else:
        log("❌ Firebird client libraries: Not found")
        log("💡 Solutions:")
        log("  1. Install on host: apt-get install firebird3.0-client-core libfbclient2")
        log("  2. Mount host libs: -v /usr/lib/x86_64-linux-gnu:/usr/lib/x86_64-linux-gnu:ro")
        log("  3. Rebuild container (auto-install may have failed)")
    
    # Teste de conexão apenas se ambos estiverem disponíveis
    if FDB_AVAILABLE and FIREBIRD_CLIENT_AVAILABLE:
        log("🔌 Testing database connection...")
        try:
            result = firebird_server.test_connection()
            if result["connected"]:
                log(f"✅ Database connection OK - Firebird {result['version']}")
                log("🎯 Ready to execute SQL queries on external Firebird database")
            else:
                log("❌ Database connection failed")
                # Mostrar apenas primeira linha do erro
                error_lines = result['error'].split('\n')
                log(f"   Error: {error_lines[0]}")
                log("💡 Use test_connection tool for detailed diagnosis")
        except Exception as e:
            log(f"Connection test failed: {e}")
    else:
        log("⚠️  Skipping connection test - missing required libraries")
        log("   Use server_status tool to see detailed diagnostics")
    
    log("")
    log("🚀 Starting MCP server...")
    log("📋 Available tools: test_connection, execute_query, list_tables, server_status")
    
    if FDB_AVAILABLE and FIREBIRD_CLIENT_AVAILABLE:
        log("🔗 Ready to handle MCP requests for external Firebird database")
    else:
        log("⚠️  Limited functionality - missing Firebird components")
        log("   Tools will show installation instructions")
    
    log("")
    
    # Iniciar servidor MCP (sempre inicia)
    server = MCPServer()
    server.run()

if __name__ == "__main__":
    main()