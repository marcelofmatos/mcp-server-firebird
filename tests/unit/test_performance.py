"""Testes de performance e benchmark para MCP Server Firebird."""

import time
from unittest.mock import Mock, patch

import pytest

import server


class TestPerformanceBenchmarks:
    """Testes de performance e benchmarks."""

    @pytest.mark.slow
    @pytest.mark.unit
    def test_connection_performance(self, mock_fdb, mock_library_detection):
        """Testa performance de conexões."""
        # Mock para conexão rápida
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = ['3.0.10']
        
        mock_connection = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_fdb.connect.return_value = mock_connection
        
        fb_server = server.FirebirdMCPServer()
        
        # Medir tempo de múltiplas conexões
        start_time = time.time()
        
        for _ in range(10):
            result = fb_server.test_connection()
            assert result['connected'] is True
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 10 conexões devem ser rápidas (mock é instantâneo)
        assert total_time < 1.0
        
        # Calcular throughput
        connections_per_second = 10 / total_time
        assert connections_per_second > 10  # Pelo menos 10 conn/s

    @pytest.mark.slow
    @pytest.mark.unit
    def test_query_execution_performance(self, mock_fdb, mock_library_detection):
        """Testa performance de execução de queries."""
        # Mock para query rápida
        mock_cursor = Mock()
        mock_cursor.description = [('ID',), ('NAME',)]
        mock_cursor.fetchall.return_value = [(i, f'Name{i}') for i in range(1000)]
        
        mock_connection = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_fdb.connect.return_value = mock_connection
        
        fb_server = server.FirebirdMCPServer()
        
        # Medir tempo de múltiplas queries
        start_time = time.time()
        
        for _ in range(5):
            result = fb_server.execute_query("SELECT ID, NAME FROM CUSTOMERS")
            assert result['success'] is True
            assert result['row_count'] == 1000
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 5 queries de 1000 rows devem ser rápidas
        assert total_time < 1.0

    @pytest.mark.slow
    @pytest.mark.unit
    def test_memory_usage_during_large_results(self, mock_fdb, mock_library_detection):
        """Testa uso de memória com resultados grandes."""
        try:
            import psutil
        except ImportError:
            pytest.skip("psutil não disponível")
        
        # Mock para resultado grande
        mock_cursor = Mock()
        mock_cursor.description = [('ID',), ('DATA',)]
        
        # Simular 10k registros
        large_data = [(i, f'Large data string {i} ' * 100) for i in range(10000)]
        mock_cursor.fetchall.return_value = large_data
        
        mock_connection = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_fdb.connect.return_value = mock_connection
        
        fb_server = server.FirebirdMCPServer()
        
        # Medir memória antes
        process = psutil.Process()
        mem_before = process.memory_info().rss
        
        # Executar query com resultado grande
        result = fb_server.execute_query("SELECT * FROM LARGE_TABLE")
        
        # Medir memória depois
        mem_after = process.memory_info().rss
        memory_increase = mem_after - mem_before
        
        assert result['success'] is True
        assert result['row_count'] == 10000
        
        # Verificar que não houve vazamento excessivo (50MB limit)
        assert memory_increase < 50 * 1024 * 1024

    @pytest.mark.slow
    @pytest.mark.unit
    def test_concurrent_query_performance(self, mock_fdb, mock_library_detection):
        """Testa performance com queries concorrentes."""
        import threading
        import time
        
        # Mock otimizado
        mock_cursor = Mock()
        mock_cursor.description = [('COUNT',)]
        mock_cursor.fetchall.return_value = [(100,)]
        
        mock_connection = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_fdb.connect.return_value = mock_connection
        
        results = []
        times = []
        
        def execute_query():
            fb_server = server.FirebirdMCPServer()
            start = time.time()
            result = fb_server.execute_query("SELECT COUNT(*) FROM CUSTOMERS")
            end = time.time()
            
            results.append(result)
            times.append(end - start)
        
        # Executar 5 threads concorrentes
        threads = []
        start_time = time.time()
        
        for _ in range(5):
            thread = threading.Thread(target=execute_query)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # Verificar resultados
        assert len(results) == 5
        assert all(r['success'] for r in results)
        
        # Tempo total deve ser razoável
        assert total_time < 2.0
        
        # Tempo médio por query
        avg_time = sum(times) / len(times)
        assert avg_time < 0.5

    @pytest.mark.unit
    def test_json_serialization_performance(self):
        """Testa performance de serialização JSON."""
        import json
        
        # Dados grandes para serialização
        large_data = {
            'success': True,
            'data': [
                {'id': i, 'name': f'Customer {i}', 'email': f'customer{i}@example.com'}
                for i in range(5000)
            ],
            'row_count': 5000,
            'columns': ['id', 'name', 'email']
        }
        
        # Medir tempo de serialização
        start_time = time.time()
        
        for _ in range(10):
            json_str = json.dumps(large_data)
            assert len(json_str) > 100000
        
        end_time = time.time()
        serialization_time = end_time - start_time
        
        # 10 serializações devem ser rápidas
        assert serialization_time < 1.0

    @pytest.mark.unit
    def test_i18n_performance(self):
        """Testa performance do sistema de i18n."""
        i18n = server.I18n()
        
        # Simular dicionário grande
        i18n.strings = {
            f"section_{i}": {
                f"key_{j}": f"Value {i}-{j}"
                for j in range(100)
            }
            for i in range(50)
        }
        
        # Medir tempo de múltiplas consultas
        start_time = time.time()
        
        for i in range(50):
            for j in range(10):  # Apenas 10 de cada seção
                key = f"section_{i}.key_{j}"
                value = i18n.get(key)
                assert value == f"Value {i}-{j}"
        
        end_time = time.time()
        lookup_time = end_time - start_time
        
        # 500 lookups devem ser muito rápidas
        assert lookup_time < 0.1

    @pytest.mark.unit
    def test_mcp_protocol_overhead(self, mcp_server_instance):
        """Testa overhead do protocolo MCP."""
        import json
        
        # Simular request complexo
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "execute_query",
                "arguments": {
                    "sql": "SELECT * FROM CUSTOMERS WHERE CITY = ?",
                    "params": ["São Paulo"]
                }
            },
            "id": 1
        }
        
        with patch.object(server.firebird_server, 'execute_query') as mock_execute:
            mock_execute.return_value = {
                'success': True,
                'data': [{'ID': i, 'NAME': f'Customer {i}'} for i in range(100)],
                'row_count': 100
            }
            
            # Medir tempo de processamento
            start_time = time.time()
            
            for _ in range(100):
                mcp_server_instance.handle_request(request)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # 100 requests devem ser processados rapidamente
            assert processing_time < 1.0
            
            # Média por request
            avg_time = processing_time / 100
            assert avg_time < 0.01  # Menos de 10ms por request


class TestScalabilityTests:
    """Testes de escalabilidade."""

    @pytest.mark.slow
    @pytest.mark.unit
    def test_increasing_data_size(self, mock_fdb, mock_library_detection):
        """Testa escalabilidade com aumento do tamanho dos dados."""
        data_sizes = [100, 1000, 5000, 10000]
        times = []
        
        for size in data_sizes:
            # Mock para dados de tamanho variável
            mock_cursor = Mock()
            mock_cursor.description = [('ID',), ('DATA',)]
            mock_cursor.fetchall.return_value = [
                (i, f'Data {i}') for i in range(size)
            ]
            
            mock_connection = Mock()
            mock_connection.cursor.return_value = mock_cursor
            mock_fdb.connect.return_value = mock_connection
            
            fb_server = server.FirebirdMCPServer()
            
            # Medir tempo
            start_time = time.time()
            result = fb_server.execute_query("SELECT * FROM TEST_TABLE")
            end_time = time.time()
            
            assert result['success'] is True
            assert result['row_count'] == size
            
            times.append(end_time - start_time)
        
        # Verificar que crescimento é aproximadamente linear
        # (em mock, deve ser quase constante)
        for t in times:
            assert t < 0.1  # Todos devem ser muito rápidos

    @pytest.mark.slow
    @pytest.mark.unit
    def test_increasing_connection_count(self, mock_fdb, mock_library_detection):
        """Testa escalabilidade com aumento de conexões."""
        import threading
        
        connection_counts = [1, 5, 10, 20]
        
        for count in connection_counts:
            # Mock para múltiplas conexões
            mock_cursor = Mock()
            mock_cursor.fetchone.return_value = ['3.0.10']
            
            mock_connection = Mock()
            mock_connection.cursor.return_value = mock_cursor
            mock_fdb.connect.return_value = mock_connection
            
            results = []
            
            def test_connection():
                fb_server = server.FirebirdMCPServer()
                result = fb_server.test_connection()
                results.append(result)
            
            # Executar threads
            threads = []
            start_time = time.time()
            
            for _ in range(count):
                thread = threading.Thread(target=test_connection)
                threads.append(thread)
                thread.start()
            
            for thread in threads:
                thread.join()
            
            end_time = time.time()
            total_time = end_time - start_time
            
            assert len(results) == count
            assert all(r['connected'] for r in results)
            
            # Deve escalar bem (mock é instantâneo)
            assert total_time < 1.0

    @pytest.mark.unit
    def test_memory_stability_over_time(self, mock_fdb, mock_library_detection):
        """Testa estabilidade de memória ao longo do tempo."""
        try:
            import psutil
        except ImportError:
            pytest.skip("psutil não disponível")
        
        # Mock padrão
        mock_cursor = Mock()
        mock_cursor.description = [('ID',)]
        mock_cursor.fetchall.return_value = [(1,)]
        
        mock_connection = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_fdb.connect.return_value = mock_connection
        
        fb_server = server.FirebirdMCPServer()
        process = psutil.Process()
        
        # Executar muitas operações
        memory_samples = []
        
        for i in range(100):
            result = fb_server.execute_query("SELECT 1 FROM RDB$DATABASE")
            assert result['success'] is True
            
            if i % 10 == 0:  # Amostrar a cada 10 operações
                memory_samples.append(process.memory_info().rss)
        
        # Verificar que memória não cresce indefinidamente
        memory_growth = max(memory_samples) - min(memory_samples)
        
        # Crescimento deve ser limitado (10MB max para 100 operações)
        assert memory_growth < 10 * 1024 * 1024


class TestStressTests:
    """Testes de stress."""

    @pytest.mark.slow
    @pytest.mark.unit
    def test_rapid_fire_requests(self, mcp_server_instance):
        """Testa requests em sequência rápida."""
        with patch.object(server.firebird_server, 'test_connection') as mock_test:
            mock_test.return_value = {'connected': True, 'version': '3.0.10'}
            
            request = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {"name": "test_connection", "arguments": {}},
                "id": 1
            }
            
            # Executar 1000 requests rapidamente
            start_time = time.time()
            
            for _ in range(1000):
                mcp_server_instance.handle_request(request)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Deve processar 1000 requests rapidamente
            assert total_time < 5.0
            
            # Rate mínimo
            requests_per_second = 1000 / total_time
            assert requests_per_second > 200

    @pytest.mark.slow
    @pytest.mark.unit
    def test_error_recovery_stress(self, mock_fdb, mock_library_detection):
        """Testa recuperação de erros sob stress."""
        fb_server = server.FirebirdMCPServer()
        
        # Alternar entre sucesso e erro
        success_count = 0
        error_count = 0
        
        for i in range(100):
            if i % 2 == 0:
                # Mock de sucesso
                mock_cursor = Mock()
                mock_cursor.fetchall.return_value = [(1,)]
                mock_connection = Mock()
                mock_connection.cursor.return_value = mock_cursor
                mock_fdb.connect.return_value = mock_connection
                
                result = fb_server.execute_query("SELECT 1")
                if result.get('success'):
                    success_count += 1
            else:
                # Mock de erro
                mock_fdb.connect.side_effect = Exception("Connection error")
                
                result = fb_server.execute_query("SELECT 1")
                if not result.get('success'):
                    error_count += 1
        
        # Deve ter recuperado de erros adequadamente
        assert success_count > 0
        assert error_count > 0
        
        # Sistema deve ter processado todas as tentativas
        assert success_count + error_count == 100

    @pytest.mark.slow
    @pytest.mark.unit
    def test_large_json_response_handling(self, mcp_server_instance):
        """Testa handling de respostas JSON grandes."""
        # Simular query que retorna muito dados
        large_data = {
            'success': True,
            'data': [
                {
                    'id': i,
                    'name': f'Customer {i}',
                    'description': f'A very long description for customer {i} ' * 20,
                    'metadata': {'field_{j}': f'value_{j}' for j in range(10)}
                }
                for i in range(1000)
            ],
            'row_count': 1000
        }
        
        with patch.object(server.firebird_server, 'execute_query') as mock_execute:
            mock_execute.return_value = large_data
            
            request = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "execute_query",
                    "arguments": {"sql": "SELECT * FROM LARGE_TABLE"}
                },
                "id": 1
            }
            
            # Deve processar sem erro
            start_time = time.time()
            mcp_server_instance.handle_request(request)
            end_time = time.time()
            
            # Deve ser razoavelmente rápido mesmo com dados grandes
            assert (end_time - start_time) < 1.0
