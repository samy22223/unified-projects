"""
Auto-Completion Context Management

This module provides context management for auto-completion requests,
handling user sessions, application state, and contextual information.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field


@dataclass
class UserContext:
    """User-specific context information."""
    user_id: str
    session_id: str
    preferences: Dict[str, Any] = field(default_factory=dict)
    history: List[str] = field(default_factory=list)
    current_application: Optional[str] = None
    current_task: Optional[str] = None
    last_activity: datetime = field(default_factory=datetime.utcnow)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ApplicationContext:
    """Application-specific context information."""
    app_name: str
    app_type: str
    current_file: Optional[str] = None
    current_directory: Optional[str] = None
    open_files: List[str] = field(default_factory=list)
    recent_commands: List[str] = field(default_factory=list)
    environment: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class AutoCompletionContext:
    """
    Context management system for auto-completion.

    This class manages:
    - User sessions and preferences
    - Application state and context
    - Context-aware provider selection
    - Context history and learning
    """

    def __init__(self, max_contexts: int = 10000, context_ttl: int = 3600):
        """
        Initialize the context manager.

        Args:
            max_contexts: Maximum number of contexts to store
            context_ttl: Time to live for contexts in seconds
        """
        self.logger = logging.getLogger(__name__)

        # Context storage
        self.user_contexts: Dict[str, UserContext] = {}
        self.app_contexts: Dict[str, ApplicationContext] = {}
        self.session_contexts: Dict[str, Dict[str, Any]] = {}

        # Configuration
        self.max_contexts = max_contexts
        self.context_ttl = context_ttl

        # Context learning
        self.context_patterns: Dict[str, List[str]] = {}
        self.provider_preferences: Dict[str, Dict[str, float]] = {}

        # Cleanup task
        self.cleanup_task: Optional[asyncio.Task] = None
        self._start_cleanup_task()

        self.logger.info("AutoCompletionContext initialized")

    def _start_cleanup_task(self):
        """Start the background cleanup task."""
        self.cleanup_task = asyncio.create_task(self._cleanup_expired_contexts())

    async def _cleanup_expired_contexts(self):
        """Background task to cleanup expired contexts."""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes

                now = datetime.utcnow()
                expired_threshold = now - timedelta(seconds=self.context_ttl)

                # Cleanup user contexts
                expired_users = [
                    user_id for user_id, context in self.user_contexts.items()
                    if context.last_activity < expired_threshold
                ]

                for user_id in expired_users:
                    del self.user_contexts[user_id]

                # Cleanup application contexts
                expired_apps = [
                    app_name for app_name, context in self.app_contexts.items()
                    if context.metadata.get("last_updated", datetime.min) < expired_threshold
                ]

                for app_name in expired_apps:
                    del self.app_contexts[app_name]

                # Cleanup session contexts
                expired_sessions = [
                    session_id for session_id, context in self.session_contexts.items()
                    if context.get("last_activity", datetime.min) < expired_threshold
                ]

                for session_id in expired_sessions:
                    del self.session_contexts[session_id]

                if expired_users or expired_apps or expired_sessions:
                    self.logger.debug(
                        f"Cleaned up {len(expired_users)} users, "
                        f"{len(expired_apps)} apps, {len(expired_sessions)} sessions"
                    )

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in context cleanup: {e}")

    async def get_context(self, user_id: Optional[str] = None,
                         session_id: Optional[str] = None,
                         app_context: Optional[str] = None) -> Dict[str, Any]:
        """
        Get context information for a request.

        Args:
            user_id: User identifier
            session_id: Session identifier
            app_context: Application context name

        Returns:
            Dictionary containing relevant context information
        """
        context = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "session_id": session_id,
            "app_context": app_context
        }

        # Add user context
        if user_id and user_id in self.user_contexts:
            user_context = self.user_contexts[user_id]
            context["user_preferences"] = user_context.preferences
            context["user_history"] = user_context.history[-10:]  # Last 10 items
            context["current_application"] = user_context.current_application
            context["current_task"] = user_context.current_task

        # Add application context
        if app_context and app_context in self.app_contexts:
            app_context_data = self.app_contexts[app_context]
            context["app_type"] = app_context_data.app_type
            context["current_file"] = app_context_data.current_file
            context["current_directory"] = app_context_data.current_directory
            context["open_files"] = app_context_data.open_files
            context["recent_commands"] = app_context_data.recent_commands[-5:]
            context["environment"] = app_context_data.environment

        # Add session context
        if session_id and session_id in self.session_contexts:
            session_data = self.session_contexts[session_id]
            context["session_data"] = session_data

        # Add learned patterns
        if user_id:
            context["learned_patterns"] = self.context_patterns.get(user_id, [])

        # Add provider preferences
        if user_id:
            context["provider_preferences"] = self.provider_preferences.get(user_id, {})

        return context

    async def update_user_context(self, user_id: str, session_id: str,
                                updates: Dict[str, Any]):
        """
        Update user context information.

        Args:
            user_id: User identifier
            session_id: Session identifier
            updates: Context updates to apply
        """
        # Get or create user context
        if user_id not in self.user_contexts:
            self.user_contexts[user_id] = UserContext(
                user_id=user_id,
                session_id=session_id
            )

        user_context = self.user_contexts[user_id]

        # Apply updates
        for key, value in updates.items():
            if hasattr(user_context, key):
                setattr(user_context, key, value)
            else:
                # Store in preferences if not a direct attribute
                user_context.preferences[key] = value

        # Update activity timestamp
        user_context.last_activity = datetime.utcnow()

        # Maintain history
        if "current_query" in updates:
            user_context.history.append(updates["current_query"])
            # Keep only last 100 items
            if len(user_context.history) > 100:
                user_context.history = user_context.history[-100:]

        # Learn from context
        await self._learn_from_context(user_id, updates)

    async def update_application_context(self, app_name: str, updates: Dict[str, Any]):
        """
        Update application context information.

        Args:
            app_name: Application name
            updates: Context updates to apply
        """
        # Get or create application context
        if app_name not in self.app_contexts:
            self.app_contexts[app_name] = ApplicationContext(app_name=app_name, app_type="unknown")

        app_context = self.app_contexts[app_name]

        # Apply updates
        for key, value in updates.items():
            if hasattr(app_context, key):
                if key == "recent_commands" and isinstance(value, str):
                    app_context.recent_commands.append(value)
                    # Keep only last 20 commands
                    if len(app_context.recent_commands) > 20:
                        app_context.recent_commands = app_context.recent_commands[-20:]
                else:
                    setattr(app_context, key, value)
            else:
                app_context.metadata[key] = value

        # Update metadata timestamp
        app_context.metadata["last_updated"] = datetime.utcnow()

    async def update_session_context(self, session_id: str, updates: Dict[str, Any]):
        """
        Update session context information.

        Args:
            session_id: Session identifier
            updates: Context updates to apply
        """
        if session_id not in self.session_contexts:
            self.session_contexts[session_id] = {}

        session_context = self.session_contexts[session_id]

        # Apply updates
        session_context.update(updates)
        session_context["last_activity"] = datetime.utcnow()

    async def _learn_from_context(self, user_id: str, context: Dict[str, Any]):
        """
        Learn patterns from user context for better suggestions.

        Args:
            user_id: User identifier
            context: Context information to learn from
        """
        if user_id not in self.context_patterns:
            self.context_patterns[user_id] = []

        # Learn application preferences
        if "current_application" in context:
            app = context["current_application"]
            if app and app not in self.context_patterns[user_id]:
                self.context_patterns[user_id].append(app)

        # Learn provider preferences based on usage
        if "provider_used" in context:
            provider = context["provider_used"]
            if provider and user_id in self.provider_preferences:
                if provider not in self.provider_preferences[user_id]:
                    self.provider_preferences[user_id][provider] = 0.5
                else:
                    # Increase preference score
                    self.provider_preferences[user_id][provider] = min(
                        1.0,
                        self.provider_preferences[user_id][provider] + 0.1
                    )

    async def get_provider_preferences(self, user_id: str) -> Dict[str, float]:
        """
        Get provider preferences for a user.

        Args:
            user_id: User identifier

        Returns:
            Dictionary of provider preferences
        """
        return self.provider_preferences.get(user_id, {})

    async def set_provider_preference(self, user_id: str, provider: str, score: float):
        """
        Set provider preference score for a user.

        Args:
            user_id: User identifier
            provider: Provider name
            score: Preference score (0.0 to 1.0)
        """
        if user_id not in self.provider_preferences:
            self.provider_preferences[user_id] = {}

        self.provider_preferences[user_id][provider] = max(0.0, min(1.0, score))

    async def get_context_suggestions(self, user_id: str, query: str) -> List[str]:
        """
        Get context-aware suggestions based on user history and patterns.

        Args:
            user_id: User identifier
            query: Current query

        Returns:
            List of context-aware suggestions
        """
        suggestions = []

        # Get user context
        if user_id in self.user_contexts:
            user_context = self.user_contexts[user_id]

            # Suggest from history
            for item in user_context.history:
                if query.lower() in item.lower() and item != query:
                    suggestions.append(item)

            # Suggest based on current application
            if user_context.current_application:
                suggestions.append(f"{query} {user_context.current_application}")

        # Limit and deduplicate suggestions
        suggestions = list(set(suggestions))[:5]

        return suggestions

    async def get_application_info(self, app_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific application context.

        Args:
            app_name: Application name

        Returns:
            Application context information
        """
        if app_name in self.app_contexts:
            app_context = self.app_contexts[app_name]
            return {
                "app_name": app_context.app_name,
                "app_type": app_context.app_type,
                "current_file": app_context.current_file,
                "current_directory": app_context.current_directory,
                "open_files": app_context.open_files,
                "recent_commands": app_context.recent_commands,
                "environment": app_context.environment,
                "metadata": app_context.metadata
            }
        return None

    async def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific user context.

        Args:
            user_id: User identifier

        Returns:
            User context information
        """
        if user_id in self.user_contexts:
            user_context = self.user_contexts[user_id]
            return {
                "user_id": user_context.user_id,
                "session_id": user_context.session_id,
                "preferences": user_context.preferences,
                "current_application": user_context.current_application,
                "current_task": user_context.current_task,
                "last_activity": user_context.last_activity.isoformat(),
                "history_count": len(user_context.history)
            }
        return None

    async def clear_user_context(self, user_id: str):
        """Clear all context for a specific user."""
        if user_id in self.user_contexts:
            del self.user_contexts[user_id]

        if user_id in self.context_patterns:
            del self.context_patterns[user_id]

        if user_id in self.provider_preferences:
            del self.provider_preferences[user_id]

        self.logger.info(f"Cleared context for user: {user_id}")

    async def clear_application_context(self, app_name: str):
        """Clear context for a specific application."""
        if app_name in self.app_contexts:
            del self.app_contexts[app_name]
            self.logger.info(f"Cleared context for application: {app_name}")

    async def get_stats(self) -> Dict[str, Any]:
        """Get context management statistics."""
        return {
            "user_contexts": len(self.user_contexts),
            "app_contexts": len(self.app_contexts),
            "session_contexts": len(self.session_contexts),
            "learned_patterns": sum(len(patterns) for patterns in self.context_patterns.values()),
            "provider_preferences": sum(len(prefs) for prefs in self.provider_preferences.values()),
            "timestamp": datetime.utcnow().isoformat()
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the context system."""
        return {
            "status": "healthy",
            "user_contexts_count": len(self.user_contexts),
            "app_contexts_count": len(self.app_contexts),
            "session_contexts_count": len(self.session_contexts),
            "cleanup_task_running": self.cleanup_task is not None and not self.cleanup_task.done(),
            "stats": await self.get_stats()
        }

    async def shutdown(self):
        """Shutdown the context management system."""
        self.logger.info("Shutting down AutoCompletionContext...")

        # Cancel cleanup task
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass

        # Clear all contexts
        self.user_contexts.clear()
        self.app_contexts.clear()
        self.session_contexts.clear()
        self.context_patterns.clear()
        self.provider_preferences.clear()

        self.logger.info("AutoCompletionContext shutdown complete")
