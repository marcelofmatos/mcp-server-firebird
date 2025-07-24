#!/usr/bin/env python3
"""
MCP Server Firebird Expert - External Connection
Robust server for connecting to external Firebird databases
Provides specialized assistance and detailed diagnostics

# ==========================================
# CONTRIBUTION ENCOURAGEMENT
# ==========================================

Want to help improve this project? 
If you find a bug, have a suggestion, or want to contribute new features, please open an issue at:
https://github.com/marcelofmatos/mcp-server-firebird/issues

Your feedback and contributions are very welcome!
"""

import json
import sys
import os
import logging
import ctypes.util
from typing import Dict, List, Any, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.WARNING, stream=sys.stderr)
logger = logging.getLogger(__name__)

def log(message: str):
    """Log to stderr - visible in Docker/Claude Desktop"""
    print(f"[MCP-FIREBIRD] {message}", file=sys.stderr, flush=True)

# ==========================================
# INTERNATIONALIZATION (I18N)
# ==========================================

class I18n:
    def __init__(self, language: str = "en_US"):
        self.language = language
        self.strings = {}
        self.load_language()
    
    def load_language(self):
        """Load language strings from JSON file"""
        try:
            # Get script directory
            script_dir = os.path.dirname(os.path.abspath(__file__))
            lang_file = os.path.join(script_dir, "i18n", f"{self.language}.json")
            
            if os.path.exists(lang_file):
                with open(lang_file, 'r', encoding='utf-8') as f:
                    self.strings = json.load(f)
                log(f"✅ Loaded language: {self.language}")
            else:
                # Fallback to English
                fallback_file = os.path.join(script_dir, "i18n", "en_US.json")
                if os.path.exists(fallback_file):
                    with open(fallback_file, 'r', encoding='utf-8') as f:
                        self.strings = json.load(f)
                    log(f"⚠️  Language {self.language} not found, using en_US fallback")
                else:
                    log(f"❌ No language files found, using hardcoded English")
                    self._load_fallback_strings()
        except Exception as e:
            log(f"❌ Error loading language {self.language}: {e}")
            self._load_fallback_strings()
    
    def _load_fallback_strings(self):
        """Load minimal fallback strings in case of file loading error"""
        self.strings = {
            "server_info": {
                "initialized": "MCP Server initialized",
                "starting": "=== FIREBIRD EXPERT MCP SERVER STARTING ===",
                "ready": "=== FIREBIRD EXPERT SERVER READY ==="
            },
            "connection": {
                "successful": "Connection successful!",
                "failed": "Connection failed"
            },
            "errors": {
                "fdb_not_available": "FDB library not available",
                "method_not_found": "Method not found"
            }
        }
    
    def get(self, key_path: str, **kwargs) -> str:
        """Get localized string by dot-separated key path"""
        try:
            keys = key_path.split('.')
            value = self.strings
            for key in keys:
                value = value[key]
            
            # Format string with provided arguments
            if kwargs:
                return value.format(**kwargs)
            return value
        except (KeyError, TypeError):
            log(f"⚠️  Missing translation key: {key_path}")
            return key_path  # Return key as fallback

# Initialize i18n with language from environment variable
LANGUAGE = os.getenv('FIREBIRD_LANGUAGE', os.getenv('LANG', 'en_US')).split('.')[0]
i18n = I18n(LANGUAGE)

# ==========================================
# FIREBIRD LIBRARY DETECTION
# ==========================================

# Global state variables
FDB_AVAILABLE = False
FDB_ERROR = None
FIREBIRD_CLIENT_AVAILABLE = False
CLIENT_LIBRARY_PATH = None

# Import FDB with robust detection
try:
    import fdb
    FDB_AVAILABLE = True
    log(f"✅ {i18n.get('libraries.fdb_loaded')}")
    log(f"📦 {i18n.get('libraries.fdb_version')}: {fdb.__version__}")
    
    # Check if can locate client libraries
    try:
        fbclient_path = ctypes.util.find_library('fbclient')
        if fbclient_path:
            FIREBIRD_CLIENT_AVAILABLE = True
            CLIENT_LIBRARY_PATH = fbclient_path
            log(f"✅ {i18n.get('libraries.client_found')}: {fbclient_path}")
        else:
            log(f"⚠️  {i18n.get('libraries.client_not_found')}")
            log(f"🔍 LD_LIBRARY_PATH: {os.getenv('LD_LIBRARY_PATH', i18n.get('environment.not_set'))}")
            
            # Search in alternative paths
            possible_paths = [
                "/opt/firebird/lib/libfbclient.so",
                "/opt/firebird/lib/libfbclient.so.2",
                "/usr/lib/libfbclient.so.2",
                "/usr/lib/libfbclient.so",
                "/usr/lib/x86_64-linux-gnu/libfbclient.so.2",
                "/usr/lib/x86_64-linux-gnu/libfbclient.so"
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    FIREBIRD_CLIENT_AVAILABLE = True
                    CLIENT_LIBRARY_PATH = path
                    log(f"✅ {i18n.get('libraries.client_alternative')}: {path}")
                    break
            
            if not FIREBIRD_CLIENT_AVAILABLE:
                log(f"❌ {i18n.get('libraries.no_client_found')}")
                
    except Exception as e:
        log(f"⚠️  {i18n.get('libraries.library_check_failed')}: {e}")
        
except ImportError as e:
    FDB_AVAILABLE = False
    FDB_ERROR = str(e)
    log(f"❌ Could not import FDB: {e}")
    log(f"💡 FDB Python library not available")

# ==========================================
# DATABASE CONFIGURATION
# ==========================================

DB_CONFIG = {
    'host': os.getenv('FIREBIRD_HOST', 'localhost'),
    'port': int(os.getenv('FIREBIRD_PORT', 3050)),
    'database': os.getenv('FIREBIRD_DATABASE', '/path/to/database.fdb'),
    'user': os.getenv('FIREBIRD_USER', 'SYSDBA'),
    'password': os.getenv('FIREBIRD_PASSWORD', 'masterkey'),
    'charset': os.getenv('FIREBIRD_CHARSET', 'UTF8')
}

log(f"📍 {i18n.get('connection.target_database')}: {DB_CONFIG['host']}:{DB_CONFIG['port']}")

# ==========================================
# FIREBIRD MCP SERVER CLASS
# ==========================================

class FirebirdMCPServer:
    def __init__(self):
        self.dsn = f"{DB_CONFIG['host']}/{DB_CONFIG['port']}:{DB_CONFIG['database']}"
        log(f"🔗 {i18n.get('connection.dsn_configured')}: {self.dsn}")
        
    def test_connection(self):
        """Test connection to external Firebird with detailed diagnostics"""
        if not FDB_AVAILABLE:
            return {
                "connected": False,
                "error": f"{i18n.get('errors.fdb_not_available')}: {FDB_ERROR}",
                "solution": "FDB Python library not installed - should be available in container",
                "type": "fdb_library_error"
            }
            
        if not FIREBIRD_CLIENT_AVAILABLE:
            return {
                "connected": False,
                "error": i18n.get('errors.client_not_available'),
                "solution": (
                    "Firebird client libraries missing. This container should have them installed.\n"
                    "• Check if container build completed successfully\n"
                    "• Verify /opt/firebird/lib/ contains libfbclient.so\n"
                    "• Check LD_LIBRARY_PATH configuration"
                ),
                "type": "client_library_error",
                "library_path": CLIENT_LIBRARY_PATH,
                "ld_library_path": os.getenv('LD_LIBRARY_PATH')
            }
            
        try:
            log(f"🔌 {i18n.get('connection.attempting')}: {self.dsn}")
            conn = fdb.connect(
                dsn=self.dsn,
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                charset=DB_CONFIG['charset']
            )
            cursor = conn.cursor()
            cursor.execute("SELECT RDB$GET_CONTEXT('SYSTEM', 'ENGINE_VERSION') FROM RDB$DATABASE")
            version = cursor.fetchone()[0]
            conn.close()
            log(f"✅ {i18n.get('connection.successful')}")
            
            return {
                "connected": True,
                "version": version.strip(),
                "dsn": self.dsn,
                "user": DB_CONFIG['user'],
                "charset": DB_CONFIG['charset']
            }
            
        except Exception as e:
            log(f"❌ {i18n.get('connection.failed')}: {e}")
            error_msg = str(e)
            error_type = "unknown_error"
            
            # Specific diagnosis based on error type
            if "could not be determined" in error_msg.lower():
                error_type = "client_library_error"
                error_msg += "\n\n💡 FIREBIRD CLIENT ISSUE: Client libraries not properly configured"
                error_msg += "\n• The container should have Firebird client libraries installed"
                error_msg += "\n• Check if /opt/firebird/lib/libfbclient.so exists"
                error_msg += "\n• Verify LD_LIBRARY_PATH includes Firebird lib directory"
                
            elif "libtommath" in error_msg.lower() or "libtomcrypt" in error_msg.lower():
                error_type = "dependency_error"
                error_msg += "\n\n💡 DEPENDENCY ISSUE: Missing required Firebird dependencies"
                error_msg += "\n• libtommath.so.0 or libtomcrypt.so.0 not found"
                error_msg += "\n• This indicates the Firebird installation is incomplete"
                error_msg += "\n• The container build may have failed during dependency installation"
                
            elif "network error" in error_msg.lower() or "connection refused" in error_msg.lower():
                error_type = "network_error"
                error_msg += f"\n\n💡 NETWORK ISSUE: Cannot reach {DB_CONFIG['host']}:{DB_CONFIG['port']}"
                error_msg += "\n• Check if Firebird server is running and accessible"
                error_msg += "\n• Verify firewall rules allow connections"
                error_msg += "\n• Confirm host and port are correct"
                
            elif "login" in error_msg.lower() or "password" in error_msg.lower() or "authentication" in error_msg.lower():
                error_type = "authentication_error"
                error_msg += "\n\n💡 AUTHENTICATION ISSUE: Invalid credentials"
                error_msg += f"\n• Check username: {DB_CONFIG['user']}"
                error_msg += "\n• Verify password in FIREBIRD_PASSWORD environment variable"
                error_msg += "\n• Ensure user exists in Firebird security database"
                
            elif "database" in error_msg.lower() and "not found" in error_msg.lower():
                error_type = "database_error"
                error_msg += f"\n\n💡 DATABASE ISSUE: Database file not found"
                error_msg += f"\n• Check database path: {DB_CONFIG['database']}"
                error_msg += "\n• Verify database file exists on Firebird server"
                error_msg += "\n• Check file permissions on server"
            
            return {
                "connected": False,
                "error": error_msg,
                "type": error_type,
                "dsn": self.dsn,
                "config": DB_CONFIG
            }
    
    def execute_query(self, sql: str, params: Optional[List] = None):
        """Execute SQL query with robust error handling"""
        if not FDB_AVAILABLE:
            return {
                "success": False,
                "error": f"{i18n.get('errors.fdb_not_available')}: {FDB_ERROR}",
                "solution": "FDB Python library not installed in container",
                "type": "fdb_library_error"
            }
            
        if not FIREBIRD_CLIENT_AVAILABLE:
            return {
                "success": False,
                "error": i18n.get('errors.client_not_available'),
                "solution": "Firebird client libraries missing from container",
                "type": "client_library_error"
            }
            
        try:
            conn = fdb.connect(
                dsn=self.dsn,
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                charset=DB_CONFIG['charset']
            )
            cursor = conn.cursor()
            
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            
            if sql.strip().upper().startswith('SELECT'):
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                rows = cursor.fetchall()
                data = [dict(zip(columns, row)) for row in rows]
                result = {
                    "success": True,
                    "data": data,
                    "row_count": len(data),
                    "columns": columns,
                    "sql": sql
                }
            else:
                affected = cursor.rowcount
                conn.commit()
                result = {
                    "success": True,
                    "affected_rows": affected,
                    "sql": sql
                }
                
            conn.close()
            return result
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "sql": sql,
                "params": params
            }
    
    def get_tables(self):
        """List database tables"""
        if not FDB_AVAILABLE:
            return {
                "success": False,
                "error": i18n.get('errors.fdb_not_available'),
                "solution": "FDB Python library not installed",
                "type": "fdb_library_error"
            }
            
        if not FIREBIRD_CLIENT_AVAILABLE:
            return {
                "success": False,
                "error": i18n.get('errors.client_not_available'),
                "solution": "Firebird client libraries missing from container",
                "type": "client_library_error"
            }
            
        try:
            conn = fdb.connect(
                dsn=self.dsn,
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                charset=DB_CONFIG['charset']
            )
            cursor = conn.cursor()
            cursor.execute("""
                SELECT TRIM(RDB$RELATION_NAME) as TABLE_NAME
                FROM RDB$RELATIONS 
                WHERE RDB$VIEW_BLR IS NULL 
                AND (RDB$SYSTEM_FLAG IS NULL OR RDB$SYSTEM_FLAG = 0)
                ORDER BY RDB$RELATION_NAME
            """)
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            return {
                "success": True,
                "tables": tables,
                "count": len(tables),
                "database": DB_CONFIG['database']
            }
            
        except Exception as e:
            log(f"❌ {i18n.get('errors.tables_failed')}: {e}")
            return {
                "success": False,
                "error": str(e),
                "database": DB_CONFIG['database']
            }

# Firebird server instance
firebird_server = FirebirdMCPServer()

# ==========================================
# MCP SERVER
# ==========================================

class MCPServer:
    def __init__(self):
        log(f"🚀 {i18n.get('server_info.initialized')}")
    
    def send_response(self, request_id: Any, result: Any):
        """Send JSON-RPC response"""
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }
        print(json.dumps(response), flush=True)
    
    def send_error(self, request_id: Any, code: int, message: str):
        """Send JSON-RPC error"""
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": code, "message": message}
        }
        print(json.dumps(response), flush=True)
    
    def handle_initialize(self, request_id: Any, params: Dict):
        """Handle initialize request"""
        result = {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {"listChanged": False},
                "resources": {"subscribe": False, "listChanged": False},
                "prompts": {"listChanged": False}
            },
            "serverInfo": {
                "name": os.getenv("MCP_SERVER_NAME", i18n.get('server_info.name')),
                "version": os.getenv("MCP_SERVER_VERSION", "1.0.0")
            }
        }
        self.send_response(request_id, result)
    
    def handle_tools_list(self, request_id: Any, params: Dict):
        """List available tools"""
        tools = [
            {
                "name": i18n.get('tools.test_connection.name'),
                "description": i18n.get('tools.test_connection.description'),
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": i18n.get('tools.execute_query.name'),
                "description": i18n.get('tools.execute_query.description'),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "sql": {
                            "type": "string", 
                            "description": i18n.get('tools.execute_query.sql_description')
                        },
                        "params": {
                            "type": "array", 
                            "description": i18n.get('tools.execute_query.params_description')
                        }
                    },
                    "required": ["sql"]
                }
            },
            {
                "name": i18n.get('tools.list_tables.name'),
                "description": i18n.get('tools.list_tables.description'),
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": i18n.get('tools.server_status.name'),
                "description": i18n.get('tools.server_status.description'),
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]
        
        self.send_response(request_id, {"tools": tools})
    
    def handle_resources_list(self, request_id: Any, params: Dict):
        """List available resources"""
        resources = []
        self.send_response(request_id, {"resources": resources})
    
    def handle_prompts_list(self, request_id: Any, params: Dict):
        """List available prompts"""
        prompts = [
            {
                "name": i18n.get('prompts.firebird_expert.name'),
                "description": i18n.get('prompts.firebird_expert.description'),
                "arguments": [
                    {
                        "name": "operation_type",
                        "description": i18n.get('prompts.firebird_expert.operation_type'),
                        "required": False
                    },
                    {
                        "name": "table_context",
                        "description": i18n.get('prompts.firebird_expert.table_context'),
                        "required": False
                    },
                    {
                        "name": "complexity_level",
                        "description": i18n.get('prompts.firebird_expert.complexity_level'),
                        "required": False
                    }
                ]
            },
            {
                "name": i18n.get('prompts.firebird_performance.name'),
                "description": i18n.get('prompts.firebird_performance.description'),
                "arguments": [
                    {
                        "name": "query_type",
                        "description": i18n.get('prompts.firebird_performance.query_type'),
                        "required": False
                    },
                    {
                        "name": "focus_area",
                        "description": i18n.get('prompts.firebird_performance.focus_area'),
                        "required": False
                    }
                ]
            },
            {
                "name": i18n.get('prompts.firebird_architecture.name'),
                "description": i18n.get('prompts.firebird_architecture.description'),
                "arguments": [
                    {
                        "name": "topic",
                        "description": i18n.get('prompts.firebird_architecture.topic'),
                        "required": False
                    },
                    {
                        "name": "version_focus",
                        "description": i18n.get('prompts.firebird_architecture.version_focus'),
                        "required": False
                    }
                ]
            }
        ]
        self.send_response(request_id, {"prompts": prompts})
    
    def handle_prompts_get(self, request_id: Any, params: Dict):
        """Get specific prompt with dynamic context"""
        try:
            prompt_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if prompt_name == "firebird_expert":
                operation_type = arguments.get("operation_type", "query")
                table_context = arguments.get("table_context", "")
                complexity_level = arguments.get("complexity_level", "intermediate")
                
                # Get table list dynamically for context
                tables_info = ""
                try:
                    tables_result = firebird_server.get_tables()
                    if tables_result.get("success") and tables_result.get("tables"):
                        table_list = tables_result["tables"][:20]
                        tables_info = f"\n\n{i18n.get('prompt_templates.firebird_expert.available_tables')}: {', '.join(table_list)}"
                except:
                    pass
                
                complexity_guidance = i18n.get(f'complexity_levels.{complexity_level}', 'Default level')
                operation_guidance = i18n.get(f'operation_guidance.{operation_type}', 'General best practices guidance')
                
                context_text = f"For table {table_context}: " if table_context else ""
                
                prompt_text = f"""{i18n.get('prompt_templates.firebird_expert.title')}

{i18n.get('prompt_templates.firebird_expert.intro')}
{context_text}

{i18n.get('prompt_templates.firebird_expert.environment_config')}
- **Firebird {firebird_server.test_connection().get('version', 'N/A') if FDB_AVAILABLE and FIREBIRD_CLIENT_AVAILABLE else 'External'}**
- **Host**: {DB_CONFIG['host']}:{DB_CONFIG['port']}
- **Database**: {DB_CONFIG['database']}
- **User**: {DB_CONFIG['user']}
- **Charset**: {DB_CONFIG['charset']}

{i18n.get('prompt_templates.firebird_expert.guidelines').format(operation_type=operation_type.upper())}
**{i18n.get('prompt_templates.firebird_expert.complexity_level').format(complexity_level=complexity_level)}**: {complexity_guidance}
**{i18n.get('prompt_templates.firebird_expert.specific_guidance')}**: {operation_guidance}

{i18n.get('prompt_templates.firebird_expert.firebird_expertise')}
1. {i18n.get('prompt_templates.firebird_expert.sql_syntax')}
2. {i18n.get('prompt_templates.firebird_expert.performance')}
3. {i18n.get('prompt_templates.firebird_expert.transactions')}
4. {i18n.get('prompt_templates.firebird_expert.stored_procedures')}
5. {i18n.get('prompt_templates.firebird_expert.administration')}
6. {i18n.get('prompt_templates.firebird_expert.architecture')}

{i18n.get('prompt_templates.firebird_expert.advanced_features')}
- {i18n.get('prompt_templates.firebird_expert.window_functions')}
- {i18n.get('prompt_templates.firebird_expert.cte')}
- {i18n.get('prompt_templates.firebird_expert.merge')}
- {i18n.get('prompt_templates.firebird_expert.temp_tables')}
- {i18n.get('prompt_templates.firebird_expert.partial_indexes')}
- {i18n.get('prompt_templates.firebird_expert.expression_indexes')}
- {i18n.get('prompt_templates.firebird_expert.computed_columns')}
- {i18n.get('prompt_templates.firebird_expert.generators')}{tables_info}

{i18n.get('prompt_templates.firebird_expert.response_approach')}
{i18n.get('prompt_templates.firebird_expert.explain_context')}
{i18n.get('prompt_templates.firebird_expert.mention_alternatives')}
{i18n.get('prompt_templates.firebird_expert.performance_impact')}
{i18n.get('prompt_templates.firebird_expert.version_compatibility')}
{i18n.get('prompt_templates.firebird_expert.practical_examples')}
{i18n.get('prompt_templates.firebird_expert.highlight_pitfalls')}
"""
                
            elif prompt_name == "firebird_performance":
                query_type = arguments.get("query_type", "general")
                focus_area = arguments.get("focus_area", "general")
                
                query_optimization = i18n.get(f'query_optimizations.{query_type}', 'General performance optimizations')
                focus_technique = i18n.get(f'focus_techniques.{focus_area}', 'General optimization techniques')
                
                prompt_text = f"""{i18n.get('prompt_templates.firebird_performance.title')}

{i18n.get('prompt_templates.firebird_performance.intro')}

{i18n.get('prompt_templates.firebird_performance.focus_queries').format(query_type=query_type.title())}
{query_optimization}

{i18n.get('prompt_templates.firebird_performance.specialization').format(focus_area=focus_area.title())}
{focus_technique}

{i18n.get('prompt_templates.firebird_performance.analysis_tools')}
```sql
{i18n.get('prompt_templates.firebird_performance.plan_comment')}
SET PLAN ON;
SET STATS ON;

{i18n.get('prompt_templates.firebird_performance.monitor_comment')}
SELECT * FROM MON$STATEMENTS WHERE MON$STATE = 1;
SELECT * FROM MON$IO_STATS;
SELECT * FROM MON$RECORD_STATS;

{i18n.get('prompt_templates.firebird_performance.statistics_comment')}
SELECT * FROM RDB$RELATION_STATISTICS;
SELECT * FROM RDB$INDEX_STATISTICS;
```

{i18n.get('prompt_templates.firebird_performance.methodology')}
1. {i18n.get('prompt_templates.firebird_performance.analysis')}
2. {i18n.get('prompt_templates.firebird_performance.indexes')}
3. {i18n.get('prompt_templates.firebird_performance.rewrite')}
4. {i18n.get('prompt_templates.firebird_performance.test')}
5. {i18n.get('prompt_templates.firebird_performance.monitor')}

{i18n.get('prompt_templates.firebird_performance.important_metrics')}
- {i18n.get('prompt_templates.firebird_performance.selectivity')}
- {i18n.get('prompt_templates.firebird_performance.page_reads')}
- {i18n.get('prompt_templates.firebird_performance.memory_usage')}
- {i18n.get('prompt_templates.firebird_performance.lock_conflicts')}
- {i18n.get('prompt_templates.firebird_performance.garbage_collection')}

{i18n.get('prompt_templates.firebird_performance.best_practices')}
{i18n.get('prompt_templates.firebird_performance.prepared_statements')}
{i18n.get('prompt_templates.firebird_performance.update_statistics')}
{i18n.get('prompt_templates.firebird_performance.monitor_growth')}
{i18n.get('prompt_templates.firebird_performance.archiving')}
{i18n.get('prompt_templates.firebird_performance.configure_buffers')}
"""
                
            elif prompt_name == "firebird_architecture":
                topic = arguments.get("topic", "general")
                version_focus = arguments.get("version_focus", "current")
                
                architecture_topic = i18n.get(f'architecture_topics.{topic}', 'General Firebird system administration')
                version_feature = i18n.get(f'version_features.{version_focus}', 'General features and considerations')
                
                prompt_text = f"""{i18n.get('prompt_templates.firebird_architecture.title')}

{i18n.get('prompt_templates.firebird_architecture.intro')}

{i18n.get('prompt_templates.firebird_architecture.focus_topic').format(topic=topic.title())}
{architecture_topic}

{i18n.get('prompt_templates.firebird_architecture.version_info').format(version_focus=version_focus)}
{version_feature}

{i18n.get('prompt_templates.firebird_architecture.server_architectures')}
- {i18n.get('prompt_templates.firebird_architecture.classic')}
- {i18n.get('prompt_templates.firebird_architecture.superserver')}
- {i18n.get('prompt_templates.firebird_architecture.superclassic')}
- {i18n.get('prompt_templates.firebird_architecture.embedded')}

{i18n.get('prompt_templates.firebird_architecture.critical_configs')}
```
{i18n.get('prompt_templates.firebird_architecture.config_comment')}
DefaultDbCachePages = 2048
TempCacheLimit = 67108864
LockMemSize = 1048576
LockHashSlots = 8191
EventMemSize = 65536
DeadlockTimeout = 10
LockTimeout = -1
RemoteServicePort = 3050
```

{i18n.get('prompt_templates.firebird_architecture.essential_monitoring')}
```sql
{i18n.get('prompt_templates.firebird_architecture.active_connections')}
SELECT * FROM MON$ATTACHMENTS;

{i18n.get('prompt_templates.firebird_architecture.long_transactions')}
SELECT * FROM MON$TRANSACTIONS 
WHERE MON$STATE = 1 
AND DATEDIFF(MINUTE, MON$TIMESTAMP, CURRENT_TIMESTAMP) > 5;

{i18n.get('prompt_templates.firebird_architecture.memory_usage')}
SELECT * FROM MON$MEMORY_USAGE;

{i18n.get('prompt_templates.firebird_architecture.io_stats')}
SELECT * FROM MON$IO_STATS;
```

{i18n.get('prompt_templates.firebird_architecture.operational_practices')}
1. {i18n.get('prompt_templates.firebird_architecture.regular_backup')}
2. {i18n.get('prompt_templates.firebird_architecture.proactive_monitoring')}
3. {i18n.get('prompt_templates.firebird_architecture.preventive_maintenance')}
4. {i18n.get('prompt_templates.firebird_architecture.security')}
5. {i18n.get('prompt_templates.firebird_architecture.documentation')}
6. {i18n.get('prompt_templates.firebird_architecture.disaster_recovery')}

{i18n.get('prompt_templates.firebird_architecture.troubleshooting')}
{i18n.get('prompt_templates.firebird_architecture.analyze_logs')}
{i18n.get('prompt_templates.firebird_architecture.check_corruption')}
{i18n.get('prompt_templates.firebird_architecture.monitor_temp_files')}
{i18n.get('prompt_templates.firebird_architecture.track_transactions')}
{i18n.get('prompt_templates.firebird_architecture.investigate_deadlocks')}
"""
            
            else:
                raise ValueError(f"{i18n.get('prompts.unknown_prompt')}: {prompt_name}")
            
            result = {
                "description": f"Prompt {prompt_name} generated dynamically",
                "messages": [{
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": prompt_text
                    }
                }]
            }
            
            self.send_response(request_id, result)
            
        except Exception as e:
            self.send_error(request_id, -32603, f"{i18n.get('prompts.error_generating')}: {str(e)}")
    
    def handle_tools_call(self, request_id: Any, params: Dict):
        """Execute tool"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        try:
            if tool_name == "test_connection":
                result_data = firebird_server.test_connection()
                content = [{
                    "type": "text",
                    "text": f"🔌 {i18n.get('connection.test_results')}:\n```json\n{json.dumps(result_data, indent=2)}\n```"
                }]
            
            elif tool_name == "execute_query":
                sql = arguments.get("sql")
                if not sql:
                    raise ValueError(i18n.get('tools.sql_required'))
                
                params_list = arguments.get("params")
                result_data = firebird_server.execute_query(sql, params_list)
                content = [{
                    "type": "text",
                    "text": f"📊 {i18n.get('tools.query_results')}:\n```json\n{json.dumps(result_data, indent=2)}\n```"
                }]
            
            elif tool_name == "list_tables":
                result = firebird_server.get_tables()
                content = [{
                    "type": "text",
                    "text": f"📋 {i18n.get('tools.database_tables')}:\n```json\n{json.dumps(result, indent=2)}\n```"
                }]
            
            elif tool_name == "server_status":
                # Check connection status if possible
                connection_test = None
                if FDB_AVAILABLE and FIREBIRD_CLIENT_AVAILABLE:
                    try:
                        connection_test = firebird_server.test_connection()
                    except:
                        connection_test = {"error": "Connection test failed"}
                
                status = {
                    "server_info": {
                        "name": os.getenv("MCP_SERVER_NAME", i18n.get('server_info.name')),
                        "version": os.getenv("MCP_SERVER_VERSION", "1.0.0"),
                        "python_version": sys.version
                    },
                    "fdb_python_library": {
                        "available": FDB_AVAILABLE,
                        "version": fdb.__version__ if FDB_AVAILABLE else None,
                        "error": FDB_ERROR if not FDB_AVAILABLE else None
                    },
                    "firebird_client_libraries": {
                        "available": FIREBIRD_CLIENT_AVAILABLE,
                        "path": CLIENT_LIBRARY_PATH,
                        "status": "✅ Found" if FIREBIRD_CLIENT_AVAILABLE else "❌ Not found"
                    },
                    "database_config": {
                        "host": DB_CONFIG['host'],
                        "port": DB_CONFIG['port'],
                        "database": DB_CONFIG['database'],
                        "user": DB_CONFIG['user'],
                        "charset": DB_CONFIG['charset']
                    },
                    "dsn": firebird_server.dsn,
                    "connection_test": connection_test,
                    "environment": {
                        "LD_LIBRARY_PATH": os.getenv('LD_LIBRARY_PATH', 'not set'),
                        "FIREBIRD_HOME": os.getenv('FIREBIRD_HOME', 'not set'),
                        "PATH": os.getenv('PATH', 'not set')
                    },
                    "recommendations": []
                }
                
                # Add recommendations based on status
                if not FDB_AVAILABLE:
                    status["recommendations"].append("Install FDB: pip install fdb==2.0.2")
                
                if not FIREBIRD_CLIENT_AVAILABLE:
                    status["recommendations"].extend([
                        "Check if /opt/firebird/lib/libfbclient.so exists",
                        "Verify LD_LIBRARY_PATH includes Firebird library directory",
                        "Rebuild container if libraries are missing"
                    ])
                
                content = [{
                    "type": "text",
                    "text": f"🔍 {i18n.get('tools.server_status_title')}:\n```json\n{json.dumps(status, indent=2)}\n```"
                }]
            
            else:
                raise ValueError(f"{i18n.get('tools.unknown_tool')}: {tool_name}")
            
            self.send_response(request_id, {
                "content": content,
                "isError": False
            })
            
        except Exception as e:
            error_content = [{
                "type": "text",
                "text": f"❌ {i18n.get('tools.error_executing')} {tool_name}: {str(e)}"
            }]
            self.send_response(request_id, {
                "content": error_content,
                "isError": True
            })
    
    def handle_request(self, request: Dict):
        """Process JSON-RPC request"""
        try:
            method = request.get("method")
            request_id = request.get("id")
            params = request.get("params", {})
            
            if method == "initialize":
                self.handle_initialize(request_id, params)
            elif method == "tools/list":
                self.handle_tools_list(request_id, params)
            elif method == "tools/call":
                self.handle_tools_call(request_id, params)
            elif method == "resources/list":
                self.handle_resources_list(request_id, params)
            elif method == "prompts/list":
                self.handle_prompts_list(request_id, params)
            elif method == "prompts/get":
                self.handle_prompts_get(request_id, params)
            elif method == "notifications/initialized":
                log(f"📨 {i18n.get('errors.notification_received')}")
            else:
                self.send_error(request_id, -32601, f"{i18n.get('errors.method_not_found')}: {method}")
                
        except Exception as e:
            log(f"❌ {i18n.get('server_info.error_handling')}: {e}")
            self.send_error(request.get("id"), -32603, str(e))
    
    def run(self):
        """Main server loop"""
        log(f"👂 {i18n.get('server_info.waiting')}")
        
        try:
            for line in sys.stdin:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    request = json.loads(line)
                    self.handle_request(request)
                except json.JSONDecodeError as e:
                    log(f"❌ {i18n.get('server_info.invalid_json')}: {e}")
                except Exception as e:
                    log(f"❌ {i18n.get('server_info.error_processing')}: {e}")
                    
        except KeyboardInterrupt:
            log(f"🛑 {i18n.get('server_info.interrupted')}")
        except Exception as e:
            log(f"❌ {i18n.get('server_info.server_error')}: {e}")
        finally:
            log(f"🔚 {i18n.get('server_info.shutting_down')}")

# ==========================================
# MAIN FUNCTION
# ==========================================

def main():
    """Main function with complete diagnostics"""
    log(i18n.get('server_info.starting'))
    log(f"📍 {i18n.get('environment.target_host')}: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    log(f"🗄️  {i18n.get('environment.target_database')}: {DB_CONFIG['database']}")
    log(f"👤 {i18n.get('environment.user')}: {DB_CONFIG['user']}")
    log(f"🌐 {i18n.get('environment.charset')}: {DB_CONFIG['charset']}")
    
    # Library status
    log(i18n.get('libraries.checking'))
    
    if FDB_AVAILABLE:
        log(f"✅ {i18n.get('libraries.fdb_available')}")
        log(f"📦 {i18n.get('libraries.fdb_version')}: {fdb.__version__}")
    else:
        log(f"❌ {i18n.get('libraries.fdb_not_available')}")
        log(f"   ⚠️  {i18n.get('libraries.fdb_error')}: {FDB_ERROR}")
    
    if FIREBIRD_CLIENT_AVAILABLE:
        log(f"✅ {i18n.get('libraries.client_available')}")
        log(f"📚 {i18n.get('libraries.client_location')}: {CLIENT_LIBRARY_PATH}")
    else:
        log(f"❌ {i18n.get('libraries.client_not_available')}")
        log(f"💡 {i18n.get('libraries.expected_locations')}:")
        log("   • /opt/firebird/lib/libfbclient.so")
        log("   • /usr/lib/libfbclient.so.2")
        log("   • /usr/lib/x86_64-linux-gnu/libfbclient.so.2")
    
    # Environment information
    log(i18n.get('environment.info'))
    log(f"🔗 LD_LIBRARY_PATH: {os.getenv('LD_LIBRARY_PATH', i18n.get('environment.not_set'))}")
    log(f"🏠 FIREBIRD_HOME: {os.getenv('FIREBIRD_HOME', i18n.get('environment.not_set'))}")
    
    # Connection test only if components are available
    if FDB_AVAILABLE and FIREBIRD_CLIENT_AVAILABLE:
        log(i18n.get('connection.testing'))
        try:
            result = firebird_server.test_connection()
            if result["connected"]:
                log(f"✅ {i18n.get('connection.successful')}")
                log(f"🔥 Firebird version: {result['version']}")
                log(f"🎯 {i18n.get('connection.ready_assistance')}")
            else:
                log(f"❌ {i18n.get('connection.failed')}")
                log(f"   ⚠️  Error type: {result.get('type', 'unknown')}")
                error_lines = result['error'].split('\n')
                log(f"   📝 Error: {error_lines[0]}")
                log("💡 Use test_connection tool for detailed diagnosis")
        except Exception as e:
            log(f"❌ Connection test failed: {e}")
    else:
        log(i18n.get('connection.skipping_test'))
        log("   Missing required libraries - use server_status tool for diagnostics")
    
    log("")
    log(i18n.get('server_info.starting_server'))
    log(f"📋 {i18n.get('tools.available')}:")
    log(f"   • test_connection - {i18n.get('tools.test_connection.description')}")
    log(f"   • execute_query - Execute SQL queries with expert guidance")
    log(f"   • list_tables - {i18n.get('tools.list_tables.description')}")
    log(f"   • server_status - {i18n.get('tools.server_status.description')}")
    log("")
    log(f"🎯 {i18n.get('prompts.available')}:")
    log(f"   • firebird_expert - {i18n.get('prompts.firebird_expert.description')}")
    log(f"   • firebird_performance - {i18n.get('prompts.firebird_performance.description')}")
    log(f"   • firebird_architecture - {i18n.get('prompts.firebird_architecture.description')}")
    
    if FDB_AVAILABLE and FIREBIRD_CLIENT_AVAILABLE:
        log(f"🔗 {i18n.get('connection.ready_assistance')}")
    else:
        log(f"⚠️  {i18n.get('libraries.limited_functionality')}")
        log(f"   {i18n.get('libraries.installation_instructions')}")
    
    log(i18n.get('server_info.ready'))
    log("")
    
    # Start MCP server
    server = MCPServer()
    server.run()

if __name__ == "__main__":
    main()
