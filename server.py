#!/usr/bin/env python3
"""
Servidor MCP Nativo para Firebird
Implementa o protocolo MCP correto (JSON-RPC over stdio)
Versão robusta que funciona mesmo sem bibliotecas Firebird
"""

import json
import sys
import os
import asyncio
import logging
from typing import Dict, List, Any, Optional

# Configurar logging
logging.basicConfig(level=logging.WARNING, stream=sys.stderr)
logger = logging.getLogger(__name__)

def log_stderr(message: str):
    """Log para stderr - aparece no Claude Desktop"""
    print(f"[MCP-FIREBIRD] {message}", file=sys.stderr, flush=True)

log_stderr("Starting MCP Firebird Server...")

# Importar FDB (com tratamento de erro robusto)
FDB_AVAILABLE = False
try:
    import fdb
    FDB_AVAILABLE = True
    log_stderr("FDB library loaded successfully")
except Exception as e:
    log_stderr(f"WARNING: FDB import failed: {e}")
    log_stderr("MCP Server will start anyway (connection tests will fail)")

# Configuração do banco
DB_CONFIG = {
    'host': os.getenv('FIREBIRD_HOST', 'localhost'),
    'port': int(os.getenv('FIREBIRD_PORT', 3050)),
    'database': os.getenv('FIREBIRD_DATABASE', '/path/to/database.fdb'),
    'user': os.getenv('FIREBIRD_USER', 'SYSDBA'),
    'password': os.getenv('FIREBIRD_PASSWORD', 'masterkey'),
    'charset': os.getenv('FIREBIRD_CHARSET', 'UTF8')
}

log_stderr(f"Database config: {DB_CONFIG['host']}:{DB_CONFIG['port']}")

class FirebirdMCPServer:
    def __init__(self):
        self.dsn = f"{DB_CONFIG['host']}/{DB_CONFIG['port']}:{DB_CONFIG['database']}"
        log_stderr(f"DSN: {self.dsn}")
        
    def test_connection(self):
        """Testar conexão com Firebird"""
        if not FDB_AVAILABLE:
            return {
                "connected": False, 
                "error": "FDB library not available - install Firebird client libraries"
            }
        
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
            log_stderr("Connection test: SUCCESS")
            return {"connected": True, "version": version.strip()}
        except Exception as e:
            log_stderr(f"Connection test: FAILED - {e}")
            return {"connected": False, "error": str(e)}
    
    def execute_query(self, sql: str, params: Optional[List] = None):
        """Executar query SQL"""
        if not FDB_AVAILABLE:
            return {
                "success": False, 
                "error": "FDB library not available - install Firebird client libraries"
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
                conn.close()
                return {"success": True, "data": data}
            else:
                affected = cursor.rowcount
                conn.commit()
                conn.close()
                return {"success": True, "affected_rows": affected}
                
        except Exception as e:
            log_stderr(f"Query failed: {e}")
            return {"success": False, "error": str(e)}
    
    def get_tables(self):
        """Listar tabelas"""
        if not FDB_AVAILABLE:
            return []
            
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
            log_stderr(f"Get tables failed: {e}")
            return []

# Criar instância do servidor
firebird_server = FirebirdMCPServer()

class MCPServer:
    def __init__(self):
        self.capabilities = {
            "tools": {}
        }
        log_stderr("MCP Server initialized")
    
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
            "error": {
                "code": code,
                "message": message
            }
        }
        print(json.dumps(response), flush=True)
    
    def handle_initialize(self, request_id: Any, params: Dict):
        """Responder ao initialize"""
        log_stderr("Handling initialize request")
        
        result = {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {
                    "listChanged": False
                },
                "resources": {
                    "subscribe": False,
                    "listChanged": False
                }
            },
            "serverInfo": {
                "name": "firebird-mcp-server",
                "version": "1.0.0"
            }
        }
        
        self.send_response(request_id, result)
        log_stderr("Initialize response sent")
    
    def handle_resources_list(self, request_id: Any, params: Dict):
        """Listar recursos disponíveis"""
        log_stderr("Handling resources/list request")
        
        # MCP pode ter recursos (arquivos, documentos, etc.)
        # Para Firebird, vamos retornar lista vazia por enquanto
        resources = []
        
        result = {"resources": resources}
        self.send_response(request_id, result)
        log_stderr("Resources list response sent")
    
    def handle_tools_list(self, request_id: Any, params: Dict):
        """Listar ferramentas disponíveis"""
        log_stderr("Handling tools/list request")
        
        tools = [
            {
                "name": "test_connection",
                "description": "Test connection to Firebird database",
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
                        "sql": {
                            "type": "string",
                            "description": "SQL query to execute"
                        },
                        "params": {
                            "type": "array",
                            "description": "Optional parameters for the query"
                        }
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
                "name": "get_server_status",
                "description": "Get MCP server status and configuration",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]
        
        result = {"tools": tools}
        self.send_response(request_id, result)
        log_stderr("Tools list response sent")
    
    def handle_tools_call(self, request_id: Any, params: Dict):
        """Executar ferramenta"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        log_stderr(f"Handling tools/call request: {tool_name}")
        
        try:
            if tool_name == "test_connection":
                result_data = firebird_server.test_connection()
                content = [
                    {
                        "type": "text",
                        "text": f"Connection test result:\n```json\n{json.dumps(result_data, indent=2)}\n```"
                    }
                ]
            
            elif tool_name == "execute_query":
                sql = arguments.get("sql")
                params_list = arguments.get("params")
                
                if not sql:
                    raise ValueError("SQL query is required")
                
                result_data = firebird_server.execute_query(sql, params_list)
                content = [
                    {
                        "type": "text", 
                        "text": f"Query result:\n```json\n{json.dumps(result_data, indent=2)}\n```"
                    }
                ]
            
            elif tool_name == "list_tables":
                tables = firebird_server.get_tables()
                content = [
                    {
                        "type": "text",
                        "text": f"Tables in database:\n```json\n{json.dumps(tables, indent=2)}\n```"
                    }
                ]
            
            elif tool_name == "get_server_status":
                status = {
                    "fdb_available": FDB_AVAILABLE,
                    "database_config": {
                        "host": DB_CONFIG['host'],
                        "port": DB_CONFIG['port'],
                        "database": DB_CONFIG['database'],
                        "user": DB_CONFIG['user']
                    },
                    "dsn": firebird_server.dsn
                }
                content = [
                    {
                        "type": "text",
                        "text": f"Server status:\n```json\n{json.dumps(status, indent=2)}\n```"
                    }
                ]
            
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
            
            result = {
                "content": content,
                "isError": False
            }
            
            self.send_response(request_id, result)
            log_stderr(f"Tool {tool_name} executed successfully")
            
        except Exception as e:
            log_stderr(f"Tool {tool_name} failed: {e}")
            error_content = [
                {
                    "type": "text",
                    "text": f"Error executing {tool_name}: {str(e)}"
                }
            ]
            result = {
                "content": error_content,
                "isError": True
            }
            self.send_response(request_id, result)
    
    def handle_request(self, request: Dict):
        """Processar requisição JSON-RPC"""
        try:
            method = request.get("method")
            request_id = request.get("id")
            params = request.get("params", {})
            
            log_stderr(f"Received request: {method}")
            
            if method == "initialize":
                self.handle_initialize(request_id, params)
            elif method == "tools/list":
                self.handle_tools_list(request_id, params)
            elif method == "tools/call":
                self.handle_tools_call(request_id, params)
            elif method == "resources/list":
                self.handle_resources_list(request_id, params)
            elif method == "notifications/initialized":
                # Notificação - não precisa resposta
                log_stderr("Received initialized notification")
            else:
                log_stderr(f"Unknown method: {method}")
                self.send_error(request_id, -32601, f"Method not found: {method}")
                
        except Exception as e:
            log_stderr(f"Error handling request: {e}")
            self.send_error(request.get("id"), -32603, str(e))
    
    def run(self):
        """Loop principal do servidor"""
        log_stderr("MCP Server ready - waiting for requests")
        
        try:
            for line in sys.stdin:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    request = json.loads(line)
                    self.handle_request(request)
                except json.JSONDecodeError as e:
                    log_stderr(f"Invalid JSON: {e}")
                except Exception as e:
                    log_stderr(f"Error processing request: {e}")
                    
        except KeyboardInterrupt:
            log_stderr("Server interrupted")
        except Exception as e:
            log_stderr(f"Server error: {e}")
        finally:
            log_stderr("Server shutting down")

def main():
    """Função principal"""
    log_stderr("Starting MCP Firebird Native Server")
    
    # Mostrar status inicial
    if FDB_AVAILABLE:
        log_stderr("FDB library is available")
        # Testar conexão na inicialização (rápido)
        try:
            result = firebird_server.test_connection()
            if result["connected"]:
                log_stderr(f"Database connection OK - Firebird {result['version']}")
            else:
                log_stderr(f"Database connection failed: {result['error']}")
        except Exception as e:
            log_stderr(f"Initial connection test failed: {e}")
    else:
        log_stderr("FDB library not available - database functions will not work")
        log_stderr("Install Firebird client libraries to enable database access")
    
    # Iniciar servidor MCP
    server = MCPServer()
    server.run()

if __name__ == "__main__":
    main()

# Configuração do banco
DB_CONFIG = {
    'host': os.getenv('FIREBIRD_HOST', 'localhost'),
    'port': int(os.getenv('FIREBIRD_PORT', 3050)),
    'database': os.getenv('FIREBIRD_DATABASE', '/path/to/database.fdb'),
    'user': os.getenv('FIREBIRD_USER', 'SYSDBA'),
    'password': os.getenv('FIREBIRD_PASSWORD', 'masterkey'),
    'charset': os.getenv('FIREBIRD_CHARSET', 'UTF8')
}

log_stderr(f"Database config: {DB_CONFIG['host']}:{DB_CONFIG['port']}")

class FirebirdMCPServer:
    def __init__(self):
        self.dsn = f"{DB_CONFIG['host']}/{DB_CONFIG['port']}:{DB_CONFIG['database']}"
        log_stderr(f"DSN: {self.dsn}")
        
    def test_connection(self):
        """Testar conexão com Firebird"""
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
            log_stderr("Connection test: SUCCESS")
            return {"connected": True, "version": version.strip()}
        except Exception as e:
            log_stderr(f"Connection test: FAILED - {e}")
            return {"connected": False, "error": str(e)}
    
    def execute_query(self, sql: str, params: Optional[List] = None):
        """Executar query SQL"""
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
                conn.close()
                return {"success": True, "data": data}
            else:
                affected = cursor.rowcount
                conn.commit()
                conn.close()
                return {"success": True, "affected_rows": affected}
                
        except Exception as e:
            log_stderr(f"Query failed: {e}")
            return {"success": False, "error": str(e)}
    
    def get_tables(self):
        """Listar tabelas"""
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
            log_stderr(f"Get tables failed: {e}")
            return []

# Criar instância do servidor
firebird_server = FirebirdMCPServer()

class MCPServer:
    def __init__(self):
        self.capabilities = {
            "tools": {}
        }
        log_stderr("MCP Server initialized")
    
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
            "error": {
                "code": code,
                "message": message
            }
        }
        print(json.dumps(response), flush=True)
    
    def handle_initialize(self, request_id: Any, params: Dict):
        """Responder ao initialize"""
        log_stderr("Handling initialize request")
        
        result = {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {
                    "listChanged": False
                }
            },
            "serverInfo": {
                "name": "firebird-mcp-server",
                "version": "1.0.0"
            }
        }
        
        self.send_response(request_id, result)
        log_stderr("Initialize response sent")
    
    def handle_tools_list(self, request_id: Any, params: Dict):
        """Listar ferramentas disponíveis"""
        log_stderr("Handling tools/list request")
        
        tools = [
            {
                "name": "test_connection",
                "description": "Test connection to Firebird database",
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
                        "sql": {
                            "type": "string",
                            "description": "SQL query to execute"
                        },
                        "params": {
                            "type": "array",
                            "description": "Optional parameters for the query"
                        }
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
            }
        ]
        
        result = {"tools": tools}
        self.send_response(request_id, result)
        log_stderr("Tools list response sent")
    
    def handle_tools_call(self, request_id: Any, params: Dict):
        """Executar ferramenta"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        log_stderr(f"Handling tools/call request: {tool_name}")
        
        try:
            if tool_name == "test_connection":
                result_data = firebird_server.test_connection()
                content = [
                    {
                        "type": "text",
                        "text": f"Connection test result: {json.dumps(result_data, indent=2)}"
                    }
                ]
            
            elif tool_name == "execute_query":
                sql = arguments.get("sql")
                params_list = arguments.get("params")
                
                if not sql:
                    raise ValueError("SQL query is required")
                
                result_data = firebird_server.execute_query(sql, params_list)
                content = [
                    {
                        "type": "text", 
                        "text": f"Query result: {json.dumps(result_data, indent=2)}"
                    }
                ]
            
            elif tool_name == "list_tables":
                tables = firebird_server.get_tables()
                content = [
                    {
                        "type": "text",
                        "text": f"Tables in database: {json.dumps(tables, indent=2)}"
                    }
                ]
            
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
            
            result = {
                "content": content,
                "isError": False
            }
            
            self.send_response(request_id, result)
            log_stderr(f"Tool {tool_name} executed successfully")
            
        except Exception as e:
            log_stderr(f"Tool {tool_name} failed: {e}")
            error_content = [
                {
                    "type": "text",
                    "text": f"Error executing {tool_name}: {str(e)}"
                }
            ]
            result = {
                "content": error_content,
                "isError": True
            }
            self.send_response(request_id, result)
    
    def handle_request(self, request: Dict):
        """Processar requisição JSON-RPC"""
        try:
            method = request.get("method")
            request_id = request.get("id")
            params = request.get("params", {})
            
            log_stderr(f"Received request: {method}")
            
            if method == "initialize":
                self.handle_initialize(request_id, params)
            elif method == "tools/list":
                self.handle_tools_list(request_id, params)
            elif method == "tools/call":
                self.handle_tools_call(request_id, params)
            elif method == "notifications/initialized":
                # Notificação - não precisa resposta
                log_stderr("Received initialized notification")
            else:
                log_stderr(f"Unknown method: {method}")
                self.send_error(request_id, -32601, f"Method not found: {method}")
                
        except Exception as e:
            log_stderr(f"Error handling request: {e}")
            self.send_error(request.get("id"), -32603, str(e))
    
    def run(self):
        """Loop principal do servidor"""
        log_stderr("MCP Server ready - waiting for requests")
        
        try:
            for line in sys.stdin:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    request = json.loads(line)
                    self.handle_request(request)
                except json.JSONDecodeError as e:
                    log_stderr(f"Invalid JSON: {e}")
                except Exception as e:
                    log_stderr(f"Error processing request: {e}")
                    
        except KeyboardInterrupt:
            log_stderr("Server interrupted")
        except Exception as e:
            log_stderr(f"Server error: {e}")
        finally:
            log_stderr("Server shutting down")

def main():
    """Função principal"""
    log_stderr("Starting MCP Firebird Native Server")
    
    # Testar conexão na inicialização (rápido)
    try:
        result = firebird_server.test_connection()
        if result["connected"]:
            log_stderr(f"Database connection OK - Firebird {result['version']}")
        else:
            log_stderr(f"Database connection failed: {result['error']}")
    except Exception as e:
        log_stderr(f"Initial connection test failed: {e}")
    
    # Iniciar servidor MCP
    server = MCPServer()
    server.run()

if __name__ == "__main__":
    main()