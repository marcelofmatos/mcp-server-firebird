# Sistema de Internacionalização (i18n)

O servidor MCP Firebird Expert agora suporta múltiplos idiomas através de arquivos JSON separados.

## 📁 Estrutura de Arquivos

```
mcp-server-firebird/
├── server.py                 # Servidor principal
├── i18n/                     # Diretório de idiomas
│   ├── pt_BR.json            # Português do Brasil
│   └── en_US.json            # Inglês americano
└── README_i18n.md           # Este arquivo
```

## 🌍 Configuração de Idioma

O idioma é definido através de variáveis de ambiente:

### Opção 1: Variável FIREBIRD_LANGUAGE
```bash
export FIREBIRD_LANGUAGE=pt_BR
python server.py
```

### Opção 2: Variável LANG (padrão do sistema)
```bash
export LANG=pt_BR.UTF-8
python server.py
```

### Padrão
Se nenhuma variável estiver definida, o sistema usa `en_US` como padrão.

## 🔧 Como Funciona

1. **Classe I18n**: Carrega e gerencia as strings localizadas
2. **Função get()**: Acessa strings usando chaves separadas por ponto
3. **Fallback**: Se um idioma não existe, usa en_US automaticamente
4. **Formatação**: Suporta formatação de strings com parâmetros

### Exemplo de Uso no Código

```python
# Carregar string simples
message = i18n.get('server_info.initialized')

# String com formatação
message = i18n.get('prompt_templates.firebird_expert.guidelines', 
                   operation_type='SELECT')
```

## 📝 Estrutura dos Arquivos JSON

### Seções Principais

- **server_info**: Informações do servidor e mensagens de sistema
- **connection**: Mensagens relacionadas à conexão com o banco
- **libraries**: Status e diagnósticos das bibliotecas Firebird
- **environment**: Informações do ambiente de execução
- **tools**: Descrições e mensagens das ferramentas MCP
- **prompts**: Configuração e templates dos prompts
- **prompt_templates**: Templates completos dos prompts especializados
- **complexity_levels**: Níveis de complexidade para prompts
- **operation_guidance**: Orientações por tipo de operação SQL
- **errors**: Mensagens de erro

### Exemplo de Entrada no JSON

```json
{
  "server_info": {
    "initialized": "MCP Server initialized",
    "starting": "=== FIREBIRD EXPERT MCP SERVER STARTING ==="
  },
  "tools": {
    "test_connection": {
      "name": "test_connection",
      "description": "Test connection to external Firebird database"
    }
  }
}
```

## ➕ Adicionando Novos Idiomas

Para adicionar um novo idioma (ex: español):

1. **Criar arquivo**: `i18n/es_ES.json`
2. **Copiar estrutura**: Use `en_US.json` como base
3. **Traduzir strings**: Mantenha as chaves, traduza os valores
4. **Testar**: `export FIREBIRD_LANGUAGE=es_ES && python server.py`

### Exemplo para Español

```json
{
  "server_info": {
    "initialized": "Servidor MCP inicializado",
    "starting": "=== INICIANDO SERVIDOR MCP EXPERTO FIREBIRD ==="
  }
}
```

## 🎯 Benefícios

- **Manutenção**: Strings centralizadas em arquivos JSON
- **Flexibilidade**: Fácil adição de novos idiomas
- **Consistência**: Mesmo template para todos os idiomas
- **Segurança**: Fallback automático para evitar crashes
- **Performance**: Carregamento único na inicialização

## 🔍 Debug e Troubleshooting

### Logs de Debug
O sistema mostra logs sobre o carregamento de idiomas:
```
✅ Loaded language: pt_BR
⚠️  Language fr_FR not found, using en_US fallback
❌ No language files found, using hardcoded English
```

### Verificar Idioma Ativo
```bash
# Ver variáveis de ambiente
echo $FIREBIRD_LANGUAGE
echo $LANG

# Verificar logs do servidor para confirmar idioma carregado
```

### Problemas Comuns

1. **Arquivo não encontrado**: Verifique se o arquivo JSON existe em `i18n/`
2. **JSON inválido**: Valide a sintaxe JSON com um validador
3. **Chave ausente**: O sistema retorna a chave como fallback e registra um warning
4. **Codificação**: Arquivos JSON devem usar UTF-8

## 🚀 Vantagens da Implementação

- **Escalabilidade**: Fácil expansão para novos idiomas
- **Manutenibilidade**: Separação clara entre lógica e apresentação
- **Internacionalização**: Suporte nativo a diferentes culturas
- **Robustez**: Sistema de fallback evita erros críticos
- **Padronização**: Estrutura consistente em todos os idiomas

O sistema está pronto para uso em ambiente de produção e pode ser facilmente expandido conforme necessário.
