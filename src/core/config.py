"""Configuration module for MCP Server Firebird."""

import os
import sys
import ctypes.util
from typing import Tuple, Optional

def log(message: str):
    """Log to stderr - visible in Docker/Claude Desktop"""
    print(f"[MCP-FIREBIRD] {message}", file=sys.stderr, flush=True)

# Database Configuration
DB_CONFIG = {
    'host': os.getenv('FIREBIRD_HOST', 'localhost'),
    'port': int(os.getenv('FIREBIRD_PORT', 3050)),
    'database': os.getenv('FIREBIRD_DATABASE', '/path/to/database.fdb'),
    'user': os.getenv('FIREBIRD_USER', 'SYSDBA'),
    'password': os.getenv('FIREBIRD_PASSWORD', 'masterkey'),
    'charset': os.getenv('FIREBIRD_CHARSET', 'UTF8')
}

# Default Prompt System Configuration
DEFAULT_PROMPT_CONFIG = {
    'enabled': os.getenv('FIREBIRD_DEFAULT_PROMPT_ENABLED', 'true').lower() == 'true',
    'prompt_name': os.getenv('FIREBIRD_DEFAULT_PROMPT', 'firebird_expert'),
    'operation_type': os.getenv('FIREBIRD_DEFAULT_OPERATION', 'query'),
    'complexity_level': os.getenv('FIREBIRD_DEFAULT_COMPLEXITY', 'intermediate'),
    'auto_apply': os.getenv('FIREBIRD_AUTO_APPLY_PROMPT', 'false').lower() == 'true',  # Compact: conservative
    'compact_mode': True  # Optimized token usage
}

def initialize_libraries() -> Tuple[bool, Optional[object], str, bool, Optional[str]]:
    """
    Initialize Firebird libraries and return status.
    
    Returns:
        Tuple of (fdb_available, fdb_module, fdb_error, client_available, client_path)
    """
    fdb_available = False
    fdb_module = None
    fdb_error = None
    firebird_client_available = False
    client_library_path = None
    
    # Try to import FDB
    try:
        import fdb
        fdb_available = True
        fdb_module = fdb
        log(f"✅ FDB Python library loaded successfully")
        log(f"📦 FDB version: {fdb.__version__}")
        
        # Check for client libraries
        try:
            fbclient_path = ctypes.util.find_library('fbclient')
            if fbclient_path:
                firebird_client_available = True
                client_library_path = fbclient_path
                log(f"✅ Firebird client library found: {fbclient_path}")
            else:
                log(f"⚠️  Firebird client libraries not found in standard paths")
                log(f"🔍 LD_LIBRARY_PATH: {os.getenv('LD_LIBRARY_PATH', 'not set')}")
                
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
                        firebird_client_available = True
                        client_library_path = path
                        log(f"✅ Found Firebird client at alternative path: {path}")
                        break
                
                if not firebird_client_available:
                    log(f"❌ No Firebird client libraries found")
                    
        except Exception as e:
            log(f"⚠️  Library path check failed: {e}")
            
    except ImportError as e:
        fdb_available = False
        fdb_error = str(e)
        log(f"❌ Could not import FDB: {e}")
        log(f"💡 FDB Python library not available")
    
    return fdb_available, fdb_module, fdb_error, firebird_client_available, client_library_path

def get_server_info() -> dict:
    """Get server information for MCP responses."""
    return {
        "name": os.getenv("MCP_SERVER_NAME", "firebird-expert-server"),
        "version": os.getenv("MCP_SERVER_VERSION", "1.0.0")
    }
