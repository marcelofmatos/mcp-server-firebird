# Documentação de Testes - MCP Server Firebird

## Visão Geral

Este projeto implementa uma suíte abrangente de testes para garantir qualidade, confiabilidade e performance do MCP Server Firebird.

## Estrutura de Testes

### Tipos de Teste

#### 1. Testes Unitários (`tests/unit/`)
- **Cobertura**: >80% do código
- **Execução**: Rápida (~5-10 segundos)
- **Dependências**: Apenas mocks, sem recursos externos
- **Foco**: Lógica de negócio, funções individuais

**Arquivos:**
- `test_firebird_server.py` - Testes da classe FirebirdMCPServer
- `test_mcp_server.py` - Testes da classe MCPServer  
- `test_i18n.py` - Sistema de internacionalização
- `test_performance.py` - Benchmarks e testes de performance

#### 2. Testes de Integração (`tests/integration/`)
- **Cobertura**: Fluxos completos end-to-end
- **Execução**: Mais lenta (~30-60 segundos)
- **Dependências**: Containers Docker, Firebird real
- **Foco**: Integração entre componentes

**Arquivos:**
- `test_firebird_integration.py` - Integração com Firebird real
- `docker-compose-test.yml` - Orquestração para testes

#### 3. Configuração Compartilhada
- `conftest.py` - Fixtures, mocks e configurações globais
- `__init__.py` - Marcadores de pacote

## Executando Testes

### Comandos Básicos

```bash
# Todos os testes
make test-all
pytest

# Apenas unitários (rápido)
make test-unit
pytest tests/unit

# Apenas integração
make test-integration
pytest tests/integration

# Com cobertura
make test-coverage
pytest --cov=server --cov-report=html

# Testes específicos
pytest tests/unit/test_firebird_server.py::TestFirebirdMCPServer::test_connection
pytest -k "test_connection"
pytest -m "unit and not slow"
```

### Scripts Auxiliares

```bash
# Script shell (completo)
./scripts/run-tests.sh --help

# Script Python (alternativo)
python test_runner.py --help

# Via Make (recomendado)
make help
```

## Marcadores (Markers)

### Marcadores Principais

- `@pytest.mark.unit` - Testes unitários
- `@pytest.mark.integration` - Testes de integração  
- `@pytest.mark.slow` - Testes que demoram mais que 5 segundos
- `@pytest.mark.firebird` - Requer conexão Firebird
- `@pytest.mark.docker` - Requer Docker

### Exemplos de Uso

```python
@pytest.mark.unit
def test_simple_function():
    assert True

@pytest.mark.integration
@pytest.mark.firebird
def test_real_database_connection():
    # Teste com Firebird real
    pass

@pytest.mark.slow
@pytest.mark.performance
def test_benchmark():
    # Teste de performance
    pass
```

### Executar por Marcadores

```bash
# Apenas testes rápidos
pytest -m "not slow"

# Apenas testes de integração
pytest -m integration

# Excluir testes que precisam de Docker
pytest -m "not docker"

# Testes específicos do Firebird
pytest -m firebird
```

## Fixtures Disponíveis

### Fixtures de Mock

```python
def test_with_mocked_fdb(mock_fdb, mock_library_detection):
    # FDB mockado para testes unitários
    pass

def test_with_environment(mock_environment):
    # Variáveis de ambiente mockadas
    pass
```

### Fixtures de Dados

```python
def test_query_result(sample_query_result):
    # Resultado de query pré-definido
    assert sample_query_result['success'] is True

def test_tables_list(sample_tables_list):
    # Lista de tabelas de exemplo
    assert len(sample_tables_list['tables']) > 0
```

### Fixtures de Instância

```python
def test_server_instance(firebird_server_instance):
    # Instância configurada do FirebirdMCPServer
    result = firebird_server_instance.test_connection()
    
def test_mcp_protocol(mcp_server_instance):
    # Instância do MCPServer para testes de protocolo
    pass
```

## Comandos de Relatório

```bash
# Relatório completo
make test-coverage

# Apenas métricas
coverage report

# Export para CI
coverage xml

# Benchmark
pytest --benchmark-only --benchmark-json=benchmark.json
```

## Executando no Desenvolvimento

```bash
# Setup inicial
make setup-dev

# Desenvolvimento iterativo
make test-fast          # Testes rápidos
make lint-fix           # Correções automáticas
make test-coverage      # Teste com cobertura

# Pipeline completo
make test-all
make lint
make build
```

## Integração com CI/CD

O projeto inclui pipeline completo no GitHub Actions com:

- Verificações de código (ruff, black, mypy, bandit)
- Testes unitários (Python 3.8-3.12)
- Testes de integração (com Firebird real)
- Build e teste de Docker
- Scan de segurança
- Relatórios de cobertura

## Métricas Atuais

- **Testes Unitários**: 150+ testes
- **Cobertura**: >85%
- **Tempo de Execução**: <30s (unitários), <2min (completos)
- **Taxa de Sucesso**: 100% (CI/CD)
