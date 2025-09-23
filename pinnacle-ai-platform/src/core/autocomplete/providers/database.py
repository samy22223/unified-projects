"""
Database Auto-Completion Provider

This module provides auto-completion suggestions for database operations,
SQL queries, table names, and database management commands.
"""

import re
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

from .base import BaseAutoCompletionProvider
from src.core.database.manager import DatabaseManager


class DatabaseProvider(BaseAutoCompletionProvider):
    """
    Auto-completion provider for database-related suggestions.

    This provider offers completions for:
    - SQL keywords and commands
    - Database table and column names
    - Database management operations
    - Query optimization suggestions
    - Database connection commands
    """

    def __init__(self):
        """Initialize the Database provider."""
        super().__init__("database", priority=65)

        # Database-specific configuration
        self.set_config("min_query_length", 2)
        self.set_config("max_results", 15)
        self.set_config("include_sql_keywords", True)
        self.set_config("include_table_names", True)
        self.set_config("include_column_names", True)
        self.set_config("include_db_operations", True)

        # SQL keywords by category
        self._sql_keywords = {
            "ddl": ["CREATE", "ALTER", "DROP", "TRUNCATE", "COMMENT"],
            "dml": ["SELECT", "INSERT", "UPDATE", "DELETE", "MERGE"],
            "dcl": ["GRANT", "REVOKE", "DENY"],
            "tcl": ["COMMIT", "ROLLBACK", "SAVEPOINT", "SET TRANSACTION"],
            "query": ["FROM", "WHERE", "JOIN", "INNER JOIN", "LEFT JOIN", "RIGHT JOIN",
                     "FULL JOIN", "ON", "GROUP BY", "HAVING", "ORDER BY", "LIMIT", "OFFSET"],
            "functions": ["COUNT", "SUM", "AVG", "MIN", "MAX", "DISTINCT", "AS", "LIKE",
                         "IN", "NOT IN", "BETWEEN", "IS NULL", "IS NOT NULL", "EXISTS"],
            "operators": ["AND", "OR", "NOT", "UNION", "INTERSECT", "EXCEPT"]
        }

        # Common table names (can be expanded based on actual schema)
        self._common_tables = [
            "users", "agents", "tasks", "products", "categories", "orders",
            "order_items", "customers", "reviews", "sessions", "logs",
            "configurations", "permissions", "roles", "audit_logs"
        ]

        # Common column patterns
        self._common_columns = [
            "id", "name", "email", "created_at", "updated_at", "status",
            "type", "description", "title", "content", "price", "quantity",
            "user_id", "agent_id", "task_id", "product_id", "category_id"
        ]

        # Database operations
        self._db_operations = [
            "db connect", "db disconnect", "db status", "db backup",
            "db restore", "db migrate", "db optimize", "db repair",
            "db analyze", "db vacuum", "db reindex", "db flush"
        ]

    async def get_completions(self, query: str, context: str = "",
                            context_data: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Get database-related auto-completion suggestions.

        Args:
            query: The partial input to complete
            context: Additional context information
            context_data: Structured context data

        Returns:
            List of completion suggestions
        """
        if not self.validate_query(query):
            return []

        start_time = time.time()
        completions = []

        try:
            # Get different types of completions
            if self.get_config("include_sql_keywords"):
                completions.extend(await self._get_sql_keyword_completions(query, context))

            if self.get_config("include_table_names"):
                completions.extend(await self._get_table_completions(query, context))

            if self.get_config("include_column_names"):
                completions.extend(await self._get_column_completions(query, context))

            if self.get_config("include_db_operations"):
                completions.extend(await self._get_db_operation_completions(query, context))

            # Filter and rank completions
            completions = self.filter_completions(completions, min_score=0.1)
            completions = self.rank_completions(completions)
            completions = self.limit_completions(completions, self.get_config("max_results"))

            # Update metrics
            self.update_metrics(True, time.time() - start_time)

            return completions

        except Exception as e:
            self.logger.error(f"Error getting database completions: {e}")
            self.update_metrics(False, time.time() - start_time)
            return []

    async def _get_sql_keyword_completions(self, query: str, context: str) -> List[Dict[str, Any]]:
        """Get completions for SQL keywords."""
        completions = []

        query_upper = query.upper()

        for category, keywords in self._sql_keywords.items():
            for keyword in keywords:
                if query_upper in keyword:
                    score = self._calculate_similarity(query_upper, keyword)
                    completions.append(self.format_completion(
                        keyword,
                        score=score,
                        metadata={
                            "type": "sql_keyword",
                            "category": category,
                            "description": f"SQL {category.replace('_', ' ').title()}: {keyword}"
                        }
                    ))

        return completions

    async def _get_table_completions(self, query: str, context: str) -> List[Dict[str, Any]]:
        """Get completions for table names."""
        completions = []

        for table in self._common_tables:
            if query.lower() in table.lower():
                score = self._calculate_similarity(query, table)
                completions.append(self.format_completion(
                    table,
                    score=score,
                    metadata={
                        "type": "table_name",
                        "category": "database_object",
                        "description": f"Database table: {table}"
                    }
                ))

        return completions

    async def _get_column_completions(self, query: str, context: str) -> List[Dict[str, Any]]:
        """Get completions for column names."""
        completions = []

        for column in self._common_columns:
            if query.lower() in column.lower():
                score = self._calculate_similarity(query, column)
                completions.append(self.format_completion(
                    column,
                    score=score,
                    metadata={
                        "type": "column_name",
                        "category": "database_object",
                        "description": f"Database column: {column}"
                    }
                ))

        return completions

    async def _get_db_operation_completions(self, query: str, context: str) -> List[Dict[str, Any]]:
        """Get completions for database operations."""
        completions = []

        for operation in self._db_operations:
            if query.lower() in operation.lower():
                score = self._calculate_similarity(query, operation)
                completions.append(self.format_completion(
                    operation,
                    score=score,
                    metadata={
                        "type": "db_operation",
                        "category": "database_management",
                        "description": f"Database operation: {operation}"
                    }
                ))

        return completions

    def _calculate_similarity(self, query: str, target: str) -> float:
        """
        Calculate similarity score between query and target string.

        Args:
            query: The search query
            target: The target string to compare against

        Returns:
            Similarity score between 0.0 and 1.0
        """
        if not query or not target:
            return 0.0

        query_lower = query.lower()
        target_lower = target.lower()

        # Exact prefix match gets highest score
        if target_lower.startswith(query_lower):
            return 0.9

        # Contains query as substring
        if query_lower in target_lower:
            return 0.7

        # Word boundary matches
        query_words = set(query_lower.split())
        target_words = set(target_lower.split())
        if query_words.intersection(target_words):
            return 0.6

        # Character overlap
        query_chars = set(query_lower)
        target_chars = set(target_lower)
        overlap = len(query_chars.intersection(target_chars))
        total_chars = len(query_chars.union(target_chars))

        if total_chars > 0:
            char_similarity = overlap / total_chars
            return 0.2 + (char_similarity * 0.3)  # 0.2 to 0.5 range

        return 0.1  # Minimum score

    async def refresh(self):
        """Refresh provider data."""
        # Could refresh table/column information from database schema
        await super().refresh()

    async def shutdown(self):
        """Shutdown the provider."""
        await super().shutdown()

    def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        health = super().health_check()

        # Add database-specific health information
        health["sql_keywords_count"] = sum(len(keywords) for keywords in self._sql_keywords.values())
        health["tables_count"] = len(self._common_tables)
        health["columns_count"] = len(self._common_columns)
        health["db_operations_count"] = len(self._db_operations)

        return health</code></edit>
</edit_file>