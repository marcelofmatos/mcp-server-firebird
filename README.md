# MCP Server Firebird

Um servidor MCP (Model Context Protocol) completo para conectar a bancos de dados Firebird externos. Este servidor permite que assistentes de IA executem queries SQL, listem tabelas e gerenciem conexões com bancos Firebird de forma segura e eficiente.

## 📦 Índice

- [🔥 Características](#-características)
- [🌍 Internacionalização](#-internacionalização)
- [🚀 Instalação Rápida](#-instalação-rápida)
- [⚙️ Configuração](#️-configuração)
- [🛠️ Ferramentas MCP](#️-ferramentas-mcp-disponíveis)
- [🧪 Desenvolvimento e Testes](#-desenvolvimento-e-testes)
- [🔍 Troubleshooting](#-troubleshooting)
- [📊 Exemplos de Uso](#-exemplos-de-uso)
- [🤝 Contribuição](#-contribuição)

## 🔥 Características

- ✅ **Protocolo MCP Completo** - Implementa todas as especificações do MCP 2024-11-05
- ✅ **Firebird 3.0.10 Oficial** - Bibliotecas cliente incluídas no container
- ✅ **Auto-contido** - Não precisa de volumes ou instalações no host
- ✅ **Diagnósticos Inteligentes** - Detecta e resolve problemas automaticamente
- ✅ **Conexões Externas** - Conecta a qualquer servidor Firebird remoto
- ✅ **4 Ferramentas MCP** - test_connection, execute_query, list_tables, server_status
- ✅ **Seguro** - Usuário não-root, health check integrado
- ✅ **Internacionalização** - Suporte a múltiplos idiomas (pt_BR, en_US)
- ✅ **Testes Abrangentes** - Cobertura de testes > 80% com testes unitários e de integração
- ✅ **Qualidade de Código** - Linting, formatação automática e verificações de segurança
- ✅ **CI/CD Automatizado** - Pipeline completo com GitHub Actions
- 🎯 **Sistema de Prompt Padrão** - Aplica automaticamente contexto expert quando as respostas iniciarem o uso do servidor MCP
- 🧠 **3 Prompts Especializados** - firebird_expert, firebird_performance, firebird_architecture

## 🌍 Internacionalização

O servidor suporta múltiplos idiomas através de arquivos JSON centralizados:

- **Idiomas disponíveis**: Português (pt_BR), Inglês (en_US)
- **Configuração automática**: Via variáveis `FIREBIRD_LANGUAGE` ou `LANG`
- **Fallback inteligente**: Usa inglês se idioma não encontrado
- **Strings localizadas**: Mensagens de erro, logs, diagnósticos e prompts
- **Fácil expansão**: Adicione novos idiomas criando arquivos JSON em `i18n/`

### Configuração de Idioma

```bash
# Português
docker run -e FIREBIRD_LANGUAGE=pt_BR ...

# Inglês (padrão)
docker run -e FIREBIRD_LANGUAGE=en_US ...

# Automático via LANG
export LANG=pt_BR.UTF-8
```

## 🎯 Sistema de Prompt Padrão

O MCP Firebird inclui um sistema inovador que **automaticamente aplica contexto expert** ao iniciar as respostas caso o servidor MCP seja requisitado, sem necessidade de configuração manual e aprimorando o uso da ferramenta.

### 🚀 Funcionalidades

- **🤖 Aplicação Automática**: Contexto firebird_expert por padrão no início da interação.
- **🔧 Configuração Flexível**: Via environment variables ou tool parameters
- **📊 Níveis de Complexidade**: basic, intermediate, advanced
- **⏭️ Override Granular**: Desabilitar por tool call ou mudar operação

### 📝 Configurações Rápidas

```bash
# Configuração Expert (padrão)
source .env

# Ou usar configurador
./scripts/quick_config.sh

# Configurações alternativas:
export FIREBIRD_DEFAULT_PROMPT=firebird_performance  # Foco em performance
export FIREBIRD_DEFAULT_PROMPT=firebird_architecture # Foco em administração
export FIREBIRD_DEFAULT_PROMPT_ENABLED=false         # Desabilitar
```

### 🎯 Exemplo de primeira resposta

**Com Expert Mode (padrão):**
```
🔥 **FIREBIRD EXPERT MODE ACTIVE**

**Environment:** localhost:3050 | DB: database.fdb | User: SYSDBA
**Expert Guidelines (intermediate level):**
✅ Provide Firebird-specific solutions
✅ Consider performance implications
✅ Include practical examples
✅ Answer language {lang}

---

📊 Query Results: {...}
```

**Desabilitar temporariamente:**
```json
{"tool": "execute_query", "arguments": {"sql": "SELECT...", "disable_expert_mode": true}}
```



## 🚀 Instalação Rápida

### Pré-requisitos

- Docker instalado
- Acesso a um servidor Firebird externo
- Informações de conexão (host, porta, banco, usuário, senha)

### Execução Básica

```bash
docker run -d \
  --name mcp-firebird \
  -e FIREBIRD_HOST=192.168.1.50 \
  -e FIREBIRD_DATABASE=/dados/sistema.fdb \
  -e FIREBIRD_USER=SYSDBA \
  -e FIREBIRD_PASSWORD=masterkey \
  ghcr.io/marcelofmatos/mcp-server-firebird:latest
```

### Verificar Status

```bash
# Ver logs do container
docker logs mcp-firebird

# Verificar se está rodando
docker ps | grep mcp-firebird
```

## ⚙️ Configuração

### Variáveis de Ambiente

| Variável | Descrição | Padrão | Obrigatório |
|----------|-----------|--------|-------------|
| `FIREBIRD_HOST` | Endereço do servidor Firebird | `localhost` | ✅ |
| `FIREBIRD_PORT` | Porta do servidor Firebird | `3050` | ❌ |
| `FIREBIRD_DATABASE` | Caminho completo do banco | `/path/to/database.fdb` | ✅ |
| `FIREBIRD_USER` | Usuário do banco | `SYSDBA` | ❌ |
| `FIREBIRD_PASSWORD` | Senha do usuário | `masterkey` | ✅ |
| `FIREBIRD_CHARSET` | Charset da conexão | `UTF8` | ❌ |
| `FIREBIRD_LANGUAGE` | Idioma das mensagens | `en_US` | ❌ |
| `MCP_SERVER_NAME` | Nome do servidor MCP | `firebird-expert-server` | ❌ |
| `MCP_SERVER_VERSION` | Versão do servidor | `1.0.0` | ❌ |

### Exemplos de Configuração

#### 1. Servidor Local
```bash
docker run -d \
  --name mcp-firebird-local \
  -e FIREBIRD_HOST=localhost \
  -e FIREBIRD_DATABASE=/var/lib/firebird/employee.fdb \
  -e FIREBIRD_PASSWORD=sua_senha \
  -e FIREBIRD_LANGUAGE=pt_BR \
  ghcr.io/marcelofmatos/mcp-server-firebird:latest
```

#### 2. Servidor Corporativo
```bash
docker run -d \
  --name mcp-firebird-corp \
  -e FIREBIRD_HOST=firebird.empresa.com \
  -e FIREBIRD_PORT=3050 \
  -e FIREBIRD_DATABASE=/aplicacao/sistema.fdb \
  -e FIREBIRD_USER=APP_USER \
  -e FIREBIRD_PASSWORD=senha_segura \
  -e FIREBIRD_CHARSET=ISO8859_1 \
  ghcr.io/marcelofmatos/mcp-server-firebird:latest
```

#### 3. Servidor em VPS
```bash
docker run -d \
  --name mcp-firebird-vps \
  -e FIREBIRD_HOST=10.20.30.40 \
  -e FIREBIRD_DATABASE=/home/dados/banco.fdb \
  -e FIREBIRD_USER=USUARIO_DB \
  -e FIREBIRD_PASSWORD=password123 \
  ghcr.io/marcelofmatos/mcp-server-firebird:latest
```

## 🛠️ Ferramentas MCP Disponíveis

### 1. test_connection
Testa a conexão com o banco Firebird e fornece diagnósticos detalhados.

**Uso:**
```json
{
  "name": "test_connection"
}
```

**Retorna:**
- Status da conexão
- Versão do Firebird
- Diagnósticos de problemas
- Soluções específicas

### 2. execute_query
Executa queries SQL no banco Firebird.

**Uso:**
```json
{
  "name": "execute_query",
  "arguments": {
    "sql": "SELECT * FROM CUSTOMERS WHERE CITY = ?",
    "params": ["São Paulo"]
  }
}
```

**Suporta:**
- SELECT (retorna dados)
- INSERT, UPDATE, DELETE (retorna linhas afetadas)
- Queries parametrizadas
- Transações automáticas

### 3. list_tables
Lista todas as tabelas de usuário do banco.

**Uso:**
```json
{
  "name": "list_tables"
}
```

**Retorna:**
- Lista de tabelas
- Contador de tabelas
- Nome do banco

### 4. server_status
Mostra status completo do servidor MCP e bibliotecas.

**Uso:**
```json
{
  "name": "server_status"
}
```

**Retorna:**
- Status das bibliotecas FDB e Firebird
- Configuração atual
- Teste de conexão
- Recomendações

## 🎯 Prompts Especialistas Disponíveis

O servidor inclui prompts especialistas dinâmicos:

### 1. firebird_expert
Assistente especialista em Firebird com conhecimento profundo do SGBD.

### 2. firebird_performance
Especialista em otimização e performance para Firebird.

### 3. firebird_architecture
Especialista em arquitetura e administração Firebird.

## 🧪 Desenvolvimento e Testes

### Configuração do Ambiente de Desenvolvimento

```bash
# Clonar repositório
git clone https://github.com/marcelofmatos/mcp-server-firebird
cd mcp-server-firebird

# Configurar ambiente completo
make setup-dev

# Ou manual:
./scripts/setup-dev.sh
```

### Executando Testes

O projeto possui uma suíte completa de testes:

```bash
# Todos os testes
make test-all

# Apenas testes unitários
make test-unit

# Testes de integração
make test-integration

# Testes de performance
make test-performance

# Execução rápida (sem testes lentos)
make test-fast

# Com relatório de cobertura HTML
make test-coverage
```

### Qualidade de Código

```bash
# Verificações de qualidade
make lint

# Corrigir problemas automaticamente
make lint-fix

# Formatação de código
make format

# Verificação de tipos
make type-check

# Verificação de segurança
make security-check

# Pre-commit hooks
make pre-commit
```

### Estrutura de Testes

```
tests/
├── unit/                    # Testes unitários
│   ├── test_firebird_server.py
│   ├── test_mcp_server.py
│   ├── test_i18n.py
│   └── test_performance.py
├── integration/             # Testes de integração
│   ├── test_firebird_integration.py
│   └── docker-compose-test.yml
├── conftest.py             # Configurações compartilhadas
└── __init__.py
```

### Cobertura de Testes

O projeto mantém cobertura de testes superior a 80%:

- **Testes unitários**: 150+ testes cobrindo todas as funções principais
- **Testes de integração**: Validação com containers Firebird reais
- **Testes de performance**: Benchmarks e testes de escalabilidade
- **Testes de segurança**: Verificação de vulnerabilidades

### Comandos de Desenvolvimento

```bash
# Ambiente de desenvolvimento completo
make dev

# Executar servidor local (sem Docker)
make dev-server

# Monitorar mudanças
make watch

# Relatório de cobertura
make coverage-report

# Benchmark de performance
make benchmark

# Limpeza completa
make clean-all
```

### CI/CD Pipeline

O projeto inclui pipeline completo no GitHub Actions:

- **Verificações de código**: Ruff, Black, MyPy, Bandit
- **Testes multi-versão**: Python 3.8-3.12
- **Testes de integração**: Com Firebird real
- **Build Docker**: Verificação de container
- **Scan de segurança**: Trivy e CodeQL
- **Relatórios**: Coverage, benchmarks, artefatos

## 🔍 Troubleshooting

### Problema: Container não inicia

**Sintomas:**
```bash
docker logs mcp-firebird
# Erro: FDB library not available
```

**Solução:**
```bash
# Rebuildar/baixar imagem mais recente
docker pull ghcr.io/marcelofmatos/mcp-server-firebird:latest
docker run --rm -it ghcr.io/marcelofmatos/mcp-server-firebird:latest python3 -c "import fdb; print('OK')"
```

### Problema: Erro de conexão de rede

**Sintomas:**
```
❌ Connection failed: network error
💡 NETWORK ISSUE: Cannot reach 192.168.1.50:3050
```

**Soluções:**
1. Verificar se o servidor Firebird está rodando
2. Testar conectividade de rede:
   ```bash
   # Do host Docker
   telnet 192.168.1.50 3050
   ```
3. Verificar firewall
4. Confirmar host e porta

### Problema: Erro de autenticação

**Sintomas:**
```
❌ Connection failed: login error
💡 AUTHENTICATION ISSUE: Invalid credentials
```

**Soluções:**
1. Verificar usuário e senha:
   ```bash
   docker run --rm \
     -e FIREBIRD_HOST=seu.servidor \
     -e FIREBIRD_PASSWORD=senha_correta \
     ghcr.io/marcelofmatos/mcp-server-firebird:latest
   ```
2. Confirmar que usuário existe no Firebird
3. Testar conexão com ferramenta externa (FlameRobin, IBExpert)

### Problema: Banco não encontrado

**Sintomas:**
```
❌ Connection failed: database not found
💡 DATABASE ISSUE: Database file not found
```

**Soluções:**
1. Verificar caminho do banco:
   ```bash
   # Caminho deve ser absoluto no servidor Firebird
   -e FIREBIRD_DATABASE=/caminho/completo/banco.fdb
   ```
2. Confirmar que arquivo existe no servidor
3. Verificar permissões do arquivo

### Problema: Dependências faltando

**Sintomas:**
```
❌ Connection failed: libtommath.so.0: cannot open shared object file
```

**Soluções:**
1. Usar a imagem oficial mais recente:
   ```bash
   docker pull ghcr.io/marcelofmatos/mcp-server-firebird:latest
   ```
2. Se persistir, reportar issue no GitHub

## 📊 Exemplos de Uso

### Exemplo 1: Teste de Conectividade
```bash
# Iniciar container
docker run -d \
  --name firebird-test \
  -e FIREBIRD_HOST=192.168.1.100 \
  -e FIREBIRD_DATABASE=/dados/teste.fdb \
  -e FIREBIRD_PASSWORD=123456 \
  ghcr.io/marcelofmatos/mcp-server-firebird:latest

# Verificar logs
docker logs firebird-test

# Resultado esperado:
# [MCP-FIREBIRD] ✅ Database connection OK - Firebird 3.0.x
```

### Exemplo 2: Consulta de Dados
Use a ferramenta `execute_query` via MCP para:
```sql
-- Listar clientes
SELECT CUSTOMER_ID, COMPANY_NAME, CITY 
FROM CUSTOMERS 
WHERE COUNTRY = 'Brasil'
ORDER BY COMPANY_NAME

-- Contar registros
SELECT COUNT(*) as TOTAL_CUSTOMERS 
FROM CUSTOMERS

-- Inserir dados
INSERT INTO CUSTOMERS (CUSTOMER_ID, COMPANY_NAME, CITY) 
VALUES ('NEW01', 'Nova Empresa', 'São Paulo')
```

### Exemplo 3: Monitoramento
```bash
# Container com restart automático
docker run -d \
  --name mcp-firebird-prod \
  --restart unless-stopped \
  --health-cmd="python3 -c 'import fdb; print(\"OK\")'" \
  --health-interval=30s \
  --health-timeout=10s \
  --health-retries=3 \
  -e FIREBIRD_HOST=prod.empresa.com \
  -e FIREBIRD_DATABASE=/sistema/producao.fdb \
  -e FIREBIRD_USER=SYS_USER \
  -e FIREBIRD_PASSWORD="$PROD_PASSWORD" \
  ghcr.io/marcelofmatos/mcp-server-firebird:latest

# Monitorar health
docker inspect mcp-firebird-prod | grep -A 5 Health
```

## 🐳 Docker Compose

Exemplo de `docker-compose.yml`:

```yaml
version: '3.8'

services:
  mcp-firebird:
    image: ghcr.io/marcelofmatos/mcp-server-firebird:latest
    container_name: mcp-firebird-server
    restart: unless-stopped
    environment:
      - FIREBIRD_HOST=firebird.empresa.com
      - FIREBIRD_PORT=3050
      - FIREBIRD_DATABASE=/aplicacao/sistema.fdb
      - FIREBIRD_USER=APP_USER
      - FIREBIRD_PASSWORD=senha_segura
      - FIREBIRD_CHARSET=UTF8
      - FIREBIRD_LANGUAGE=pt_BR
    healthcheck:
      test: ["CMD", "python3", "-c", "import fdb; print('OK')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # Firebird para testes (opcional)
  firebird-test:
    image: jacobalberty/firebird:v4.0
    container_name: firebird-test-db
    environment:
      - FIREBIRD_DATABASE=test.fdb
      - FIREBIRD_USER=SYSDBA
      - FIREBIRD_PASSWORD=test123
      - ISC_PASSWORD=test123
    ports:
      - "3050:3050"
    volumes:
      - firebird_data:/firebird/data
    profiles:
      - testing

volumes:
  firebird_data:
    driver: local
```

Executar:
```bash
# Produção
docker-compose up -d

# Com Firebird de teste
docker-compose --profile testing up -d

# Logs
docker-compose logs -f mcp-firebird
```

## 🔧 Desenvolvimento Avançado

### Build Local
```bash
# Clonar repositório
git clone https://github.com/marcelofmatos/mcp-server-firebird
cd mcp-server-firebird

# Build da imagem
make build

# Testar localmente
make dev
```

### Estrutura do Projeto
```
mcp-server-firebird/
├── server.py               # Servidor MCP principal
├── requirements.txt        # Dependências de produção
├── requirements-dev.txt    # Dependências de desenvolvimento
├── pyproject.toml         # Configuração do projeto
├── Dockerfile             # Container de produção
├── docker-compose.yml     # Orquestração
├── Makefile              # Comandos de automação
├── .pre-commit-config.yaml # Hooks de qualidade
├── scripts/              # Scripts auxiliares
│   ├── run-tests.sh      # Executor de testes
│   └── setup-dev.sh      # Setup de desenvolvimento
├── tests/                # Testes abrangentes
│   ├── unit/            # Testes unitários
│   ├── integration/     # Testes de integração
│   └── conftest.py      # Configurações de teste
├── i18n/                # Internacionalização
│   ├── en_US.json       # Inglês (padrão)
│   └── pt_BR.json       # Português brasileiro
├── .github/             # CI/CD
│   └── workflows/
│       ├── tests.yml    # Pipeline de testes
│       └── docker-image.yml # Build e deploy
└── README.md           # Esta documentação
```

### Comandos Make Disponíveis

```bash
# Ambiente
make setup-dev          # Configuração completa de desenvolvimento
make install-deps       # Instalar dependências

# Testes
make test-all           # Todos os testes
make test-unit          # Testes unitários
make test-integration   # Testes de integração
make test-performance   # Testes de performance
make test-fast          # Execução rápida
make test-coverage      # Com relatório HTML

# Qualidade
make lint               # Verificações de código
make lint-fix           # Corrigir automaticamente
make format            # Formatação
make type-check        # Verificação de tipos
make security-check    # Verificação de segurança
make pre-commit        # Pre-commit hooks

# Docker
make build             # Build da imagem
make run               # Executar container
make dev               # Ambiente de desenvolvimento
make logs              # Ver logs

# Utilitários
make clean-all         # Limpeza completa
make coverage-report   # Relatório de cobertura
make benchmark         # Benchmark de performance
make health-check      # Verificar saúde do sistema
```

## 📚 Recursos Adicionais

- **Especificação MCP**: [Model Context Protocol](https://spec.modelcontextprotocol.io/)
- **Documentação Firebird**: [Firebird Documentation](https://firebirdsql.org/en/documentation/)
- **FDB Python Driver**: [python-fdb](https://github.com/FirebirdSQL/fdb)
- **Pytest Documentation**: [Testing Framework](https://docs.pytest.org/)
- **Docker Best Practices**: [Container Guidelines](https://docs.docker.com/develop/dev-best-practices/)

## 🤝 Contribuição

Contribuições são bem-vindas! Por favor, siga nosso guia de contribuição:

### Fluxo de Desenvolvimento

1. **Fork do repositório**
2. **Configurar ambiente local**:
   ```bash
   git clone https://github.com/seu-usuario/mcp-server-firebird
   cd mcp-server-firebird
   make setup-dev
   ```
3. **Criar branch para feature**:
   ```bash
   git checkout -b feature/nova-funcionalidade
   ```
4. **Desenvolver com testes**:
   ```bash
   # Desenvolvimento iterativo
   make test-fast      # Testes rápidos durante desenvolvimento
   make lint-fix       # Correções automáticas
   make test-all       # Teste completo antes de commit
   ```
5. **Commit das mudanças**:
   ```bash
   git add .
   git commit -m "feat: adicionar nova funcionalidade"
   ```
6. **Push e Pull Request**

### Padrões de Qualidade

- **Cobertura de testes**: Mínimo 80%
- **Linting**: Código deve passar em todas as verificações (ruff, black, mypy, bandit)
- **Documentação**: Novas funcionalidades devem ser documentadas
- **Testes**: Toda funcionalidade deve ter testes unitários
- **Commits**: Usar [Conventional Commits](https://www.conventionalcommits.org/)

### Executando Localmente

```bash
# Verificações antes do commit
make pre-commit

# Pipeline completo como no CI
make test-all
make lint
make build
```

## 🔒 Segurança

### Práticas de Segurança Implementadas

- **Usuário não-root** no container
- **Scanning de vulnerabilidades** com Trivy e Bandit
- **Dependências auditadas** regularmente
- **Secrets não expostos** em logs
- **Validação de entrada** em todas as queries
- **Prepared statements** para prevenir SQL injection

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🆘 Suporte

- **Issues**: [GitHub Issues](https://github.com/marcelofmatos/mcp-server-firebird/issues)
- **Discussões**: [GitHub Discussions](https://github.com/marcelofmatos/mcp-server-firebird/discussions)
- **Wiki**: [Project Wiki](https://github.com/marcelofmatos/mcp-server-firebird/wiki)

### Status dos Badges

![Tests](https://github.com/marcelofmatos/mcp-server-firebird/workflows/Tests%20and%20Quality%20Checks/badge.svg)
![Docker](https://github.com/marcelofmatos/mcp-server-firebird/workflows/Docker%20image%20on%20GHCR/badge.svg)
![Coverage](https://codecov.io/gh/marcelofmatos/mcp-server-firebird/branch/main/graph/badge.svg)
![Security](https://img.shields.io/badge/security-bandit-green)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![Firebird](https://img.shields.io/badge/firebird-3.0%2B-orange)

---

## 🏷️ Tags da Imagem

- `latest` - Versão mais recente estável
- `1.0.0` - Versão específica
- `main` - Versão de desenvolvimento

```bash
# Usar versão específica
docker pull ghcr.io/marcelofmatos/mcp-server-firebird:1.0.0

# Usar versão de desenvolvimento
docker pull ghcr.io/marcelofmatos/mcp-server-firebird:main
```

---

**Feito com ❤️ para a comunidade Firebird e MCP**

**[⬆ Voltar ao topo](#mcp-server-firebird)**
