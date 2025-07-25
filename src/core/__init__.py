"""Core module for MCP Server Firebird."""

from .i18n import I18n
from .config import DB_CONFIG, DEFAULT_PROMPT_CONFIG, initialize_libraries

__all__ = ['I18n', 'DB_CONFIG', 'DEFAULT_PROMPT_CONFIG', 'initialize_libraries']
