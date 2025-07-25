"""MCP Server Firebird - Modular implementation."""

from .core import I18n, DB_CONFIG, DEFAULT_PROMPT_CONFIG, initialize_libraries
from .firebird import FirebirdMCPServer, SQLPatternAnalyzer  
from .prompts import DefaultPromptManager, PromptGenerator
from .mcp import MCPServer

__all__ = [
    'I18n', 'DB_CONFIG', 'DEFAULT_PROMPT_CONFIG', 'initialize_libraries',
    'FirebirdMCPServer', 'SQLPatternAnalyzer',
    'DefaultPromptManager', 'PromptGenerator', 
    'MCPServer'
]

__version__ = "1.0.0"
