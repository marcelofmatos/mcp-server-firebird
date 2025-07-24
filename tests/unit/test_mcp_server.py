"""Testes unitários para MCPServer."""

import json
from io import StringIO
from unittest.mock import Mock, patch

import pytest

import server


class TestMCPServer:
    """Testes para a classe MCPServer."""

    def test_init(self):
        """Testa inicialização do MCPServer."""
        mcp_server = server.MCPServer()
        assert mcp_server is not None

    @pytest.mark.unit
    def test_send_response(self, mcp_server_instance, captured_output):
        """Testa envio de resposta JSON-RPC."""
        test_result = {"status": "ok", "data": [1, 2, 3]}
        
        mcp_server_instance.send_response(1, test_result)
        
        output = captured_output.getvalue()
        response = json.loads(output.strip())
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert response["result"] == test_result

    @pytest.mark.unit
    def test_send_error(self, mcp_server_instance, captured_output):
        """Testa envio de erro JSON-RPC."""
        mcp_server_instance.send_error(1, -32601, "Method not found")
        
        output = captured_output.getvalue()
        response = json.loads(output.strip())
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert response["error"]["code"] == -32601
        assert response["error"]["message"] == "Method not found"

    @pytest.mark.unit
    def test_handle_initialize(self, mcp_server_instance, captured_output):
        """Testa handling de inicialização."""
        params = {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        }
        
        mcp_server_instance.handle_initialize(1, params)
        
        output = captured_output.getvalue()
        response = json.loads(output.strip())
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert response["result"]["protocolVersion"] == "2024-11-05"
        assert "capabilities" in response["result"]
        assert "serverInfo" in response["result"]

    @pytest.mark.unit
    def test_handle_tools_list(self, mcp_server_instance, captured_output):
        """Testa listagem de ferramentas."""
        mcp_server_instance.handle_tools_list(1, {})
        
        output = captured_output.getvalue()
        response = json.loads(output.strip())
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "tools" in response["result"]
        
        tools = response["result"]["tools"]
        tool_names = [tool["name"] for tool in tools]
        
        assert "test_connection" in tool_names
        assert "execute_query" in tool_names
        assert "list_tables" in tool_names
        assert "server_status" in tool_names

    @pytest.mark.unit
    def test_handle_resources_list(self, mcp_server_instance, captured_output):
        """Testa listagem de recursos."""
        mcp_server_instance.handle_resources_list(1, {})
        
        output = captured_output.getvalue()
        response = json.loads(output.strip())
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "resources" in response["result"]
        assert isinstance(response["result"]["resources"], list)

    @pytest.mark.unit
    def test_handle_prompts_list(self, mcp_server_instance, captured_output):
        """Testa listagem de prompts."""
        mcp_server_instance.handle_prompts_list(1, {})
        
        output = captured_output.getvalue()
        response = json.loads(output.strip())
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "prompts" in response["result"]
        
        prompts = response["result"]["prompts"]
        prompt_names = [prompt["name"] for prompt in prompts]
        
        assert "firebird_expert" in prompt_names
        assert "firebird_performance" in prompt_names
        assert "firebird_architecture" in prompt_names

    @pytest.mark.unit
    def test_handle_prompts_get_firebird_expert(self, mcp_server_instance, captured_output):
        """Testa obtenção do prompt firebird_expert."""
        params = {
            "name": "firebird_expert",
            "arguments": {
                "operation_type": "select",
                "complexity_level": "intermediate"
            }
        }
        
        mcp_server_instance.handle_prompts_get(1, params)
        
        output = captured_output.getvalue()
        response = json.loads(output.strip())
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "description" in response["result"]
        assert "messages" in response["result"]
        assert len(response["result"]["messages"]) > 0

    @pytest.mark.unit
    def test_handle_prompts_get_unknown_prompt(self, mcp_server_instance, captured_output):
        """Testa obtenção de prompt desconhecido."""
        params = {"name": "unknown_prompt"}
        
        mcp_server_instance.handle_prompts_get(1, params)
        
        output = captured_output.getvalue()
        response = json.loads(output.strip())
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "error" in response

    @pytest.mark.unit
    def test_handle_tools_call_test_connection(self, mcp_server_instance, captured_output):
        """Testa chamada da ferramenta test_connection."""
        with patch.object(server.firebird_server, 'test_connection') as mock_test:
            mock_test.return_value = {
                "connected": True,
                "version": "3.0.10",
                "dsn": "test/db"
            }
            
            params = {"name": "test_connection", "arguments": {}}
            mcp_server_instance.handle_tools_call(1, params)
            
            output = captured_output.getvalue()
            response = json.loads(output.strip())
            
            assert response["jsonrpc"] == "2.0"
            assert response["id"] == 1
            assert "content" in response["result"]
            assert response["result"]["isError"] is False

    @pytest.mark.unit
    def test_handle_tools_call_execute_query(self, mcp_server_instance, captured_output):
        """Testa chamada da ferramenta execute_query."""
        with patch.object(server.firebird_server, 'execute_query') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "data": [{"ID": 1, "NAME": "Test"}],
                "row_count": 1
            }
            
            params = {
                "name": "execute_query",
                "arguments": {
                    "sql": "SELECT ID, NAME FROM CUSTOMERS",
                    "params": None
                }
            }
            
            mcp_server_instance.handle_tools_call(1, params)
            
            output = captured_output.getvalue()
            response = json.loads(output.strip())
            
            assert response["jsonrpc"] == "2.0"
            assert response["id"] == 1
            assert "content" in response["result"]
            assert response["result"]["isError"] is False
            
            mock_execute.assert_called_once_with("SELECT ID, NAME FROM CUSTOMERS", None)

    @pytest.mark.unit
    def test_handle_tools_call_execute_query_no_sql(self, mcp_server_instance, captured_output):
        """Testa execute_query sem SQL."""
        params = {
            "name": "execute_query",
            "arguments": {}
        }
        
        mcp_server_instance.handle_tools_call(1, params)
        
        output = captured_output.getvalue()
        response = json.loads(output.strip())
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert response["result"]["isError"] is True

    @pytest.mark.unit
    def test_handle_tools_call_list_tables(self, mcp_server_instance, captured_output):
        """Testa chamada da ferramenta list_tables."""
        with patch.object(server.firebird_server, 'get_tables') as mock_get_tables:
            mock_get_tables.return_value = {
                "success": True,
                "tables": ["CUSTOMERS", "ORDERS"],
                "count": 2
            }
            
            params = {"name": "list_tables", "arguments": {}}
            mcp_server_instance.handle_tools_call(1, params)
            
            output = captured_output.getvalue()
            response = json.loads(output.strip())
            
            assert response["jsonrpc"] == "2.0"
            assert response["id"] == 1
            assert "content" in response["result"]
            assert response["result"]["isError"] is False

    @pytest.mark.unit
    def test_handle_tools_call_server_status(self, mcp_server_instance, captured_output):
        """Testa chamada da ferramenta server_status."""
        with patch.object(server.firebird_server, 'test_connection') as mock_test:
            mock_test.return_value = {"connected": True}
            
            params = {"name": "server_status", "arguments": {}}
            mcp_server_instance.handle_tools_call(1, params)
            
            output = captured_output.getvalue()
            response = json.loads(output.strip())
            
            assert response["jsonrpc"] == "2.0"
            assert response["id"] == 1
            assert "content" in response["result"]
            assert response["result"]["isError"] is False

    @pytest.mark.unit
    def test_handle_tools_call_unknown_tool(self, mcp_server_instance, captured_output):
        """Testa chamada de ferramenta desconhecida."""
        params = {"name": "unknown_tool", "arguments": {}}
        mcp_server_instance.handle_tools_call(1, params)
        
        output = captured_output.getvalue()
        response = json.loads(output.strip())
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert response["result"]["isError"] is True

    @pytest.mark.unit
    def test_handle_request_initialize(self, mcp_server_instance):
        """Testa handling de request initialize."""
        request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {},
            "id": 1
        }
        
        with patch.object(mcp_server_instance, 'handle_initialize') as mock_handle:
            mcp_server_instance.handle_request(request)
            mock_handle.assert_called_once_with(1, {})

    @pytest.mark.unit
    def test_handle_request_tools_list(self, mcp_server_instance):
        """Testa handling de request tools/list."""
        request = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": 1
        }
        
        with patch.object(mcp_server_instance, 'handle_tools_list') as mock_handle:
            mcp_server_instance.handle_request(request)
            mock_handle.assert_called_once_with(1, {})

    @pytest.mark.unit
    def test_handle_request_tools_call(self, mcp_server_instance):
        """Testa handling de request tools/call."""
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": "test_connection"},
            "id": 1
        }
        
        with patch.object(mcp_server_instance, 'handle_tools_call') as mock_handle:
            mcp_server_instance.handle_request(request)
            mock_handle.assert_called_once_with(1, {"name": "test_connection"})

    @pytest.mark.unit
    def test_handle_request_unknown_method(self, mcp_server_instance, captured_output):
        """Testa handling de método desconhecido."""
        request = {
            "jsonrpc": "2.0",
            "method": "unknown/method",
            "params": {},
            "id": 1
        }
        
        mcp_server_instance.handle_request(request)
        
        output = captured_output.getvalue()
        response = json.loads(output.strip())
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "error" in response
        assert response["error"]["code"] == -32601

    @pytest.mark.unit
    def test_handle_request_notifications_initialized(self, mcp_server_instance):
        """Testa handling de notificação initialized."""
        request = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        
        # Não deve gerar erro nem resposta
        result = mcp_server_instance.handle_request(request)
        assert result is None

    @pytest.mark.unit
    def test_handle_request_exception(self, mcp_server_instance, captured_output):
        """Testa handling de request com exceção."""
        request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {},
            "id": 1
        }
        
        with patch.object(mcp_server_instance, 'handle_initialize', side_effect=Exception("Test error")):
            mcp_server_instance.handle_request(request)
            
            output = captured_output.getvalue()
            response = json.loads(output.strip())
            
            assert response["jsonrpc"] == "2.0"
            assert response["id"] == 1
            assert "error" in response
            assert response["error"]["code"] == -32603

    @pytest.mark.unit
    def test_run_with_valid_json(self, mcp_server_instance):
        """Testa run com JSON válido."""
        test_input = '{"jsonrpc": "2.0", "method": "initialize", "id": 1}\n'
        
        with patch('sys.stdin', StringIO(test_input)), \
             patch.object(mcp_server_instance, 'handle_request') as mock_handle:
            
            try:
                mcp_server_instance.run()
            except StopIteration:
                # Esperado quando stdin termina
                pass
            
            mock_handle.assert_called_once()

    @pytest.mark.unit
    def test_run_with_invalid_json(self, mcp_server_instance, capsys):
        """Testa run com JSON inválido."""
        test_input = 'invalid json\n'
        
        with patch('sys.stdin', StringIO(test_input)):
            try:
                mcp_server_instance.run()
            except StopIteration:
                # Esperado quando stdin termina
                pass
            
            captured = capsys.readouterr()
            assert "Invalid JSON" in captured.err or "invalid_json" in captured.err

    @pytest.mark.unit
    def test_run_with_empty_lines(self, mcp_server_instance):
        """Testa run com linhas vazias."""
        test_input = '\n\n\n'
        
        with patch('sys.stdin', StringIO(test_input)), \
             patch.object(mcp_server_instance, 'handle_request') as mock_handle:
            
            try:
                mcp_server_instance.run()
            except StopIteration:
                # Esperado quando stdin termina
                pass
            
            # Não deve chamar handle_request para linhas vazias
            mock_handle.assert_not_called()

    @pytest.mark.unit
    def test_run_keyboard_interrupt(self, mcp_server_instance, capsys):
        """Testa run com KeyboardInterrupt."""
        with patch('sys.stdin', StringIO("")), \
             patch.object(mcp_server_instance, 'handle_request', side_effect=KeyboardInterrupt):
            
            mcp_server_instance.run()
            
            captured = capsys.readouterr()
            assert "interrupted" in captured.err.lower()


class TestJSONRPCProtocol:
    """Testes específicos do protocolo JSON-RPC."""

    @pytest.mark.unit
    def test_json_rpc_response_format(self, mcp_server_instance, captured_output):
        """Testa formato de resposta JSON-RPC."""
        mcp_server_instance.send_response(123, {"test": "data"})
        
        output = captured_output.getvalue()
        response = json.loads(output.strip())
        
        # Verificar campos obrigatórios JSON-RPC 2.0
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 123
        assert "result" in response
        assert "error" not in response

    @pytest.mark.unit
    def test_json_rpc_error_format(self, mcp_server_instance, captured_output):
        """Testa formato de erro JSON-RPC."""
        mcp_server_instance.send_error(456, -32600, "Invalid Request")
        
        output = captured_output.getvalue()
        response = json.loads(output.strip())
        
        # Verificar campos obrigatórios JSON-RPC 2.0
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 456
        assert "error" in response
        assert "result" not in response
        assert response["error"]["code"] == -32600
        assert response["error"]["message"] == "Invalid Request"

    @pytest.mark.unit
    def test_mcp_protocol_version(self, mcp_server_instance, captured_output):
        """Testa versão do protocolo MCP."""
        mcp_server_instance.handle_initialize(1, {})
        
        output = captured_output.getvalue()
        response = json.loads(output.strip())
        
        assert response["result"]["protocolVersion"] == "2024-11-05"

    @pytest.mark.unit
    def test_server_capabilities(self, mcp_server_instance, captured_output):
        """Testa capabilities do servidor."""
        mcp_server_instance.handle_initialize(1, {})
        
        output = captured_output.getvalue()
        response = json.loads(output.strip())
        
        capabilities = response["result"]["capabilities"]
        assert "tools" in capabilities
        assert "resources" in capabilities
        assert "prompts" in capabilities

    @pytest.mark.unit
    def test_server_info(self, mcp_server_instance, captured_output):
        """Testa informações do servidor."""
        with patch.dict('os.environ', {
            'MCP_SERVER_NAME': 'test-firebird-server',
            'MCP_SERVER_VERSION': '2.0.0'
        }):
            mcp_server_instance.handle_initialize(1, {})
            
            output = captured_output.getvalue()
            response = json.loads(output.strip())
            
            server_info = response["result"]["serverInfo"]
            assert server_info["name"] == "test-firebird-server"
            assert server_info["version"] == "2.0.0"
