"""Compact prompt generation - reduced tokens while maintaining functionality."""

from typing import Dict
from ..core.config import DB_CONFIG
from ..core.i18n import I18n

class PromptGenerator:
    """Generate compact prompts with minimal tokens."""
    
    def __init__(self, firebird_server=None, i18n: I18n = None):
        self.firebird_server = firebird_server
        self.i18n = i18n or I18n()
        self.base_prompts = {
            "firebird_expert": self._generate_expert_prompt,
            "firebird_performance": self._generate_performance_prompt,
            "firebird_architecture": self._generate_architecture_prompt
        }
    
    def generate(self, prompt_name: str, arguments: Dict) -> str:
        """Generate prompt with dynamic context."""
        if prompt_name in self.base_prompts:
            return self.base_prompts[prompt_name](arguments)
        else:
            raise ValueError(f"Unknown prompt: {prompt_name}")
    
    def _generate_expert_prompt(self, args: Dict) -> str:
        """Compact expert prompt (~200 tokens vs 2000+)."""
        operation = args.get("operation_type", "query")
        level = args.get("complexity_level", "intermediate")
        table_ctx = args.get("table_context", "")
        
        # Get minimal table info
        tables_info = ""
        if self.firebird_server and not table_ctx:
            try:
                result = self.firebird_server.get_tables()
                if result.get("success") and result.get("tables"):
                    tables = result["tables"][:10]
                    tables_info = f" | {self.i18n.get('prompt_templates.firebird_expert.available_tables').format(tables=', '.join(tables[:5]))}"
                    if len(tables) > 5:
                        tables_info += "..."
            except:
                pass
        
        template = self.i18n.get('prompt_templates.firebird_expert')
        
        return f"""{template['title']}

{template['intro']}

{template['environment_config'].format(
    host=DB_CONFIG['host'], 
    port=DB_CONFIG['port'],
    database=DB_CONFIG['database'],
    user=DB_CONFIG['user']
)}{tables_info}

**Operation**: {operation} ({level})
**Guidance**: {self.i18n.get(f'operation_guidance.{operation}', 'Optimize and validate')}

{template['firebird_expertise']}
{template['advanced_features']}

{template['response_approach']}
"""
    
    def _generate_performance_prompt(self, args: Dict) -> str:
        """Compact performance prompt (~150 tokens)."""
        query_type = args.get("query_type", "general")
        focus = args.get("focus_area", "indexes")
        
        template = self.i18n.get('prompt_templates.firebird_performance')
        
        return f"""{template['title']}

{template['intro']}

{template['focus_queries'].format(query_type=query_type)}
{template['methodology']}

**Focus**: {focus}
**Metrics**: {template['key_metrics']}

Env: {DB_CONFIG['host']}:{DB_CONFIG['port']} - {DB_CONFIG['database']}
"""
    
    def _generate_architecture_prompt(self, args: Dict) -> str:
        """Compact architecture prompt (~150 tokens)."""
        topic = args.get("topic", "general")
        version = args.get("version_focus", "current")
        
        template = self.i18n.get('prompt_templates.firebird_architecture')
        
        return f"""{template['title']}

{template['intro']}

{template['focus_topic'].format(topic=topic)} | Version: {version}

**Architectures**: {template['architectures']}
**Practices**: {template['practices']}

Env: {DB_CONFIG['host']}:{DB_CONFIG['port']} - {DB_CONFIG['database']}
"""
    
    def register_firebird_server(self, server):
        """Register FirebirdMCPServer instance for dynamic context."""
        self.firebird_server = server
    
    def get_available_prompts(self) -> list:
        """Get list of available prompt templates."""
        return list(self.base_prompts.keys())
