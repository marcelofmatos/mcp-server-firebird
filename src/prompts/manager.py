"""Compact prompt manager - minimal auto-context application."""

import sys
from ..core.config import DEFAULT_PROMPT_CONFIG, DB_CONFIG
from ..core.i18n import I18n

def log(message: str):
    """Log to stderr - visible in Docker/Claude Desktop"""
    print(f"[MCP-FIREBIRD] {message}", file=sys.stderr, flush=True)

class DefaultPromptManager:
    """Minimal prompt manager with reduced token usage."""
    
    def __init__(self, i18n: I18n = None):
        self.config = DEFAULT_PROMPT_CONFIG.copy()
        # Override to be more conservative
        self.config['auto_apply'] = False  # Only apply when explicitly requested
        self.i18n = i18n or I18n()
        
        status = self.i18n.get('prompts.manager.enabled') if self.config['enabled'] else self.i18n.get('prompts.manager.disabled')
        log(f"🎯 Compact prompt system: {status}")
        
        if self.config['enabled']:
            log(f"📝 {self.i18n.get('prompts.manager.active_prompt')}: {self.config['prompt_name']}")
    
    def get_default_context(self) -> str:
        """Generate minimal context (~50 tokens vs 200+)."""
        if not self.config['enabled']:
            return ""
        
        try:
            template = self.i18n.get('prompts.manager')
            env_info = f"{DB_CONFIG['host']}:{DB_CONFIG['port']}"
            
            return f"""{template['expert_mode_active']}

{template['environment'].format(env=env_info)}
{template['guidelines']}

{template['separator']}

"""
        except Exception as e:
            log(f"⚠️ Context error: {e}")
            return ""
    
    def apply_to_response(self, content: str, tool_name: str = None, disabled: bool = False) -> str:
        """Apply minimal context only when beneficial."""
        # Only apply to critical tools and when not disabled
        if disabled or not self.config['enabled'] or not self.config['auto_apply']:
            return content
        
        # Apply only to main SQL operations, skip diagnostic tools
        if tool_name == 'execute_query':
            context = self.get_default_context()
            if context:
                return f"{context}{content}"
        
        return content
    
    def get_enhanced_tool_description(self, tool_name: str, original_desc: str) -> str:
        """Add minimal enhancement info."""
        if not self.config['enabled'] or tool_name not in ['execute_query', 'test_connection']:
            return original_desc
        
        template = self.i18n.get('prompts.manager')
        return f"{original_desc}\n\n🎯 {template['auto_expert_mode']}"
    
    def update_config(self, **kwargs):
        """Update prompt configuration dynamically."""
        for key, value in kwargs.items():
            if key in self.config:
                old_value = self.config[key]
                self.config[key] = value
                log(f"🔧 {self.i18n.get('prompts.manager.config_updated', key, old_value, value)}")
            else:
                log(f"⚠️ {self.i18n.get('prompts.manager.unknown_config_key', key)}")
    
    def get_status(self) -> dict:
        """Compact status info."""
        return {
            "enabled": self.config['enabled'],
            "mode": "compact",
            "auto_apply": self.config['auto_apply'],
            "prompt_name": self.config['prompt_name'],
            "operation_type": self.config['operation_type'],
            "complexity_level": self.config['complexity_level'],
            "language": self.i18n.language if self.i18n else "en_US",
            "database_context": {
                "host": DB_CONFIG['host'],
                "port": DB_CONFIG['port'],
                "database": DB_CONFIG['database'],
                "user": DB_CONFIG['user'],
                "charset": DB_CONFIG['charset']
            }
        }
