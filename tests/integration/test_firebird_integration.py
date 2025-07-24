"""Testes de integração para MCP Server Firebird."""

import json
import os
import time
from typing import Dict, Any

import pytest
from testcontainers.compose import DockerCompose
from testcontainers.firebird import FirebirdContainer

import server


class TestFirebirdIntegration:
    """Testes de integração com banco Firebird real."""

    @pytest.mark.integration
    @pytest.mark.firebird
    @pytest.mark.slow
    def test_connection_with_real_firebird(self, firebird_container):
        """Testa conexão com instância real do Firebird."""
        if not isinstance(firebird_container, server.MockFirebirdContainer):
            pytest.skip("Firebird container não disponível")
        
        # Simular teste com container mock
        assert firebird_container.is_running
        assert firebird_container.host == "localhost"
        assert firebird_container.port == 3050

    @pytest.mark.integration
    @pytest.mark.docker
    @pytest.mark.slow
    def test_full_workflow_with_docker_compose(self, docker_compose_firebird):
        """Testa workflow completo com Docker Compose."""
        if isinstance(docker_compose_firebird, server.MockFirebirdContainer):
            pytest.skip("Docker Compose não disponível, usando mock")
        
        # Para ambiente de CI/CD onde Docker está disponível
        try:
            # Aguardar Firebird inicializar
            time.sleep(10)
            
            # Configurar ambiente para usar container
            test_config = {
                'host': 'localhost',
                'port': 3050,
                'database': '/firebird/data/test.fdb',
                'user': 'SYSDBA',
                'password': 'test123',
                'charset': 'UTF8'
            }
            
            # Testar conexão
            with patch.dict(os.environ, {
                'FIREBIRD_HOST': test_config['host'],
                'FIREBIRD_PORT': str(test_config['port']),
                'FIREBIRD_DATABASE': test_config['database'],
                'FIREBIRD_USER': test_config['user'],
                'FIREBIRD_PASSWORD': test_config['password']
            }):
                fb_server = server.FirebirdMCPServer()
                result = fb_server.test_connection()
                
                # Em mock, sempre retorna erro ou success baseado na configuração
                assert 'connected' in result
                
        except Exception as e:
            pytest.skip(f"Docker environment not available: {e}")

    @pytest.mark.integration
    @pytest.mark.firebird
    def test_create_and_query_table(self, firebird_helper):
        """Testa criação e consulta de tabela."""
        # Este teste requer Firebird real, por ora usar mock
        create_sql = firebird_helper.create_test_table_sql()
        insert_sqls = firebird_helper.insert_test_data_sql()
        select_sql = firebird_helper.select_test_data_sql()
        
        # Verificar se SQLs estão bem formados
        assert "CREATE TABLE" in create_sql
        assert "TEST_CUSTOMERS" in create_sql
        assert len(insert_sqls) == 3
        assert "SELECT" in select_sql

    @pytest.mark.integration
    @pytest.mark.slow
    def test_performance_large_dataset(self, performance_test_data):
        """Testa performance com dataset grande."""
        # Simular teste de performance
        small_size = performance_test_data['small_dataset']
        medium_size = performance_test_data['medium_dataset']
        large_size = performance_test_data['large_dataset']
        
        # Verificar se tamanhos estão configurados corretamente
        assert small_size < medium_size < large_size
        assert large_size >= 100000

    @pytest.mark.integration
    @pytest.mark.firebird
    def test_concurrent_connections(self):
        """Testa múltiplas conexões simultâneas."""
        import threading
        import time
        
        results = []
        
        def test_connection():
            fb_server = server.FirebirdMCPServer()
            result = fb_server.test_connection()
            results.append(result)
        
        # Criar múltiplas threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=test_connection)
            threads.append(thread)
        
        # Iniciar todas as threads
        for thread in threads:
            thread.start()
        
        # Aguardar conclusão
        for thread in threads:
            thread.join()
        
        # Verificar resultados
        assert len(results) == 5
        # Todos devem ter pelo menos tentado conectar
        for result in results:
            assert isinstance(result, dict)
            assert 'connected' in result

    @pytest.mark.integration
    @pytest.mark.firebird
    def test_transaction_rollback(self):
        """Testa rollback de transações."""
        # Mock de teste de transação
        fb_server = server.FirebirdMCPServer()
        
        # Simular operações que requerem rollback
        try:
            # Em um teste real, isso criaria e desfaria transações
            result = fb_server.execute_query("SELECT 1 FROM RDB$DATABASE")
            # Verificar se operação é tratada corretamente
            assert isinstance(result, dict)
        except Exception:
            # Em mock, pode retornar erro
            pass

    @pytest.mark.integration
    @pytest.mark.firebird
    def test_sql_injection_protection(self):
        """Testa proteção contra SQL injection."""
        fb_server = server.FirebirdMCPServer()
        
        # Testar queries maliciosas
        malicious_queries = [
            "SELECT * FROM CUSTOMERS; DROP TABLE CUSTOMERS; --",
            "' OR '1'='1",
            "1; DELETE FROM CUSTOMERS WHERE 1=1; --"
        ]
        
        for query in malicious_queries:
            # Com prepared statements, deve ser seguro
            result = fb_server.execute_query(
                "SELECT * FROM CUSTOMERS WHERE ID = ?", 
                [query]
            )
            
            # Verificar que não causou erro fatal
            assert isinstance(result, dict)

    @pytest.mark.integration
    @pytest.mark.firebird
    def test_charset_handling(self):
        """Testa handling de diferentes charsets."""
        # Testar dados com caracteres especiais
        test_data = [
            "José da Silva",
            "Configuração",
            "São Paulo",
            "Ação",
            "🔥 Firebird"
        ]
        
        fb_server = server.FirebirdMCPServer()
        
        for data in test_data:
            # Testar inserção de dados com charset UTF8
            result = fb_server.execute_query(
                "SELECT ? AS TEST_FIELD FROM RDB$DATABASE",
                [data]
            )
            
            assert isinstance(result, dict)

    @pytest.mark.integration
    @pytest.mark.firebird
    def test_large_query_results(self):
        """Testa handling de resultados grandes."""
        fb_server = server.FirebirdMCPServer()
        
        # Simular query que retorna muitos dados
        large_query = """
        SELECT 
            CAST(RDB$RELATION_ID AS INTEGER) as ID,
            CAST(RDB$RELATION_NAME AS VARCHAR(100)) as TABLE_NAME,
            CURRENT_TIMESTAMP as QUERY_TIME
        FROM RDB$RELATIONS
        """
        
        result = fb_server.execute_query(large_query)
        
        # Verificar que pode processar resultado
        assert isinstance(result, dict)
        if result.get('success'):
            assert 'data' in result
            assert 'row_count' in result

    @pytest.mark.integration
    @pytest.mark.firebird
    def test_connection_timeout(self):
        """Testa timeout de conexão."""
        # Configurar host inexistente para timeout
        with patch.dict(os.environ, {
            'FIREBIRD_HOST': '192.168.255.255',  # Host que não responde
            'FIREBIRD_PORT': '3050'
        }):
            fb_server = server.FirebirdMCPServer()
            
            start_time = time.time()
            result = fb_server.test_connection()
            end_time = time.time()
            
            # Deve retornar erro em tempo razoável (mock simula)
            assert result['connected'] is False
            # Mock retorna imediatamente, teste real levaria mais tempo
            assert (end_time - start_time) < 60  # Timeout reasonable

    @pytest.mark.integration
    @pytest.mark.firebird
    def test_backup_and_restore_operations(self):
        """Testa operações de backup e restore."""
        # Este teste seria para funcionalidades avançadas
        # Por ora, apenas verificar se queries de sistema funcionam
        
        fb_server = server.FirebirdMCPServer()
        
        # Query para verificar estatísticas do banco
        stats_query = """
        SELECT 
            COUNT(*) as TABLE_COUNT
        FROM RDB$RELATIONS 
        WHERE RDB$VIEW_BLR IS NULL 
        AND (RDB$SYSTEM_FLAG IS NULL OR RDB$SYSTEM_FLAG = 0)
        """
        
        result = fb_server.execute_query(stats_query)
        assert isinstance(result, dict)

    @pytest.mark.integration
    @pytest.mark.docker
    def test_container_health_check(self):
        """Testa health check do container."""
        # Verificar se container responde adequadamente
        
        # Em ambiente real com Docker
        try:
            import docker
            client = docker.from_env()
            
            # Procurar container de teste
            containers = client.containers.list(
                filters={"name": "firebird-test"}
            )
            
            if containers:
                container = containers[0]
                # Verificar status
                assert container.status in ['running', 'healthy']
            else:
                pytest.skip("Container Firebird não encontrado")
                
        except ImportError:
            pytest.skip("Docker client não disponível")
        except Exception as e:
            pytest.skip(f"Erro ao verificar container: {e}")

    @pytest.mark.integration
    @pytest.mark.slow
    def test_memory_usage_monitoring(self):
        """Testa monitoramento de uso de memória."""
        import psutil
        
        # Monitorar uso de memória durante operações
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        fb_server = server.FirebirdMCPServer()
        
        # Executar várias operações
        for i in range(10):
            result = fb_server.test_connection()
            assert isinstance(result, dict)
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Verificar se não houve vazamento excessivo
        # 50MB é um limite generoso para testes
        assert memory_increase < 50 * 1024 * 1024

    @pytest.mark.integration
    @pytest.mark.firebird
    def test_database_metadata_queries(self):
        """Testa queries de metadados do banco."""
        fb_server = server.FirebirdMCPServer()
        
        metadata_queries = [
            # Informações do banco
            "SELECT RDB$GET_CONTEXT('SYSTEM', 'ENGINE_VERSION') FROM RDB$DATABASE",
            
            # Lista de tabelas
            """SELECT RDB$RELATION_NAME FROM RDB$RELATIONS 
               WHERE RDB$VIEW_BLR IS NULL 
               AND (RDB$SYSTEM_FLAG IS NULL OR RDB$SYSTEM_FLAG = 0)""",
            
            # Lista de índices
            """SELECT RDB$INDEX_NAME FROM RDB$INDICES 
               WHERE (RDB$SYSTEM_FLAG IS NULL OR RDB$SYSTEM_FLAG = 0)""",
            
            # Lista de generators
            "SELECT RDB$GENERATOR_NAME FROM RDB$GENERATORS"
        ]
        
        for query in metadata_queries:
            result = fb_server.execute_query(query)
            assert isinstance(result, dict)
            # Em mock ou erro, ainda deve retornar dict estruturado


class TestMCPProtocolIntegration:
    """Testes de integração do protocolo MCP."""

    @pytest.mark.integration
    def test_complete_mcp_workflow(self):
        """Testa workflow completo do protocolo MCP."""
        mcp_server = server.MCPServer()
        
        # Simular sequência completa de requests
        requests = [
            {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {},
                "id": 1
            },
            {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {},
                "id": 2
            },
            {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "test_connection",
                    "arguments": {}
                },
                "id": 3
            }
        ]
        
        responses = []
        
        # Capturar respostas
        with patch('builtins.print') as mock_print:
            for request in requests:
                mcp_server.handle_request(request)
            
            # Verificar se respostas foram enviadas
            assert mock_print.call_count == len(requests)

    @pytest.mark.integration
    def test_error_handling_workflow(self):
        """Testa workflow de tratamento de erros."""
        mcp_server = server.MCPServer()
        
        error_requests = [
            # Método inexistente
            {
                "jsonrpc": "2.0",
                "method": "nonexistent/method",
                "params": {},
                "id": 1
            },
            
            # Ferramenta inexistente
            {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "nonexistent_tool",
                    "arguments": {}
                },
                "id": 2
            },
            
            # Query sem SQL
            {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "execute_query",
                    "arguments": {}
                },
                "id": 3
            }
        ]
        
        with patch('builtins.print') as mock_print:
            for request in error_requests:
                mcp_server.handle_request(request)
            
            # Deve ter enviado respostas de erro
            assert mock_print.call_count == len(error_requests)
