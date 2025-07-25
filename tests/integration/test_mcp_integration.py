"""Integration tests for the complete MCP Server system."""

import pytest
import sys
import os
import json
from unittest.mock import Mock, patch

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from mcp.server import MCPServer
from firebird.server import FirebirdMCPServer
from prompts.manager import DefaultPromptManager
from prompts.generator import PromptGenerator
from core.i18n import I18n


class TestMCPServerIntegration:
    """Integration tests for the complete MCP Server system."""
    
    def setup_method(self):
        """Set up test fixtures with mocked components."""
        # Mock Firebird server (no real DB connection)
        self.mock_firebird_server = Mock(spec=FirebirdMCPServer)
        self.mock_firebird_server.fdb_available = True
        self.mock_firebird_server.client_available = True
        self.mock_firebird_server.client_path = "/opt/firebird/lib/libfbclient.so"
        self.mock_firebird_server.dsn = "localhost/3050:test.fdb"
        
        # Set up prompt system
        self.prompt_manager = DefaultPromptManager()
        self.prompt_generator = PromptGenerator()
        
        # Set up i18n
        self.i18n = I18n('en_US')
        
        # Create MCP server
        self.mcp_server = MCPServer(
            firebird_server=self.mock_firebird_server,
            prompt_manager=self.prompt_manager,
            prompt_generator=self.prompt_generator,
            i18n=self.i18n
        )
    
    def test_mcp_server_initialization(self):
        """Test proper initialization of MCP server with all components."""
        assert self.mcp_server.firebird_server == self.mock_firebird_server
        assert self.mcp_server.prompt_manager == self.prompt_manager
        assert self.mcp_server.prompt_generator == self.prompt_generator
        assert self.mcp_server.i18n == self.i18n
    
    def test_initialize_request_handling(self):
        """Test MCP initialize request handling."""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {}
        }
        
        with patch('builtins.print') as mock_print:
            self.mcp_server.handle_request(request)
            
            # Check that response was printed
            mock_print.assert_called()
            response_str = mock_print.call_args[0][0]
            response = json.loads(response_str)
            
            assert response['jsonrpc'] == "2.0"
            assert response['id'] == 1
            assert 'result' in response
            assert response['result']['protocolVersion'] == "2024-11-05"
            assert 'capabilities' in response['result']
            assert 'serverInfo' in response['result']
    
    def test_tools_list_request_handling(self):
        """Test tools/list request handling."""
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        with patch('builtins.print') as mock_print:
            self.mcp_server.handle_request(request)
            
            response_str = mock_print.call_args[0][0]
            response = json.loads(response_str)
            
            assert response['id'] == 2
            assert 'tools' in response['result']
            tools = response['result']['tools']
            
            # Check that all expected tools are present
            tool_names = [tool['name'] for tool in tools]
            assert 'test_connection' in tool_names
            assert 'execute_query' in tool_names
            assert 'list_tables' in tool_names
            assert 'server_status' in tool_names
    
    def test_prompts_list_request_handling(self):
        """Test prompts/list request handling."""
        request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "prompts/list",
            "params": {}
        }
        
        with patch('builtins.print') as mock_print:
            self.mcp_server.handle_request(request)
            
            response_str = mock_print.call_args[0][0]
            response = json.loads(response_str)
            
            assert response['id'] == 3
            assert 'prompts' in response['result']
            prompts = response['result']['prompts']
            
            # Check that all expected prompts are present
            prompt_names = [prompt['name'] for prompt in prompts]
            assert 'firebird_expert' in prompt_names
            assert 'firebird_performance' in prompt_names
            assert 'firebird_architecture' in prompt_names
    
    def test_test_connection_tool_call(self):
        """Test test_connection tool execution."""
        # Mock successful connection
        self.mock_firebird_server.test_connection.return_value = {
            "connected": True,
            "version": "3.0.7",
            "dsn": "localhost/3050:test.fdb",
            "user": "SYSDBA",
            "charset": "UTF8"
        }
        
        request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "test_connection",
                "arguments": {}
            }
        }
        
        with patch('builtins.print') as mock_print:
            self.mcp_server.handle_request(request)
            
            response_str = mock_print.call_args[0][0]
            response = json.loads(response_str)
            
            assert response['id'] == 4
            assert response['result']['isError'] is False
            assert len(response['result']['content']) > 0
            
            content = response['result']['content'][0]['text']
            assert 'Connection Test Results' in content
            assert 'connected": true' in content
    
    def test_execute_query_tool_call(self):
        """Test execute_query tool execution."""
        # Mock successful query execution
        self.mock_firebird_server.execute_query.return_value = {
            "success": True,
            "data": [
                {"id": 1, "name": "John"},
                {"id": 2, "name": "Jane"}
            ],
            "row_count": 2,
            "columns": ["id", "name"],
            "sql": "SELECT id, name FROM users",
            "analysis": {
                "type": "select",
                "complexity": "simple",
                "category": "query",
                "suggestions": []
            }
        }
        
        request = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "execute_query",
                "arguments": {
                    "sql": "SELECT id, name FROM users"
                }
            }
        }
        
        with patch('builtins.print') as mock_print:
            self.mcp_server.handle_request(request)
            
            response_str = mock_print.call_args[0][0]
            response = json.loads(response_str)
            
            assert response['id'] == 5
            assert response['result']['isError'] is False
            
            content = response['result']['content'][0]['text']
            assert 'Query Results' in content
            assert 'FIREBIRD EXPERT MODE ACTIVE' in content  # Expert mode should be applied
            assert 'John' in content
    
    def test_prompts_get_request_handling(self):
        """Test prompts/get request handling."""
        request = {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "prompts/get",
            "params": {
                "name": "firebird_expert",
                "arguments": {
                    "operation_type": "select",
                    "complexity_level": "advanced"
                }
            }
        }
        
        with patch('builtins.print') as mock_print:
            self.mcp_server.handle_request(request)
            
            response_str = mock_print.call_args[0][0]
            response = json.loads(response_str)
            
            assert response['id'] == 6
            assert 'result' in response
            assert 'messages' in response['result']
            
            message = response['result']['messages'][0]
            assert message['role'] == 'user'
            prompt_text = message['content']['text']
            
            assert 'Firebird Database Expert' in prompt_text
            assert 'SELECT' in prompt_text
            assert 'advanced' in prompt_text
    
    def test_error_handling_for_unknown_method(self):
        """Test error handling for unknown methods."""
        request = {
            "jsonrpc": "2.0",
            "id": 7,
            "method": "unknown/method",
            "params": {}
        }
        
        with patch('builtins.print') as mock_print:
            self.mcp_server.handle_request(request)
            
            response_str = mock_print.call_args[0][0]
            response = json.loads(response_str)
            
            assert response['id'] == 7
            assert 'error' in response
            assert response['error']['code'] == -32601
            assert 'Method not found' in response['error']['message']
    
    def test_error_handling_for_invalid_tool(self):
        """Test error handling for invalid tool calls."""
        request = {
            "jsonrpc": "2.0",
            "id": 8,
            "method": "tools/call",
            "params": {
                "name": "invalid_tool",
                "arguments": {}
            }
        }
        
        with patch('builtins.print') as mock_print:
            self.mcp_server.handle_request(request)
            
            response_str = mock_print.call_args[0][0]
            response = json.loads(response_str)
            
            assert response['id'] == 8
            assert response['result']['isError'] is True
            
            content = response['result']['content'][0]['text']
            assert 'Unknown tool' in content
    
    def test_expert_mode_disable_functionality(self):
        """Test that expert mode can be disabled per tool call."""
        self.mock_firebird_server.test_connection.return_value = {
            "connected": True,
            "version": "3.0.7"
        }
        
        request = {
            "jsonrpc": "2.0",
            "id": 9,
            "method": "tools/call",
            "params": {
                "name": "test_connection",
                "arguments": {
                    "disable_expert_mode": True
                }
            }
        }
        
        with patch('builtins.print') as mock_print:
            self.mcp_server.handle_request(request)
            
            response_str = mock_print.call_args[0][0]
            response = json.loads(response_str)
            
            content = response['result']['content'][0]['text']
            # Expert mode should NOT be applied when disabled
            assert 'FIREBIRD EXPERT MODE ACTIVE' not in content
    
    def test_server_status_comprehensive_check(self):
        """Test comprehensive server status reporting."""
        request = {
            "jsonrpc": "2.0",
            "id": 10,
            "method": "tools/call",
            "params": {
                "name": "server_status",
                "arguments": {}
            }
        }
        
        with patch('builtins.print') as mock_print:
            self.mcp_server.handle_request(request)
            
            response_str = mock_print.call_args[0][0]
            response = json.loads(response_str)
            
            content = response['result']['content'][0]['text']
            
            # Parse the JSON status from the content
            assert 'Server Status' in content
            assert 'server_info' in content
            assert 'firebird_client_libraries' in content
            assert 'default_prompt_system' in content
            assert 'features' in content


if __name__ == '__main__':
    pytest.main([__file__])
