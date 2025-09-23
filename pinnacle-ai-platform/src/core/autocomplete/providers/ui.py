"""
UI Auto-Completion Provider

This module provides auto-completion suggestions for UI elements,
CSS properties, HTML tags, and frontend-related commands.
"""

import time
from typing import Dict, List, Any, Optional
from datetime import datetime

from .base import BaseAutoCompletionProvider


class UIProvider(BaseAutoCompletionProvider):
    """
    Auto-completion provider for UI-related suggestions.

    This provider offers completions for:
    - HTML tags and attributes
    - CSS properties and values
    - UI component names
    - Frontend framework commands
    - UI testing commands
    """

    def __init__(self):
        """Initialize the UI provider."""
        super().__init__("ui", priority=60)

        self.set_config("min_query_length", 1)
        self.set_config("max_results", 15)
        self.set_config("include_html_tags", True)
        self.set_config("include_css_properties", True)
        self.set_config("include_ui_components", True)

        # HTML tags
        self._html_tags = [
            "div", "span", "p", "h1", "h2", "h3", "h4", "h5", "h6",
            "a", "img", "button", "input", "form", "label", "select",
            "option", "textarea", "ul", "ol", "li", "table", "tr", "td", "th",
            "nav", "header", "footer", "main", "section", "article", "aside"
        ]

        # CSS properties
        self._css_properties = [
            "color", "background", "background-color", "font-size", "font-family",
            "margin", "padding", "border", "width", "height", "display", "position",
            "flex", "grid", "align-items", "justify-content", "text-align",
            "line-height", "letter-spacing", "text-decoration", "opacity"
        ]

        # UI components
        self._ui_components = [
            "button", "card", "modal", "dropdown", "navbar", "sidebar",
            "tab", "accordion", "carousel", "tooltip", "popover", "alert",
            "badge", "progress", "spinner", "pagination", "breadcrumb"
        ]

    async def get_completions(self, query: str, context: str = "",
                            context_data: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get UI-related auto-completion suggestions."""
        if not self.validate_query(query):
            return []

        start_time = time.time()
        completions = []

        try:
            if self.get_config("include_html_tags"):
                completions.extend(await self._get_html_completions(query, context))

            if self.get_config("include_css_properties"):
                completions.extend(await self._get_css_completions(query, context))

            if self.get_config("include_ui_components"):
                completions.extend(await self._get_component_completions(query, context))

            completions = self.filter_completions(completions, min_score=0.1)
            completions = self.rank_completions(completions)
            completions = self.limit_completions(completions, self.get_config("max_results"))

            self.update_metrics(True, time.time() - start_time)
            return completions

        except Exception as e:
            self.logger.error(f"Error getting UI completions: {e}")
            self.update_metrics(False, time.time() - start_time)
            return []

    async def _get_html_completions(self, query: str, context: str) -> List[Dict[str, Any]]:
        """Get completions for HTML tags."""
        completions = []

        for tag in self._html_tags:
            if query.lower() in tag.lower():
                score = self._calculate_similarity(query, tag)
                completions.append(self.format_completion(
                    tag,
                    score=score,
                    metadata={
                        "type": "html_tag",
                        "category": "ui_element",
                        "description": f"HTML tag: <{tag}>"
                    }
                ))

        return completions

    async def _get_css_completions(self, query: str, context: str) -> List[Dict[str, Any]]:
        """Get completions for CSS properties."""
        completions = []

        for prop in self._css_properties:
            if query.lower() in prop.lower():
                score = self._calculate_similarity(query, prop)
                completions.append(self.format_completion(
                    prop,
                    score=score,
                    metadata={
                        "type": "css_property",
                        "category": "ui_style",
                        "description": f"CSS property: {prop}"
                    }
                ))

        return completions

    async def _get_component_completions(self, query: str, context: str) -> List[Dict[str, Any]]:
        """Get completions for UI components."""
        completions = []

        for component in self._ui_components:
            if query.lower() in component.lower():
                score = self._calculate_similarity(query, component)
                completions.append(self.format_completion(
                    component,
                    score=score,
                    metadata={
                        "type": "ui_component",
                        "category": "ui_element",
                        "description": f"UI component: {component}"
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
        health["html_tags_count"] = len(self._html_tags)
        health["css_properties_count"] = len(self._css_properties)
        health["ui_components_count"] = len(self._ui_components)
        return health</code></edit>
</edit_file>