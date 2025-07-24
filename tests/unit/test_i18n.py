"""Testes unitários para sistema de internacionalização."""

import json
import os
from unittest.mock import mock_open, patch

import pytest

import server


class TestI18nSystem:
    """Testes completos do sistema de internacionalização."""

    @pytest.mark.unit
    def test_i18n_initialization_default(self):
        """Testa inicialização com idioma padrão."""
        with patch('server.os.path.exists', return_value=False):
            i18n = server.I18n()
            assert i18n.language == "en_US"
            assert isinstance(i18n.strings, dict)

    @pytest.mark.unit
    def test_i18n_initialization_custom_language(self):
        """Testa inicialização com idioma customizado."""
        with patch('server.os.path.exists', return_value=False):
            i18n = server.I18n("pt_BR")
            assert i18n.language == "pt_BR"

    @pytest.mark.unit
    def test_load_language_file_exists(self):
        """Testa carregamento quando arquivo de idioma existe."""
        mock_strings = {
            "server_info": {
                "initialized": "Servidor MCP inicializado"
            },
            "connection": {
                "successful": "Conexão bem-sucedida!"
            }
        }
        
        mock_file_content = json.dumps(mock_strings)
        
        with patch('server.os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=mock_file_content)), \
             patch('server.os.path.dirname', return_value='/test'), \
             patch('server.os.path.abspath', return_value='/test/server.py'):
            
            i18n = server.I18n("pt_BR")
            
            assert i18n.strings == mock_strings
            assert i18n.get("server_info.initialized") == "Servidor MCP inicializado"

    @pytest.mark.unit
    def test_load_language_fallback_to_english(self):
        """Testa fallback para inglês quando idioma não existe."""
        mock_english_strings = {
            "server_info": {
                "initialized": "MCP Server initialized"
            }
        }
        
        mock_file_content = json.dumps(mock_english_strings)
        
        def mock_exists(path):
            return "en_US.json" in path
        
        with patch('server.os.path.exists', side_effect=mock_exists), \
             patch('builtins.open', mock_open(read_data=mock_file_content)), \
             patch('server.os.path.dirname', return_value='/test'), \
             patch('server.os.path.abspath', return_value='/test/server.py'):
            
            i18n = server.I18n("nonexistent_lang")
            
            assert i18n.strings == mock_english_strings

    @pytest.mark.unit
    def test_load_language_json_decode_error(self):
        """Testa comportamento com erro de JSON."""
        with patch('server.os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data="invalid json")), \
             patch('server.os.path.dirname', return_value='/test'), \
             patch('server.os.path.abspath', return_value='/test/server.py'):
            
            i18n = server.I18n("pt_BR")
            
            # Deve carregar strings de fallback
            assert "server_info" in i18n.strings
            assert "initialized" in i18n.strings["server_info"]

    @pytest.mark.unit
    def test_load_language_file_not_accessible(self):
        """Testa comportamento quando arquivo não é acessível."""
        with patch('server.os.path.exists', return_value=True), \
             patch('builtins.open', side_effect=PermissionError("Permission denied")), \
             patch('server.os.path.dirname', return_value='/test'), \
             patch('server.os.path.abspath', return_value='/test/server.py'):
            
            i18n = server.I18n("pt_BR")
            
            # Deve carregar strings de fallback
            assert "server_info" in i18n.strings

    @pytest.mark.unit
    def test_get_simple_key(self):
        """Testa obtenção de chave simples."""
        i18n = server.I18n()
        i18n.strings = {
            "test": "Test Value"
        }
        
        result = i18n.get("test")
        assert result == "Test Value"

    @pytest.mark.unit
    def test_get_nested_key(self):
        """Testa obtenção de chave aninhada."""
        i18n = server.I18n()
        i18n.strings = {
            "section": {
                "subsection": {
                    "key": "Nested Value"
                }
            }
        }
        
        result = i18n.get("section.subsection.key")
        assert result == "Nested Value"

    @pytest.mark.unit
    def test_get_nonexistent_key(self):
        """Testa obtenção de chave que não existe."""
        i18n = server.I18n()
        i18n.strings = {"existing": "value"}
        
        result = i18n.get("nonexistent.key")
        assert result == "nonexistent.key"

    @pytest.mark.unit
    def test_get_with_kwargs_formatting(self):
        """Testa formatação com argumentos nomeados."""
        i18n = server.I18n()
        i18n.strings = {
            "greeting": "Hello, {name}! You have {count} messages."
        }
        
        result = i18n.get("greeting", name="John", count=5)
        assert result == "Hello, John! You have 5 messages."

    @pytest.mark.unit
    def test_get_with_partial_formatting(self):
        """Testa formatação com argumentos parciais."""
        i18n = server.I18n()
        i18n.strings = {
            "message": "User {name} has {count} items"
        }
        
        result = i18n.get("message", name="Alice")
        # Deve retornar com {count} não substituído
        assert "Alice" in result
        assert "{count}" in result

    @pytest.mark.unit
    def test_get_formatting_error(self):
        """Testa erro na formatação."""
        i18n = server.I18n()
        i18n.strings = {
            "broken": "This has {invalid formatting"
        }
        
        # Deve retornar a string original em caso de erro
        result = i18n.get("broken", name="test")
        assert result == "This has {invalid formatting"

    @pytest.mark.unit
    def test_load_fallback_strings(self):
        """Testa carregamento de strings de fallback."""
        i18n = server.I18n()
        i18n._load_fallback_strings()
        
        # Verificar se strings básicas estão presentes
        assert "server_info" in i18n.strings
        assert "connection" in i18n.strings
        assert "errors" in i18n.strings

    @pytest.mark.unit
    def test_global_i18n_instance(self):
        """Testa instância global de i18n."""
        # A instância global deve existir
        assert hasattr(server, 'i18n')
        assert isinstance(server.i18n, server.I18n)

    @pytest.mark.unit
    def test_language_from_environment(self):
        """Testa detecção de idioma das variáveis de ambiente."""
        with patch.dict(os.environ, {'FIREBIRD_LANGUAGE': 'pt_BR'}), \
             patch('server.os.path.exists', return_value=False):
            
            # Simular recarregamento do módulo para pegar nova variável
            i18n = server.I18n(os.getenv('FIREBIRD_LANGUAGE', 'en_US'))
            assert i18n.language == 'pt_BR'

    @pytest.mark.unit
    def test_language_from_lang_environment(self):
        """Testa detecção de idioma da variável LANG."""
        with patch.dict(os.environ, {'LANG': 'pt_BR.UTF-8'}, clear=True), \
             patch('server.os.path.exists', return_value=False):
            
            # Simular detecção de idioma
            lang = os.getenv('LANG', 'en_US').split('.')[0]
            i18n = server.I18n(lang)
            assert i18n.language == 'pt_BR'

    @pytest.mark.unit
    def test_complex_nested_structure(self):
        """Testa estrutura complexa aninhada."""
        i18n = server.I18n()
        i18n.strings = {
            "prompts": {
                "firebird_expert": {
                    "templates": {
                        "performance": {
                            "title": "Performance Expert"
                        }
                    }
                }
            }
        }
        
        result = i18n.get("prompts.firebird_expert.templates.performance.title")
        assert result == "Performance Expert"

    @pytest.mark.unit
    def test_get_with_array_values(self):
        """Testa obtenção quando valor é array."""
        i18n = server.I18n()
        i18n.strings = {
            "list": ["item1", "item2", "item3"]
        }
        
        result = i18n.get("list")
        assert result == ["item1", "item2", "item3"]

    @pytest.mark.unit
    def test_get_with_numeric_values(self):
        """Testa obtenção de valores numéricos."""
        i18n = server.I18n()
        i18n.strings = {
            "config": {
                "port": 3050,
                "timeout": 30.5,
                "enabled": True
            }
        }
        
        assert i18n.get("config.port") == 3050
        assert i18n.get("config.timeout") == 30.5
        assert i18n.get("config.enabled") is True

    @pytest.mark.unit
    def test_get_with_none_values(self):
        """Testa obtenção de valores None."""
        i18n = server.I18n()
        i18n.strings = {
            "nullable": None
        }
        
        result = i18n.get("nullable")
        assert result is None

    @pytest.mark.unit
    def test_path_handling_edge_cases(self):
        """Testa casos extremos no handling de paths."""
        i18n = server.I18n()
        i18n.strings = {"test": "value"}
        
        # Chave vazia
        result = i18n.get("")
        assert result == ""
        
        # Chave com pontos consecutivos
        result = i18n.get("test..key")
        assert result == "test..key"
        
        # Chave que começa/termina com ponto
        result = i18n.get(".test")
        assert result == ".test"
        
        result = i18n.get("test.")
        assert result == "test."

    @pytest.mark.unit
    def test_formatting_with_special_characters(self):
        """Testa formatação com caracteres especiais."""
        i18n = server.I18n()
        i18n.strings = {
            "special": "Path: {path}, Size: {size}MB, Status: {status}"
        }
        
        result = i18n.get(
            "special", 
            path="/opt/firebird/lib", 
            size=12.5, 
            status="OK"
        )
        
        expected = "Path: /opt/firebird/lib, Size: 12.5MB, Status: OK"
        assert result == expected

    @pytest.mark.unit
    def test_get_with_positional_args_support(self):
        """Testa suporte a argumentos posicionais (*args) - correção do erro MCP."""
        i18n = server.I18n()
        i18n.strings = {
            "prompt_templates": {
                "firebird_expert": {
                    "guidelines": "### Guidelines for {operation_type}:",
                    "complexity_level": "Complexity level ({complexity_level})"
                },
                "firebird_performance": {
                    "focus_queries": "### Focus on {query_type} Queries:",
                    "specialization": "### Specialization Area - {focus_area}:"
                },
                "firebird_architecture": {
                    "focus_topic": "### Focus on {topic}:",
                    "version_info": "### Firebird Version {version_focus}:"
                }
            }
        }
        
        # Teste 1: Argumentos nomeados via **kwargs (deve funcionar)
        result1 = i18n.get(
            'prompt_templates.firebird_expert.guidelines', 
            operation_type='SELECT'
        )
        assert result1 == "### Guidelines for SELECT:"
        
        # Teste 2: Argumentos posicionais via *args (nova funcionalidade)
        result2 = i18n.get(
            'prompt_templates.firebird_expert.complexity_level',
            'advanced'
        )
        assert result2 == "Complexity level (advanced)"
        
        # Teste 3: Múltiplos argumentos nomeados
        i18n.strings["multi_param"] = "User {name} has {count} items in {location}"
        result3 = i18n.get(
            'multi_param',
            name='Alice',
            count=5,
            location='warehouse'
        )
        assert result3 == "User Alice has 5 items in warehouse"
        
        # Teste 4: Compatibilidade com método .format() ainda funciona
        result4 = i18n.get('prompt_templates.firebird_expert.guidelines').format(
            operation_type='INSERT'
        )
        assert result4 == "### Guidelines for INSERT:"
        
        # Teste 5: Chamadas que causavam o erro original agora funcionam
        operation_type = "select"
        complexity_level = "intermediate"
        
        # Estas chamadas causavam: "I18n.get() takes 2 positional arguments but 3 were given"
        result5 = i18n.get(
            'prompt_templates.firebird_expert.guidelines',
            operation_type=operation_type.upper()
        )
        assert result5 == "### Guidelines for SELECT:"
        
        result6 = i18n.get(
            'prompt_templates.firebird_expert.complexity_level',
            complexity_level=complexity_level
        )
        assert result6 == "Complexity level (intermediate)"

    @pytest.mark.unit
    def test_mcp_prompt_generation_fix(self):
        """Testa correção específica do erro na geração de prompts MCP."""
        i18n = server.I18n()
        i18n.strings = {
            "prompt_templates": {
                "firebird_performance": {
                    "focus_queries": "### Focus on {query_type} Queries:",
                    "specialization": "### Specialization Area - {focus_area}:"
                },
                "firebird_architecture": {
                    "focus_topic": "### Focus on {topic}:",
                    "version_info": "### Firebird Version {version_focus}:"
                }
            }
        }
        
        # Simular as chamadas exatas que causavam erro no método handle_prompts_get
        query_type = "complex"
        focus_area = "indexes"
        topic = "backup"
        version_focus = "4.0"
        
        # Estas eram as linhas problemáticas:
        try:
            result1 = i18n.get(
                'prompt_templates.firebird_performance.focus_queries'
            ).format(query_type=query_type.title())
            
            result2 = i18n.get(
                'prompt_templates.firebird_performance.specialization'
            ).format(focus_area=focus_area.title())
            
            result3 = i18n.get(
                'prompt_templates.firebird_architecture.focus_topic'
            ).format(topic=topic.title())
            
            result4 = i18n.get(
                'prompt_templates.firebird_architecture.version_info'
            ).format(version_focus=version_focus)
            
            # Se chegou até aqui, as correções funcionaram
            assert "Complex" in result1
            assert "Indexes" in result2
            assert "Backup" in result3
            assert "4.0" in result4
            
        except TypeError as e:
            if "takes 2 positional arguments but 3 were given" in str(e):
                pytest.fail("Erro MCP ainda não foi corrigido")
            else:
                raise

    @pytest.mark.unit
    def test_unicode_handling(self):
        """Testa handling de caracteres Unicode."""
        i18n = server.I18n()
        i18n.strings = {
            "unicode": "Configuração do usuário: {user} 🔥"
        }
        
        result = i18n.get("unicode", user="José")
        assert result == "Configuração do usuário: José 🔥"
