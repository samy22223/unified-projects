"""
CLI Auto-Completion Provider

This module provides auto-completion suggestions for CLI commands,
terminal operations, and system administration commands.
"""

import time
from typing import Dict, List, Any, Optional
from datetime import datetime

from .base import BaseAutoCompletionProvider


class CLIProvider(BaseAutoCompletionProvider):
    """
    Auto-completion provider for CLI-related suggestions.

    This provider offers completions for:
    - System commands (ls, cd, mkdir, etc.)
    - Development tools (git, npm, pip, etc.)
    - Process management (ps, kill, etc.)
    - File operations (cp, mv, rm, etc.)
    - Network commands (curl, wget, etc.)
    """

    def __init__(self):
        """Initialize the CLI provider."""
        super().__init__("cli", priority=55)

        self.set_config("min_query_length", 1)
        self.set_config("max_results", 15)
        self.set_config("include_system_commands", True)
        self.set_config("include_dev_tools", True)
        self.set_config("include_file_ops", True)

        # System commands
        self._system_commands = [
            "ls", "cd", "pwd", "mkdir", "rmdir", "rm", "cp", "mv", "cat",
            "less", "more", "head", "tail", "grep", "find", "chmod", "chown",
            "ps", "top", "htop", "kill", "killall", "df", "du", "free", "uptime"
        ]

        # Development tools
        self._dev_tools = [
            "git", "npm", "pip", "python", "node", "docker", "docker-compose",
            "kubectl", "terraform", "ansible", "make", "gradle", "maven"
        ]

        # File operations
        self._file_operations = [
            "touch", "nano", "vim", "vi", "emacs", "code", "subl", "atom",
            "tar", "gzip", "gunzip", "zip", "unzip", "wget", "curl", "scp", "rsync"
        ]

    async def get_completions(self, query: str, context: str = "",
                            context_data: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get CLI-related auto-completion suggestions."""
        if not self.validate_query(query):
            return []

        start_time = time.time()
        completions = []

        try:
            if self.get_config("include_system_commands"):
                completions.extend(await self._get_system_completions(query, context))

            if self.get_config("include_dev_tools"):
                completions.extend(await self._get_dev_tool_completions(query, context))

            if self.get_config("include_file_ops"):
                completions.extend(await self._get_file_op_completions(query, context))

            completions = self.filter_completions(completions, min_score=0.1)
            completions = self.rank_completions(completions)
            completions = self.limit_completions(completions, self.get_config("max_results"))

            self.update_metrics(True, time.time() - start_time)
            return completions

        except Exception as e:
            self.logger.error(f"Error getting CLI completions: {e}")
            self.update_metrics(False, time.time() - start_time)
            return []

    async def _get_system_completions(self, query: str, context: str) -> List[Dict[str, Any]]:
        """Get completions for system commands."""
        completions = []

        for cmd in self._system_commands:
            if query.lower() in cmd.lower():
                score = self._calculate_similarity(query, cmd)
                completions.append(self.format_completion(
                    cmd,
                    score=score,
                    metadata={
                        "type": "system_command",
                        "category": "cli_system",
                        "description": f"System command: {cmd}"
                    }
                ))

        return completions

    async def _get_dev_tool_completions(self, query: str, context: str) -> List[Dict[str, Any]]:
        """Get completions for development tools."""
        completions = []

        for tool in self._dev_tools:
            if query.lower() in tool.lower():
                score = self._calculate_similarity(query, tool)
                completions.append(self.format_completion(
                    tool,
                    score=score,
                    metadata={
                        "type": "dev_tool",
                        "category": "cli_development",
                        "description": f"Development tool: {tool}"
                    }
                ))

        return completions

    async def _get_file_op_completions(self, query: str, context: str) -> List[Dict[str, Any]]:
        """Get completions for file operations."""
        completions = []

        for op in self._file_operations:
            if query.lower() in op.lower():
                score = self._calculate_similarity(query, op)
                completions.append(self.format_completion(
                    op,
                    score=score,
                    metadata={
                        "type": "file_operation",
                        "category": "cli_file",
                        "description": f"File operation: {op}"
                    }
                ))

        return completions

    def _calculate_similarity(self, query: str, target: str) -> float:
        """Calculate similarity score between query and target string."""
        if not query or not target:
            return 0.0

        query_lower = query.lower()
        target_lower = target.lower()

        if target_lower.startswith(query_lower):
            return 0.9

        if query_lower in target_lower:
            return 0.7

        query_chars = set(query_lower)
        target_chars = set(target_lower)
        overlap = len(query_chars.intersection(target_chars))
        total_chars = len(query_chars.union(target_chars))

        if total_chars > 0:
            char_similarity = overlap / total_chars
            return 0.2 + (char_similarity * 0.3)

        return 0.1

    async def refresh(self):
        """Refresh provider data."""
        await super().refresh()

    async def shutdown(self):
        """Shutdown the provider."""
        await super().shutdown()

    def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        health = super().health_check()
        health["system_commands_count"] = len(self._system_commands)
        health["dev_tools_count"] = len(self._dev_tools)
        health["file_operations_count"] = len(self._file_operations)
        return health</code></edit>
</edit_file>