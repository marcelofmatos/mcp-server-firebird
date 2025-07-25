"""Firebird MCP Server implementation."""

import sys
import os
from typing import List, Optional, Dict, Any

from ..core.config import DB_CONFIG
from .analyzer import SQLPatternAnalyzer

def log(message: str):
    """Log to stderr - visible in Docker/Claude Desktop"""
    print(f"[MCP-FIREBIRD] {message}", file=sys.stderr, flush=True)

class FirebirdMCPServer:
    """Main Firebird MCP Server class handling database operations."""
    
    def __init__(self, fdb_module=None, fdb_available=False, client_available=False, client_path=None):
        self.fdb = fdb_module
        self.fdb_available = fdb_available
        self.client_available = client_available
        self.client_path = client_path
        self.dsn = f"{DB_CONFIG['host']}/{DB_CONFIG['port']}:{DB_CONFIG['database']}"
        self.analyzer = SQLPatternAnalyzer()
        
        log(f"🔗 DSN configured: {self.dsn}")
        
    def test_connection(self) -> Dict[str, Any]:
        """Test connection to external Firebird with detailed diagnostics."""
        if not self.fdb_available:
            return {
                "connected": False,
                "error": "FDB library not available",
                "solution": "FDB Python library not installed - should be available in container",
                "type": "fdb_library_error"
            }
            
        if not self.client_available:
            return {
                "connected": False,
                "error": "Firebird client libraries not available",
                "solution": (
                    "Firebird client libraries missing. This container should have them installed.\n"
                    "• Check if container build completed successfully\n"
                    "• Verify /opt/firebird/lib/ contains libfbclient.so\n"
                    "• Check LD_LIBRARY_PATH configuration"
                ),
                "type": "client_library_error",
                "library_path": self.client_path,
                "ld_library_path": os.getenv('LD_LIBRARY_PATH')
            }
            
        try:
            log(f"🔌 Attempting connection: {self.dsn}")
            conn = self.fdb.connect(
                dsn=self.dsn,
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                charset=DB_CONFIG['charset']
            )
            cursor = conn.cursor()
            cursor.execute("SELECT RDB$GET_CONTEXT('SYSTEM', 'ENGINE_VERSION') FROM RDB$DATABASE")
            version = cursor.fetchone()[0]
            conn.close()
            log(f"✅ Connection successful")
            
            return {
                "connected": True,
                "version": version.strip(),
                "dsn": self.dsn,
                "user": DB_CONFIG['user'],
                "charset": DB_CONFIG['charset']
            }
            
        except Exception as e:
            log(f"❌ Connection failed: {e}")
            error_msg = str(e)
            error_type = "unknown_error"
            
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
    
    def execute_query(self, sql: str, params: Optional[List] = None) -> Dict[str, Any]:
        """Execute SQL query with robust error handling and analysis."""
        if not self.fdb_available:
            return {
                "success": False,
                "error": "FDB library not available",
                "solution": "FDB Python library not installed in container",
                "type": "fdb_library_error"
            }
            
        if not self.client_available:
            return {
                "success": False,
                "error": "Firebird client libraries not available",
                "solution": "Firebird client libraries missing from container",
                "type": "client_library_error"
            }
        
        analysis = self.analyzer.analyze(sql)
            
        try:
            conn = self.fdb.connect(
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
                    "sql": sql,
                    "analysis": analysis
                }
            else:
                affected = cursor.rowcount
                conn.commit()
                result = {
                    "success": True,
                    "affected_rows": affected,
                    "sql": sql,
                    "analysis": analysis
                }
                
            conn.close()
            return result
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "sql": sql,
                "params": params,
                "analysis": analysis
            }
    
    def get_tables(self) -> Dict[str, Any]:
        """List database tables with additional metadata."""
        if not self.fdb_available:
            return {
                "success": False,
                "error": "FDB library not available",
                "solution": "FDB Python library not installed",
                "type": "fdb_library_error"
            }
            
        if not self.client_available:
            return {
                "success": False,
                "error": "Firebird client libraries not available",
                "solution": "Firebird client libraries missing from container",
                "type": "client_library_error"
            }
            
        try:
            conn = self.fdb.connect(
                dsn=self.dsn,
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                charset=DB_CONFIG['charset']
            )
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT TRIM(RDB$RELATION_NAME) as TABLE_NAME,
                       COALESCE(RDB$DESCRIPTION, 'No description') as DESCRIPTION
                FROM RDB$RELATIONS 
                WHERE RDB$VIEW_BLR IS NULL 
                AND (RDB$SYSTEM_FLAG IS NULL OR RDB$SYSTEM_FLAG = 0)
                ORDER BY RDB$RELATION_NAME
            """)
            tables_data = cursor.fetchall()
            
            tables = []
            for row in tables_data:
                tables.append({
                    "name": row[0],
                    "description": row[1] if row[1] != "No description" else None
                })
            
            conn.close()
            
            return {
                "success": True,
                "tables": [t["name"] for t in tables],
                "tables_detailed": tables,
                "count": len(tables),
                "database": DB_CONFIG['database']
            }
            
        except Exception as e:
            log(f"❌ Failed to retrieve tables: {e}")
            return {
                "success": False,
                "error": str(e),
                "database": DB_CONFIG['database']
            }
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific table."""
        if not self.fdb_available or not self.client_available:
            return {
                "success": False,
                "error": "Required libraries not available"
            }
        
        try:
            conn = self.fdb.connect(
                dsn=self.dsn,
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                charset=DB_CONFIG['charset']
            )
            cursor = conn.cursor()
            
            # Get table columns
            cursor.execute("""
                SELECT 
                    TRIM(rf.RDB$FIELD_NAME) as COLUMN_NAME,
                    TRIM(f.RDB$FIELD_TYPE) as FIELD_TYPE,
                    f.RDB$FIELD_LENGTH as FIELD_LENGTH,
                    f.RDB$FIELD_SCALE as FIELD_SCALE,
                    rf.RDB$NULL_FLAG as NULL_FLAG,
                    TRIM(rf.RDB$DEFAULT_SOURCE) as DEFAULT_VALUE
                FROM RDB$RELATION_FIELDS rf
                JOIN RDB$FIELDS f ON rf.RDB$FIELD_SOURCE = f.RDB$FIELD_NAME
                WHERE rf.RDB$RELATION_NAME = ?
                ORDER BY rf.RDB$FIELD_POSITION
            """, [table_name.upper()])
            
            columns = cursor.fetchall()
            conn.close()
            
            return {
                "success": True,
                "table_name": table_name,
                "columns": [
                    {
                        "name": col[0],
                        "type": col[1],
                        "length": col[2],
                        "scale": col[3],
                        "nullable": col[4] is None,
                        "default": col[5]
                    }
                    for col in columns
                ]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "table_name": table_name
            }
