#!/usr/bin/env python3
"""
Script de teste para verificar conectividade com servidor MCP Firebird
Versão atualizada para usar biblioteca FDB
"""

import requests
import json
import time
import sys
from typing import Dict, Any

def test_fdb_direct(host: str, database: str, user: str, password: str) -> bool:
    """Testa conexão direta com FDB (sem servidor MCP)"""
    print(f"\n🔍 Testando conexão FDB direta...")
    try:
        import fdb
        
        dsn = f"{host}/3050:{database}"
        print(f"   DSN: {dsn}")
        
        conn = fdb.connect(
            dsn=dsn,
            user=user,
            password=password,
            charset='UTF8'
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT RDB$GET_CONTEXT('SYSTEM', 'ENGINE_VERSION') FROM RDB$DATABASE")
        version = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"   ✅ Conexão FDB OK - Firebird {version.strip()}")
        return True
        
    except ImportError:
        print("   ❌ Biblioteca FDB não disponível")
        return False
    except Exception as e:
        print(f"   ❌ Erro FDB: {e}")
        return False

def test_mcp_server(base_url: str = "http://localhost:3000") -> bool:
    """Testa todas as funcionalidades básicas do servidor MCP"""
    
    print(f"🔍 Testando servidor MCP em: {base_url}")
    print("=" * 50)
    
    success_count = 0
    total_tests = 0
    
    # Teste 1: Health Check
    total_tests += 1
    print("\n1. 🏥 Testando Health Check...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'healthy':
                print("   ✅ Health check OK")
                print(f"   📊 Versão do banco: {data.get('server_version', 'N/A')}")
                success_count += 1
            else:
                print(f"   ❌ Servidor não saudável: {data}")
        else:
            print(f"   ❌ HTTP {response.status_code}: {response.text}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # Teste 2: Informações do Banco
    total_tests += 1
    print("\n2. 📚 Testando informações do banco...")
    try:
        response = requests.get(f"{base_url}/info", timeout=10)
        if response.status_code == 200:
            data = response.json()
            tables = data.get('tables', [])
            print("   ✅ Informações obtidas com sucesso")
            print(f"   📋 Tabelas encontradas: {len(tables)}")
            if tables:
                print(f"   📄 Primeiras tabelas: {', '.join(tables[:5])}")
            success_count += 1
        else:
            print(f"   ❌ HTTP {response.status_code}: {response.text}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # Teste 3: Listar Tabelas
    total_tests += 1
    print("\n3. 📋 Testando listagem de tabelas...")
    try:
        response = requests.get(f"{base_url}/tables", timeout=10)
        if response.status_code == 200:
            tables = response.json()
            print("   ✅ Tabelas listadas com sucesso")
            print(f"   📊 Total de tabelas: {len(tables)}")
            success_count += 1
        else:
            print(f"   ❌ HTTP {response.status_code}: {response.text}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # Teste 4: Query Simples
    total_tests += 1
    print("\n4. 🔍 Testando query simples...")
    try:
        query_data = {
            "sql": "SELECT 1 as TESTE, CURRENT_TIMESTAMP as AGORA FROM RDB$DATABASE"
        }
        response = requests.post(f"{base_url}/query", json=query_data, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("   ✅ Query executada com sucesso")
                print(f"   ⏱️  Tempo de execução: {data.get('execution_time', 'N/A')}s")
                if data.get('data'):
                    print(f"   📊 Resultado: {data['data'][0]}")
                success_count += 1
            else:
                print(f"   ❌ Query falhou: {data.get('error')}")
        else:
            print(f"   ❌ HTTP {response.status_code}: {response.text}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # Teste 5: Teste de Conexão
    total_tests += 1
    print("\n5. 🔌 Testando conexão direta...")
    try:
        response = requests.get(f"{base_url}/connection/test", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('connected'):
                print("   ✅ Conexão com banco OK")
                print(f"   🔗 Banco: {data.get('database', 'N/A')}")
                success_count += 1
            else:
                print(f"   ❌ Conexão falhou: {data.get('error')}")
        else:
            print(f"   ❌ HTTP {response.status_code}: {response.text}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # Resultado Final
    print("\n" + "=" * 50)
    print(f"📊 RESULTADO FINAL: {success_count}/{total_tests} testes passaram")
    
    if success_count == total_tests:
        print("🎉 Todos os testes passaram! Servidor MCP está funcionando perfeitamente.")
        return True
    else:
        print("⚠️  Alguns testes falharam. Verifique a configuração.")
        return False

def test_specific_table(base_url: str, table_name: str) -> None:
    """Testa operações em uma tabela específica"""
    print(f"\n🔍 Testando tabela específica: {table_name}")
    print("-" * 30)
    
    # Schema da tabela
    try:
        response = requests.get(f"{base_url}/tables/{table_name}/schema", timeout=10)
        if response.status_code == 200:
            schema = response.json()
            print(f"   ✅ Schema obtido para {table_name}")
            print(f"   📊 Campos: {len(schema.get('fields', []))}")
            for field in schema.get('fields', [])[:3]:  # Primeiros 3 campos
                print(f"   📄 {field['name']} ({field['type']})")
        else:
            print(f"   ❌ Erro ao obter schema: HTTP {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # Query na tabela
    try:
        query_data = {
            "sql": f"SELECT FIRST 5 * FROM {table_name}"
        }
        response = requests.post(f"{base_url}/query", json=query_data, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                rows = data.get('data', [])
                print(f"   ✅ Consulta executada: {len(rows)} registros")
            else:
                print(f"   ❌ Query falhou: {data.get('error')}")
        else:
            print(f"   ❌ HTTP {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")

def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Teste do servidor MCP Firebird')
    parser.add_argument('--url', default='http://localhost:3000', 
                       help='URL base do servidor MCP')
    parser.add_argument('--table', help='Nome de tabela específica para testar')
    parser.add_argument('--wait', type=int, default=0,
                       help='Aguardar X segundos antes de iniciar testes')
    parser.add_argument('--direct', action='store_true',
                       help='Testar conexão FDB direta (requer --host, --database, --user, --password)')
    parser.add_argument('--host', help='Host do Firebird (para teste direto)')
    parser.add_argument('--database', help='Caminho do banco (para teste direto)')
    parser.add_argument('--user', help='Usuário (para teste direto)')
    parser.add_argument('--password', help='Senha (para teste direto)')
    
    args = parser.parse_args()
    
    if args.wait > 0:
        print(f"⏳ Aguardando {args.wait} segundos...")
        time.sleep(args.wait)
    
    success = True
    
    # Teste direto FDB se solicitado
    if args.direct:
        if not all([args.host, args.database, args.user, args.password]):
            print("❌ Para teste direto, forneça: --host, --database, --user, --password")
            sys.exit(1)
        
        fdb_success = test_fdb_direct(args.host, args.database, args.user, args.password)
        if not fdb_success:
            success = False
    
    # Teste principal do servidor MCP
    mcp_success = test_mcp_server(args.url)
    if not mcp_success:
        success = False
    
    # Teste de tabela específica se fornecida
    if args.table:
        test_specific_table(args.url, args.table)
    
    # Exit code baseado no sucesso
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()