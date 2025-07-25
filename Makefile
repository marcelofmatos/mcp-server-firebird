# Makefile para Servidor MCP Firebird
.PHONY: help build build-clean build-push build-verbose run stop logs test clean setup dev prod

# Configurações
DOCKER_IMAGE = ghcr.io/marcelofmatos/mcp-server-firebird
DOCKER_TAG = latest
CONTAINER_NAME = mcp-firebird-server
TEST_URL = http://localhost:3000
PYTHON_ENV = python3

# Cores para output
RED = \033[0;31m
GREEN = \033[0;32m
YELLOW = \033[1;33m
BLUE = \033[0;34m
NC = \033[0m # No Color

help: ## Mostra esta ajuda
	@echo "$(BLUE)Servidor MCP Firebird - Comandos Disponíveis:$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

# ==========================================
# AMBIENTE E CONFIGURAÇÃO
# ==========================================

setup-dev: ## Configura ambiente de desenvolvimento completo
	@echo "$(BLUE)Configurando ambiente de desenvolvimento...$(NC)"
	@chmod +x scripts/setup-dev.sh
	@./scripts/setup-dev.sh
	@echo "$(GREEN)Ambiente de desenvolvimento configurado!$(NC)"

setup: ## Configura ambiente inicial
	@echo "$(BLUE)Configurando ambiente...$(NC)"
	@mkdir -p logs reports htmlcov
	@if [ ! -f .env ]; then cp .env.example .env; echo "$(YELLOW)Arquivo .env criado. Configure suas variáveis!$(NC)"; fi
	@echo "$(GREEN)Ambiente configurado!$(NC)"

install-deps: ## Instala dependências de desenvolvimento
	@echo "$(BLUE)Instalando dependências...$(NC)"
	@$(PYTHON_ENV) -m pip install --upgrade pip
	@$(PYTHON_ENV) -m pip install -r requirements-dev.txt
	@echo "$(GREEN)Dependências instaladas!$(NC)"

pre-commit-setup: ## Configura pre-commit hooks
	@echo "$(BLUE)Configurando pre-commit hooks...$(NC)"
	@pre-commit install
	@echo "$(GREEN)Pre-commit hooks configurados!$(NC)"

# ==========================================
# TESTES E QUALIDADE
# ==========================================

test-all: ## Executa todos os testes
	@chmod +x scripts/run-tests.sh
	@./scripts/run-tests.sh

test-unit: ## Executa apenas testes unitários
	@chmod +x scripts/run-tests.sh
	@./scripts/run-tests.sh -t unit

test-integration: ## Executa testes de integração
	@chmod +x scripts/run-tests.sh
	@./scripts/run-tests.sh -t integration

test-performance: ## Executa testes de performance
	@chmod +x scripts/run-tests.sh
	@./scripts/run-tests.sh -t performance

test-fast: ## Execução rápida (sem testes lentos)
	@chmod +x scripts/run-tests.sh
	@./scripts/run-tests.sh -f

test-verbose: ## Testes com output verboso
	@chmod +x scripts/run-tests.sh
	@./scripts/run-tests.sh -v

test-coverage: ## Testes com relatório de cobertura HTML
	@chmod +x scripts/run-tests.sh
	@./scripts/run-tests.sh --html

test-ci: ## Testes para CI/CD (sem cores, com XML)
	@chmod +x scripts/run-tests.sh
	@./scripts/run-tests.sh --xml --no-cov

test-watch: ## Monitora arquivos e executa testes automaticamente
	@echo "$(BLUE)Monitorando arquivos para execução automática de testes...$(NC)"
	@$(PYTHON_ENV) -m pytest-watch

# ==========================================
# QUALIDADE DE CÓDIGO
# ==========================================

lint: ## Executa verificações de qualidade de código
	@chmod +x scripts/run-tests.sh
	@./scripts/run-tests.sh --lint

lint-fix: ## Executa linting e corrige problemas automaticamente
	@echo "$(BLUE)Executando correções automáticas...$(NC)"
	@ruff check . --fix
	@black .
	@echo "$(GREEN)Correções aplicadas!$(NC)"

format: ## Formata código com black
	@echo "$(BLUE)Formatando código...$(NC)"
	@black .
	@echo "$(GREEN)Código formatado!$(NC)"

format-check: ## Verifica formatação sem modificar
	@echo "$(BLUE)Verificando formatação...$(NC)"
	@black --check --diff .

type-check: ## Verifica tipos com mypy
	@echo "$(BLUE)Verificando tipos...$(NC)"
	@mypy .

security-check: ## Verifica segurança com bandit
	@echo "$(BLUE)Verificando segurança...$(NC)"
	@bandit -r server.py src/ -f json -o reports/bandit-report.json
	@bandit -r server.py src/

pre-commit: ## Executa todos os hooks do pre-commit
	@echo "$(BLUE)Executando pre-commit hooks...$(NC)"
	@pre-commit run --all-files

clean-code: ## Limpa e formata código
	$(MAKE) clean-test
	$(MAKE) lint-fix
	$(MAKE) test-fast

# ==========================================
# DOCKER E PRODUÇÃO
# ==========================================

build: ## Constrói a imagem Docker
	@echo "$(BLUE)Construindo imagem Docker via build.sh...$(NC)"
	@chmod +x build.sh
	@./build.sh
	@echo "$(GREEN)Imagem construída com sucesso!$(NC)"

run: ## Inicia o servidor
	@echo "$(BLUE)Iniciando servidor MCP...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)Servidor iniciado!$(NC)"
	@echo "$(YELLOW)Aguarde alguns segundos e teste com: make test-server$(NC)"

stop: ## Para o servidor
	@echo "$(BLUE)Parando servidor...$(NC)"
	docker-compose down
	@echo "$(GREEN)Servidor parado!$(NC)"

restart: stop run ## Reinicia o servidor

logs: ## Mostra logs do servidor
	docker-compose logs -f mcp-server

logs-tail: ## Mostra últimas 50 linhas dos logs
	docker-compose logs --tail=50 mcp-server

status: ## Verifica status do servidor
	@echo "$(BLUE)Status dos containers:$(NC)"
	@docker-compose ps
	@echo ""
	@echo "$(BLUE)Health check:$(NC)"
	@curl -s $(TEST_URL)/health | python3 -m json.tool || echo "$(RED)Servidor não está respondendo$(NC)"

prod: ## Build para produção (sem cache)
	@echo "$(BLUE)Construindo para produção...$(NC)"
	@chmod +x build.sh
	@./build.sh --clean
	@echo "$(GREEN)Build de produção concluído!$(NC)"

build-clean: ## Build sem cache Docker
	@echo "$(BLUE)Build limpo (sem cache)...$(NC)"
	@chmod +x build.sh
	@./build.sh --clean

build-push: ## Build e push para registry
	@echo "$(BLUE)Build e push para registry...$(NC)"
	@chmod +x build.sh
	@./build.sh --push

build-verbose: ## Build com logs detalhados
	@echo "$(BLUE)Build verboso...$(NC)"
	@chmod +x build.sh
	@./build.sh --verbose

build-prod-push: ## Build produção e push
	@echo "$(BLUE)Build de produção e push...$(NC)"
	@chmod +x build.sh
	@./build.sh --clean --push

# ==========================================
# DESENVOLVIMENTO
# ==========================================

dev: ## Modo desenvolvimento completo
	@echo "$(BLUE)Iniciando modo desenvolvimento...$(NC)"
	$(MAKE) setup-dev
	$(MAKE) test-fast
	$(MAKE) build
	$(MAKE) run
	@echo "$(GREEN)Ambiente de desenvolvimento pronto!$(NC)"

dev-server: ## Executa servidor em modo desenvolvimento (sem Docker)
	@echo "$(BLUE)Iniciando servidor em modo desenvolvimento...$(NC)"
	@$(PYTHON_ENV) server.py

dev-clean: ## Limpa ambiente de desenvolvimento
	$(MAKE) clean-test
	$(MAKE) clean
	@echo "$(GREEN)Ambiente de desenvolvimento limpo!$(NC)"

watch: ## Monitora mudanças e recarrega servidor
	@echo "$(BLUE)Monitorando mudanças no código...$(NC)"
	@watchdog -p './' -e python server.py

# ==========================================
# TESTES DE SERVIDOR
# ==========================================

test-server: ## Executa testes básicos do servidor
	@echo "$(BLUE)Executando testes básicos do servidor...$(NC)"
	@if command -v python3 >/dev/null 2>&1; then \
		python3 test-connection.py --url $(TEST_URL); \
	else \
		echo "$(YELLOW)Python3 não encontrado, testando com curl...$(NC)"; \
		curl -f $(TEST_URL)/health && echo "$(GREEN)Health check OK$(NC)" || echo "$(RED)Health check falhou$(NC)"; \
	fi

test-server-wait: ## Executa testes aguardando 10 segundos
	@echo "$(BLUE)Executando testes com delay...$(NC)"
	python3 test-connection.py --url $(TEST_URL) --wait 10

# ==========================================
# UTILITÁRIOS
# ==========================================

shell: ## Acessa shell do container
	docker exec -it $(CONTAINER_NAME) /bin/bash

inspect: ## Inspeciona container em execução
	@echo "$(BLUE)Informações do container:$(NC)"
	docker inspect $(CONTAINER_NAME)

env-check: ## Verifica variáveis de ambiente
	@echo "$(BLUE)Verificando configurações:$(NC)"
	@if [ -f .env ]; then \
		echo "$(GREEN)Arquivo .env encontrado:$(NC)"; \
		grep -E '^[A-Z]' .env; \
	else \
		echo "$(RED)Arquivo .env não encontrado!$(NC)"; \
		echo "$(YELLOW)Execute: make setup$(NC)"; \
	fi

info: ## Mostra informações do banco via API
	@echo "$(BLUE)Informações do banco:$(NC)"
	@curl -s $(TEST_URL)/info | python3 -m json.tool || echo "$(RED)Erro ao obter informações$(NC)"

tables: ## Lista tabelas do banco
	@echo "$(BLUE)Tabelas disponíveis:$(NC)"
	@curl -s $(TEST_URL)/tables | python3 -m json.tool || echo "$(RED)Erro ao listar tabelas$(NC)"

query: ## Executa query de exemplo (uso: make query SQL="SELECT * FROM tabela")
	@echo "$(BLUE)Executando query: $(SQL)$(NC)"
	@curl -s -X POST $(TEST_URL)/query \
		-H "Content-Type: application/json" \
		-d '{"sql": "$(SQL)"}' | python3 -m json.tool

# ==========================================
# RELATÓRIOS E DOCUMENTAÇÃO
# ==========================================

coverage-report: ## Gera relatório detalhado de cobertura
	@echo "$(BLUE)Gerando relatório de cobertura...$(NC)"
	@$(PYTHON_ENV) -m coverage html
	@$(PYTHON_ENV) -m coverage report
	@echo "$(GREEN)Relatório disponível em htmlcov/index.html$(NC)"

docs-serve: ## Serve documentação localmente
	@echo "$(BLUE)Servindo documentação...$(NC)"
	@$(PYTHON_ENV) -m http.server 8000 -d htmlcov
	@echo "$(GREEN)Documentação disponível em http://localhost:8000$(NC)"

benchmark: ## Executa benchmark de performance
	@echo "$(BLUE)Executando benchmark...$(NC)"
	@$(PYTHON_ENV) -m pytest tests/unit/test_performance.py --benchmark-only

# ==========================================
# LIMPEZA
# ==========================================

clean-test: ## Remove artefatos de teste
	@echo "$(BLUE)Limpando artefatos de teste...$(NC)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete 2>/dev/null || true
	@rm -rf htmlcov/ coverage.xml .coverage reports/ junit.xml
	@echo "$(GREEN)Artefatos de teste limpos!$(NC)"

clean: ## Remove containers e imagens
	@echo "$(BLUE)Limpando recursos Docker...$(NC)"
	docker-compose down -v 2>/dev/null || true
	docker rmi $(DOCKER_IMAGE):$(DOCKER_TAG) 2>/dev/null || true
	docker rmi mcp-firebird-server:latest 2>/dev/null || true
	docker system prune -f
	@echo "$(GREEN)Limpeza Docker concluída!$(NC)"

clean-all: clean clean-test ## Limpeza completa

# ==========================================
# BACKUP E MANUTENÇÃO
# ==========================================

backup-logs: ## Faz backup dos logs
	@echo "$(BLUE)Fazendo backup dos logs...$(NC)"
	@mkdir -p backup/logs-$(shell date +%Y%m%d-%H%M%S)
	@docker-compose logs --no-color > backup/logs-$(shell date +%Y%m%d-%H%M%S)/mcp-server.log
	@echo "$(GREEN)Backup dos logs concluído!$(NC)"

update: ## Atualiza imagem e reinicia
	@echo "$(BLUE)Atualizando servidor...$(NC)"
	$(MAKE) stop
	$(MAKE) build
	$(MAKE) run
	$(MAKE) test-server
	@echo "$(GREEN)Atualização concluída!$(NC)"

# ==========================================
# TARGETS PARA MONITORAMENTO
# ==========================================

watch-logs: ## Monitora logs continuamente
	watch -n 2 'docker-compose logs --tail=20 mcp-server'

quick-test: ## Teste rápido sem logs
	@curl -s $(TEST_URL)/health >/dev/null && echo "$(GREEN)✓ Servidor OK$(NC)" || echo "$(RED)✗ Servidor com problema$(NC)"

health-check: ## Verifica saúde do sistema
	@echo "$(BLUE)Verificando saúde do sistema...$(NC)"
	@echo "Docker: $$(command -v docker >/dev/null && echo '✓' || echo '✗')"
	@echo "Python: $$(command -v $(PYTHON_ENV) >/dev/null && echo '✓' || echo '✗')"
	@echo "Pytest: $$($$(PYTHON_ENV) -c 'import pytest' 2>/dev/null && echo '✓' || echo '✗')"
	@echo "Pre-commit: $$(command -v pre-commit >/dev/null && echo '✓' || echo '✗')"

# ==========================================
# INFORMAÇÕES
# ==========================================

docker-info: ## Mostra informações Docker úteis
	@echo "$(BLUE)Informações Docker:$(NC)"
	@echo "Imagem: $(DOCKER_IMAGE):$(DOCKER_TAG)"
	@echo "Container: $(CONTAINER_NAME)"
	@echo "URL de teste: $(TEST_URL)"
	@echo ""
	@echo "$(BLUE)Comandos de build:$(NC)"
	@echo "  make build         - Build padrão"
	@echo "  make build-clean   - Build sem cache"
	@echo "  make build-push    - Build e push"
	@echo "  make build-verbose - Build detalhado"
	@echo "  make prod          - Build produção"
	@echo ""
	@echo "$(BLUE)Comandos de desenvolvimento:$(NC)"
	@echo "  make setup-dev   - Configuração completa de desenvolvimento"
	@echo "  make dev         - Ambiente de desenvolvimento"
	@echo "  make test-all    - Todos os testes"
	@echo "  make lint        - Verificações de código"
	@echo "  make clean-all   - Limpeza completa"

info-project: ## Mostra informações do projeto
	@echo "$(BLUE)Informações do Projeto:$(NC)"
	@echo "Nome: MCP Server Firebird"
	@echo "Versão: $$(grep version pyproject.toml | head -1 | cut -d'"' -f2)"
	@echo "Python: $$($(PYTHON_ENV) --version)"
	@echo "Diretório: $$(pwd)"
	@echo ""
	@echo "$(BLUE)Estrutura:$(NC)"
	@echo "├── server.py          # Servidor principal"
	@echo "├── tests/             # Testes"
	@echo "│   ├── unit/         # Testes unitários"
	@echo "│   └── integration/  # Testes de integração"
	@echo "├── scripts/          # Scripts auxiliares"
	@echo "├── i18n/             # Internacionalização"
	@echo "└── reports/          # Relatórios de teste"

# Target padrão
.DEFAULT_GOAL := help
