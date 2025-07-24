"""Configuração compartilhada para testes do MCP Server Firebird."""

import json
import os
import sys
from typing import Any, Dict, Generator
from unittest.mock import MagicMock, Mock, patch

import pytest
from testcontainers.compose import DockerCompose

# Adicionar o diretório raiz ao path para importar server.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import server  # noqa: E402


@pytest.fixture
def mock_fdb():
    """Mock do módulo FDB para testes unitários."""
    with patch.dict('sys.modules', {'fdb': Mock()}):
        mock_fdb = sys.modules['fdb']
        mock_fdb.__version__ = "2.0.2"
        
        # Mock da conexão
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_fdb.connect.return_value = mock_connection
        
        yield mock_fdb


@pytest.fixture
def mock_environment():
    """Mock das variáveis de ambiente."""
    env_vars = {
        'FIREBIRD_HOST': 'test-host',
        'FIREBIRD_PORT': '3050',
        'FIREBIRD_DATABASE': '/test/database.fdb',
        'FIREBIRD_USER': 'TEST_USER',
        'FIREBIRD_PASSWORD': 'test_password',
        'FIREBIRD_CHARSET': 'UTF8',
        'FIREBIRD_LANGUAGE': 'en_US',
        'MCP_SERVER_NAME': 'test-server',
        'MCP_SERVER_VERSION': '1.0.0'
    }
    
    with patch.dict(os.environ, env_vars):
        yield env_vars


@pytest.fixture
def sample_query_result():
    """Resultado de exemplo para queries."""
    return {
        'success': True,
        'data': [
            {'ID': 1, 'NAME': 'Test Item 1', 'VALUE': 100.50},
            {'ID': 2, 'NAME': 'Test Item 2', 'VALUE': 200.75}
        ],
        'row_count': 2,
        'columns': ['ID', 'NAME', 'VALUE']
    }


@pytest.fixture
def sample_tables_list():
    """Lista de exemplo de tabelas."""
    return {
        'success': True,
        'tables': ['CUSTOMERS', 'ORDERS', 'PRODUCTS', 'SUPPLIERS'],
        'count': 4,
        'database': '/test/database.fdb'
    }


@pytest.fixture
def firebird_server_instance(mock_environment, mock_fdb):
    """Instância do FirebirdMCPServer para testes."""
    with patch('server.FDB_AVAILABLE', True), \
         patch('server.FIREBIRD_CLIENT_AVAILABLE', True):
        return server.FirebirdMCPServer()


@pytest.fixture
def mcp_server_instance():
    """Instância do MCPServer para testes."""
    return server.MCPServer()


@pytest.fixture
def mock_connection_successful():
    """Mock de conexão bem-sucedida com Firebird."""
    connection_result = {
        'connected': True,
        'version': '3.0.10',
        'dsn': 'test-host/3050:/test/database.fdb',
        'user': 'TEST_USER',
        'charset': 'UTF8'
    }
    
    with patch.object(server.FirebirdMCPServer, 'test_connection', return_value=connection_result):
        yield connection_result


@pytest.fixture
def mock_connection_failed():
    """Mock de conexão falha com Firebird."""
    connection_result = {
        'connected': False,
        'error': 'Connection refused',
        'type': 'network_error',
        'dsn': 'test-host/3050:/test/database.fdb'
    }
    
    with patch.object(server.FirebirdMCPServer, 'test_connection', return_value=connection_result):
        yield connection_result


@pytest.fixture
def json_rpc_request():
    """Factory para criar requisições JSON-RPC."""
    def _create_request(method: str, params: Dict[str, Any] = None, request_id: int = 1):
        return {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": request_id
        }
    return _create_request


@pytest.fixture
def captured_output():
    """Captura stdout para verificar respostas JSON-RPC."""
    from io import StringIO
    import sys
    
    old_stdout = sys.stdout
    sys.stdout = mystdout = StringIO()
    yield mystdout
    sys.stdout = old_stdout


@pytest.fixture
def i18n_instance():
    """Instância do sistema de internacionalização."""
    return server.I18n("en_US")


class MockFirebirdContainer:
    """Mock de container Firebird para testes de integração."""
    
    def __init__(self):
        self.host = "localhost"
        self.port = 3050
        self.database = "/firebird/data/test.fdb"
        self.user = "SYSDBA"
        self.password = "masterkey"
        self.is_running = False
    
    def start(self):
        """Simula início do container."""
        self.is_running = True
        return self
    
    def stop(self):
        """Simula parada do container."""
        self.is_running = False
    
    def get_connection_url(self):
        """Retorna URL de conexão."""
        return f"{self.host}:{self.port}/{self.database}"


@pytest.fixture(scope="session")
def firebird_container():
    """Container Firebird para testes de integração."""
    # Em ambiente de CI/CD ou desenvolvimento local, usar container real
    # Por ora, usar mock para testes rápidos
    container = MockFirebirdContainer()
    container.start()
    yield container
    container.stop()


@pytest.fixture(scope="session")
def docker_compose_firebird():
    """Docker Compose com Firebird para testes de integração."""
    compose_file_path = os.path.join(
        os.path.dirname(__file__), 
        "integration", 
        "docker-compose-test.yml"
    )
    
    if os.path.exists(compose_file_path):
        with DockerCompose(
            filepath=os.path.dirname(compose_file_path),
            compose_file_name="docker-compose-test.yml"
        ) as compose:
            yield compose
    else:
        # Fallback para mock se não tiver Docker Compose
        yield MockFirebirdContainer()


@pytest.fixture
def temp_database_file(tmp_path):
    """Arquivo temporário de banco para testes."""
    db_file = tmp_path / "test.fdb"
    yield str(db_file)


@pytest.fixture
def mock_library_detection():
    """Mock para detecção de bibliotecas Firebird."""
    with patch('server.FDB_AVAILABLE', True), \
         patch('server.FIREBIRD_CLIENT_AVAILABLE', True), \
         patch('server.CLIENT_LIBRARY_PATH', '/opt/firebird/lib/libfbclient.so'):
        yield


class FirebirdTestHelper:
    """Helper class para testes com Firebird."""
    
    @staticmethod
    def create_test_table_sql():
        """SQL para criar tabela de teste."""
        return """
        CREATE TABLE TEST_CUSTOMERS (
            ID INTEGER NOT NULL PRIMARY KEY,
            NAME VARCHAR(100) NOT NULL,
            EMAIL VARCHAR(255),
            CREATED_DATE TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    
    @staticmethod
    def insert_test_data_sql():
        """SQL para inserir dados de teste."""
        return [
            "INSERT INTO TEST_CUSTOMERS (ID, NAME, EMAIL) VALUES (1, 'John Doe', 'john@example.com')",
            "INSERT INTO TEST_CUSTOMERS (ID, NAME, EMAIL) VALUES (2, 'Jane Smith', 'jane@example.com')",
            "INSERT INTO TEST_CUSTOMERS (ID, NAME, EMAIL) VALUES (3, 'Bob Johnson', 'bob@example.com')"
        ]
    
    @staticmethod
    def select_test_data_sql():
        """SQL para selecionar dados de teste."""
        return "SELECT ID, NAME, EMAIL FROM TEST_CUSTOMERS ORDER BY ID"


@pytest.fixture
def firebird_helper():
    """Helper para operações com Firebird nos testes."""
    return FirebirdTestHelper()


# Configuração global para testes
def pytest_configure(config):
    """Configuração global do pytest."""
    # Adicionar marcadores customizados
    config.addinivalue_line(
        "markers", "unit: marca testes unitários"
    )
    config.addinivalue_line(
        "markers", "integration: marca testes de integração"
    )
    config.addinivalue_line(
        "markers", "slow: marca testes lentos"
    )
    config.addinivalue_line(
        "markers", "firebird: marca testes que precisam de Firebird"
    )
    config.addinivalue_line(
        "markers", "docker: marca testes que precisam de Docker"
    )


def pytest_collection_modifyitems(config, items):
    """Modifica coleção de testes para adicionar marcadores automáticos."""
    for item in items:
        # Marcar testes por localização
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
            item.add_marker(pytest.mark.slow)
        
        # Marcar testes que usam Docker
        if "docker" in item.name.lower() or "container" in item.name.lower():
            item.add_marker(pytest.mark.docker)
        
        # Marcar testes que usam Firebird
        if "firebird" in item.name.lower() or "fdb" in item.name.lower():
            item.add_marker(pytest.mark.firebird)


# Fixtures de performance para benchmarking
@pytest.fixture
def benchmark_query():
    """Query complexa para benchmarks."""
    return """
    SELECT 
        c.ID,
        c.NAME,
        COUNT(o.ID) as ORDER_COUNT,
        SUM(o.TOTAL) as TOTAL_SALES,
        AVG(o.TOTAL) as AVG_ORDER_VALUE
    FROM CUSTOMERS c
    LEFT JOIN ORDERS o ON c.ID = o.CUSTOMER_ID
    WHERE c.CREATED_DATE >= CURRENT_DATE - 30
    GROUP BY c.ID, c.NAME
    HAVING COUNT(o.ID) > 0
    ORDER BY TOTAL_SALES DESC
    """


@pytest.fixture
def performance_test_data():
    """Dados para testes de performance."""
    return {
        'small_dataset': 100,
        'medium_dataset': 10000,
        'large_dataset': 100000
    }
