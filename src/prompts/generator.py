"""Dynamic prompt generation for table schemas."""

from typing import Dict, List
from ..core.config import DB_CONFIG
from ..core.i18n import I18n

class PromptGenerator:
    """Generate dynamic prompts based on database schema."""
    
    def __init__(self, firebird_server=None, i18n: I18n = None):
        self.firebird_server = firebird_server
        self.i18n = i18n or I18n()
    
    def generate(self, prompt_name: str, arguments: Dict) -> str:
        """Generate prompt with dynamic context."""
        if prompt_name.endswith("_schema"):
            table_name = prompt_name.replace("_schema", "")
            return self._generate_table_schema_prompt(table_name)
        else:
            raise ValueError(f"Unknown prompt: {prompt_name}")
    
    def get_available_table_prompts(self) -> List[Dict[str, str]]:
        """Get list of available table schema prompts."""
        if not self.firebird_server:
            return []
        
        try:
            tables_result = self.firebird_server.get_tables()
            if not tables_result.get("success"):
                return []
            
            prompts = []
            for table_name in tables_result["tables"]:
                prompts.append({
                    "name": f"{table_name}_schema",
                    "description": self.i18n.get('table_schema.description', table_name=table_name),
                    "title": f"{table_name} schema"
                })
            
            return prompts
            
        except Exception:
            return []
    
    def _generate_table_schema_prompt(self, table_name: str) -> str:
        """Generate schema prompt for a specific table."""
        if not self.firebird_server:
            return self.i18n.get('table_schema.no_server_error')
        
        try:
            schema = self.firebird_server.get_table_schema(table_name)
            if not schema.get("success"):
                return self.i18n.get('table_schema.schema_error', table_name=table_name, error=schema.get('error', 'Unknown error'))
            
            # Build schema information
            content = []
            content.append(self.i18n.get('table_schema.header', table_name=table_name))
            content.append("")
            
            # Table info
            content.append(self.i18n.get('table_schema.table_info'))
            content.append(f"- {self.i18n.get('table_schema.table_name')}: {table_name}")
            content.append(f"- {self.i18n.get('table_schema.database')}: {DB_CONFIG['database']}")
            content.append("")
            
            # Columns
            content.append(self.i18n.get('table_schema.columns_header'))
            for col in schema["columns"]:
                nullable = self.i18n.get('table_schema.nullable_yes') if col["nullable"] == "YES" else self.i18n.get('table_schema.nullable_no')
                default = col.get("default_value") or self.i18n.get('table_schema.no_default')
                content.append(f"- {col['column_name']}: {col['data_type']} | {self.i18n.get('table_schema.nullable')}: {nullable} | {self.i18n.get('table_schema.default')}: {default}")
            content.append("")
            
            # Primary keys
            if schema["primary_keys"]:
                content.append(self.i18n.get('table_schema.primary_keys_header'))
                content.append(f"- {', '.join(schema['primary_keys'])}")
                content.append("")
            
            # Foreign keys
            if schema["foreign_keys"]:
                content.append(self.i18n.get('table_schema.foreign_keys_header'))
                fk_groups = {}
                for fk in schema["foreign_keys"]:
                    ref_table = fk["referenced_table"]
                    if ref_table not in fk_groups:
                        fk_groups[ref_table] = []
                    fk_groups[ref_table].append(f"{fk['column_name']} -> {fk['referenced_column']}")
                
                for ref_table, relationships in fk_groups.items():
                    content.append(f"- {self.i18n.get('table_schema.references')} {ref_table}: {', '.join(relationships)}")
                content.append("")
            
            # Indexes
            if schema["indexes"]:
                content.append(self.i18n.get('table_schema.indexes_header'))
                idx_groups = {}
                for idx in schema["indexes"]:
                    idx_name = idx["index_name"]
                    if idx_name not in idx_groups:
                        idx_groups[idx_name] = {
                            "columns": [],
                            "unique": idx["is_unique"]
                        }
                    idx_groups[idx_name]["columns"].append(idx["column_name"])
                
                for idx_name, info in idx_groups.items():
                    unique_text = self.i18n.get('table_schema.unique') if info["unique"] else self.i18n.get('table_schema.non_unique')
                    content.append(f"- {idx_name} ({unique_text}): {', '.join(info['columns'])}")
                content.append("")
            
            # Usage guidance
            content.append(self.i18n.get('table_schema.usage_guidance'))
            content.append(f"- {self.i18n.get('table_schema.select_guidance')}")
            content.append(f"- {self.i18n.get('table_schema.join_guidance')}")
            content.append(f"- {self.i18n.get('table_schema.insert_guidance')}")
            content.append(f"- {self.i18n.get('table_schema.update_guidance')}")
            
            return "\n".join(content)
            
        except Exception as e:
            return self.i18n.get('table_schema.generation_error', table_name=table_name, error=str(e))
    
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
    

    
    def register_firebird_server(self, server):
        """Register FirebirdMCPServer instance for dynamic context."""
        self.firebird_server = server
