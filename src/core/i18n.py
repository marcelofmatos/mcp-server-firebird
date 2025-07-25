"""Internationalization module for MCP Server Firebird."""

import json
import os
import sys
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

def log(message: str):
    """Log to stderr - visible in Docker/Claude Desktop"""
    print(f"[MCP-FIREBIRD] {message}", file=sys.stderr, flush=True)

class I18n:
    """Internationalization manager with intelligent fallback support."""
    
    def __init__(self, language: str = "en_US"):
        self.language = language
        self.fallback_language = "en_US"
        self.strings = {}
        self.fallback_strings = {}
        self.missing_keys = set()
        self.load_language()
    
    def load_language(self):
        """Load language strings from JSON file with intelligent fallback"""
        script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        success = self._load_language_file(self.language, script_dir)
        
        if self.language != self.fallback_language:
            self._load_fallback_file(script_dir)
        
        if not success and not self.fallback_strings:
            print(f"❌ No language files found, using minimal hardcoded strings", file=sys.stderr)
            self._load_minimal_fallback()
    
    def _load_language_file(self, lang: str, script_dir: str) -> bool:
        """Load a specific language file"""
        try:
            lang_file = os.path.join(script_dir, "i18n", f"{lang}.json")
            
            if os.path.exists(lang_file):
                with open(lang_file, 'r', encoding='utf-8') as f:
                    loaded_strings = json.load(f)
                    
                if lang == self.language:
                    self.strings = loaded_strings
                    print(f"✅ Loaded primary language: {lang}", file=sys.stderr)
                else:
                    self.fallback_strings = loaded_strings
                    print(f"✅ Loaded fallback language: {lang}", file=sys.stderr)
                return True
            else:
                if lang == self.language:
                    print(f"⚠️  Language file not found: {lang_file}", file=sys.stderr)
                return False
                
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in {lang} language file: {e}", file=sys.stderr)
            return False
        except Exception as e:
            print(f"❌ Error loading {lang} language file: {e}", file=sys.stderr)
            return False
    
    def _load_fallback_file(self, script_dir: str):
        """Load fallback language file"""
        if not self._load_language_file(self.fallback_language, script_dir):
            print(f"⚠️  Fallback language {self.fallback_language} not available", file=sys.stderr)
    
    def _load_minimal_fallback(self):
        """Load minimal hardcoded fallback strings"""
        self.fallback_strings = {
            "server_info": {
                "name": "firebird-expert-server",
                "initialized": "MCP Server initialized",
                "starting": "=== FIREBIRD EXPERT MCP SERVER STARTING ===",
                "ready": "=== FIREBIRD EXPERT SERVER READY ===",
                "waiting": "Waiting for requests",
                "interrupted": "Server interrupted",
                "shutting_down": "Server shutting down",
                "error_handling": "Error handling request",
                "invalid_json": "Invalid JSON received",
                "error_processing": "Error processing request",
                "server_error": "Server error occurred"
            },
            "connection": {
                "successful": "Connection successful!",
                "failed": "Connection failed",
                "attempting": "Attempting connection",
                "test_results": "Connection Test Results",
                "target_database": "Target database",
                "dsn_configured": "DSN configured",
                "testing": "Testing database connection",
                "skipping_test": "Skipping connection test",
                "ready_assistance": "Ready to provide expert Firebird assistance"
            },
            "errors": {
                "fdb_not_available": "FDB library not available",
                "client_not_available": "Firebird client libraries not available",
                "method_not_found": "Method not found",
                "notification_received": "Notification received",
                "tables_failed": "Failed to retrieve tables"
            },
            "tools": {
                "sql_required": "SQL query is required",
                "unknown_tool": "Unknown tool",
                "error_executing": "Error executing",
                "query_results": "Query Results",
                "database_tables": "Database Tables",
                "server_status_title": "Server Status",
                "available": "Available tools",
                "test_connection": {
                    "name": "test_connection",
                    "description": "Test connection to external Firebird database with detailed diagnostics"
                },
                "execute_query": {
                    "name": "execute_query",
                    "description": "Execute SQL queries with expert guidance and error handling",
                    "sql_description": "SQL query to execute",
                    "params_description": "Optional parameters for parameterized queries"
                },
                "list_tables": {
                    "name": "list_tables",
                    "description": "List all user tables in the database"
                },
                "server_status": {
                    "name": "server_status",
                    "description": "Get comprehensive server status including library versions and configuration"
                }
            },
            "libraries": {
                "checking": "Checking Firebird components",
                "fdb_loaded": "FDB Python library loaded successfully",
                "fdb_version": "FDB version",
                "fdb_available": "FDB Python library available",
                "fdb_not_available": "FDB Python library not available",
                "fdb_error": "FDB Error",
                "client_found": "Firebird client library found",
                "client_not_found": "Firebird client libraries not found",
                "client_alternative": "Found Firebird client at alternative path",
                "client_available": "Firebird client libraries available",
                "client_not_available": "Firebird client libraries not found",
                "client_location": "Client library location",
                "library_check_failed": "Library path check failed",
                "no_client_found": "No Firebird client libraries found",
                "expected_locations": "Expected locations",
                "limited_functionality": "Limited functionality - missing components",
                "installation_instructions": "Installation instructions available via tools"
            },
            "environment": {
                "target_host": "Target host",
                "target_database": "Target database",
                "user": "User",
                "charset": "Charset",
                "not_set": "not set",
                "info": "Environment information"
            },
            "prompts": {
                "available": "Available prompts",
                "unknown_prompt": "Unknown prompt",
                "error_generating": "Error generating prompt",
                "firebird_expert": {
                    "name": "firebird_expert",
                    "description": "Expert Firebird database assistance with comprehensive guidance",
                    "operation_type": "Type of database operation (select, insert, update, delete, ddl, admin)",
                    "table_context": "Specific table context for targeted advice",
                    "complexity_level": "Complexity level (basic, intermediate, advanced)"
                },
                "firebird_performance": {
                    "name": "firebird_performance",
                    "description": "Performance optimization specialist for Firebird",
                    "query_type": "Type of query to optimize (select, update, complex)",
                    "focus_area": "Performance focus area (indexes, memory, io)"
                },
                "firebird_architecture": {
                    "name": "firebird_architecture",
                    "description": "Architecture and administration specialist",
                    "topic": "Administrative topic (backup, security, monitoring)",
                    "version_focus": "Firebird version focus (2.5, 3.0, 4.0, current)"
                }
            }
        }
    
    def get(self, key_path: str, *args, **kwargs) -> str:
        """Get localized string by dot-separated key path with intelligent fallback"""
        value = self._get_from_dict(self.strings, key_path)
        
        if value is None and self.fallback_strings:
            value = self._get_from_dict(self.fallback_strings, key_path)
        
        if value is None:
            if key_path not in self.missing_keys:
                print(f"⚠️  Missing translation key: {key_path}", file=sys.stderr)
                self.missing_keys.add(key_path)
            return key_path
        
        try:
            if args or kwargs:
                if args:
                    return value.format(*args)
                elif kwargs:
                    return value.format(**kwargs)
            return value
        except (ValueError, KeyError) as e:
            print(f"⚠️  Error formatting string '{key_path}': {e}", file=sys.stderr)
            return value
    
    def _get_from_dict(self, strings_dict: dict, key_path: str):
        """Navigate through nested dictionary using dot notation"""
        try:
            keys = key_path.split('.')
            value = strings_dict
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return None
    
    def get_available_languages(self) -> List[str]:
        """Get list of available language files"""
        try:
            script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            i18n_dir = os.path.join(script_dir, "i18n")
            
            if not os.path.exists(i18n_dir):
                return []
            
            languages = []
            for file in os.listdir(i18n_dir):
                if file.endswith('.json'):
                    lang_code = file[:-5]
                    languages.append(lang_code)
            
            return sorted(languages)
        except Exception as e:
            print(f"⚠️  Error getting available languages: {e}", file=sys.stderr)
            return []
    
    def validate_completeness(self) -> Dict:
        """Validate completeness of current language against fallback"""
        if not self.fallback_strings:
            return {"status": "no_fallback", "missing_keys": []}
        
        missing_keys = []
        self._compare_dicts(self.fallback_strings, self.strings, "", missing_keys)
        
        return {
            "status": "complete" if not missing_keys else "incomplete",
            "missing_keys": missing_keys,
            "completion_percentage": self._calculate_completion_percentage(missing_keys)
        }
    
    def _compare_dicts(self, reference: dict, target: dict, prefix: str, missing: list):
        """Recursively compare dictionaries to find missing keys"""
        for key, value in reference.items():
            current_path = f"{prefix}.{key}" if prefix else key
            
            if key not in target:
                missing.append(current_path)
            elif isinstance(value, dict) and isinstance(target.get(key), dict):
                self._compare_dicts(value, target[key], current_path, missing)
    
    def _calculate_completion_percentage(self, missing_keys: list) -> float:
        """Calculate completion percentage"""
        if not self.fallback_strings:
            return 100.0
        
        total_keys = self._count_keys(self.fallback_strings)
        missing_count = len(missing_keys)
        
        if total_keys == 0:
            return 100.0
        
        return round(((total_keys - missing_count) / total_keys) * 100, 2)
    
    def _count_keys(self, d: dict) -> int:
        """Count total number of leaf keys in nested dictionary"""
        count = 0
        for value in d.values():
            if isinstance(value, dict):
                count += self._count_keys(value)
            else:
                count += 1
        return count
