"""MCP (Model Context Protocol) server implementation."""

import json
import sys
import os
from typing import Dict, Any

from ..core.config import get_server_info
from ..core.i18n import I18n

def log(message: str):
    """Log to stderr - visible in Docker/Claude Desktop"""
    print(f"[MCP-FIREBIRD] {message}", file=sys.stderr, flush=True)

class MCPServer:
    """MCP protocol server handling JSON-RPC communication."""
    
    def __init__(self, firebird_server, prompt_manager, prompt_generator, i18n: I18n):
        self.firebird_server = firebird_server
        self.prompt_manager = prompt_manager
        self.prompt_generator = prompt_generator
        self.i18n = i18n
        log(f"🚀 {self.i18n.get('server_info.initialized')}")
    
    def send_response(self, request_id: Any, result: Any):
        """Send JSON-RPC response."""
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }
        print(json.dumps(response), flush=True)
    
    def send_error(self, request_id: Any, code: int, message: str):
        """Send JSON-RPC error."""
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": code, "message": message}
        }
        print(json.dumps(response), flush=True)
    
    def handle_initialize(self, request_id: Any, params: Dict):
        """Handle MCP initialize request."""
        server_info = get_server_info()
        result = {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {"listChanged": False},
                "resources": {"subscribe": False, "listChanged": False},
                "prompts": {"listChanged": False}
            },
            "serverInfo": server_info
        }
        self.send_response(request_id, result)
    
    def handle_tools_list(self, request_id: Any, params: Dict):
        """List available tools with enhanced descriptions."""
        tools = [
            {
                "name": self.i18n.get('tools.test_connection.name'),
                "description": self.prompt_manager.get_enhanced_tool_description(
                    'test_connection',
                    self.i18n.get('tools.test_connection.description')
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "disable_expert_mode": {
                            "type": "boolean",
                            "description": "Set to true to disable automatic expert context",
                            "default": False
                        }
                    },
                    "required": []
                }
            },
            {
                "name": self.i18n.get('tools.execute_query.name'),
                "description": self.prompt_manager.get_enhanced_tool_description(
                    'execute_query',
                    self.i18n.get('tools.execute_query.description')
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "sql": {
                            "type": "string", 
                            "description": self.i18n.get('tools.execute_query.sql_description')
                        },
                        "params": {
                            "type": "array", 
                            "description": self.i18n.get('tools.execute_query.params_description')
                        },
                        "disable_expert_mode": {
                            "type": "boolean",
                            "description": "Set to true to disable automatic expert context",
                            "default": False
                        },
                        "expert_operation": {
                            "type": "string",
                            "description": "Override default operation type (select, insert, update, delete, ddl, admin)",
                            "enum": ["select", "insert", "update", "delete", "ddl", "admin"]
                        }
                    },
                    "required": ["sql"]
                }
            },
            {
                "name": self.i18n.get('tools.list_tables.name'),
                "description": self.prompt_manager.get_enhanced_tool_description(
                    'list_tables',
                    self.i18n.get('tools.list_tables.description')
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "disable_expert_mode": {
                            "type": "boolean",
                            "description": "Set to true to disable automatic expert context",
                            "default": False
                        }
                    },
                    "required": []
                }
            },
            {
                "name": self.i18n.get('tools.server_status.name'),
                "description": self.i18n.get('tools.server_status.description'),
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]
        
        self.send_response(request_id, {"tools": tools})
    
    def handle_resources_list(self, request_id: Any, params: Dict):
        """List available resources."""
        resources = []
        self.send_response(request_id, {"resources": resources})
    
    def handle_prompts_list(self, request_id: Any, params: Dict):
        """List available prompts dynamically based on database tables."""
        table_prompts = self.prompt_generator.get_available_table_prompts()
        
        prompts = []
        for table_prompt in table_prompts:
            prompts.append({
                "name": table_prompt["name"],
                "description": table_prompt["description"],
                "arguments": []
            })
        
        self.send_response(request_id, {"prompts": prompts})
    
    def handle_prompts_get(self, request_id: Any, params: Dict):
        """Get specific prompt with dynamic context."""
        try:
            prompt_name = params.get("name")
            arguments = params.get("arguments", {})
            
            prompt_text = self.prompt_generator.generate(prompt_name, arguments)
            
            result = {
                "description": f"Schema information for table: {prompt_name.replace('_schema', '')}",
                "messages": [{
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": prompt_text
                    }
                }]
            }
            
            self.send_response(request_id, result)
            
        except Exception as e:
            self.send_error(request_id, -32603, f"{self.i18n.get('table_schema.error_generating')}: {str(e)}")
    
    def handle_tools_call(self, request_id: Any, params: Dict):
        """Execute tool with automatic expert context."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        disable_expert_mode = arguments.get("disable_expert_mode", False)
        expert_operation = arguments.get("expert_operation", self.prompt_manager.config['operation_type'])
        
        try:
            if tool_name == "test_connection":
                result_data = self.firebird_server.test_connection()
                base_content = f"🔌 {self.i18n.get('connection.test_results')}:\n```json\n{json.dumps(result_data, indent=2)}\n```"
                
                enhanced_content = self.prompt_manager.apply_to_response(
                    base_content, 
                    tool_name, 
                    disabled=disable_expert_mode
                )
                
                content = [{
                    "type": "text",
                    "text": enhanced_content
                }]
            
            elif tool_name == "execute_query":
                sql = arguments.get("sql")
                if not sql:
                    raise ValueError(self.i18n.get('tools.sql_required'))
                
                params_list = arguments.get("params")
                result_data = self.firebird_server.execute_query(sql, params_list)
                
                base_content = f"📊 {self.i18n.get('tools.query_results')}:\n```json\n{json.dumps(result_data, indent=2)}\n```"
                
                if not disable_expert_mode and expert_operation:
                    original_operation = self.prompt_manager.config['operation_type']
                    self.prompt_manager.config['operation_type'] = expert_operation
                    
                    enhanced_content = self.prompt_manager.apply_to_response(
                        base_content, 
                        tool_name, 
                        disabled=False
                    )
                    
                    self.prompt_manager.config['operation_type'] = original_operation
                else:
                    enhanced_content = self.prompt_manager.apply_to_response(
                        base_content, 
                        tool_name, 
                        disabled=disable_expert_mode
                    )
                
                content = [{
                    "type": "text",
                    "text": enhanced_content
                }]
            
            elif tool_name == "list_tables":
                result = self.firebird_server.get_tables()
                base_content = f"📋 {self.i18n.get('tools.database_tables')}:\n```json\n{json.dumps(result, indent=2)}\n```"
                
                enhanced_content = self.prompt_manager.apply_to_response(
                    base_content, 
                    tool_name, 
                    disabled=disable_expert_mode
                )
                
                content = [{
                    "type": "text",
                    "text": enhanced_content
                }]
            
            elif tool_name == "server_status":
                status = self._get_server_status()
                content = [{
                    "type": "text",
                    "text": f"🔍 {self.i18n.get('tools.server_status_title')}:\n```json\n{json.dumps(status, indent=2)}\n```"
                }]
            
            else:
                raise ValueError(f"{self.i18n.get('tools.unknown_tool')}: {tool_name}")
            
            self.send_response(request_id, {
                "content": content,
                "isError": False
            })
            
        except Exception as e:
            error_content = [{
                "type": "text",
                "text": f"❌ {self.i18n.get('tools.error_executing')} {tool_name}: {str(e)}"
            }]
            self.send_response(request_id, {
                "content": error_content,
                "isError": True
            })
    
    def _get_server_status(self) -> Dict:
        """Get comprehensive server status."""
        connection_test = None
        if self.firebird_server.fdb_available and self.firebird_server.client_available:
            try:
                connection_test = self.firebird_server.test_connection()
            except:
                connection_test = {"error": "Connection test failed"}
        
        server_info = get_server_info()
        
        status = {
            "server_info": {
                "name": server_info["name"],
                "version": server_info["version"],
                "python_version": sys.version
            },
            "internationalization": {
                "current_language": self.i18n.language,
                "fallback_language": self.i18n.fallback_language,
                "available_languages": self.i18n.get_available_languages(),
                "completeness": self.i18n.validate_completeness(),
                "missing_keys_count": len(self.i18n.missing_keys),
                "has_fallback_loaded": bool(self.i18n.fallback_strings)
            },
            "default_prompt_system": self.prompt_manager.get_status(),
            "fdb_python_library": {
                "available": self.firebird_server.fdb_available,
                "version": self.firebird_server.fdb.__version__ if self.firebird_server.fdb_available else None,
                "error": getattr(self.firebird_server, 'fdb_error', None) if not self.firebird_server.fdb_available else None
            },
            "firebird_client_libraries": {
                "available": self.firebird_server.client_available,
                "path": self.firebird_server.client_path,
                "status": "✅ Found" if self.firebird_server.client_available else "❌ Not found"
            },
            "database_config": {
                "dsn": self.firebird_server.dsn
            },
            "connection_test": connection_test,
            "environment": {
                "LD_LIBRARY_PATH": os.getenv('LD_LIBRARY_PATH', 'not set'),
                "FIREBIRD_HOME": os.getenv('FIREBIRD_HOME', 'not set'),
                "PATH": os.getenv('PATH', 'not set')
            },
            "features": {
                "sql_pattern_analysis": True,
                "enhanced_error_diagnostics": True,
                "multilingual_support": True,
                "expert_prompt_integration": True,
                "dynamic_prompt_generation": True
            },
            "recommendations": []
        }
        
        if not self.firebird_server.fdb_available:
            status["recommendations"].append("Install FDB: pip install fdb==2.0.2")
        
        if not self.firebird_server.client_available:
            status["recommendations"].extend([
                "Check if /opt/firebird/lib/libfbclient.so exists",
                "Verify LD_LIBRARY_PATH includes Firebird library directory",
                "Rebuild container if libraries are missing"
            ])
        
        # Add dynamic prompts information
        table_prompts = self.prompt_generator.get_available_table_prompts()
        status["dynamic_prompts"] = {
            "available_table_schemas": len(table_prompts),
            "tables": [prompt["title"] for prompt in table_prompts[:10]]  # Show first 10
        }
        
        return status
    
    def handle_request(self, request: Dict):
        """Process JSON-RPC request."""
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
            elif method == "resources/list":
                self.handle_resources_list(request_id, params)
            elif method == "prompts/list":
                self.handle_prompts_list(request_id, params)
            elif method == "prompts/get":
                self.handle_prompts_get(request_id, params)
            elif method == "notifications/initialized":
                log(f"📨 {self.i18n.get('errors.notification_received')}")
            else:
                self.send_error(request_id, -32601, f"{self.i18n.get('errors.method_not_found')}: {method}")
                
        except Exception as e:
            log(f"❌ {self.i18n.get('server_info.error_handling')}: {e}")
            self.send_error(request.get("id"), -32603, str(e))
    
    def run(self):
        """Main server loop."""
        log(f"👂 {self.i18n.get('server_info.waiting')}")
        
        try:
            for line in sys.stdin:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    request = json.loads(line)
                    self.handle_request(request)
                except json.JSONDecodeError as e:
                    log(f"❌ {self.i18n.get('server_info.invalid_json')}: {e}")
                except Exception as e:
                    log(f"❌ {self.i18n.get('server_info.error_processing')}: {e}")
                    
        except KeyboardInterrupt:
            log(f"🛑 {self.i18n.get('server_info.interrupted')}")
        except Exception as e:
            log(f"❌ {self.i18n.get('server_info.server_error')}: {e}")
        finally:
            log(f"🔚 {self.i18n.get('server_info.shutting_down')}")
