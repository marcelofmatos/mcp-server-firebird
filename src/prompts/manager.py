"""Compact prompt manager - minimal auto-context application."""

import sys
from ..core.config import DEFAULT_PROMPT_CONFIG, DB_CONFIG
from ..core.i18n import I18n

def log(message: str):
    """Log to stderr - visible in Docker/Claude Desktop"""
    print(f"[MCP-FIREBIRD] {message}", file=sys.stderr, flush=True)

class DefaultPromptManager:
    """Minimal prompt manager with reduced token usage."""
    
    def __init__(self, i18n: I18n = None, firebird_server=None):
        self.config = DEFAULT_PROMPT_CONFIG.copy()
        self.firebird_server = firebird_server
        # Mantém comportamento original mas com tokens otimizados
        self.i18n = i18n or I18n()
        
        status = self.i18n.get('prompts.manager.enabled') if self.config['enabled'] else self.i18n.get('prompts.manager.disabled')
        log(f"🎯 Compact prompt system: {status}")
        log(f"🔄 Auto-apply: {self.config['auto_apply']}")
        
        if self.config['enabled']:
            log(f"📝 {self.i18n.get('prompts.manager.active_prompt')}: {self.config['prompt_name']}")
            log(f"🎯 Expert context will be applied to: execute_query, test_connection, list_tables")
    
    def _get_firebird_version(self) -> str:
        """Obter versão Firebird do servidor conectado."""
        if self.firebird_server:
            try:
                result = self.firebird_server.test_connection()
                if result.get("connected") and result.get("version"):
                    return result["version"]
            except:
                pass
        return "5.0+"  # fallback
    
    def get_default_context(self) -> str:
        """Generate minimal context (~50 tokens vs 200+)."""
        if not self.config['enabled']:
            log("🚫 Context disabled in config")
            return ""
        
        try:
            template = self.i18n.get('prompts.manager')
            env_info = f"{DB_CONFIG['host']}:{DB_CONFIG['port']}"
            version = self._get_firebird_version()
            
            context = f"""{template['expert_title'].format(version=version)}

{template['environment'].format(env=env_info)}
{template['guidelines']}

{template['separator']}

"""
            log(f"🎯 Generated compact context ({len(context)} chars) with version {version}")
            return context
        except Exception as e:
            log(f"⚠️ Context error: {e}")
            return ""
    
    def apply_to_response(self, content: str, tool_name: str = None, disabled: bool = False) -> str:
        """Apply minimal context to main database tools (como original)."""
        log(f"🔍 apply_to_response called: tool={tool_name}, disabled={disabled}, enabled={self.config['enabled']}, auto_apply={self.config['auto_apply']}")
        
        if disabled:
            log("🚫 Context application disabled by parameter")
            return content
            
        if not self.config['enabled']:
            log("🚫 Context application disabled in config")
            return content
            
        if not self.config['auto_apply']:
            log("🚫 Auto-apply disabled in config")
            return content
        
        # Aplica nas mesmas tools que antes, mas com context compacto
        target_tools = ['execute_query', 'test_connection', 'list_tables']
        if tool_name in target_tools:
            context = self.get_default_context()
            if context:
                log(f"🎯 Applying compact expert context to {tool_name}")
                return f"{context}{content}"
            else:
                log(f"⚠️ No context generated for {tool_name}")
        else:
            log(f"🙇 Tool {tool_name} not in target list: {target_tools}")
        
        return content
    
    def get_enhanced_tool_description(self, tool_name: str, original_desc: str) -> str:
        """Add minimal enhancement info to main tools."""
        if not self.config['enabled']:
            return original_desc
        
        # Aplica enhancement nas mesmas tools que antes
        target_tools = ['execute_query', 'test_connection', 'list_tables']
        if tool_name in target_tools:
            template = self.i18n.get('prompts.manager')
            return f"{original_desc}\n\n🎯 {template['auto_expert_mode']}"
        
        return original_desc
    
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
