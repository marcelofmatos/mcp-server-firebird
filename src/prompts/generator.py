"""Dynamic prompt generation with context awareness and i18n support."""

from typing import Dict, Callable
from ..core.config import DB_CONFIG
from ..core.i18n import I18n

class PromptGenerator:
    """Generate dynamic prompts with contextual information, current environment data, and i18n support."""
    
    def __init__(self, firebird_server=None, i18n: I18n = None):
        self.firebird_server = firebird_server
        self.i18n = i18n or I18n()
        self.base_prompts = {
            "firebird_expert": self._generate_expert_prompt,
            "firebird_performance": self._generate_performance_prompt,
            "firebird_architecture": self._generate_architecture_prompt
        }
    
    def generate(self, prompt_name: str, arguments: Dict) -> str:
        """
        Generate prompt with dynamic context.
        
        Args:
            prompt_name: Name of the prompt to generate
            arguments: Arguments for prompt customization
            
        Returns:
            Generated prompt text with current context
            
        Raises:
            ValueError: If prompt_name is not recognized
        """
        if prompt_name in self.base_prompts:
            return self.base_prompts[prompt_name](arguments)
        else:
            raise ValueError(f"Unknown prompt: {prompt_name}")
    
    def _generate_expert_prompt(self, args: Dict) -> str:
        """Generate comprehensive Firebird expert prompt with current context and i18n."""
        operation_type = args.get("operation_type", "query")
        table_context = args.get("table_context", "")
        complexity_level = args.get("complexity_level", "intermediate")
        
        # Get available tables dynamically if firebird_server is available
        tables_info = ""
        if self.firebird_server:
            try:
                tables_result = self.firebird_server.get_tables()
                if tables_result.get("success") and tables_result.get("tables"):
                    table_list = tables_result["tables"][:20]  # Limit to first 20 tables
                    tables_info = f"\n\n**{self.i18n.get('prompt_templates.firebird_expert.available_tables')}**: {', '.join(table_list)}"
            except Exception:
                pass  # Silently continue if table retrieval fails
        
        # Build localized prompt using i18n templates
        template = self.i18n.get('prompt_templates.firebird_expert')
        
        # Get operation-specific guidance
        operation_guidance = self.i18n.get(f'operation_guidance.{operation_type}', 
                                          self.i18n.get('operation_guidance.select'))
        
        # Get complexity-specific guidance
        complexity_guidance = self.i18n.get(f'complexity_levels.{complexity_level}',
                                           self.i18n.get('complexity_levels.intermediate'))
        
        context_text = f"{table_context}: " if table_context else ""
        
        return f"""{template.get('title', '## Firebird Expert - Technical Assistant')}

{template.get('intro', 'You are a technical expert in Firebird RDBMS.')}

{context_text}

{template.get('environment_config', '### Environment Configuration:')}
- **{self.i18n.get('environment.target_host')}**: {DB_CONFIG['host']}:{DB_CONFIG['port']}
- **{self.i18n.get('environment.target_database')}**: {DB_CONFIG['database']}
- **{self.i18n.get('environment.user')}**: {DB_CONFIG['user']}
- **{self.i18n.get('environment.charset')}**: {DB_CONFIG['charset']}
- **{template.get('complexity_level', 'Complexity level')}**: {complexity_level}

{template.get('guidelines', '### Guidelines for')} {operation_type}:
{operation_guidance}

{template.get('specific_guidance', 'Specific guidance')} ({complexity_level}):
{complexity_guidance}

{template.get('firebird_expertise', '### Firebird Expertise:')}
- {template.get('sql_syntax', '**SQL Syntax**: Firebird dialects and features')}
- {template.get('performance', '**Performance**: Indexes, statistics, execution plans')}
- {template.get('transactions', '**Transactions**: Isolation, concurrency, deadlocks')}
- {template.get('stored_procedures', '**Stored Procedures**: PSQL, triggers, functions')}
- {template.get('administration', '**Administration**: Backup/restore, security, monitoring')}
- {template.get('architecture', '**Architecture**: Classic, SuperServer, SuperClassic')}

{template.get('advanced_features', '### Advanced Features:')}
- {template.get('window_functions', '**Window Functions** (FB 3.0+)')}
- {template.get('cte', '**Common Table Expressions (CTE)')}
- {template.get('merge', '**Merge Statement')}
- {template.get('temp_tables', '**Global Temporary Tables')}
- {template.get('partial_indexes', '**Partial Indexes')}
- {template.get('expression_indexes', '**Expression Indexes')}
- {template.get('computed_columns', '**Computed Columns')}
- {template.get('generators', '**Generators/Sequences')}

{template.get('response_approach', '### Response Approach:')}
{template.get('explain_context', '- Explain technical context of solutions')}
{template.get('mention_alternatives', '- Mention alternatives when relevant')}
{template.get('performance_impact', '- Indicate performance impacts')}
{template.get('version_compatibility', '- Consider version compatibility')}
{template.get('practical_examples', '- Provide practical, working examples')}
{template.get('highlight_pitfalls', '- Highlight potential pitfalls or limitations')}{tables_info}
"""
    
    def _generate_performance_prompt(self, args: Dict) -> str:
        """Generate performance optimization specialist prompt with i18n."""
        query_type = args.get("query_type", "general")
        focus_area = args.get("focus_area", "general")
        
        # Build localized prompt using i18n templates
        template = self.i18n.get('prompt_templates.firebird_performance')
        
        # Get query-specific optimization techniques
        query_optimization = self.i18n.get(f'query_optimizations.{query_type}',
                                          self.i18n.get('query_optimizations.simple'))
        
        # Get focus-specific techniques
        focus_technique = self.i18n.get(f'focus_techniques.{focus_area}',
                                       self.i18n.get('focus_techniques.indexes'))
        
        return f"""{template.get('title', '## Firebird Performance Expert')}

{template.get('intro', 'Performance optimization specialist for Firebird RDBMS.')}

{template.get('focus_queries', '### Focus on').format(query_type=query_type)} 
{query_optimization}

{template.get('specialization', '### Specialization Area').format(focus_area=focus_area)}:
{focus_technique}

**{self.i18n.get('environment.info')}**: {DB_CONFIG['host']}:{DB_CONFIG['port']} - {DB_CONFIG['database']}

{template.get('analysis_tools', '### Analysis Tools:')}
```sql
{template.get('plan_comment', '-- Analyze execution plan')}
SET PLAN ON;
SET STATS ON;

{template.get('monitor_comment', '-- Monitor real-time performance')}
SELECT * FROM MON$STATEMENTS WHERE MON$STATE = 1;
SELECT * FROM MON$IO_STATS;
SELECT * FROM MON$RECORD_STATS;
SELECT * FROM MON$MEMORY_USAGE;

{template.get('statistics_comment', '-- Table and index statistics')}
SELECT * FROM RDB$RELATION_STATISTICS;
SELECT * FROM RDB$INDEX_STATISTICS;

SELECT * FROM MON$LOCKS;
SELECT * FROM MON$TRANSACTIONS WHERE MON$STATE = 1;
```

{template.get('methodology', '### Optimization Methodology:')}
1. {template.get('analysis', '**Analysis**: Identify bottlenecks')}
2. {template.get('indexes', '**Indexes**: Create appropriate indexes')}
3. {template.get('rewrite', '**Rewrite**: Optimize SQL structure')}
4. {template.get('test', '**Test**: Validate improvements')}
5. {template.get('monitor', '**Monitor**: Track performance')}

{template.get('important_metrics', '### Important Metrics:')}
- {template.get('selectivity', '**Selectivity**: Lower is better for indexes')}
- {template.get('page_reads', '**Page Reads**: Minimize physical reads')}
- {template.get('memory_usage', '**Memory Usage**: Optimize cache usage')}
- {template.get('lock_conflicts', '**Lock Conflicts**: Reduce contention')}
- {template.get('garbage_collection', '**Garbage Collection**: Keep statistics updated')}

{template.get('best_practices', '### Best Practices:')}
{template.get('prepared_statements', '- Use prepared statements')}
{template.get('update_statistics', '- Keep statistics updated')}
{template.get('monitor_growth', '- Monitor table growth')}
{template.get('archiving', '- Implement archiving for historical data')}
{template.get('configure_buffers', '- Configure page_size and page_buffers properly')}
"""
    
    def _generate_architecture_prompt(self, args: Dict) -> str:
        """Generate architecture and administration specialist prompt with i18n."""
        topic = args.get("topic", "general")
        version_focus = args.get("version_focus", "current")
        
        # Build localized prompt using i18n templates
        template = self.i18n.get('prompt_templates.firebird_architecture')
        
        # Get topic-specific information
        topic_info = self.i18n.get(f'architecture_topics.{topic}',
                                  self.i18n.get('architecture_topics.backup'))
        
        # Get version-specific features
        version_info = self.i18n.get(f'version_features.{version_focus}',
                                    self.i18n.get('version_features.3.0'))
        
        return f"""{template.get('title', '## Firebird Architecture Expert')}

{template.get('intro', 'System administration and enterprise Firebird architecture specialist.')}

{template.get('focus_topic', '### Focus on').format(topic=topic)}:
{topic_info}

{template.get('version_info', '### Firebird Version').format(version_focus=version_focus)}:
{version_info}

**{self.i18n.get('environment.info')}**: {DB_CONFIG['host']}:{DB_CONFIG['port']} - {DB_CONFIG['database']}

{template.get('server_architectures', '### Server Architectures:')}
- {template.get('classic', '**Classic**: Process-per-connection, greater isolation')}
- {template.get('superserver', '**SuperServer**: Thread per connection, shared cache')}
- {template.get('superclassic', '**SuperClassic**: Hybrid, shared worker processes')}
- {template.get('embedded', '**Embedded**: Integrated library, single-user')}

{template.get('critical_configs', '### Critical Configurations:')}
```ini
{template.get('config_comment', '# firebird.conf main parameters')}
DefaultDbCachePages = 2048
TempCacheLimit = 67108864
LockMemSize = 1048576
LockHashSlots = 8191
EventMemSize = 65536
DeadlockTimeout = 10
LockTimeout = -1
RemoteServicePort = 3050
MaxUnflushedWrites = 100
MaxUnflushedWriteTime = 5
```

{template.get('essential_monitoring', '### Essential Monitoring:')}
```sql
{template.get('active_connections', '-- Active connections')}
SELECT MON$ATTACHMENT_ID, MON$USER, MON$REMOTE_ADDRESS, MON$TIMESTAMP, MON$STATE
FROM MON$ATTACHMENTS;

{template.get('long_transactions', '-- Long transactions (common problem)')}
SELECT MON$TRANSACTION_ID, MON$ATTACHMENT_ID, MON$STATE,
       DATEDIFF(MINUTE, MON$TIMESTAMP, CURRENT_TIMESTAMP) as DURATION_MINUTES
FROM MON$TRANSACTIONS 
WHERE MON$STATE = 1 AND DATEDIFF(MINUTE, MON$TIMESTAMP, CURRENT_TIMESTAMP) > 1;

{template.get('memory_usage', '-- Memory usage')}
SELECT MON$STAT_GROUP, MON$STAT_ID, MON$MEMORY_USED, MON$MEMORY_ALLOCATED
FROM MON$MEMORY_USAGE;

{template.get('io_stats', '-- I/O Statistics')}
SELECT MON$STAT_GROUP, MON$PAGE_READS, MON$PAGE_WRITES, MON$PAGE_FETCHES, MON$PAGE_MARKS
FROM MON$IO_STATS;
```

{template.get('operational_practices', '### Operational Practices:')}
1. {template.get('regular_backup', '**Regular backup**: Multiple strategies (gbak + nbackup)')}
2. {template.get('proactive_monitoring', '**Proactive monitoring**: Automated scripts')}
3. {template.get('preventive_maintenance', '**Preventive maintenance**: Sweep, rebuild, statistics')}
4. {template.get('security', '**Security**: Principle of least privilege')}
5. {template.get('documentation', '**Documentation**: Changes, configurations, procedures')}
6. {template.get('disaster_recovery', '**Disaster Recovery**: Regular restore testing')}

{template.get('troubleshooting', '### Troubleshooting:')}
{template.get('analyze_logs', '- Analyze Firebird error logs')}
{template.get('check_corruption', '- Check corruption with gfix -validate')}
{template.get('monitor_temp_files', '- Monitor temporary file growth')}
{template.get('track_transactions', '- Track long-running transactions')}
{template.get('investigate_deadlocks', '- Investigate deadlocks and lock conflicts')}
"""
    
    def register_firebird_server(self, server):
        """Register FirebirdMCPServer instance for dynamic context."""
        self.firebird_server = server
    
    def get_available_prompts(self) -> list:
        """Get list of available prompt templates."""
        return list(self.base_prompts.keys())
