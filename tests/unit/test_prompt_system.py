"""Unit tests for Prompt System."""

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
        assert 'FIREBIRD EXPERT MODE ACTIVE' in context
        assert 'Expert Guidelines' in context
    
    def test_get_default_context_disabled(self):
        """Test context generation when disabled."""
        self.manager.config['enabled'] = False
        context = self.manager.get_default_context()
        
        assert context == ""
    
    def test_apply_to_response_enabled(self):
        """Test applying context to responses when enabled."""
        content = "Query result: SUCCESS"
        enhanced = self.manager.apply_to_response(content, tool_name='execute_query')
        
        assert len(enhanced) > len(content)
        assert 'FIREBIRD EXPERT MODE ACTIVE' in enhanced
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
        
        assert len(enhanced) > len(original_desc)
        assert 'Auto-Expert Mode' in enhanced
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
    """Test cases for PromptGenerator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.generator = PromptGenerator()
    
    def test_firebird_expert_prompt_generation(self):
        """Test generation of firebird_expert prompt."""
        args = {
            'operation_type': 'select',
            'complexity_level': 'intermediate',
            'table_context': 'customers'
        }
        
        prompt = self.generator.generate('firebird_expert', args)
        
        assert isinstance(prompt, str)
        assert len(prompt) > 100  # Should be substantial
        assert 'Firebird Database Expert' in prompt
        assert 'select'.upper() in prompt
        assert 'intermediate' in prompt
        assert 'customers' in prompt
    
    def test_firebird_performance_prompt_generation(self):
        """Test generation of firebird_performance prompt."""
        args = {
            'query_type': 'complex',
            'focus_area': 'indexes'
        }
        
        prompt = self.generator.generate('firebird_performance', args)
        
        assert isinstance(prompt, str)
        assert 'Performance Optimization' in prompt
        assert 'complex'.title() in prompt
        assert 'indexes'.title() in prompt
        assert 'SET PLAN ON' in prompt  # Should include monitoring commands
    
    def test_firebird_architecture_prompt_generation(self):
        """Test generation of firebird_architecture prompt."""
        args = {
            'topic': 'security',
            'version_focus': '4.0'
        }
        
        prompt = self.generator.generate('firebird_architecture', args)
        
        assert isinstance(prompt, str)
        assert 'Architecture & Administration' in prompt
        assert 'security'.title() in prompt
        assert '4.0' in prompt
        assert 'firebird.conf' in prompt  # Should include config examples
    
    def test_unknown_prompt_error(self):
        """Test error handling for unknown prompt names."""
        with pytest.raises(ValueError) as exc_info:
            self.generator.generate('unknown_prompt', {})
        
        assert 'Unknown prompt' in str(exc_info.value)
    
    def test_prompt_with_empty_args(self):
        """Test prompt generation with empty arguments."""
        prompt = self.generator.generate('firebird_expert', {})
        
        assert isinstance(prompt, str)
        assert len(prompt) > 100
        assert 'Firebird Database Expert' in prompt
    
    def test_prompt_with_firebird_server_context(self):
        """Test prompt generation with FirebirdMCPServer context."""
        # Mock firebird server with table data
        class MockFirebirdServer:
            def get_tables(self):
                return {
                    "success": True,
                    "tables": ["customers", "orders", "products", "users"]
                }
        
        mock_server = MockFirebirdServer()
        generator = PromptGenerator(mock_server)
        
        prompt = generator.generate('firebird_expert', {})
        
        assert 'Available Tables' in prompt
        assert 'customers' in prompt
        assert 'orders' in prompt
    
    def test_get_available_prompts(self):
        """Test retrieval of available prompt names."""
        prompts = self.generator.get_available_prompts()
        
        assert isinstance(prompts, list)
        assert 'firebird_expert' in prompts
        assert 'firebird_performance' in prompts
        assert 'firebird_architecture' in prompts
    
    def test_register_firebird_server(self):
        """Test registration of Firebird server for context."""
        class MockServer:
            pass
        
        mock_server = MockServer()
        self.generator.register_firebird_server(mock_server)
        
        assert self.generator.firebird_server == mock_server


if __name__ == '__main__':
    pytest.main([__file__])
