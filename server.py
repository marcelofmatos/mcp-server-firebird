#!/usr/bin/env python3
"""
MCP Server Definitivo para Firebird - Conexão Externa
Versão completa e robusta para conectar a bancos Firebird externos
Detecta bibliotecas em runtime e oferece diagnósticos detalhados
"""

import json
import sys
import os
import logging
import ctypes.util
from typing import Dict, List, Any, Optional

# Configurar logging
logging.basicConfig(level=logging.WARNING, stream=sys.stderr)
logger = logging.getLogger(__name__)

def log(message: str):
    """Log para stderr - visível no Docker/Claude Desktop"""
    print(f"[MCP-FIREBIRD] {message}", file=sys.stderr, flush=True)

# ==========================================
# DETECÇÃO DE BIBLIOTECAS FIREBIRD
# ==========================================

# Variáveis de estado global
FDB_AVAILABLE = False
FDB_ERROR = None
FIREBIRD_CLIENT_AVAILABLE = False
CLIENT_LIBRARY_PATH = None

# Importar FDB com detecção robusta
try:
    import fdb
    FDB_AVAILABLE = True
    log("✅ FDB Python library loaded successfully")
    log(f"📦 FDB version: {fdb.__version__}")
    
    # Verificar se consegue localizar as bibliotecas cliente
    try:
        fbclient_path = ctypes.util.find_library('fbclient')
        if fbclient_path:
            FIREBIRD_CLIENT_AVAILABLE = True
            CLIENT_LIBRARY_PATH = fbclient_path
            log(f"✅ Firebird client library found: {fbclient_path}")
        else:
            log("⚠️  Firebird client libraries not found in standard paths")
            log(f"🔍 LD_LIBRARY_PATH: {os.getenv('LD_LIBRARY_PATH', 'not set')}")
            
            # Procurar em caminhos alternativos
            possible_paths = [
                "/opt/firebird/lib/libfbclient.so",
                "/opt/firebird/lib/libfbclient.so.2",
                "/usr/lib/libfbclient.so.2",
                "/usr/lib/libfbclient.so",
                "/usr/lib/x86_64-linux-gnu/libfbclient.so.2",
                "/usr/lib/x86_64-linux-gnu/libfbclient.so"
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    FIREBIRD_CLIENT_AVAILABLE = True
                    CLIENT_LIBRARY_PATH = path
                    log(f"✅ Found Firebird client at alternative path: {path}")
                    break
            
            if not FIREBIRD_CLIENT_AVAILABLE:
                log("❌ No Firebird client libraries found in any standard location")
                
    except Exception as e:
        log(f"⚠️  Library path check failed: {e}")
        
except ImportError as e:
    FDB_AVAILABLE = False
    FDB_ERROR = str(e)
    log(f"❌ Could not import FDB: {e}")
    log("💡 FDB Python library not available")

# ==========================================
# CONFIGURAÇÃO DO BANCO
# ==========================================

DB_CONFIG = {
    'host': os.getenv('FIREBIRD_HOST', 'localhost'),
    'port': int(os.getenv('FIREBIRD_PORT', 3050)),
    'database': os.getenv('FIREBIRD_DATABASE', '/path/to/database.fdb'),
    'user': os.getenv('FIREBIRD_USER', 'SYSDBA'),
    'password': os.getenv('FIREBIRD_PASSWORD', 'masterkey'),
    'charset': os.getenv('FIREBIRD_CHARSET', 'UTF8')
}

log(f"📍 Target database: {DB_CONFIG['host']}:{DB_CONFIG['port']}")

# ==========================================
# CLASSE FIREBIRD MCP SERVER
# ==========================================

class FirebirdMCPServer:
    def __init__(self):
        self.dsn = f"{DB_CONFIG['host']}/{DB_CONFIG['port']}:{DB_CONFIG['database']}"
        log(f"🔗 DSN configured: {self.dsn}")
        
    def test_connection(self):
        """Testar conexão com Firebird externo com diagnósticos detalhados"""
        if not FDB_AVAILABLE:
            return {
                "connected": False,
                "error": f"FDB library not available: {FDB_ERROR}",
                "solution": "FDB Python library not installed - should be available in container",
                "type": "fdb_library_error"
            }
            
        if not FIREBIRD_CLIENT_AVAILABLE:
            return {
                "connected": False,
                "error": "Firebird client libraries not found",
                "solution": (
                    "Firebird client libraries missing. This container should have them installed.\n"
                    "• Check if container build completed successfully\n"
                    "• Verify /opt/firebird/lib/ contains libfbclient.so\n"
                    "• Check LD_LIBRARY_PATH configuration"
                ),
                "type": "client_library_error",
                "library_path": CLIENT_LIBRARY_PATH,
                "ld_library_path": os.getenv('LD_LIBRARY_PATH')
            }
            
        try:
            log(f"🔌 Attempting connection to: {self.dsn}")
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
            
            return {
                "connected": True,
                "version": version.strip(),
                "dsn": self.dsn,
                "user": DB_CONFIG['user'],
                "charset": DB_CONFIG['charset']
            }
            
        except Exception as e:
            log(f"❌ Connection failed: {e}")
            error_msg = str(e)
            error_type = "unknown_error"
            
            # Diagnóstico específico baseado no tipo de erro
            if "could not be determined" in error_msg.lower():
                error_type = "client_library_error"
                error_msg += "\n\n💡 FIREBIRD CLIENT ISSUE: Client libraries not properly configured"
                error_msg += "\n• The container should have Firebird client libraries installed"
                error_msg += "\n• Check if /opt/firebird/lib/libfbclient.so exists"
                error_msg += "\n• Verify LD_LIBRARY_PATH includes Firebird lib directory"
                
            elif "libtommath" in error_msg.lower() or "libtomcrypt" in error_msg.lower():
                error_type = "dependency_error"
                error_msg += "\n\n💡 DEPENDENCY ISSUE: Missing required Firebird dependencies"
                error_msg += "\n• libtommath.so.0 or libtomcrypt.so.0 not found"
                error_msg += "\n• This indicates the Firebird installation is incomplete"
                error_msg += "\n• The container build may have failed during dependency installation"
                
            elif "network error" in error_msg.lower() or "connection refused" in error_msg.lower():
                error_type = "network_error"
                error_msg += f"\n\n💡 NETWORK ISSUE: Cannot reach {DB_CONFIG['host']}:{DB_CONFIG['port']}"
                error_msg += "\n• Check if Firebird server is running and accessible"
                error_msg += "\n• Verify firewall rules allow connections"
                error_msg += "\n• Confirm host and port are correct"
                
            elif "login" in error_msg.lower() or "password" in error_msg.lower() or "authentication" in error_msg.lower():
                error_type = "authentication_error"
                error_msg += "\n\n💡 AUTHENTICATION ISSUE: Invalid credentials"
                error_msg += f"\n• Check username: {DB_CONFIG['user']}"
                error_msg += "\n• Verify password in FIREBIRD_PASSWORD environment variable"
                error_msg += "\n• Ensure user exists in Firebird security database"
                
            elif "database" in error_msg.lower() and "not found" in error_msg.lower():
                error_type = "database_error"
                error_msg += f"\n\n💡 DATABASE ISSUE: Database file not found"
                error_msg += f"\n• Check database path: {DB_CONFIG['database']}"
                error_msg += "\n• Verify database file exists on Firebird server"
                error_msg += "\n• Check file permissions on server"
            
            return {
                "connected": False,
                "error": error_msg,
                "type": error_type,
                "dsn": self.dsn,
                "config": DB_CONFIG
            }
    
    def execute_query(self, sql: str, params: Optional[List] = None):
        """Executar query SQL com tratamento de erros robusto"""
        if not FDB_AVAILABLE:
            return {
                "success": False,
                "error": f"FDB library not available: {FDB_ERROR}",
                "solution": "FDB Python library not installed in container",
                "type": "fdb_library_error"
            }
            
        if not FIREBIRD_CLIENT_AVAILABLE:
            return {
                "success": False,
                "error": "Firebird client libraries not available",
                "solution": "Firebird client libraries missing from container",
                "type": "client_library_error"
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
                result = {
                    "success": True,
                    "data": data,
                    "row_count": len(data),
                    "columns": columns,
                    "sql": sql
                }
            else:
                affected = cursor.rowcount
                conn.commit()
                result = {
                    "success": True,
                    "affected_rows": affected,
                    "sql": sql
                }
                
            conn.close()
            return result
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "sql": sql,
                "params": params
            }
    
    def get_tables(self):
        """Listar tabelas do banco"""
        if not FDB_AVAILABLE:
            return {
                "success": False,
                "error": "FDB library not available",
                "solution": "FDB Python library not installed",
                "type": "fdb_library_error"
            }
            
        if not FIREBIRD_CLIENT_AVAILABLE:
            return {
                "success": False,
                "error": "Firebird client libraries not available",
                "solution": "Firebird client libraries missing from container",
                "type": "client_library_error"
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
            
            return {
                "success": True,
                "tables": tables,
                "count": len(tables),
                "database": DB_CONFIG['database']
            }
            
        except Exception as e:
            log(f"❌ Get tables failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "database": DB_CONFIG['database']
            }

# Instância do servidor Firebird
firebird_server = FirebirdMCPServer()

# ==========================================
# SERVIDOR MCP
# ==========================================

class MCPServer:
    def __init__(self):
        log("🚀 MCP Server initialized")
    
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
                "name": os.getenv("MCP_SERVER_NAME", "firebird-mcp-server"),
                "version": os.getenv("MCP_SERVER_VERSION", "1.0.0")
            }
        }
        self.send_response(request_id, result)
    
    def handle_tools_list(self, request_id: Any, params: Dict):
        """Listar ferramentas disponíveis"""
        tools = [
            {
                "name": "test_connection",
                "description": "Test connection to external Firebird database with detailed diagnostics",
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
                        "sql": {
                            "type": "string", 
                            "description": "SQL query to execute"
                        },
                        "params": {
                            "type": "array", 
                            "description": "Optional parameters for parameterized queries"
                        }
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
                    "text": f"🔌 Connection Test Results:\n```json\n{json.dumps(result_data, indent=2)}\n```"
                }]
            
            elif tool_name == "execute_query":
                sql = arguments.get("sql")
                if not sql:
                    raise ValueError("SQL query is required")
                
                params_list = arguments.get("params")
                result_data = firebird_server.execute_query(sql, params_list)
                content = [{
                    "type": "text",
                    "text": f"📊 Query Results:\n```json\n{json.dumps(result_data, indent=2)}\n```"
                }]
            
            elif tool_name == "list_tables":
                result = firebird_server.get_tables()
                content = [{
                    "type": "text",
                    "text": f"📋 Database Tables:\n```json\n{json.dumps(result, indent=2)}\n```"
                }]
            
            elif tool_name == "server_status":
                # Verificar status da conexão se possível
                connection_test = None
                if FDB_AVAILABLE and FIREBIRD_CLIENT_AVAILABLE:
                    try:
                        connection_test = firebird_server.test_connection()
                    except:
                        connection_test = {"error": "Connection test failed"}
                
                status = {
                    "server_info": {
                        "name": os.getenv("MCP_SERVER_NAME", "firebird-mcp-server"),
                        "version": os.getenv("MCP_SERVER_VERSION", "1.0.0"),
                        "python_version": sys.version
                    },
                    "fdb_python_library": {
                        "available": FDB_AVAILABLE,
                        "version": fdb.__version__ if FDB_AVAILABLE else None,
                        "error": FDB_ERROR if not FDB_AVAILABLE else None
                    },
                    "firebird_client_libraries": {
                        "available": FIREBIRD_CLIENT_AVAILABLE,
                        "path": CLIENT_LIBRARY_PATH,
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
                        "LD_LIBRARY_PATH": os.getenv('LD_LIBRARY_PATH', 'not set'),
                        "FIREBIRD_HOME": os.getenv('FIREBIRD_HOME', 'not set'),
                        "PATH": os.getenv('PATH', 'not set')
                    },
                    "recommendations": []
                }
                
                # Adicionar recomendações baseadas no status
                if not FDB_AVAILABLE:
                    status["recommendations"].append("Install FDB: pip install fdb==2.0.2")
                
                if not FIREBIRD_CLIENT_AVAILABLE:
                    status["recommendations"].extend([
                        "Check if /opt/firebird/lib/libfbclient.so exists",
                        "Verify LD_LIBRARY_PATH includes Firebird library directory",
                        "Rebuild container if libraries are missing"
                    ])
                
                content = [{
                    "type": "text",
                    "text": f"🔍 Complete Server Status:\n```json\n{json.dumps(status, indent=2)}\n```"
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
                "text": f"❌ Error executing {tool_name}: {str(e)}"
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
                log("📨 Received initialized notification")
            else:
                self.send_error(request_id, -32601, f"Method not found: {method}")
                
        except Exception as e:
            log(f"❌ Error handling request: {e}")
            self.send_error(request.get("id"), -32603, str(e))
    
    def run(self):
        """Loop principal do servidor"""
        log("👂 MCP Server ready - waiting for requests")
        
        try:
            for line in sys.stdin:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    request = json.loads(line)
                    self.handle_request(request)
                except json.JSONDecodeError as e:
                    log(f"❌ Invalid JSON: {e}")
                except Exception as e:
                    log(f"❌ Error processing request: {e}")
                    
        except KeyboardInterrupt:
            log("🛑 Server interrupted")
        except Exception as e:
            log(f"❌ Server error: {e}")
        finally:
            log("🔚 Server shutting down")

# ==========================================
# FUNÇÃO PRINCIPAL
# ==========================================

def main():
    """Função principal com diagnósticos completos"""
    log("🔥 === MCP FIREBIRD SERVER STARTING ===")
    log(f"📍 Target Host: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    log(f"🗄️  Target Database: {DB_CONFIG['database']}")
    log(f"👤 User: {DB_CONFIG['user']}")
    log(f"🌐 Charset: {DB_CONFIG['charset']}")
    
    # Status das bibliotecas
    log("🔍 === CHECKING FIREBIRD COMPONENTS ===")
    
    if FDB_AVAILABLE:
        log("✅ FDB Python library: Available")
        log(f"📦 FDB version: {fdb.__version__}")
    else:
        log("❌ FDB Python library: Not available")
        log(f"   ⚠️  Error: {FDB_ERROR}")
    
    if FIREBIRD_CLIENT_AVAILABLE:
        log("✅ Firebird client libraries: Available")
        log(f"📚 Client library location: {CLIENT_LIBRARY_PATH}")
    else:
        log("❌ Firebird client libraries: Not found")
        log("💡 Expected locations:")
        log("   • /opt/firebird/lib/libfbclient.so")
        log("   • /usr/lib/libfbclient.so.2")
        log("   • /usr/lib/x86_64-linux-gnu/libfbclient.so.2")
    
    # Informações do ambiente
    log("🌍 === ENVIRONMENT INFO ===")
    log(f"🔗 LD_LIBRARY_PATH: {os.getenv('LD_LIBRARY_PATH', 'not set')}")
    log(f"🏠 FIREBIRD_HOME: {os.getenv('FIREBIRD_HOME', 'not set')}")
    
    # Teste de conexão apenas se componentes estiverem disponíveis
    if FDB_AVAILABLE and FIREBIRD_CLIENT_AVAILABLE:
        log("🔌 === TESTING DATABASE CONNECTION ===")
        try:
            result = firebird_server.test_connection()
            if result["connected"]:
                log(f"✅ Database connection successful!")
                log(f"🔥 Firebird version: {result['version']}")
                log("🎯 Ready to execute SQL queries on external Firebird database")
            else:
                log("❌ Database connection failed")
                log(f"   ⚠️  Error type: {result.get('type', 'unknown')}")
                error_lines = result['error'].split('\n')
                log(f"   📝 Error: {error_lines[0]}")
                log("💡 Use test_connection tool for detailed diagnosis")
        except Exception as e:
            log(f"❌ Connection test failed: {e}")
    else:
        log("⚠️  === SKIPPING CONNECTION TEST ===")
        log("   Missing required libraries - use server_status tool for diagnostics")
    
    log("")
    log("🚀 === STARTING MCP SERVER ===")
    log("📋 Available tools:")
    log("   • test_connection - Test database connection with diagnostics")
    log("   • execute_query - Execute SQL queries (SELECT/INSERT/UPDATE/DELETE)")
    log("   • list_tables - List all tables in database")
    log("   • server_status - Complete server and library status")
    
    if FDB_AVAILABLE and FIREBIRD_CLIENT_AVAILABLE:
        log("🔗 Ready to handle MCP requests for external Firebird database")
    else:
        log("⚠️  Limited functionality - missing Firebird components")
        log("   Tools will show installation/configuration instructions")
    
    log("🔥 === MCP SERVER READY ===")
    log("")
    
    # Iniciar servidor MCP
    server = MCPServer()
    server.run()

if __name__ == "__main__":
    main()