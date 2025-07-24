"""Testes unitários para FirebirdMCPServer."""

import json
import os
from unittest.mock import Mock, patch, MagicMock

import pytest

import server


class TestFirebirdMCPServer:
    """Testes para a classe FirebirdMCPServer."""

    def test_init_with_default_config(self, mock_environment):
        """Testa inicialização com configuração padrão."""
        with patch('server.FDB_AVAILABLE', True), \
             patch('server.FIREBIRD_CLIENT_AVAILABLE', True):
            
            fb_server = server.FirebirdMCPServer()
            
            assert fb_server.dsn == "test-host/3050:/test/database.fdb"

    def test_init_with_custom_port(self, mock_environment):
        """Testa inicialização com porta customizada."""
        with patch.dict(os.environ, {'FIREBIRD_PORT': '3051'}), \
             patch('server.FDB_AVAILABLE', True), \
             patch('server.FIREBIRD_CLIENT_AVAILABLE', True):
            
            fb_server = server.FirebirdMCPServer()
            
            assert fb_server.dsn == "test-host/3051:/test/database.fdb"

    @pytest.mark.unit
    def test_test_connection_fdb_not_available(self):
        """Testa test_connection quando FDB não está disponível."""
        with patch('server.FDB_AVAILABLE', False), \
             patch('server.FDB_ERROR', 'ImportError: No module named fdb'):
            
            fb_server = server.FirebirdMCPServer()
            result = fb_server.test_connection()
            
            assert result['connected'] is False
            assert 'fdb_library_error' in result['type']
            assert 'FDB Python library not installed' in result['solution']

    @pytest.mark.unit
    def test_test_connection_client_not_available(self):
        """Testa test_connection quando cliente Firebird não está disponível."""
        with patch('server.FDB_AVAILABLE', True), \
             patch('server.FIREBIRD_CLIENT_AVAILABLE', False):
            
            fb_server = server.FirebirdMCPServer()
            result = fb_server.test_connection()
            
            assert result['connected'] is False
            assert result['type'] == 'client_library_error'
            assert 'Firebird client libraries missing' in result['solution']

    @pytest.mark.unit
    def test_test_connection_successful(self, mock_fdb, mock_library_detection):
        """Testa conexão bem-sucedida."""
        # Configurar mock para conexão bem-sucedida
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = ['3.0.10']
        
        mock_connection = Mock()
        mock_connection.cursor.return_value = mock_cursor
        
        mock_fdb.connect.return_value = mock_connection
        
        fb_server = server.FirebirdMCPServer()
        result = fb_server.test_connection()
        
        assert result['connected'] is True
        assert result['version'] == '3.0.10'
        assert 'test-host/3050:/test/database.fdb' in result['dsn']

    @pytest.mark.unit
    def test_test_connection_network_error(self, mock_fdb, mock_library_detection):
        """Testa erro de rede na conexão."""
        mock_fdb.connect.side_effect = Exception("network error - connection refused")
        
        fb_server = server.FirebirdMCPServer()
        result = fb_server.test_connection()
        
        assert result['connected'] is False
        assert result['type'] == 'network_error'
        assert 'NETWORK ISSUE' in result['error']

    @pytest.mark.unit
    def test_test_connection_authentication_error(self, mock_fdb, mock_library_detection):
        """Testa erro de autenticação."""
        mock_fdb.connect.side_effect = Exception("login failed - invalid password")
        
        fb_server = server.FirebirdMCPServer()
        result = fb_server.test_connection()
        
        assert result['connected'] is False
        assert result['type'] == 'authentication_error'
        assert 'AUTHENTICATION ISSUE' in result['error']

    @pytest.mark.unit
    def test_test_connection_database_not_found(self, mock_fdb, mock_library_detection):
        """Testa erro de banco não encontrado."""
        mock_fdb.connect.side_effect = Exception("database not found")
        
        fb_server = server.FirebirdMCPServer()
        result = fb_server.test_connection()
        
        assert result['connected'] is False
        assert result['type'] == 'database_error'
        assert 'DATABASE ISSUE' in result['error']

    @pytest.mark.unit
    def test_execute_query_select_successful(self, mock_fdb, mock_library_detection):
        """Testa execução bem-sucedida de SELECT."""
        # Configurar mock
        mock_cursor = Mock()
        mock_cursor.description = [('ID',), ('NAME',), ('EMAIL',)]
        mock_cursor.fetchall.return_value = [
            (1, 'John Doe', 'john@example.com'),
            (2, 'Jane Smith', 'jane@example.com')
        ]
        
        mock_connection = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_fdb.connect.return_value = mock_connection
        
        fb_server = server.FirebirdMCPServer()
        result = fb_server.execute_query("SELECT ID, NAME, EMAIL FROM CUSTOMERS")
        
        assert result['success'] is True
        assert result['row_count'] == 2
        assert result['columns'] == ['ID', 'NAME', 'EMAIL']
        assert len(result['data']) == 2
        assert result['data'][0]['NAME'] == 'John Doe'

    @pytest.mark.unit
    def test_execute_query_insert_successful(self, mock_fdb, mock_library_detection):
        """Testa execução bem-sucedida de INSERT."""
        mock_cursor = Mock()
        mock_cursor.rowcount = 1
        
        mock_connection = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_fdb.connect.return_value = mock_connection
        
        fb_server = server.FirebirdMCPServer()
        result = fb_server.execute_query("INSERT INTO CUSTOMERS (NAME) VALUES ('Test')")
        
        assert result['success'] is True
        assert result['affected_rows'] == 1
        mock_connection.commit.assert_called_once()

    @pytest.mark.unit
    def test_execute_query_with_parameters(self, mock_fdb, mock_library_detection):
        """Testa execução de query com parâmetros."""
        mock_cursor = Mock()
        mock_cursor.description = [('COUNT',)]
        mock_cursor.fetchall.return_value = [(5,)]
        
        mock_connection = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_fdb.connect.return_value = mock_connection
        
        fb_server = server.FirebirdMCPServer()
        result = fb_server.execute_query(
            "SELECT COUNT(*) FROM CUSTOMERS WHERE CITY = ?", 
            ['São Paulo']
        )
        
        assert result['success'] is True
        mock_cursor.execute.assert_called_with(
            "SELECT COUNT(*) FROM CUSTOMERS WHERE CITY = ?", 
            ['São Paulo']
        )

    @pytest.mark.unit
    def test_execute_query_sql_error(self, mock_fdb, mock_library_detection):
        """Testa erro SQL na execução."""
        mock_fdb.connect.side_effect = Exception("SQL syntax error")
        
        fb_server = server.FirebirdMCPServer()
        result = fb_server.execute_query("INVALID SQL")
        
        assert result['success'] is False
        assert 'SQL syntax error' in result['error']

    @pytest.mark.unit
    def test_get_tables_successful(self, mock_fdb, mock_library_detection):
        """Testa listagem bem-sucedida de tabelas."""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            ('CUSTOMERS',),
            ('ORDERS',),
            ('PRODUCTS',)
        ]
        
        mock_connection = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_fdb.connect.return_value = mock_connection
        
        fb_server = server.FirebirdMCPServer()
        result = fb_server.get_tables()
        
        assert result['success'] is True
        assert result['count'] == 3
        assert 'CUSTOMERS' in result['tables']
        assert 'ORDERS' in result['tables']
        assert 'PRODUCTS' in result['tables']

    @pytest.mark.unit
    def test_get_tables_fdb_not_available(self):
        """Testa get_tables quando FDB não está disponível."""
        with patch('server.FDB_AVAILABLE', False):
            fb_server = server.FirebirdMCPServer()
            result = fb_server.get_tables()
            
            assert result['success'] is False
            assert result['type'] == 'fdb_library_error'

    @pytest.mark.unit
    def test_get_tables_error(self, mock_fdb, mock_library_detection):
        """Testa erro na listagem de tabelas."""
        mock_fdb.connect.side_effect = Exception("Connection failed")
        
        fb_server = server.FirebirdMCPServer()
        result = fb_server.get_tables()
        
        assert result['success'] is False
        assert 'Connection failed' in result['error']


class TestI18n:
    """Testes para o sistema de internacionalização."""

    @pytest.mark.unit
    def test_init_default_language(self):
        """Testa inicialização com idioma padrão."""
        with patch('server.os.path.exists', return_value=False):
            i18n = server.I18n()
            assert i18n.language == "en_US"

    @pytest.mark.unit
    def test_init_custom_language(self):
        """Testa inicialização com idioma customizado."""
        with patch('server.os.path.exists', return_value=False):
            i18n = server.I18n("pt_BR")
            assert i18n.language == "pt_BR"

    @pytest.mark.unit
    def test_get_existing_key(self, i18n_instance):
        """Testa obtenção de chave existente."""
        # Mock do dicionário de strings
        i18n_instance.strings = {
            "server_info": {
                "initialized": "MCP Server initialized"
            }
        }
        
        result = i18n_instance.get("server_info.initialized")
        assert result == "MCP Server initialized"

    @pytest.mark.unit
    def test_get_nonexistent_key(self, i18n_instance):
        """Testa obtenção de chave inexistente."""
        result = i18n_instance.get("nonexistent.key")
        assert result == "nonexistent.key"

    @pytest.mark.unit
    def test_get_with_formatting(self, i18n_instance):
        """Testa obtenção de chave com formatação."""
        i18n_instance.strings = {
            "messages": {
                "greeting": "Hello, {name}!"
            }
        }
        
        result = i18n_instance.get("messages.greeting", name="World")
        assert result == "Hello, World!"

    @pytest.mark.unit
    def test_load_language_file_not_found(self):
        """Testa carregamento quando arquivo não existe."""
        with patch('server.os.path.exists', return_value=False), \
             patch('server.os.path.dirname', return_value='/test'), \
             patch('server.os.path.abspath', return_value='/test/server.py'):
            
            i18n = server.I18n("nonexistent")
            # Deve carregar strings de fallback
            assert "server_info" in i18n.strings

    @pytest.mark.unit
    def test_load_language_json_error(self):
        """Testa carregamento com erro de JSON."""
        with patch('server.os.path.exists', return_value=True), \
             patch('builtins.open', side_effect=json.JSONDecodeError("Invalid JSON", "", 0)):
            
            i18n = server.I18n("en_US")
            # Deve carregar strings de fallback
            assert "server_info" in i18n.strings


class TestDatabaseConfiguration:
    """Testes para configuração do banco."""

    @pytest.mark.unit
    def test_db_config_defaults(self):
        """Testa configuração padrão do banco."""
        with patch.dict(os.environ, {}, clear=True):
            # Recarregar módulo para pegar novos valores
            import importlib
            importlib.reload(server)
            
            config = server.DB_CONFIG
            assert config['host'] == 'localhost'
            assert config['port'] == 3050
            assert config['user'] == 'SYSDBA'
            assert config['password'] == 'masterkey'
            assert config['charset'] == 'UTF8'

    @pytest.mark.unit
    def test_db_config_from_environment(self, mock_environment):
        """Testa configuração do banco via variáveis de ambiente."""
        # Recarregar configuração
        import importlib
        importlib.reload(server)
        
        config = server.DB_CONFIG
        assert config['host'] == 'test-host'
        assert config['port'] == 3050
        assert config['database'] == '/test/database.fdb'
        assert config['user'] == 'TEST_USER'
        assert config['password'] == 'test_password'

    @pytest.mark.unit
    def test_db_config_port_conversion(self):
        """Testa conversão de porta para inteiro."""
        with patch.dict(os.environ, {'FIREBIRD_PORT': '3051'}):
            import importlib
            importlib.reload(server)
            
            config = server.DB_CONFIG
            assert config['port'] == 3051
            assert isinstance(config['port'], int)


class TestLibraryDetection:
    """Testes para detecção de bibliotecas."""

    @pytest.mark.unit 
    def test_fdb_available_detection(self):
        """Testa detecção quando FDB está disponível."""
        with patch('builtins.__import__', return_value=Mock(__version__="2.0.2")):
            # Simular reimport
            import importlib
            importlib.reload(server)
            
            assert server.FDB_AVAILABLE is True

    @pytest.mark.unit
    def test_fdb_not_available_detection(self):
        """Testa detecção quando FDB não está disponível."""
        with patch('builtins.__import__', side_effect=ImportError("No module named 'fdb'")):
            import importlib
            importlib.reload(server)
            
            assert server.FDB_AVAILABLE is False
            assert "No module named 'fdb'" in server.FDB_ERROR

    @pytest.mark.unit
    def test_client_library_detection(self):
        """Testa detecção de biblioteca cliente."""
        with patch('server.ctypes.util.find_library', return_value='/opt/firebird/lib/libfbclient.so'):
            import importlib
            importlib.reload(server)
            
            assert server.FIREBIRD_CLIENT_AVAILABLE is True
            assert '/opt/firebird/lib/libfbclient.so' in server.CLIENT_LIBRARY_PATH


class TestUtilityFunctions:
    """Testes para funções utilitárias."""

    @pytest.mark.unit
    def test_log_function(self, capsys):
        """Testa função de log."""
        server.log("Test message")
        captured = capsys.readouterr()
        assert "[MCP-FIREBIRD] Test message" in captured.err

    @pytest.mark.unit
    def test_main_function_library_check(self, mock_environment):
        """Testa função main com verificação de bibliotecas."""
        with patch('server.FDB_AVAILABLE', True), \
             patch('server.FIREBIRD_CLIENT_AVAILABLE', True), \
             patch('server.MCPServer') as mock_mcp_server:
            
            # Mock do servidor MCP
            mock_server_instance = Mock()
            mock_mcp_server.return_value = mock_server_instance
            
            # Chamar main
            server.main()
            
            # Verificar se servidor foi criado e executado
            mock_mcp_server.assert_called_once()
            mock_server_instance.run.assert_called_once()
