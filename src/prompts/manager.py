"""Default prompt management for automatic expert context application."""

import sys
from ..core.config import DEFAULT_PROMPT_CONFIG, DB_CONFIG
from ..core.i18n import I18n

def log(message: str):
    """Log to stderr - visible in Docker/Claude Desktop"""
    print(f"[MCP-FIREBIRD] {message}", file=sys.stderr, flush=True)

class DefaultPromptManager:
    """Manages automatic application of default prompts for enhanced user experience."""
    
    def __init__(self, i18n: I18n = None):
        self.config = DEFAULT_PROMPT_CONFIG
        self.i18n = i18n or I18n()
        
        status = self.i18n.get('prompts.manager.enabled') if self.config['enabled'] else self.i18n.get('prompts.manager.disabled')
        log(f"🎯 {self.i18n.get('prompts.manager.system_status')}: {status}")
        
        if self.config['enabled']:
            log(f"📝 {self.i18n.get('prompts.manager.active_prompt')}: {self.config['prompt_name']}")
    
    def get_default_context(self) -> str:
        """Generate default prompt context with current environment information."""
        if not self.config['enabled']:
            return ""
        
        try:
            # Build environment info
            env_info = f"{DB_CONFIG['host']}:{DB_CONFIG['port']} | {self.i18n.get('environment.target_database')}: {DB_CONFIG['database']} | {self.i18n.get('environment.user')}: {DB_CONFIG['user']}"
            
            # Get complexity level text
            complexity = self.i18n.get(f'complexity_levels.{self.config["complexity_level"]}', self.config['complexity_level'])
            
            prompt_text = f"""🔥 **{self.i18n.get('prompts.manager.expert_mode_active')}**

**{self.i18n.get('prompts.manager.environment')}:** {env_info}

**{self.i18n.get('prompts.manager.expert_guidelines', complexity)}:**
✅ {self.i18n.get('prompts.manager.guideline_solutions')}
✅ {self.i18n.get('prompts.manager.guideline_performance')}  
✅ {self.i18n.get('prompts.manager.guideline_compatibility')}
✅ {self.i18n.get('prompts.manager.guideline_examples')}
✅ {self.i18n.get('prompts.manager.guideline_pitfalls')}

**{self.i18n.get('prompts.manager.areas_expertise')}:** {self.i18n.get('prompts.manager.expertise_areas')}
**{self.i18n.get('prompts.manager.advanced_features')}:** {self.i18n.get('prompts.manager.advanced_list')}

{self.i18n.get('prompts.manager.separator')}

"""
            return prompt_text
            
        except Exception as e:
            log(f"⚠️ {self.i18n.get('prompts.manager.error_generating')}: {e}")
            return ""
    
    def apply_to_response(self, content: str, tool_name: str = None, disabled: bool = False) -> str:
        """
        Apply default context to tool responses when appropriate.
        
        Args:
            content: Original tool response content
            tool_name: Name of the tool being executed
            disabled: Whether expert mode is explicitly disabled
            
        Returns:
            Enhanced content with expert context (if applicable)
        """
        if disabled or not self.config['auto_apply'] or not self.config['enabled']:
            return content
        
        # Apply expert context only to main database tools
        target_tools = ['execute_query', 'test_connection', 'list_tables']
        if tool_name in target_tools:
            context = self.get_default_context()
            if context:
                return f"{context}{content}"
        
        return content
    
    def get_enhanced_tool_description(self, tool_name: str, original_desc: str) -> str:
        """
        Add information about default prompt system to tool descriptions.
        
        Args:
            tool_name: Name of the tool
            original_desc: Original tool description
            
        Returns:
            Enhanced description mentioning auto-expert mode if enabled
        """
        if not self.config['enabled']:
            return original_desc
        
        enhanced = f"{original_desc}\n\n🎯 **{self.i18n.get('prompts.manager.auto_expert_mode')}**"
        return enhanced
    
    def update_config(self, **kwargs):
        """
        Update prompt configuration dynamically.
        
        Args:
            **kwargs: Configuration parameters to update
        """
        for key, value in kwargs.items():
            if key in self.config:
                old_value = self.config[key]
                self.config[key] = value
                log(f"🔧 {self.i18n.get('prompts.manager.config_updated', key, old_value, value)}")
            else:
                log(f"⚠️ {self.i18n.get('prompts.manager.unknown_config_key', key)}")
    
    def get_status(self) -> dict:
        """Get current prompt manager status and configuration."""
        return {
            "enabled": self.config['enabled'],
            "prompt_name": self.config['prompt_name'],
            "operation_type": self.config['operation_type'],
            "complexity_level": self.config['complexity_level'],
            "auto_apply": self.config['auto_apply'],
            "language": self.i18n.language,
            "database_context": {
                "host": DB_CONFIG['host'],
                "port": DB_CONFIG['port'],
                "database": DB_CONFIG['database'],
                "user": DB_CONFIG['user'],
                "charset": DB_CONFIG['charset']
            }
        }
