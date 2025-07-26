# Testes do MCP Server Firebird

Este diretório contém todos os testes unitários e de integração para o projeto.

## Estrutura

```
tests/
├── unit/                        # Testes unitários
│   ├── test_schema_prompts.py  # Testes dos novos prompts dinâmicos
│   ├── test_prompt_system.py   # Testes do sistema de prompts (atualizado)
│   ├── test_firebird_server.py # Testes do servidor Firebird
│   ├── test_i18n.py            # Testes de internacionalização
│   ├── test_mcp_server.py      # Testes do servidor MCP
│   ├── test_performance.py     # Testes de performance
│   └── test_sql_analyzer.py    # Testes do analisador SQL
├── integration/                 # Testes de integração
└── conftest.py                 # Configurações globais do pytest
```

## Executando os Testes

### Todos os Testes
```bash
python -m pytest tests/ -v
```

### Testes Específicos

#### Novos Prompts Dinâmicos de Schema
```bash
python -m pytest tests/unit/test_schema_prompts.py -v
```

#### Sistema de Prompts (Atualizado)
```bash
python -m pytest tests/unit/test_prompt_system.py -v
```

#### Servidor Firebird
```bash
python -m pytest tests/unit/test_firebird_server.py -v
```

#### Internacionalização
```bash
python -m pytest tests/unit/test_i18n.py -v
```

### Testes com Cobertura
```bash
python -m pytest tests/ --cov=src --cov-report=html
```

## Novos Testes Implementados

### `test_schema_prompts.py`
Testa o novo sistema de prompts dinâmicos baseados em schemas de tabelas:

- **Chaves i18n**: Valida novas chaves de tradução em pt_BR e en_US
- **Geração sem servidor**: Testa comportamento quando servidor Firebird não está disponível
- **Mock de servidor**: Testa geração de prompts com dados simulados
- **Estrutura de prompts**: Valida se os prompts gerados têm a estrutura correta
- **Tratamento de erros**: Verifica tratamento adequado de erros
- **Método generate**: Testa o método principal de geração de prompts

### `test_prompt_system.py` (Atualizado)
Atualizado para refletir as mudanças nos prompts dinâmicos:

- **Manager**: Testes do DefaultPromptManager mantidos
- **Generator**: Testes adaptados para nova arquitetura de prompts
- **Relacionamentos**: Testes específicos para tabelas com chaves estrangeiras

## Fixtures e Mocks

Os testes utilizam classes mock para simular:

- **MockFirebirdServer**: Simula servidor Firebird com dados de teste
- **MockFirebirdServerWithError**: Simula erros do servidor
- **Dados de Schema**: Estruturas completas de tabelas com colunas, chaves e índices

## Configuração

### Pré-requisitos
```bash
pip install pytest pytest-cov
```

### Variáveis de Ambiente para Testes
```bash
export FIREBIRD_DEFAULT_PROMPT_ENABLED=true
export FIREBIRD_DEFAULT_PROMPT=firebird_expert
```

## Cenários de Teste

### Prompts Dinâmicos
- ✅ Geração de prompts para cada tabela detectada
- ✅ Informações completas de schema (colunas, chaves, índices)
- ✅ Relacionamentos entre tabelas (FK -> PK)
- ✅ Orientações de uso específicas
- ✅ Suporte a internacionalização

### Compatibilidade
- ✅ Sistema de contexto especialista preservado
- ✅ Ferramentas MCP mantidas
- ✅ Funcionalidades existentes não afetadas

### Tratamento de Erros
- ✅ Servidor indisponível
- ✅ Tabelas inexistentes
- ✅ Schemas inválidos
- ✅ Erros de conexão

## Evolução dos Testes

### Antes (Prompts Estáticos)
- Testes para `firebird_expert`, `firebird_performance`, `firebird_architecture`
- Prompts fixos com argumentos parametrizáveis
- Lista estática de prompts disponíveis

### Depois (Prompts Dinâmicos)
- Testes para prompts `TABELA_schema` gerados dinamicamente
- Conteúdo baseado na estrutura real do banco
- Lista dinâmica baseada nas tabelas detectadas

## Métricas de Cobertura

Os testes cobrem:
- ✅ Geração de prompts dinâmicos
- ✅ Extração de schema de tabelas
- ✅ Tratamento de erros e fallbacks
- ✅ Internacionalização de conteúdo
- ✅ Integração com sistema MCP

Execute `pytest --cov` para métricas detalhadas de cobertura.
