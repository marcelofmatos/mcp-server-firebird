# Servidor MCP para Firebird Externo

Um servidor MCP (Model Context Protocol) que conecta a um banco de dados Firebird externo existente, permitindo que modelos de IA interajam diretamente com seus dados.

## Características

- **Conexão Externa**: Conecta a qualquer servidor Firebird existente
- **API REST**: Interface HTTP para comunicação com modelos de IA
- **MCP Protocol**: Compatível com o protocolo MCP
- **Docker**: Fácil implantação e gerenciamento
- **Health Check**: Monitoramento de saúde e conectividade
- **Schema Discovery**: Descoberta automática de estrutura do banco

## Estrutura do Projeto

```
.
├── Dockerfile                 # Imagem Docker do servidor MCP
├── docker-compose.yml        # Configuração para deployment
├── requirements.txt          # Dependências Python
├── mcp-server/
│   └── server.py            # Servidor MCP Python
└── README.md               # Esta documentação
```

## Pré-requisitos

- Servidor Firebird 3.0+ em execução e acessível
- Docker e Docker Compose instalados
- Acesso de rede ao servidor Firebird

## Configuração Rápida

### 1. Clonar/Preparar Arquivos

```bash
mkdir mcp-firebird-server
cd mcp-firebird-server
mkdir mcp-server

# Copiar todos os arquivos para as pastas apropriadas
```

### 2. Configurar Variáveis de Ambiente

Edite o `docker-compose.yml` ou crie um arquivo `.env`:

```env
FIREBIRD_HOST=seu-servidor-firebird.com
FIREBIRD_PORT=3050
FIREBIRD_DATABASE=/caminho/para/seu/banco.fdb
FIREBIRD_USER=SYSDBA
FIREBIRD_PASSWORD=sua_senha_segura
FIREBIRD_CHARSET=UTF8
MCP_SERVER_PORT=3000
MCP_LOG_LEVEL=info
```

### 3. Executar

```bash
# Construir e iniciar
docker-compose up -d

# Verificar logs
docker-compose logs -f mcp-server

# Testar conectividade
curl http://localhost:3000/health
```

## Configuração Detalhada

### Variáveis de Ambiente

| Variável | Obrigatório | Padrão | Descrição |
|----------|-------------|--------|-----------|
| `FIREBIRD_HOST` | ✅ | localhost | Endereço do servidor Firebird |
| `FIREBIRD_PORT` | ❌ | 3050 | Porta do servidor Firebird |
| `FIREBIRD_DATABASE` | ✅ | - | Caminho completo do arquivo .fdb |
| `FIREBIRD_USER` | ✅ | SYSDBA | Usuário do banco |
| `FIREBIRD_PASSWORD` | ✅ | - | Senha do usuário |
| `FIREBIRD_CHARSET` | ❌ | UTF8 | Charset da conexão |
| `MCP_SERVER_PORT` | ❌ | 3000 | Porta do servidor MCP |
| `MCP_LOG_LEVEL` | ❌ | info | Nível de log (debug, info, warning, error) |
| `TZ` | ❌ | America/Sao_Paulo | Timezone |

### Exemplos de Configuração

#### Banco Local na Rede
```env
FIREBIRD_HOST=192.168.1.100
FIREBIRD_DATABASE=/databases/sistema.fdb
FIREBIRD_USER=APP_USER
FIREBIRD_PASSWORD=senha123
```

#### Banco em Servidor Remoto
```env
FIREBIRD_HOST=db.minhaempresa.com
FIREBIRD_PORT=3050
FIREBIRD_DATABASE=/opt/databases/producao.fdb
FIREBIRD_USER=SISTEMA
FIREBIRD_PASSWORD=senha_complexa_aqui
```

#### Banco com Embedded (mesmo servidor)
```env
FIREBIRD_HOST=localhost
FIREBIRD_DATABASE=/var/lib/firebird/meuapp.fdb
FIREBIRD_USER=SYSDBA
FIREBIRD_PASSWORD=masterkey
```

## API Endpoints

### 🟢 Health Check
```http
GET /health
```
Verifica conectividade com o servidor Firebird.

**Resposta de sucesso:**
```json
{
  "status": "healthy",
  "database": "connected",
  "server_version": "5.0.0.1306",
  "database_path": "/databases/sistema.fdb"
}
```

### 📊 Informações do Banco
```http
GET /info
```
Retorna informações detalhadas sobre o banco.

**Resposta:**
```json
{
  "tables": ["USUARIOS", "PRODUTOS", "VENDAS"],
  "version": "5.0.0.1306",
  "database_path": "/databases/sistema.fdb",
  "server_info": {
    "database_name": "SISTEMA",
    "protocol": "TCPv4",
    "tables_count": 25
  }
}
```

### 🔍 Executar Query
```http
POST /query
Content-Type: application/json

{
  "sql": "SELECT * FROM USUARIOS WHERE ATIVO = ?",
  "params": ["S"]
}
```

**Resposta:**
```json
{
  "success": true,
  "data": [
    {
      "ID": 1,
      "NOME": "João Silva",
      "EMAIL": "joao@email.com",
      "ATIVO": "S"
    }
  ],
  "execution_time": 0.0234
}
```

### 📋 Listar Tabelas
```http
GET /tables
```
Retorna lista de todas as tabelas do banco.

### 🏗️ Schema de Tabela
```http
GET /tables/{table_name}/schema
```
Retorna estrutura detalhada de uma tabela.

**Exemplo de resposta:**
```json
{
  "table_name": "USUARIOS",
  "fields": [
    {
      "name": "ID",
      "type": "INTEGER",
      "length": 4,
      "not_null": true,
      "position": 0
    },
    {
      "name": "NOME",
      "type": "VARCHAR",
      "length": 100,
      "not_null": true,
      "position": 1
    }
  ]
}
```

### 🔧 Testar Conexão
```http
GET /connection/test
```
Testa a conectividade com o banco em tempo real.

## Exemplos de Uso

### 1. Verificar Status do Servidor
```bash
curl http://localhost:3000/health
```

### 2. Descobrir Estrutura do Banco
```bash
# Listar tabelas
curl http://localhost:3000/tables

# Ver schema de uma tabela
curl http://localhost:3000/tables/USUARIOS/schema
```

### 3. Executar Consultas
```bash
# SELECT simples
curl -X POST http://localhost:3000/query \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT COUNT(*) as TOTAL FROM USUARIOS"}'

# SELECT com parâmetros
curl -X POST http://localhost:3000/query \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT * FROM PRODUTOS WHERE CATEGORIA = ?", "params": ["ELETRONICOS"]}'

# INSERT
curl -X POST http://localhost:3000/query \
  -H "Content-Type: application/json" \
  -d '{"sql": "INSERT INTO USUARIOS (NOME, EMAIL) VALUES (?, ?)", "params": ["Novo User", "novo@email.com"]}'
```

### 4. Usando Python
```python
import requests

# Conectar ao servidor MCP
base_url = "http://localhost:3000"

# Verificar saúde
health = requests.get(f"{base_url}/health").json()
print(f"Status: {health['status']}")

# Executar query
query_data = {
    "sql": "SELECT * FROM USUARIOS WHERE ID = ?",
    "params": [1]
}
result = requests.post(f"{base_url}/query", json=query_data).json()

if result['success']:
    print("Dados:", result['data'])
else:
    print("Erro:", result['error'])
```

## Monitoramento e Logs

### Visualizar Logs
```bash
# Logs do container
docker-compose logs -f mcp-server

# Logs em tempo real
docker logs -f mcp-firebird-server
```

### Métricas de Health Check
O servidor fornece health checks automáticos que podem ser monitorados por:
- Docker health checks
- Kubernetes liveness/readiness probes
- Sistemas de monitoramento (Prometheus, etc.)

## Segurança

### ⚠️ Importantes para Produção

1. **Senhas Seguras**: Use senhas complexas e únicas
2. **Rede**: Configure firewall para permitir apenas IPs necessários
3. **HTTPS**: Use proxy reverso com SSL em produção
4. **Usuário Específico**: Crie usuário dedicado no Firebird com permissões mínimas
5. **Backup**: Configure backup automático dos dados
6. **Logs**: Monitore logs de acesso e erros

### Exemplo de Usuário Dedicado no Firebird
```sql
-- Conectar como SYSDBA e criar usuário específico
CREATE USER mcp_user PASSWORD 'senha_forte_aqui';

-- Conceder permissões específicas
GRANT SELECT, INSERT, UPDATE, DELETE ON TABELA1 TO mcp_user;
GRANT SELECT ON TABELA2 TO mcp_user;
```

## Solução de Problemas

### Problemas Comuns

#### 1. "Connection refused"
- Verificar se o Firebird está rodando
- Confirmar host e porta
- Testar conectividade de rede: `telnet host 3050`

#### 2. "Login failed"
- Verificar usuário e senha
- Confirmar se usuário existe no banco
- Verificar permissões do usuário

#### 3. "Database not found"
- Confirmar caminho completo do arquivo .fdb
- Verificar se arquivo existe no servidor
- Confirmar permissões de acesso ao arquivo

#### 4. "Character set not supported"
- Ajustar `FIREBIRD_CHARSET` conforme banco
- Charset comum: UTF8, ISO8859_1, WIN1252

### Comandos de Diagnóstico

```bash
# Testar conectividade
docker exec mcp-firebird-server curl -f http://localhost:3000/health

# Ver configuração atual
docker exec mcp-firebird-server env | grep FIREBIRD

# Entrar no container para debug
docker exec -it mcp-firebird-server bash

# Verificar logs específicos
docker exec mcp-firebird-server tail -f /var/log/mcp/server.log
```

### Performance

Para melhor performance:

1. **Índices**: Certifique-se que consultas frequentes tenham índices
2. **Connection Pool**: Considere implementar pool de conexões para alta carga
3. **Cache**: Use cache para consultas que não mudam frequentemente
4. **Limit**: Use FIRST/SKIP para paginar resultados grandes

## Deployment

### Desenvolvimento Local
```bash
docker-compose up -d
```

### Produção com Docker
```bash
# Build da imagem
docker build -t mcp-firebird-server:1.0 .

# Run em produção
docker run -d \
  --name mcp-firebird-prod \
  -p 3000:3000 \
  -e FIREBIRD_HOST=prod-db.empresa.com \
  -e FIREBIRD_DATABASE=/databases/producao.fdb \
  -e FIREBIRD_USER=mcp_user \
  -e FIREBIRD_PASSWORD=senha_super_segura \
  --restart unless-stopped \
  mcp-firebird-server:1.0
```

### Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-firebird-server
spec:
  replicas: 2
  selector:
    matchLabels:
      app: mcp-firebird-server
  template:
    metadata:
      labels:
        app: mcp-firebird-server
    spec:
      containers:
      - name: mcp-server
        image: mcp-firebird-server:1.0
        ports:
        - containerPort: 3000
        env:
        - name: FIREBIRD_HOST
          value: "firebird-service"
        - name: FIREBIRD_DATABASE
          value: "/databases/app.fdb"
        - name: FIREBIRD_USER
          valueFrom:
            secretKeyRef:
              name: firebird-credentials
              key: username
        - name: FIREBIRD_PASSWORD
          valueFrom:
            secretKeyRef:
              name: firebird-credentials
              key: password
```

## Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature: `git checkout -b feature/nova-funcionalidade`
3. Commit suas mudanças: `git commit -am 'Adiciona nova funcionalidade'`
4. Push para a branch: `git push origin feature/nova-funcionalidade`
5. Abra um Pull Request

## Licença

Este projeto está licenciado sob a MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.
