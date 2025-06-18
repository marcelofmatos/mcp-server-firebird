# MCP Server Firebird

Um servidor MCP (Model Context Protocol) completo para conectar a bancos de dados Firebird externos. Este servidor permite que assistentes de IA executem queries SQL, listem tabelas e gerenciem conexões com bancos Firebird de forma segura e eficiente.

## 🔥 Características

- ✅ **Protocolo MCP Completo** - Implementa todas as especificações do MCP 2024-11-05
- ✅ **Firebird 3.0.10 Oficial** - Bibliotecas cliente incluídas no container
- ✅ **Auto-contido** - Não precisa de volumes ou instalações no host
- ✅ **Diagnósticos Inteligentes** - Detecta e resolve problemas automaticamente
- ✅ **Conexões Externas** - Conecta a qualquer servidor Firebird remoto
- ✅ **4 Ferramentas MCP** - test_connection, execute_query, list_tables, server_status
- ✅ **Seguro** - Usuário não-root, health check integrado

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

### Exemplos de Configuração

#### 1. Servidor Local
```bash
docker run -d \
  --name mcp-firebird-local \
  -e FIREBIRD_HOST=localhost \
  -e FIREBIRD_DATABASE=/var/lib/firebird/employee.fdb \
  -e FIREBIRD_PASSWORD=sua_senha \
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
```

Executar:
```bash
docker-compose up -d
docker-compose logs -f mcp-firebird
```

## 🔧 Desenvolvimento

### Build Local
```bash
# Clonar repositório
git clone https://github.com/marcelofmatos/mcp-server-firebird
cd mcp-server-firebird

# Build da imagem
docker build -t mcp-firebird-local .

# Testar
docker run --rm \
  -e FIREBIRD_HOST=localhost \
  -e FIREBIRD_DATABASE=/test.fdb \
  mcp-firebird-local
```

### Estrutura do Projeto
```
mcp-server-firebird/
├── Dockerfile          # Configuração do container
├── server.py           # Servidor MCP
├── README.md           # Esta documentação
└── .github/
    └── workflows/
        └── docker.yml  # CI/CD GitHub Actions
```

## 📚 Recursos Adicionais

- **Especificação MCP**: [Model Context Protocol](https://spec.modelcontextprotocol.io/)
- **Documentação Firebird**: [Firebird Documentation](https://firebirdsql.org/en/documentation/)
- **FDB Python Driver**: [python-fdb](https://github.com/FirebirdSQL/fdb)

## 🤝 Contribuição

Contribuições são bem-vindas! Por favor:

1. Faça fork do repositório
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Abra um Pull Request

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🆘 Suporte

- **Issues**: [GitHub Issues](https://github.com/marcelofmatos/mcp-server-firebird/issues)
- **Discussões**: [GitHub Discussions](https://github.com/marcelofmatos/mcp-server-firebird/discussions)

---

## 🏷️ Tags da Imagem

- `latest` - Versão mais recente estável
- `v1.0.0` - Versão específica
- `dev` - Versão de desenvolvimento

```bash
# Usar versão específica
docker pull ghcr.io/marcelofmatos/mcp-server-firebird:v1.0.0

# Usar versão de desenvolvimento
docker pull ghcr.io/marcelofmatos/mcp-server-firebird:dev
```

---

**Feito com ❤️ para a comunidade Firebird e MCP**