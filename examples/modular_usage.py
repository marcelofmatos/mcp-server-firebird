"""Exemplos de uso da arquitetura modular do MCP Server Firebird."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import individual modules
from core import I18n, DB_CONFIG, initialize_libraries
from firebird import FirebirdMCPServer, SQLPatternAnalyzer
from prompts import DefaultPromptManager, PromptGenerator
from mcp import MCPServer

def example_sql_analyzer():
    """Exemplo de uso do SQLPatternAnalyzer isoladamente."""
    print("=== Exemplo: SQL Pattern Analyzer ===")
    
    analyzer = SQLPatternAnalyzer()
    
    # Testar diferentes tipos de SQL
    queries = [
        "SELECT name FROM users WHERE active = 1",
        "SELECT u.name, COUNT(o.id) FROM users u JOIN orders o ON u.id = o.user_id GROUP BY u.name",
        "INSERT INTO users (name, email) VALUES ('John', 'john@example.com')",
        "DELETE FROM temp_data",  # Dangerous!
        "CREATE INDEX idx_users_name ON users (name)"
    ]
    
    for sql in queries:
        print(f"\nSQL: {sql}")
        analysis = analyzer.analyze(sql)
        print(f"Type: {analysis['type']}, Complexity: {analysis['complexity']}")
        if analysis['suggestions']:
            print(f"Suggestions: {analysis['suggestions'][:2]}")  # First 2 suggestions
        if analysis['firebird_features']:
            print(f"Firebird Features: {analysis['firebird_features']}")

def example_prompt_generator():
    """Exemplo de uso do PromptGenerator isoladamente."""
    print("\n=== Exemplo: Prompt Generator ===")
    
    generator = PromptGenerator()
    
    # Gerar prompt especializado
    args = {
        'operation_type': 'select',
        'complexity_level': 'advanced',
        'table_context': 'customers'
    }
    
    prompt = generator.generate('firebird_expert', args)
    print(f"Prompt gerado ({len(prompt)} chars):")
    print(prompt[:300] + "..." if len(prompt) > 300 else prompt)

def example_i18n_system():
    """Exemplo de uso do sistema de internacionalização."""
    print("\n=== Exemplo: Sistema I18N ===")
    
    # Testar diferentes idiomas
    for lang in ['en_US', 'pt_BR', 'es_ES']:  # es_ES não existe, vai usar fallback
        i18n = I18n(lang)
        print(f"\nIdioma: {lang}")
        print(f"Server name: {i18n.get('server_info.name')}")
        print(f"Connection successful: {i18n.get('connection.successful')}")
        print(f"Available languages: {i18n.get_available_languages()}")
        
        # Verificar completude
        completeness = i18n.validate_completeness()
        print(f"Completeness: {completeness['completion_percentage']:.1f}%")

def example_prompt_manager():
    """Exemplo de uso do DefaultPromptManager."""
    print("\n=== Exemplo: Default Prompt Manager ===")
    
    manager = DefaultPromptManager()
    
    # Mostrar status atual
    status = manager.get_status()
    print(f"Prompt system enabled: {status['enabled']}")
    print(f"Default prompt: {status['prompt_name']}")
    
    # Aplicar contexto a uma resposta
    original_content = "Query executed successfully: 42 rows returned"
    enhanced_content = manager.apply_to_response(original_content, tool_name='execute_query')
    
    print(f"\nOriginal content length: {len(original_content)}")
    print(f"Enhanced content length: {len(enhanced_content)}")
    print(f"Enhancement ratio: {len(enhanced_content) / len(original_content):.1f}x")

def example_firebird_server_mock():
    """Exemplo de uso do FirebirdMCPServer com mock (sem conexão real)."""
    print("\n=== Exemplo: Firebird Server (Mock) ===")
    
    # Criar servidor sem dependências reais
    server = FirebirdMCPServer(
        fdb_module=None,
        fdb_available=False,
        client_available=False,
        client_path=None
    )
    
    print(f"DSN configurado: {server.dsn}")
    
    # Testar conexão (vai falhar conforme esperado)
    result = server.test_connection()
    print(f"Connection result: {result['connected']}")
    print(f"Error type: {result.get('type', 'N/A')}")

def example_full_integration():
    """Exemplo de integração completa dos módulos."""
    print("\n=== Exemplo: Integração Completa ===")
    
    # Inicializar todos os componentes
    fdb_available, fdb_module, fdb_error, client_available, client_path = initialize_libraries()
    
    # Criar todos os componentes
    firebird_server = FirebirdMCPServer(
        fdb_module=fdb_module,
        fdb_available=fdb_available,
        client_available=client_available,
        client_path=client_path
    )
    
    prompt_manager = DefaultPromptManager()
    prompt_generator = PromptGenerator(firebird_server)
    i18n = I18n('en_US')
    
    # Criar servidor MCP
    mcp_server = MCPServer(
        firebird_server=firebird_server,
        prompt_manager=prompt_manager,
        prompt_generator=prompt_generator,
        i18n=i18n
    )
    
    print("✅ Todos os componentes inicializados com sucesso!")
    print(f"FDB disponível: {fdb_available}")
    print(f"Cliente Firebird disponível: {client_available}")
    print(f"Sistema de prompts habilitado: {prompt_manager.config['enabled']}")
    print(f"Idioma: {i18n.language}")

def example_custom_analyzer():
    """Exemplo de extensão do SQLPatternAnalyzer."""
    print("\n=== Exemplo: Analyzer Customizado ===")
    
    class CustomSQLAnalyzer(SQLPatternAnalyzer):
        """Analyzer personalizado com funcionalidades extras."""
        
        def analyze_security_risks(self, sql: str) -> list:
            """Analisa riscos de segurança na query."""
            risks = []
            sql_upper = sql.upper()
            
            if 'SELECT *' in sql_upper:
                risks.append("Avoid SELECT * for better performance and security")
            
            if 'WHERE' not in sql_upper and any(cmd in sql_upper for cmd in ['UPDATE', 'DELETE']):
                risks.append("🚨 HIGH RISK: No WHERE clause in modification query")
            
            if "'" in sql and '?' not in sql:
                risks.append("Consider using parameterized queries to prevent SQL injection")
            
            return risks
        
        def get_firebird_optimization_tips(self, sql: str) -> list:
            """Dicas específicas de otimização para Firebird."""
            tips = []
            sql_upper = sql.upper()
            
            if 'LIMIT' in sql_upper:
                tips.append("Use FIRST/SKIP instead of LIMIT for better Firebird performance")
            
            if 'UNION ' in sql_upper and 'UNION ALL' not in sql_upper:
                tips.append("Consider UNION ALL if duplicates are acceptable")
            
            if 'IN (' in sql_upper:
                tips.append("Consider EXISTS instead of IN for better performance")
            
            return tips
    
    # Usar o analyzer customizado
    custom_analyzer = CustomSQLAnalyzer()
    
    test_sql = "SELECT * FROM users WHERE name = 'John' LIMIT 10"
    
    # Análise padrão
    analysis = custom_analyzer.analyze(test_sql)
    print(f"Analysis type: {analysis['type']}")
    
    # Análises customizadas
    security_risks = custom_analyzer.analyze_security_risks(test_sql)
    optimization_tips = custom_analyzer.get_firebird_optimization_tips(test_sql)
    
    print(f"Security risks: {security_risks}")
    print(f"Optimization tips: {optimization_tips}")

def main():
    """Executar todos os exemplos."""
    print("🔥 Exemplos de Uso - MCP Server Firebird Modular")
    print("=" * 50)
    
    try:
        example_sql_analyzer()
        example_i18n_system()
        example_prompt_manager()
        example_prompt_generator()
        example_firebird_server_mock()
        example_custom_analyzer()
        example_full_integration()
        
        print("\n✅ Todos os exemplos executados com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro durante execução: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
