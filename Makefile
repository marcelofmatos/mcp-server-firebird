# Makefile para Servidor MCP Firebird
.PHONY: help build run stop logs test clean setup dev prod

# Configurações
DOCKER_IMAGE = mcp-firebird-server
DOCKER_TAG = latest
CONTAINER_NAME = mcp-firebird-server
TEST_URL = http://localhost:3000

# Cores para output
RED = \033[0;31m
GREEN = \033[0;32m
YELLOW = \033[1;33m
BLUE = \033[0;34m
NC = \033[0m # No Color

help: ## Mostra esta ajuda
	@echo "$(BLUE)Servidor MCP Firebird - Comandos Disponíveis:$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-15s$(NC) %s\n", $$1, $$2}'

setup: ## Configura ambiente inicial
	@echo "$(BLUE)Configurando ambiente...$(NC)"
	@mkdir -p mcp-server logs
	@if [ ! -f .env ]; then cp .env.example .env; echo "$(YELLOW)Arquivo .env criado. Configure suas variáveis!$(NC)"; fi
	@echo "$(GREEN)Ambiente configurado!$(NC)"

build: ## Constrói a imagem Docker
	@echo "$(BLUE)Construindo imagem Docker...$(NC)"
	docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) .
	@echo "$(GREEN)Imagem construída com sucesso!$(NC)"

run: ## Inicia o servidor
	@echo "$(BLUE)Iniciando servidor MCP...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)Servidor iniciado!$(NC)"
	@echo "$(YELLOW)Aguarde alguns segundos e teste com: make test$(NC)"

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

test: ## Executa testes básicos
	@echo "$(BLUE)Executando testes...$(NC)"
	@if command -v python3 >/dev/null 2>&1; then \
		python3 test-connection.py --url $(TEST_URL); \
	else \
		echo "$(YELLOW)Python3 não encontrado, testando com curl...$(NC)"; \
		curl -f $(TEST_URL)/health && echo "$(GREEN)Health check OK$(NC)" || echo "$(RED)Health check falhou$(NC)"; \
	fi

test-wait: ## Executa testes aguardando 10 segundos
	@echo "$(BLUE)Executando testes com delay...$(NC)"
	python3 test-connection.py --url $(TEST_URL) --wait 10

clean: ## Remove containers e imagens
	@echo "$(BLUE)Limpando recursos Docker...$(NC)"
	docker-compose down -v
	docker rmi $(DOCKER_IMAGE):$(DOCKER_TAG) 2>/dev/null || true
	docker system prune -f
	@echo "$(GREEN)Limpeza concluída!$(NC)"

dev: ## Modo desenvolvimento (rebuild + run + logs)
	@echo "$(BLUE)Iniciando modo desenvolvimento...$(NC)"
	$(MAKE) build
	$(MAKE) run
	sleep 5
	$(MAKE) test
	$(MAKE) logs

prod: ## Build para produção
	@echo "$(BLUE)Construindo para produção...$(NC)"
	docker build -t $(DOCKER_IMAGE):prod --target production .
	@echo "$(GREEN)Build de produção concluído!$(NC)"

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
	$(MAKE) test
	@echo "$(GREEN)Atualização concluída!$(NC)"

# Targets para desenvolvimento
watch-logs: ## Monitora logs continuamente
	watch -n 2 'docker-compose logs --tail=20 mcp-server'

quick-test: ## Teste rápido sem logs
	@curl -s $(TEST_URL)/health >/dev/null && echo "$(GREEN)✓ Servidor OK$(NC)" || echo "$(RED)✗ Servidor com problema$(NC)"

# Informações úteis
docker-info: ## Mostra informações Docker úteis
	@echo "$(BLUE)Informações Docker:$(NC)"
	@echo "Imagem: $(DOCKER_IMAGE):$(DOCKER_TAG)"
	@echo "Container: $(CONTAINER_NAME)"
	@echo "URL de teste: $(TEST_URL)"
	@echo ""
	@echo "$(BLUE)Comandos úteis:$(NC)"
	@echo "  make dev     - Desenvolvimento completo"
	@echo "  make logs    - Ver logs em tempo real"
	@echo "  make test    - Testar funcionalidades"
	@echo "  make clean   - Limpar tudo"
