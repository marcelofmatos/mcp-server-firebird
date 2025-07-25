# 🔧 Estrutura Modular - Guia para Desenvolvedores

## 📁 Visão Geral da Arquitetura

O MCP Server Firebird agora utiliza uma **arquitetura modular limpa** que separa responsabilidades e facilita manutenção, testes e extensões.

```
src/
├── __init__.py           # 🎯 Exports principais do projeto
├── core/                 # ⚙️  Funcionalidades fundamentais
├── firebird/            # 🔥 Lógica específica do Firebird  
├── mcp/                 # 🌐 Implementação do protocolo MCP
└── prompts/             # 💬 Sistema inteligente de prompts
```

---

## 🗂️ Detalhamento por Módulo

### `src/core/` - Base do Sistema
**Responsabilidade**: Configurações, internacionalização e inicialização

#### `config.py`
```python
# Configurações centralizadas
DB_CONFIG = {...}
DEFAULT_PROMPT_CONFIG = {...}

# Inicialização de bibliotecas Firebird
def initialize_libraries() -> Tuple[...]
```

#### `i18n.py` 
```python
# Sistema robusto de internacionalização
class I18n:
    def get(self, key_path: str) -> str
    def validate_completeness() -> dict
    def get_available_languages() -> list
```

---

### `src/firebird/` - Lógica do Firebird
**Responsabilidade**: Operações de banco e análise SQL

#### `server.py`
```python
# Servidor principal do Firebird
class FirebirdMCPServer:
    def test_connection() -> dict
    def execute_query(sql: str, params: List) -> dict
    def get_tables() -> dict
    def get_table_info(table_name: str) -> dict
```

#### `analyzer.py`
```python
# Análise inteligente de padrões SQL
class SQLPatternAnalyzer:
    def analyze(sql: str) -> dict
    def get_optimization_suggestions(sql: str) -> list
```

---

### `src/mcp/` - Protocolo MCP
**Responsabilidade**: Comunicação JSON-RPC e protocolo MCP

#### `server.py`
```python
# Servidor MCP/JSON-RPC
class MCPServer:
    def handle_initialize()
    def handle_tools_list()
    def handle_tools_call()
    def handle_prompts_get()
    def run()  # Main server loop
```

---

### `src/prompts/` - Sistema de Prompts
**Responsabilidade**: Geração e gerenciamento de prompts especializados

#### `manager.py`
```python
# Gerenciamento automático de prompts
class DefaultPromptManager:
    def apply_to_response(content: str) -> str
    def get_enhanced_tool_description() -> str
    def get_status() -> dict
```

#### `generator.py`
```python
# Geração dinâmica de prompts
class PromptGenerator:
    def generate(prompt_name: str, args: dict) -> str
    def _generate_expert_prompt() -> str
    def _generate_performance_prompt() -> str
```

---

## 🔌 Como Importar e Usar

### **Imports Simplificados**
```python
# Import completo do projeto
from src import (
    I18n, DB_CONFIG, initialize_libraries,
    FirebirdMCPServer, SQLPatternAnalyzer,
    DefaultPromptManager, PromptGenerator,
    MCPServer
)

# Imports seletivos por módulo
from src.core import I18n, DB_CONFIG
from src.firebird import SQLPatternAnalyzer
from src.prompts import PromptGenerator
```

### **Uso Individual dos Módulos**
```python
# Analisar SQL independentemente
analyzer = SQLPatternAnalyzer()
result = analyzer.analyze("SELECT * FROM users")

# Gerar prompts dinâmicos
generator = PromptGenerator()
prompt = generator.generate('firebird_expert', {
    'operation_type': 'select',
    'complexity_level': 'advanced'
})

# Sistema de internacionalização
i18n = I18n('pt_BR')
message = i18n.get('connection.successful')
```

---

## 🧪 Testes por Módulo

### **Estrutura de Testes**
```
tests/
├── unit/                     # Testes unitários isolados
│   ├── test_sql_analyzer.py  # SQLPatternAnalyzer
│   └── test_prompt_system.py # Sistema de prompts
├── integration/              # Testes de integração
│   └── test_mcp_integration.py # Sistema completo
└── conftest.py              # Configurações compartilhadas
```

### **Executar Testes**
```bash
# Todos os testes
python -m pytest tests/ -v

# Testes de um módulo específico
python -m pytest tests/unit/test_sql_analyzer.py -v

# Testes com coverage
python -m pytest tests/ --cov=src --cov-report=html
```

---

## 🔧 Extensão e Customização

### **Adicionar Novo Analisador**
```python
# src/firebird/custom_analyzer.py
from .analyzer import SQLPatternAnalyzer

class SecuritySQLAnalyzer(SQLPatternAnalyzer):
    def analyze_security_risks(self, sql: str) -> list:
        risks = []
        if 'SELECT *' in sql.upper():
            risks.append("Avoid SELECT * for security")
        return risks
```

### **Criar Prompt Especializado**
```python
# src/prompts/security_generator.py
from .generator import PromptGenerator

class SecurityPromptGenerator(PromptGenerator):
    def _generate_security_prompt(self, args: dict) -> str:
        return """# Firebird Security Specialist
        
        You are a security expert for Firebird databases...
        """
```

### **Adicionar Nova Funcionalidade MCP**
```python
# src/mcp/extended_server.py
from .server import MCPServer

class ExtendedMCPServer(MCPServer):
    def handle_custom_method(self, request_id, params):
        # Nova funcionalidade
        pass
```

---

## 📊 Benefícios da Modularização

### ✅ **Para Desenvolvedores**
- **Foco isolado**: Trabalhar em um módulo sem afetar outros
- **Testes específicos**: Testar componentes individualmente
- **Debug facilitado**: Problemas isolados por responsabilidade
- **Onboarding rápido**: Entender um módulo por vez

### ✅ **Para Manutenção**
- **Mudanças localizadas**: Alterações têm escopo limitado
- **Versionamento granular**: Controle de mudanças por módulo
- **Refactoring seguro**: Isolar melhorias
- **Dependencies claras**: Relações bem definidas

### ✅ **Para Extensão**
- **Novos módulos**: Adicionar funcionalidades sem conflitos
- **Reutilização**: Componentes utilizáveis em outros projetos
- **Substituição**: Trocar implementações mantendo interfaces
- **Composição**: Combinar módulos de formas diferentes

---

## 🎯 Padrões de Design Aplicados

### **Single Responsibility Principle**
- Cada módulo tem **uma responsabilidade clara**
- Classes focadas em **uma única funcionalidade**

### **Dependency Injection**
- Dependências **injetadas via construtor**
- **Facilita testes** com mocks

### **Interface Segregation**
- **Interfaces pequenas** e específicas
- Módulos dependem apenas do que **realmente usam**

### **Open/Closed Principle**
- **Aberto para extensão** (herança, composição)
- **Fechado para modificação** (APIs estáveis)

---

## 🚀 Comparação: Antes vs Depois

| Aspecto | Antes (Monolítico) | Depois (Modular) |
|---------|-------------------|------------------|
| **Linhas por arquivo** | 1500+ | 150-300 |
| **Responsabilidades** | Múltiplas misturadas | Uma por módulo |
| **Testabilidade** | Apenas integração | Unit + Integration |
| **Manutenibilidade** | Difícil | Fácil |
| **Extensibilidade** | Limitada | Ilimitada |
| **Debug** | Complexo | Simples |
| **Onboarding** | Lento | Rápido |
| **Reusabilidade** | Baixa | Alta |

---

## ⚡ Comandos Úteis

```bash
# Verificar estrutura
find src/ -name "*.py" | xargs wc -l | sort -n

# Analisar dependências
python -c "
import src
print('✅ All modules imported successfully')
print(f'Available: {dir(src)}')
"

# Rodar exemplo completo
python examples/modular_usage.py

# Verificar padrões de código
flake8 src/
black --check src/
mypy src/
```

---

**A nova arquitetura modular oferece uma base sólida e profissional para o crescimento sustentável do projeto MCP Server Firebird.**
