#!/usr/bin/env python3
"""
Script de diagnóstico para problemas com bibliotecas Firebird
"""

import os
import sys
import subprocess
import glob

def print_header(title):
    print(f"\n{'='*50}")
    print(f"🔍 {title}")
    print('='*50)

def print_section(title):
    print(f"\n📋 {title}")
    print('-'*30)

def run_command(cmd, description):
    """Executar comando e mostrar resultado"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print(f"✅ {description}")
        if result.stdout:
            print(f"   📄 Output: {result.stdout.strip()}")
        if result.stderr and result.returncode != 0:
            print(f"   ❌ Error: {result.stderr.strip()}")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ {description}: {e}")
        return False

def check_environment():
    """Verificar variáveis de ambiente"""
    print_section("Variáveis de Ambiente")
    
    env_vars = ['FIREBIRD', 'LD_LIBRARY_PATH', 'PATH']
    for var in env_vars:
        value = os.environ.get(var, 'NOT SET')
        print(f"   {var}: {value}")

def check_libraries():
    """Procurar bibliotecas Firebird no sistema"""
    print_section("Bibliotecas Firebird")
    
    # Locais comuns para procurar
    search_paths = [
        '/usr/lib/',
        '/usr/lib/x86_64-linux-gnu/',
        '/usr/local/lib/',
        '/opt/firebird/',
        '/lib/',
        '/lib64/'
    ]
    
    library_patterns = [
        '*fbclient*',
        '*firebird*',
        '*ib_util*'
    ]
    
    found_libraries = []
    
    for path in search_paths:
        if os.path.exists(path):
            for pattern in library_patterns:
                files = glob.glob(os.path.join(path, '**', pattern), recursive=True)
                for file in files:
                    found_libraries.append(file)
                    print(f"   ✅ Encontrado: {file}")
    
    if not found_libraries:
        print("   ❌ Nenhuma biblioteca Firebird encontrada!")
        return False
    
    return True

def check_ldconfig():
    """Verificar cache de bibliotecas dinâmicas"""
    print_section("Cache de Bibliotecas (ldconfig)")
    
    run_command("ldconfig -p | grep -i firebird", "Procurar Firebird no cache")
    run_command("ldconfig -p | grep -i fbclient", "Procurar fbclient no cache")

def test_python_imports():
    """Testar imports Python"""
    print_section("Imports Python")
    
    # Teste FDB
    try:
        import fdb
        fdb_version = getattr(fdb, '__version__', 'Unknown')
        print(f"   ✅ FDB import OK - Version: {fdb_version}")
        
        # Testar criação de conexão (sem conectar)
        try:
            # Isso deve falhar na conexão, mas não no import/setup
            conn = fdb.connect(dsn="localhost/3050:/tmp/nonexistent.fdb", 
                             user="test", password="test")
        except Exception as e:
            error_msg = str(e)
            if "could not be determined" in error_msg:
                print(f"   ❌ FDB: Bibliotecas cliente não encontradas")
                print(f"   📄 Erro: {error_msg}")
                return False
            elif "network" in error_msg.lower() or "connection" in error_msg.lower():
                print(f"   ✅ FDB: Bibliotecas OK (erro de conexão esperado)")
                return True
            else:
                print(f"   ⚠️  FDB: Erro inesperado: {error_msg}")
                return False
                
    except ImportError as e:
        print(f"   ❌ FDB import failed: {e}")
        return False
    except Exception as e:
        print(f"   ❌ FDB error: {e}")
        return False
    
    return True

def check_system_info():
    """Informações do sistema"""
    print_section("Informações do Sistema")
    
    run_command("uname -a", "Sistema operacional")
    run_command("python3 --version", "Versão Python")
    run_command("ldd --version", "Versão ldd")
    run_command("dpkg -l | grep -i firebird", "Pacotes Firebird instalados")

def suggest_fixes():
    """Sugerir correções"""
    print_section("Possíveis Soluções")
    
    print("""
   🔧 Soluções para tentar:
   
   1. Instalar bibliotecas cliente Firebird:
      apt-get update
      apt-get install libfbclient2 firebird-dev firebird3.0-client
   
   2. Configurar variáveis de ambiente:
      export FIREBIRD=/usr
      export LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH
   
   3. Atualizar cache de bibliotecas:
      ldconfig
   
   4. Usar Dockerfile Ubuntu (melhor suporte):
      Usar o Dockerfile Ubuntu fornecido nos artefatos
   
   5. Download manual das bibliotecas:
      Usar o Dockerfile alternativo com download manual
   """)

def main():
    """Função principal"""
    print_header("Diagnóstico Firebird Client Libraries")
    
    print("🎯 Verificando configuração das bibliotecas Firebird...")
    
    # Executar verificações
    env_ok = True
    check_environment()
    
    lib_ok = check_libraries()
    check_ldconfig()
    system_ok = True
    check_system_info()
    
    python_ok = test_python_imports()
    
    # Resultado final
    print_header("Resultado do Diagnóstico")
    
    issues = []
    if not lib_ok:
        issues.append("❌ Bibliotecas Firebird não encontradas")
    if not python_ok:
        issues.append("❌ Imports Python falhando")
    
    if issues:
        print("🚨 PROBLEMAS ENCONTRADOS:")
        for issue in issues:
            print(f"   {issue}")
        suggest_fixes()
        return 1
    else:
        print("🎉 TUDO OK! Bibliotecas Firebird configuradas corretamente.")
        return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)