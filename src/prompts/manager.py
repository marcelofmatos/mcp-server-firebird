"""Default prompt management for automatic expert context application."""

import sys
from ..core.config import DEFAULT_PROMPT_CONFIG, DB_CONFIG

def log(message: str):
    """Log to stderr - visible in Docker/Claude Desktop"""
    print(f"[MCP-FIREBIRD] {message}", file=sys.stderr, flush=True)

class DefaultPromptManager:
    """Manages automatic application of default prompts for enhanced user experience."""
    
    def __init__(self):
        self.config = DEFAULT_PROMPT_CONFIG
        log(f"🎯 Default prompt system: {'enabled' if self.config['enabled'] else 'disabled'}")
        if self.config['enabled']:
            log(f"📝 Default prompt: {self.config['prompt_name']}")
    
    def get_default_context(self) -> str:
        """Generate default prompt context with current environment information."""
        if not self.config['enabled']:
            return ""
        
        try:
            prompt_text = f"""🔥 **FIREBIRD EXPERT MODE ACTIVE**

**Environment:** {DB_CONFIG['host']}:{DB_CONFIG['port']} | DB: {DB_CONFIG['database']} | User: {DB_CONFIG['user']}

**Expert Guidelines ({self.config['complexity_level']} level):**
✅ Provide Firebird-specific solutions
✅ Consider performance implications  
✅ Mention version compatibility
✅ Include practical examples
✅ Highlight potential pitfalls

**Areas of Expertise:** SQL Syntax • Performance • Transactions • Stored Procedures • Administration • Architecture
**Advanced Features:** Window Functions • CTE • MERGE • GTT • Partial Indexes • Expression Indexes

---

"""
            return prompt_text
            
        except Exception as e:
            log(f"⚠️ Error generating default context: {e}")
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
        if tool_name in ['execute_query', 'test_connection', 'list_tables']:
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
        
        enhanced = f"{original_desc}\n\n🎯 **Auto-Expert Mode**: Automatically applies Firebird expert context for optimal guidance."
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
                log(f"🔧 Updated {key}: {old_value} → {value}")
            else:
                log(f"⚠️ Unknown configuration key: {key}")
    
    def get_status(self) -> dict:
        """Get current prompt manager status and configuration."""
        return {
            "enabled": self.config['enabled'],
            "prompt_name": self.config['prompt_name'],
            "operation_type": self.config['operation_type'],
            "complexity_level": self.config['complexity_level'],
            "auto_apply": self.config['auto_apply'],
            "database_context": {
                "host": DB_CONFIG['host'],
                "port": DB_CONFIG['port'],
                "database": DB_CONFIG['database'],
                "user": DB_CONFIG['user'],
                "charset": DB_CONFIG['charset']
            }
        }
