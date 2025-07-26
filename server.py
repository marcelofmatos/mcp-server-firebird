#!/usr/bin/env python3
"""
MCP Server Firebird Expert - External Connection
Robust server for connecting to external Firebird databases with specialized assistance and detailed diagnostics.

Usage instructions:
1. Configure connection via environment variables: FIREBIRD_HOST, FIREBIRD_DATABASE, FIREBIRD_USER, FIREBIRD_PASSWORD
2. Run: python server.py
3. Use MCP tools: test_connection, execute_query, list_tables, server_status
4. Access expert prompts: firebird_expert, firebird_performance, firebird_architecture
"""

import os
import sys

# Add src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src import (
    I18n, DB_CONFIG, DEFAULT_PROMPT_CONFIG, initialize_libraries,
    FirebirdMCPServer, SQLPatternAnalyzer,
    DefaultPromptManager, PromptGenerator,
    MCPServer
)

def log(message: str):
    """Log to stderr - visible in Docker/Claude Desktop"""
    print(f"[MCP-FIREBIRD] {message}", file=sys.stderr, flush=True)

def main():
    """Main function with complete initialization and diagnostics."""
    
    # Initialize internationalization
    language = os.getenv('FIREBIRD_LANGUAGE', os.getenv('LANG', 'en_US')).split('.')[0]
    i18n = I18n(language)
    
    log(i18n.get('server_info.starting'))
    log(f"📍 {i18n.get('environment.target_host')}: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    log(f"🗄️  {i18n.get('environment.target_database')}: {DB_CONFIG['database']}")
    log(f"👤 {i18n.get('environment.user')}: {DB_CONFIG['user']}")
    log(f"🌐 {i18n.get('environment.charset')}: {DB_CONFIG['charset']}")
    
    # Initialize Firebird libraries
    log(i18n.get('libraries.checking'))
    fdb_available, fdb_module, fdb_error, client_available, client_path = initialize_libraries()
    
    if fdb_available:
        log(f"✅ {i18n.get('libraries.fdb_available')}")
        log(f"📦 {i18n.get('libraries.fdb_version')}: {fdb_module.__version__}")
    else:
        log(f"❌ {i18n.get('libraries.fdb_not_available')}")
        log(f"   ⚠️  {i18n.get('libraries.fdb_error')}: {fdb_error}")
    
    if client_available:
        log(f"✅ {i18n.get('libraries.client_available')}")
        log(f"📚 {i18n.get('libraries.client_location')}: {client_path}")
    else:
        log(f"❌ {i18n.get('libraries.client_not_available')}")
        log(f"💡 {i18n.get('libraries.expected_locations')}:")
        log("   • /opt/firebird/lib/libfbclient.so")
        log("   • /usr/lib/libfbclient.so.2")
        log("   • /usr/lib/x86_64-linux-gnu/libfbclient.so.2")
    
    # Environment information
    log(i18n.get('environment.info'))
    log(f"🔗 LD_LIBRARY_PATH: {os.getenv('LD_LIBRARY_PATH', i18n.get('environment.not_set'))}")
    log(f"🏠 FIREBIRD_HOME: {os.getenv('FIREBIRD_HOME', i18n.get('environment.not_set'))}")
    
    # Initialize server components
    firebird_server = FirebirdMCPServer(
        fdb_module=fdb_module,
        fdb_available=fdb_available,
        client_available=client_available,
        client_path=client_path
    )
    
    # Initialize prompt system with i18n support
    prompt_manager = DefaultPromptManager(i18n, firebird_server)
    prompt_generator = PromptGenerator(firebird_server, i18n)
    
    # Test connection if libraries are available
    if fdb_available and client_available:
        log(i18n.get('connection.testing'))
        try:
            result = firebird_server.test_connection()
            if result["connected"]:
                log(f"✅ {i18n.get('connection.successful')}")
                log(f"🔥 Firebird version: {result['version']}")
                log(f"🎯 {i18n.get('connection.ready_assistance')}")
            else:
                log(f"❌ {i18n.get('connection.failed')}")
                log(f"   ⚠️  Error type: {result.get('type', 'unknown')}")
                error_lines = result['error'].split('\n')
                log(f"   📝 Error: {error_lines[0]}")
                log("💡 Use test_connection tool for detailed diagnosis")
        except Exception as e:
            log(f"❌ Connection test failed: {e}")
    else:
        log(i18n.get('connection.skipping_test'))
        log("   Missing required libraries - use server_status tool for diagnostics")
    
    # Display server capabilities
    log("")
    log("=== STARTING FIREBIRD EXPERT SERVER ===")
    log(f"📋 {i18n.get('tools.available')}:")
    log(f"   • test_connection - {i18n.get('tools.test_connection.description')}")
    log(f"   • execute_query - Execute SQL queries with expert guidance and analysis")
    log(f"   • list_tables - {i18n.get('tools.list_tables.description')}")
    log(f"   • server_status - {i18n.get('tools.server_status.description')}")
    log("")
    log(f"🎯 {i18n.get('prompts.available')}:")
    log(f"   • firebird_expert - {i18n.get('prompts.firebird_expert.description')}")
    log(f"   • firebird_performance - {i18n.get('prompts.firebird_performance.description')}")
    log(f"   • firebird_architecture - {i18n.get('prompts.firebird_architecture.description')}")
    
    # Final status
    if fdb_available and client_available:
        log(f"🔗 {i18n.get('connection.ready_assistance')}")
    else:
        log(f"⚠️  {i18n.get('libraries.limited_functionality')}")
        log(f"   {i18n.get('libraries.installation_instructions')}")
    
    log("=== FIREBIRD EXPERT SERVER READY ===")
    log("")
    
    # Initialize and run MCP server
    mcp_server = MCPServer(
        firebird_server=firebird_server,
        prompt_manager=prompt_manager,
        prompt_generator=prompt_generator,
        i18n=i18n
    )
    
    mcp_server.run()

if __name__ == "__main__":
    main()
