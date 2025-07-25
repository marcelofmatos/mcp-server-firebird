"""Unit tests for SQL Pattern Analyzer."""

import pytest
import sys
import os

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from firebird.analyzer import SQLPatternAnalyzer


class TestSQLPatternAnalyzer:
    """Test cases for SQLPatternAnalyzer class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = SQLPatternAnalyzer()
    
    def test_simple_select_analysis(self):
        """Test analysis of simple SELECT statements."""
        sql = "SELECT name, email FROM users WHERE active = 1"
        result = self.analyzer.analyze(sql)
        
        assert result['type'] == 'select'
        assert result['category'] == 'query'
        assert result['complexity'] == 'simple'
        assert isinstance(result['suggestions'], list)
    
    def test_complex_select_analysis(self):
        """Test analysis of complex SELECT with JOINs."""
        sql = """
        SELECT u.name, p.title, COUNT(o.id) as order_count
        FROM users u
        JOIN profiles p ON u.id = p.user_id
        LEFT JOIN orders o ON u.id = o.user_id
        WHERE u.active = 1
        GROUP BY u.id, u.name, p.title
        HAVING COUNT(o.id) > 5
        """
        result = self.analyzer.analyze(sql)
        
        assert result['type'] == 'select'
        assert result['complexity'] == 'complex'
        assert 'Consider using PLAN to verify optimal execution' in result['suggestions']
    
    def test_insert_analysis(self):
        """Test analysis of INSERT statements."""
        sql = "INSERT INTO users (name, email) VALUES ('John', 'john@example.com')"
        result = self.analyzer.analyze(sql)
        
        assert result['type'] == 'insert'
        assert result['category'] == 'modification'
        assert result['complexity'] == 'simple'
    
    def test_batch_insert_analysis(self):
        """Test analysis of batch INSERT statements."""
        sql = """
        INSERT INTO users (name, email) VALUES 
        ('John', 'john@example.com'),
        ('Jane', 'jane@example.com'),
        ('Bob', 'bob@example.com')
        """
        result = self.analyzer.analyze(sql)
        
        assert result['type'] == 'insert'
        assert result['complexity'] == 'intermediate'
        assert 'Consider transaction size for batch operations' in result['suggestions']
    
    def test_dangerous_delete_analysis(self):
        """Test analysis of DELETE without WHERE clause."""
        sql = "DELETE FROM temp_data"
        result = self.analyzer.analyze(sql)
        
        assert result['type'] == 'delete'
        assert result['complexity'] == 'dangerous'
        assert any('WARNING' in suggestion for suggestion in result['suggestions'])
    
    def test_ddl_create_analysis(self):
        """Test analysis of DDL CREATE statements."""
        sql = "CREATE TABLE customers (id INTEGER PRIMARY KEY, name VARCHAR(100))"
        result = self.analyzer.analyze(sql)
        
        assert result['type'] == 'create'
        assert result['category'] == 'ddl'
    
    def test_ddl_drop_analysis(self):
        """Test analysis of dangerous DROP statements."""
        sql = "DROP TABLE old_data"
        result = self.analyzer.analyze(sql)
        
        assert result['type'] == 'drop'
        assert result['complexity'] == 'dangerous'
        assert any('Destructive operation' in suggestion for suggestion in result['suggestions'])
    
    def test_firebird_features_detection(self):
        """Test detection of Firebird-specific features."""
        sql = "SELECT id, name FROM customers WHERE FIRST 10 SKIP 20"
        result = self.analyzer.analyze(sql)
        
        # Should detect as SELECT and provide Firebird-specific suggestions
        assert result['type'] == 'select'
        assert isinstance(result['firebird_features'], list)
    
    def test_optimization_suggestions(self):
        """Test generation of optimization suggestions."""
        sql = "SELECT * FROM large_table WHERE name LIKE '%search%'"
        suggestions = self.analyzer.get_optimization_suggestions(sql)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        assert any('prepared statements' in suggestion.lower() for suggestion in suggestions)
    
    def test_unknown_sql_pattern(self):
        """Test handling of unrecognized SQL patterns."""
        sql = "SHOW TABLES"  # Not a standard Firebird command
        result = self.analyzer.analyze(sql)
        
        assert result['type'] == 'unknown'
        assert result['category'] == 'query'  # Default category
    
    def test_empty_sql_handling(self):
        """Test handling of empty or whitespace SQL."""
        sql = "   \n\t  "
        result = self.analyzer.analyze(sql)
        
        assert result['type'] == 'unknown'
        assert isinstance(result['suggestions'], list)
    
    def test_sql_with_comments(self):
        """Test analysis of SQL with comments."""
        sql = """
        -- This is a comment
        SELECT name, email 
        FROM users /* inline comment */
        WHERE active = 1
        """
        result = self.analyzer.analyze(sql)
        
        assert result['type'] == 'select'
        assert result['category'] == 'query'


if __name__ == '__main__':
    pytest.main([__file__])
