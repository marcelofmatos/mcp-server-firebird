"""Unit tests for dynamic schema prompts."""

import pytest
import sys
import os

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from core.i18n import I18n
from prompts.generator import PromptGenerator


class TestSchemaPrompts:
    """Test cases for dynamic schema prompt generation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.i18n_pt = I18n("pt_BR")
        self.i18n_en = I18n("en_US")
        self.generator = PromptGenerator(firebird_server=None, i18n=self.i18n_pt)
    
    def test_i18n_keys_pt_br(self):
        """Test if new i18n keys work for pt_BR."""
        # Test basic keys
        header = self.i18n_pt.get('table_schema.header', table_name='TESTE')
        assert 'TESTE' in header
        assert 'Schema da Tabela' in header
        
        description = self.i18n_pt.get('table_schema.description', table_name='TESTE')
        assert 'TESTE' in description
        assert 'schema' in description.lower()
        
        columns_header = self.i18n_pt.get('table_schema.columns_header')
        assert 'Colunas' in columns_header
        
        usage_guidance = self.i18n_pt.get('table_schema.usage_guidance')
        assert 'Orientações' in usage_guidance or 'Uso' in usage_guidance
    
    def test_i18n_keys_en_us(self):
        """Test if new i18n keys work for en_US."""
        # Test basic keys
        header = self.i18n_en.get('table_schema.header', table_name='TEST')
        assert 'TEST' in header
        assert 'Table Schema' in header
        
        description = self.i18n_en.get('table_schema.description', table_name='TEST')
        assert 'TEST' in description
        assert 'schema' in description.lower()
        
        columns_header = self.i18n_en.get('table_schema.columns_header')
        assert 'Columns' in columns_header
        
        usage_guidance = self.i18n_en.get('table_schema.usage_guidance')
        assert 'Usage' in usage_guidance or 'Guidance' in usage_guidance
    
    def test_prompt_generator_without_server(self):
        """Test prompt generator without Firebird server."""
        generator = PromptGenerator(firebird_server=None, i18n=self.i18n_pt)
        
        # Test without server
        prompts = generator.get_available_table_prompts()
        assert isinstance(prompts, list)
        assert len(prompts) == 0
        
        # Test prompt generation without server
        prompt_text = generator._generate_table_schema_prompt("TESTE")
        assert isinstance(prompt_text, str)
        assert "Erro" in prompt_text or "Error" in prompt_text
    
    def test_prompt_generator_with_mock_server(self):
        """Test prompt generator with mock Firebird server."""
        class MockFirebirdServer:
            def get_tables(self):
                return {
                    "success": True,
                    "tables": ["USUARIOS", "PRODUTOS", "PEDIDOS"]
                }
            
            def get_table_schema(self, table_name):
                return {
                    "success": True,
                    "table_name": table_name,
                    "columns": [
                        {
                            "column_name": "ID",
                            "data_type": "integer",
                            "nullable": "NO",
                            "default_value": None,
                            "position": 1
                        },
                        {
                            "column_name": "NOME",
                            "data_type": "varchar(100)",
                            "nullable": "YES",
                            "default_value": None,
                            "position": 2
                        },
                        {
                            "column_name": "EMAIL",
                            "data_type": "varchar(255)",
                            "nullable": "NO",
                            "default_value": None,
                            "position": 3
                        }
                    ],
                    "primary_keys": ["ID"],
                    "foreign_keys": [],
                    "indexes": [
                        {
                            "index_name": "PK_USUARIOS",
                            "column_name": "ID",
                            "is_unique": True
                        },
                        {
                            "index_name": "IX_USUARIOS_EMAIL",
                            "column_name": "EMAIL",
                            "is_unique": True
                        }
                    ]
                }
        
        mock_server = MockFirebirdServer()
        generator = PromptGenerator(firebird_server=mock_server, i18n=self.i18n_pt)
        
        # Test available prompts
        prompts = generator.get_available_table_prompts()
        assert len(prompts) == 3
        assert any(p["name"] == "USUARIOS_schema" for p in prompts)
        assert any(p["name"] == "PRODUTOS_schema" for p in prompts)
        assert any(p["name"] == "PEDIDOS_schema" for p in prompts)
        
        # Test schema prompt generation
        prompt_text = generator._generate_table_schema_prompt("USUARIOS")
        assert isinstance(prompt_text, str)
        assert "USUARIOS" in prompt_text
        assert "ID" in prompt_text
        assert "NOME" in prompt_text
        assert "EMAIL" in prompt_text
        assert "varchar(100)" in prompt_text
        assert "varchar(255)" in prompt_text
        assert "PK_USUARIOS" in prompt_text
        assert "IX_USUARIOS_EMAIL" in prompt_text
    
    def test_schema_prompt_structure(self):
        """Test the structure of generated schema prompts."""
        class MockFirebirdServer:
            def get_table_schema(self, table_name):
                return {
                    "success": True,
                    "table_name": table_name,
                    "columns": [
                        {
                            "column_name": "ID",
                            "data_type": "integer",
                            "nullable": "NO",
                            "default_value": None,
                            "position": 1
                        }
                    ],
                    "primary_keys": ["ID"],
                    "foreign_keys": [
                        {
                            "constraint_name": "FK_TEST",
                            "column_name": "USER_ID",
                            "referenced_table": "USERS",
                            "referenced_column": "ID"
                        }
                    ],
                    "indexes": [
                        {
                            "index_name": "PK_TEST",
                            "column_name": "ID",
                            "is_unique": True
                        }
                    ]
                }
        
        mock_server = MockFirebirdServer()
        generator = PromptGenerator(firebird_server=mock_server, i18n=self.i18n_pt)
        
        prompt_text = generator._generate_table_schema_prompt("TEST_TABLE")
        
        # Check structure sections
        assert "# Schema da Tabela: TEST_TABLE" in prompt_text
        assert "## Informações da Tabela" in prompt_text
        assert "## Colunas" in prompt_text
        assert "## Chaves Primárias" in prompt_text
        assert "## Chaves Estrangeiras" in prompt_text
        assert "## Índices" in prompt_text
        assert "## Orientações de Uso" in prompt_text
    
    def test_prompt_generation_error_handling(self):
        """Test error handling in prompt generation."""
        class MockFirebirdServerWithError:
            def get_table_schema(self, table_name):
                return {
                    "success": False,
                    "error": "Table not found"
                }
        
        mock_server = MockFirebirdServerWithError()
        generator = PromptGenerator(firebird_server=mock_server, i18n=self.i18n_pt)
        
        prompt_text = generator._generate_table_schema_prompt("NONEXISTENT")
        assert "Erro" in prompt_text
        assert "NONEXISTENT" in prompt_text
        assert "Table not found" in prompt_text
    
    def test_generator_prompt_method(self):
        """Test the main generate method."""
        class MockFirebirdServer:
            def get_table_schema(self, table_name):
                return {
                    "success": True,
                    "table_name": table_name,
                    "columns": [],
                    "primary_keys": [],
                    "foreign_keys": [],
                    "indexes": []
                }
        
        mock_server = MockFirebirdServer()
        generator = PromptGenerator(firebird_server=mock_server, i18n=self.i18n_pt)
        
        # Test valid schema prompt
        prompt_text = generator.generate("USERS_schema", {})
        assert isinstance(prompt_text, str)
        assert "USERS" in prompt_text
        
        # Test invalid prompt
        with pytest.raises(ValueError) as exc_info:
            generator.generate("invalid_prompt", {})
        assert "Unknown prompt" in str(exc_info.value)


if __name__ == '__main__':
    pytest.main([__file__])
