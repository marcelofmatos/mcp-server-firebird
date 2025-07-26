"""Unit tests for Prompt System - Updated for dynamic schema prompts."""

import pytest
import sys
import os

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from prompts.manager import DefaultPromptManager
from prompts.generator import PromptGenerator


class TestDefaultPromptManager:
    """Test cases for DefaultPromptManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Override environment for testing
        os.environ['FIREBIRD_DEFAULT_PROMPT_ENABLED'] = 'true'
        os.environ['FIREBIRD_DEFAULT_PROMPT'] = 'firebird_expert'
        self.manager = DefaultPromptManager()
    
    def test_manager_initialization(self):
        """Test proper initialization of prompt manager."""
        assert self.manager.config['enabled'] is True
        assert self.manager.config['prompt_name'] == 'firebird_expert'
        assert 'operation_type' in self.manager.config
        assert 'complexity_level' in self.manager.config
    
    def test_get_default_context_enabled(self):
        """Test context generation when enabled."""
        context = self.manager.get_default_context()
        
        assert isinstance(context, str)
        assert len(context) > 0
        # Updated to match the new compact context
        assert 'especialista em Firebird' in context or 'Firebird' in context
    
    def test_get_default_context_disabled(self):
        """Test context generation when disabled."""
        self.manager.config['enabled'] = False
        context = self.manager.get_default_context()
        
        assert context == ""
    
    def test_apply_to_response_enabled(self):
        """Test applying context to responses when enabled."""
        content = "Query result: SUCCESS"
        enhanced = self.manager.apply_to_response(content, tool_name='execute_query')
        
        assert len(enhanced) >= len(content)
        assert content in enhanced
    
    def test_apply_to_response_disabled(self):
        """Test response handling when disabled."""
        content = "Query result: SUCCESS"
        enhanced = self.manager.apply_to_response(content, tool_name='execute_query', disabled=True)
        
        assert enhanced == content  # Should be unchanged
    
    def test_apply_to_non_target_tool(self):
        """Test that context is not applied to non-target tools."""
        content = "Server status: OK"
        enhanced = self.manager.apply_to_response(content, tool_name='server_status')
        
        assert enhanced == content  # Should be unchanged for server_status
    
    def test_enhanced_tool_description(self):
        """Test enhancement of tool descriptions."""
        original_desc = "Execute SQL queries"
        enhanced = self.manager.get_enhanced_tool_description('execute_query', original_desc)
        
        assert len(enhanced) >= len(original_desc)
        assert original_desc in enhanced
    
    def test_enhanced_tool_description_disabled(self):
        """Test tool description when prompt system is disabled."""
        self.manager.config['enabled'] = False
        original_desc = "Execute SQL queries"
        enhanced = self.manager.get_enhanced_tool_description('execute_query', original_desc)
        
        assert enhanced == original_desc  # Should be unchanged
    
    def test_update_config(self):
        """Test dynamic configuration updates."""
        original_complexity = self.manager.config['complexity_level']
        self.manager.update_config(complexity_level='advanced')
        
        assert self.manager.config['complexity_level'] == 'advanced'
        assert self.manager.config['complexity_level'] != original_complexity
    
    def test_get_status(self):
        """Test status retrieval."""
        status = self.manager.get_status()
        
        assert isinstance(status, dict)
        assert 'enabled' in status
        assert 'prompt_name' in status
        assert 'database_context' in status
        assert isinstance(status['database_context'], dict)


class TestPromptGenerator:
    """Test cases for PromptGenerator class - Updated for dynamic schema prompts."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.generator = PromptGenerator()
    
    def test_table_schema_prompt_generation(self):
        """Test generation of table schema prompts."""
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
                        },
                        {
                            "column_name": "NAME",
                            "data_type": "varchar(100)",
                            "nullable": "YES",
                            "default_value": None,
                            "position": 2
                        }
                    ],
                    "primary_keys": ["ID"],
                    "foreign_keys": [],
                    "indexes": [
                        {
                            "index_name": "PK_CUSTOMERS",
                            "column_name": "ID",
                            "is_unique": True
                        }
                    ]
                }
        
        mock_server = MockFirebirdServer()
        generator = PromptGenerator(mock_server)
        
        prompt = generator.generate('customers_schema', {})
        
        assert isinstance(prompt, str)
        assert len(prompt) > 100  # Should be substantial
        assert 'customers' in prompt.lower()
        assert 'ID' in prompt
        assert 'NAME' in prompt
        assert 'varchar(100)' in prompt
        assert 'PK_CUSTOMERS' in prompt
    
    def test_unknown_prompt_error(self):
        """Test error handling for unknown prompt names."""
        with pytest.raises(ValueError) as exc_info:
            self.generator.generate('unknown_prompt', {})
        
        assert 'Unknown prompt' in str(exc_info.value)
    
    def test_get_available_table_prompts(self):
        """Test retrieval of available table prompts."""
        class MockFirebirdServer:
            def get_tables(self):
                return {
                    "success": True,
                    "tables": ["customers", "orders", "products", "users"]
                }
        
        mock_server = MockFirebirdServer()
        generator = PromptGenerator(mock_server)
        
        prompts = generator.get_available_table_prompts()
        
        assert isinstance(prompts, list)
        assert len(prompts) == 4
        assert any(p["name"] == "customers_schema" for p in prompts)
        assert any(p["name"] == "orders_schema" for p in prompts)
        assert any(p["name"] == "products_schema" for p in prompts)
        assert any(p["name"] == "users_schema" for p in prompts)
    
    def test_get_available_table_prompts_no_server(self):
        """Test available prompts without server."""
        generator = PromptGenerator()
        prompts = generator.get_available_table_prompts()
        
        assert isinstance(prompts, list)
        assert len(prompts) == 0
    
    def test_register_firebird_server(self):
        """Test registration of Firebird server for context."""
        class MockServer:
            pass
        
        mock_server = MockServer()
        self.generator.register_firebird_server(mock_server)
        
        assert self.generator.firebird_server == mock_server
    
    def test_schema_prompt_with_relationships(self):
        """Test schema prompt generation with foreign key relationships."""
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
                        },
                        {
                            "column_name": "CUSTOMER_ID",
                            "data_type": "integer",
                            "nullable": "NO",
                            "default_value": None,
                            "position": 2
                        }
                    ],
                    "primary_keys": ["ID"],
                    "foreign_keys": [
                        {
                            "constraint_name": "FK_ORDERS_CUSTOMER",
                            "column_name": "CUSTOMER_ID",
                            "referenced_table": "CUSTOMERS",
                            "referenced_column": "ID"
                        }
                    ],
                    "indexes": []
                }
        
        mock_server = MockFirebirdServer()
        generator = PromptGenerator(mock_server)
        
        prompt = generator.generate('orders_schema', {})
        
        assert 'CUSTOMER_ID' in prompt
        assert 'CUSTOMERS' in prompt
        assert 'FK_ORDERS_CUSTOMER' in prompt or 'Chaves Estrangeiras' in prompt or 'Foreign Keys' in prompt


if __name__ == '__main__':
    pytest.main([__file__])
