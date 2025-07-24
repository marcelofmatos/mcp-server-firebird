#!/usr/bin/env python3
"""
Script para executar testes com diferentes configurações.
Alternativa Python para o script shell.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd, check=True, capture_output=False):
    """Executa comando e retorna resultado."""
    print(f"🔧 Executando: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd, 
            check=check, 
            capture_output=capture_output,
            text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao executar comando: {e}")
        if capture_output:
            print(f"STDOUT: {e.stdout}")
            print(f"STDERR: {e.stderr}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='Executor de testes MCP Firebird')
    parser.add_argument('--type', '-t', choices=['unit', 'integration', 'performance', 'all'],
                       default='all', help='Tipo de teste')
    parser.add_argument('--coverage', '-c', action='store_true', 
                       help='Gerar relatório de cobertura')
    parser.add_argument('--html', action='store_true',
                       help='Gerar relatórios HTML')
    parser.add_argument('--fast', '-f', action='store_true',
                       help='Execução rápida (pula testes lentos)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Output verboso')
    parser.add_argument('--parallel', '-p', action='store_true',
                       help='Executar testes em paralelo')
    parser.add_argument('--lint', action='store_true',
                       help='Apenas verificações de código')
    parser.add_argument('--install-deps', action='store_true',
                       help='Instalar dependências primeiro')
    
    args = parser.parse_args()
    
    # Verificar se está no diretório correto
    if not Path('server.py').exists():
        print("❌ Execute este script no diretório raiz do projeto")
        sys.exit(1)
    
    # Instalar dependências se solicitado
    if args.install_deps:
        print("📦 Instalando dependências...")
        run_command([sys.executable, '-m', 'pip', 'install', '-r', 'requirements-dev.txt'])
    
    # Verificar se pytest está disponível
    try:
        import pytest
        print(f"✅ pytest {pytest.__version__} encontrado")
    except ImportError:
        print("❌ pytest não encontrado. Use --install-deps para instalar.")
        sys.exit(1)
    
    # Apenas linting
    if args.lint:
        print("🔍 Executando verificações de código...")
        
        # Ruff
        try:
            run_command(['ruff', 'check', '.'])
            print("✅ Ruff: OK")
        except:
            print("⚠️  Ruff não disponível ou encontrou problemas")
        
        # Black
        try:
            run_command(['black', '--check', '.'])
            print("✅ Black: OK")
        except:
            print("⚠️  Black não disponível ou encontrou problemas")
        
        # MyPy
        try:
            run_command(['mypy', '.'])
            print("✅ MyPy: OK")
        except:
            print("⚠️  MyPy não disponível ou encontrou problemas")
        
        return
    
    # Construir comando pytest
    pytest_cmd = [sys.executable, '-m', 'pytest']
    
    # Diretório de testes
    if args.type == 'unit':
        pytest_cmd.append('tests/unit')
    elif args.type == 'integration':
        pytest_cmd.append('tests/integration')
    elif args.type == 'performance':
        pytest_cmd.extend(['-m', 'slow or performance'])
    else:
        pytest_cmd.append('tests/')
    
    # Opções de execução
    if args.verbose:
        pytest_cmd.append('-v')
    else:
        pytest_cmd.append('-q')
    
    if args.fast:
        pytest_cmd.extend(['-m', 'not slow'])
    
    if args.parallel and args.type != 'integration':
        pytest_cmd.extend(['-n', 'auto'])
    
    # Cobertura
    if args.coverage:
        pytest_cmd.extend([
            '--cov=server',
            '--cov-report=term-missing',
            '--cov-fail-under=80'
        ])
        
        if args.html:
            pytest_cmd.append('--cov-report=html:htmlcov')
    
    # Relatórios
    if args.html:
        os.makedirs('reports', exist_ok=True)
        pytest_cmd.extend([
            '--html=reports/pytest-report.html',
            '--self-contained-html'
        ])
    
    # Executar testes
    print(f"🧪 Executando testes: {args.type}")
    result = run_command(pytest_cmd, check=False)
    
    if result.returncode == 0:
        print("🎉 Todos os testes passaram!")
        
        # Mostrar relatórios gerados
        if args.html:
            print("\n📊 Relatórios gerados:")
            if Path('htmlcov/index.html').exists():
                print(f"   • Cobertura: file://{Path('htmlcov/index.html').absolute()}")
            if Path('reports/pytest-report.html').exists():
                print(f"   • Testes: file://{Path('reports/pytest-report.html').absolute()}")
    else:
        print("❌ Alguns testes falharam!")
        sys.exit(1)


if __name__ == '__main__':
    main()
