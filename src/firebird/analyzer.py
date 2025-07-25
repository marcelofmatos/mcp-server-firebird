"""SQL pattern analysis for Firebird queries."""

import re
from typing import Dict, List

class SQLPatternAnalyzer:
    """Analyzes SQL patterns for enhanced guidance and optimization suggestions."""
    
    def __init__(self):
        self.patterns = {
            'select_simple': r'^\s*SELECT\s+[\w\*,\s]+\s+FROM\s+\w+(?:\s+WHERE\s+[\w\s=<>\'\"]+)?(?:\s+ORDER\s+BY\s+[\w\s,]+)?\s*;?\s*$',
            'select_complex': r'.*(?:JOIN|UNION|SUBQUERY|WITH|WINDOW|PARTITION|GROUP\s+BY|HAVING).*',
            'select_aggregation': r'.*(?:COUNT|SUM|AVG|MIN|MAX|GROUP\s+BY).*',
            'insert_simple': r'^\s*INSERT\s+INTO\s+\w+\s*\([^)]+\)\s*VALUES\s*\([^)]+\)\s*;?\s*$',
            'insert_batch': r'.*(?:VALUES\s*\([^)]+\)\s*,|INSERT\s+INTO.*SELECT).*',
            'update_simple': r'^\s*UPDATE\s+\w+\s+SET\s+.+\s+WHERE\s+.+\s*;?\s*$',
            'update_complex': r'.*(?:JOIN|SUBQUERY|CASE\s+WHEN).*',
            'delete_simple': r'^\s*DELETE\s+FROM\s+\w+\s+WHERE\s+.+\s*;?\s*$',
            'ddl_create': r'^\s*CREATE\s+(?:TABLE|VIEW|INDEX|PROCEDURE|TRIGGER).*',
            'ddl_alter': r'^\s*ALTER\s+(?:TABLE|VIEW|INDEX|PROCEDURE).*',
            'ddl_drop': r'^\s*DROP\s+(?:TABLE|VIEW|INDEX|PROCEDURE|TRIGGER).*'
        }
    
    def analyze(self, sql: str) -> Dict:
        """
        Analyze SQL pattern and provide context and suggestions.
        
        Args:
            sql: SQL query string to analyze
            
        Returns:
            Dictionary with analysis results including type, complexity, category, and suggestions
        """
        sql_upper = sql.upper().strip()
        
        analysis = {
            'type': 'unknown',
            'complexity': 'simple',
            'category': 'query',
            'suggestions': [],
            'firebird_features': [],
            'performance_tips': []
        }
        
        if sql_upper.startswith('SELECT'):
            analysis.update(self._analyze_select(sql_upper))
        elif sql_upper.startswith('INSERT'):
            analysis.update(self._analyze_insert(sql_upper))
        elif sql_upper.startswith('UPDATE'):
            analysis.update(self._analyze_update(sql_upper))
        elif sql_upper.startswith('DELETE'):
            analysis.update(self._analyze_delete(sql_upper))
        elif any(sql_upper.startswith(ddl) for ddl in ['CREATE', 'ALTER', 'DROP']):
            analysis.update(self._analyze_ddl(sql_upper))
        
        return analysis
    
    def _analyze_select(self, sql: str) -> Dict:
        """Analyze SELECT statements."""
        result = {
            'type': 'select',
            'category': 'query',
            'suggestions': [],
            'firebird_features': [],
            'performance_tips': []
        }
        
        if re.search(self.patterns['select_complex'], sql):
            result['complexity'] = 'complex'
            result['suggestions'].extend([
                'Consider using PLAN to verify optimal execution',
                'Check if all JOIN conditions use indexed columns'
            ])
            result['performance_tips'].append('Use SET PLAN ON to analyze execution plan')
            
            if 'WITH' in sql:
                result['firebird_features'].append('Common Table Expression (CTE)')
            if 'WINDOW' in sql or 'OVER(' in sql:
                result['firebird_features'].append('Window Functions')
                
        elif re.search(self.patterns['select_aggregation'], sql):
            result['complexity'] = 'intermediate'
            result['suggestions'].extend([
                'Check index usage for GROUP BY columns',
                'Consider partial indexes for filtered aggregations'
            ])
            result['performance_tips'].append('Ensure GROUP BY columns are indexed')
        
        if 'MERGE' in sql:
            result['firebird_features'].append('MERGE statement')
        if 'GLOBAL TEMPORARY' in sql:
            result['firebird_features'].append('Global Temporary Tables')
            
        return result
    
    def _analyze_insert(self, sql: str) -> Dict:
        """Analyze INSERT statements."""
        result = {
            'type': 'insert',
            'category': 'modification',
            'suggestions': [],
            'firebird_features': [],
            'performance_tips': []
        }
        
        if re.search(self.patterns['insert_batch'], sql):
            result['complexity'] = 'intermediate'
            result['suggestions'].extend([
                'Consider transaction size for batch operations',
                'Use MERGE for upsert operations when appropriate'
            ])
            result['performance_tips'].extend([
                'Batch inserts in appropriately sized transactions',
                'Consider disabling triggers temporarily for large batches'
            ])
        
        if 'RETURNING' in sql:
            result['firebird_features'].append('RETURNING clause')
        
        return result
    
    def _analyze_update(self, sql: str) -> Dict:
        """Analyze UPDATE statements."""
        result = {
            'type': 'update',
            'category': 'modification',
            'suggestions': [],
            'firebird_features': [],
            'performance_tips': []
        }
        
        if re.search(self.patterns['update_complex'], sql):
            result['complexity'] = 'complex'
            result['suggestions'].append('Verify WHERE clause uses indexed columns')
            result['performance_tips'].append('Use selective WHERE conditions to minimize row scans')
        else:
            result['suggestions'].append('Ensure WHERE clause is selective and uses indexes')
        
        if 'RETURNING' in sql:
            result['firebird_features'].append('RETURNING clause')
        
        return result
    
    def _analyze_delete(self, sql: str) -> Dict:
        """Analyze DELETE statements."""
        result = {
            'type': 'delete',
            'category': 'modification',
            'suggestions': [
                '⚠️  Always verify WHERE clause before execution',
                'Consider using transaction for safety'
            ],
            'firebird_features': [],
            'performance_tips': [
                'Use selective WHERE conditions',
                'Consider batch deletion for large datasets'
            ]
        }
        
        if 'WHERE' not in sql:
            result['suggestions'].insert(0, '🚨 WARNING: DELETE without WHERE clause affects ALL rows!')
            result['complexity'] = 'dangerous'
        
        return result
    
    def _analyze_ddl(self, sql: str) -> Dict:
        """Analyze DDL statements."""
        result = {
            'category': 'ddl',
            'suggestions': [],
            'firebird_features': [],
            'performance_tips': []
        }
        
        if sql.startswith('CREATE'):
            result['type'] = 'create'
            if 'INDEX' in sql:
                result['performance_tips'].extend([
                    'Consider partial indexes for selective conditions',
                    'Use expression indexes for computed values'
                ])
            if 'PROCEDURE' in sql or 'TRIGGER' in sql:
                result['firebird_features'].append('PSQL (Procedural SQL)')
                
        elif sql.startswith('ALTER'):
            result['type'] = 'alter'
            result['suggestions'].append('Schema changes may require exclusive access')
            
        elif sql.startswith('DROP'):
            result['type'] = 'drop'
            result['suggestions'].extend([
                '⚠️  Destructive operation - verify before execution',
                'Consider backup before dropping objects'
            ])
            result['complexity'] = 'dangerous'
        
        return result
    
    def get_optimization_suggestions(self, sql: str) -> List[str]:
        """Get specific optimization suggestions for a query."""
        analysis = self.analyze(sql)
        suggestions = []
        
        # Add general optimization tips based on query type
        if analysis['type'] == 'select':
            suggestions.extend([
                'Use FIRST/SKIP for pagination instead of LIMIT/OFFSET',
                'Consider using EXISTS instead of IN for subqueries',
                'Use UNION ALL instead of UNION when duplicates are acceptable'
            ])
        
        # Add Firebird-specific optimization tips
        suggestions.extend([
            'Keep transactions short to avoid garbage collection issues',
            'Use prepared statements to reduce parsing overhead',
            'Monitor MON$ tables for performance analysis'
        ])
        
        return suggestions + analysis.get('performance_tips', [])
