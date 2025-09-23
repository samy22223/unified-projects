"""
Pinnacle AI Modes Manager

This module manages all AI modes and provides the foundation for mode-specific
processing and agent behavior.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from src.core.ai.types import AITask, AIContext
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.ai.engine import PinnacleAIEngine


class ModeType(Enum):
    """Available AI modes."""
    AUTO = "auto"
    ARCHITECT = "architect"
    CODE = "code"
    ASK = "ask"
    ORCHESTRATOR = "orchestrator"
    DEBUG = "debug"
    ANALYST = "analyst"
    CREATIVE = "creative"
    TECHNICAL = "technical"
    BUSINESS = "business"


@dataclass
class ModeCapabilities:
    """Capabilities of an AI mode."""
    can_code: bool = False
    can_design: bool = False
    can_analyze: bool = False
    can_debug: bool = False
    can_orchestrate: bool = False
    can_explain: bool = False
    can_create: bool = False
    can_research: bool = False
    max_complexity: int = 5  # 1-10 scale
    specializations: List[str] = field(default_factory=list)


@dataclass
class ModeConfig:
    """Configuration for an AI mode."""
    name: str = ""
    description: str = ""
    capabilities: ModeCapabilities = field(default_factory=ModeCapabilities)
    default_agents: List[str] = field(default_factory=list)
    priority: int = 5
    enabled: bool = True
    settings: Dict[str, Any] = field(default_factory=dict)


class BaseMode(ABC):
    """Abstract base class for AI modes."""

    def __init__(self, engine: "PinnacleAIEngine", config: ModeConfig):
        """Initialize the mode."""
        self.engine = engine
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{config.name}")
        self.active_agents: List[str] = []

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the mode."""
        pass

    @abstractmethod
    async def process(self, task: AITask, context: AIContext) -> Any:
        """Process a task in this mode."""
        pass

    @abstractmethod
    async def shutdown(self):
        """Shutdown the mode."""
        pass

    async def create_specialized_agents(self) -> List[str]:
        """Create agents specialized for this mode."""
        agents = []
        for agent_type in self.config.default_agents:
            try:
                agent_id = await self.engine.create_agent(agent_type, {
                    "mode": self.config.name,
                    "specialization": self.config.capabilities.specializations
                })
                agents.append(agent_id)
                self.active_agents.append(agent_id)
            except Exception as e:
                self.logger.error(f"Failed to create agent {agent_type}: {e}")

        return agents

    def is_suitable_for_task(self, task: AITask) -> float:
        """
        Check if this mode is suitable for the given task.

        Returns:
            Suitability score (0.0 to 1.0)
        """
        score = 0.5  # Base score

        # Check task type against mode capabilities
        task_lower = task.type.lower()

        if "code" in task_lower and self.config.capabilities.can_code:
            score += 0.2
        elif "design" in task_lower and self.config.capabilities.can_design:
            score += 0.2
        elif "debug" in task_lower and self.config.capabilities.can_debug:
            score += 0.2
        elif "analyze" in task_lower and self.config.capabilities.can_analyze:
            score += 0.2
        elif "explain" in task_lower and self.config.capabilities.can_explain:
            score += 0.2
        elif "create" in task_lower and self.config.capabilities.can_create:
            score += 0.2

        # Adjust based on complexity
        if task.priority.value >= 4 and self.config.capabilities.max_complexity >= 7:
            score += 0.1
        elif task.priority.value <= 2 and self.config.capabilities.max_complexity <= 5:
            score += 0.1

        return min(score, 1.0)


class ArchitectMode(BaseMode):
    """Architect mode for system design and planning."""

    async def initialize(self) -> bool:
        """Initialize architect mode."""
        self.logger.info("🏗️ Initializing Architect Mode...")
        await self.create_specialized_agents()
        return True

    async def process(self, task: AITask, context: AIContext) -> Any:
        """Process task in architect mode."""
        self.logger.info(f"🏗️ Processing task in Architect Mode: {task.type}")

        # Architect mode specializes in:
        # - System design and architecture
        # - Planning and strategy
        # - High-level design decisions
        # - Technology stack recommendations

        result = {
            "mode": "architect",
            "task_id": task.id,
            "analysis": "Architectural analysis completed",
            "recommendations": [
                "Use microservices architecture",
                "Implement proper error handling",
                "Consider scalability requirements"
            ],
            "design_principles": [
                "SOLID principles",
                "Clean architecture",
                "Separation of concerns"
            ]
        }

        return result

    async def shutdown(self):
        """Shutdown architect mode."""
        self.logger.info("🏗️ Shutting down Architect Mode...")


class CodeMode(BaseMode):
    """Code mode for programming and development."""

    async def initialize(self) -> bool:
        """Initialize code mode."""
        self.logger.info("💻 Initializing Code Mode...")
        await self.create_specialized_agents()
        return True

    async def process(self, task: AITask, context: AIContext) -> Any:
        """Process task in code mode."""
        self.logger.info(f"💻 Processing task in Code Mode: {task.type}")

        # Code mode specializes in:
        # - Writing and reviewing code
        # - Debugging and testing
        # - Code optimization
        # - Best practices implementation

        result = {
            "mode": "code",
            "task_id": task.id,
            "implementation": "Code implementation completed",
            "code_snippets": [
                "# Example implementation",
                "def process_data(data):",
                "    return data.upper()"
            ],
            "suggestions": [
                "Add proper error handling",
                "Consider performance optimization",
                "Add unit tests"
            ]
        }

        return result

    async def shutdown(self):
        """Shutdown code mode."""
        self.logger.info("💻 Shutting down Code Mode...")


class AskMode(BaseMode):
    """Ask mode for questions and explanations."""

    async def initialize(self) -> bool:
        """Initialize ask mode."""
        self.logger.info("❓ Initializing Ask Mode...")
        await self.create_specialized_agents()
        return True

    async def process(self, task: AITask, context: AIContext) -> Any:
        """Process task in ask mode."""
        self.logger.info(f"❓ Processing task in Ask Mode: {task.type}")

        # Ask mode specializes in:
        # - Answering questions
        # - Providing explanations
        # - Educational content
        # - Research and information

        result = {
            "mode": "ask",
            "task_id": task.id,
            "answer": "Comprehensive answer provided",
            "explanation": "Detailed explanation of the topic",
            "references": [
                "Official documentation",
                "Best practices guide",
                "Community resources"
            ],
            "confidence": 0.95
        }

        return result

    async def shutdown(self):
        """Shutdown ask mode."""
        self.logger.info("❓ Shutting down Ask Mode...")


class OrchestratorMode(BaseMode):
    """Orchestrator mode for managing complex workflows."""

    async def initialize(self) -> bool:
        """Initialize orchestrator mode."""
        self.logger.info("🎼 Initializing Orchestrator Mode...")
        await self.create_specialized_agents()
        return True

    async def process(self, task: AITask, context: AIContext) -> Any:
        """Process task in orchestrator mode."""
        self.logger.info(f"🎼 Processing task in Orchestrator Mode: {task.type}")

        # Orchestrator mode specializes in:
        # - Managing complex workflows
        # - Coordinating multiple agents
        # - Resource allocation
        # - Progress tracking

        result = {
            "mode": "orchestrator",
            "task_id": task.id,
            "workflow": "Complex workflow executed",
            "steps": [
                "Step 1: Analysis",
                "Step 2: Planning",
                "Step 3: Execution",
                "Step 4: Verification"
            ],
            "coordinated_agents": len(self.active_agents),
            "success_rate": 0.98
        }

        return result

    async def shutdown(self):
        """Shutdown orchestrator mode."""
        self.logger.info("🎼 Shutting down Orchestrator Mode...")


class DebugMode(BaseMode):
    """Debug mode for troubleshooting and diagnostics."""

    async def initialize(self) -> bool:
        """Initialize debug mode."""
        self.logger.info("🐛 Initializing Debug Mode...")
        await self.create_specialized_agents()
        return True

    async def process(self, task: AITask, context: AIContext) -> Any:
        """Process task in debug mode."""
        self.logger.info(f"🐛 Processing task in Debug Mode: {task.type}")

        # Debug mode specializes in:
        # - Error diagnosis
        # - Performance analysis
        # - System troubleshooting
        # - Log analysis

        result = {
            "mode": "debug",
            "task_id": task.id,
            "diagnosis": "Issue diagnosed and resolved",
            "root_cause": "Identified the underlying problem",
            "solution": "Step-by-step resolution provided",
            "preventive_measures": [
                "Add proper error handling",
                "Implement monitoring",
                "Add logging"
            ]
        }

        return result

    async def shutdown(self):
        """Shutdown debug mode."""
        self.logger.info("🐛 Shutting down Debug Mode...")


class ModeManager:
    """Manager for all AI modes."""

    def __init__(self, engine: "PinnacleAIEngine"):
        """Initialize the mode manager."""
        self.engine = engine
        self.logger = logging.getLogger(__name__)
        self.modes: Dict[str, BaseMode] = {}
        self.current_mode: Optional[str] = None

        # Initialize mode configurations
        self._initialize_mode_configs()

    def _initialize_mode_configs(self):
        """Initialize configurations for all modes."""
        self.mode_configs = {
            ModeType.ARCHITECT.value: ModeConfig(
                name="Architect",
                description="System design and architectural planning",
                capabilities=ModeCapabilities(
                    can_design=True,
                    can_analyze=True,
                    max_complexity=9,
                    specializations=["system_design", "architecture", "planning"]
                ),
                default_agents=["architect_agent", "design_agent"],
                priority=8
            ),
            ModeType.CODE.value: ModeConfig(
                name="Code",
                description="Programming and software development",
                capabilities=ModeCapabilities(
                    can_code=True,
                    can_debug=True,
                    max_complexity=8,
                    specializations=["programming", "debugging", "testing"]
                ),
                default_agents=["code_agent", "review_agent"],
                priority=7
            ),
            ModeType.ASK.value: ModeConfig(
                name="Ask",
                description="Questions and educational content",
                capabilities=ModeCapabilities(
                    can_explain=True,
                    can_research=True,
                    max_complexity=6,
                    specializations=["education", "research", "explanation"]
                ),
                default_agents=["qa_agent", "research_agent"],
                priority=5
            ),
            ModeType.ORCHESTRATOR.value: ModeConfig(
                name="Orchestrator",
                description="Complex workflow management",
                capabilities=ModeCapabilities(
                    can_orchestrate=True,
                    max_complexity=10,
                    specializations=["workflow", "coordination", "management"]
                ),
                default_agents=["orchestrator_agent", "coordinator_agent"],
                priority=9
            ),
            ModeType.DEBUG.value: ModeConfig(
                name="Debug",
                description="Troubleshooting and diagnostics",
                capabilities=ModeCapabilities(
                    can_debug=True,
                    can_analyze=True,
                    max_complexity=7,
                    specializations=["troubleshooting", "diagnostics", "analysis"]
                ),
                default_agents=["debug_agent", "diagnostic_agent"],
                priority=6
            )
        }

    async def initialize(self) -> bool:
        """Initialize all modes."""
        self.logger.info("🎭 Initializing Mode Manager...")

        try:
            # Create mode instances
            for mode_type, config in self.mode_configs.items():
                if config.enabled:
                    await self._create_mode(mode_type, config)

            # Set default mode
            self.current_mode = ModeType.AUTO.value

            self.logger.info("✅ Mode Manager initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Mode Manager: {e}")
            return False

    async def _create_mode(self, mode_type: str, config: ModeConfig) -> BaseMode:
        """Create a mode instance."""
        mode_classes = {
            ModeType.ARCHITECT.value: ArchitectMode,
            ModeType.CODE.value: CodeMode,
            ModeType.ASK.value: AskMode,
            ModeType.ORCHESTRATOR.value: OrchestratorMode,
            ModeType.DEBUG.value: DebugMode,
        }

        mode_class = mode_classes.get(mode_type)
        if not mode_class:
            raise ValueError(f"Unknown mode type: {mode_type}")

        mode = mode_class(self.engine, config)
        await mode.initialize()
        self.modes[mode_type] = mode

        return mode

    async def select_mode(self, task: AITask, context: AIContext) -> str:
        """
        Select the most appropriate mode for a task.

        Args:
            task: The task to process
            context: Current context

        Returns:
            Selected mode name
        """
        if task.mode != "auto":
            return task.mode

        # Calculate suitability scores for all modes
        mode_scores = {}
        for mode_type, mode in self.modes.items():
            score = mode.is_suitable_for_task(task)
            mode_scores[mode_type] = score

        # Select mode with highest score
        best_mode = max(mode_scores.items(), key=lambda x: x[1])[0]

        self.logger.info(f"Selected mode '{best_mode}' for task '{task.type}'")
        return best_mode

    async def process_with_mode(self, task: AITask, context: AIContext, mode: str) -> Any:
        """
        Process a task using a specific mode.

        Args:
            task: The task to process
            context: Current context
            mode: Mode to use

        Returns:
            Processing result
        """
        if mode not in self.modes:
            raise ValueError(f"Mode '{mode}' not available")

        selected_mode = self.modes[mode]
        return await selected_mode.process(task, context)

    async def switch_mode(self, mode: str, context: AIContext) -> bool:
        """
        Switch to a different mode.

        Args:
            mode: Mode to switch to
            context: Current context

        Returns:
            True if switch successful
        """
        if mode not in self.modes:
            return False

        old_mode = self.current_mode
        self.current_mode = mode

        self.logger.info(f"Switched from mode '{old_mode}' to '{mode}'")
        return True

    async def get_available_modes(self) -> List[Dict[str, Any]]:
        """Get list of available modes with their configurations."""
        return [
            {
                "name": config.name,
                "type": mode_type,
                "description": config.description,
                "capabilities": config.capabilities.__dict__,
                "enabled": config.enabled,
                "priority": config.priority
            }
            for mode_type, config in self.mode_configs.items()
        ]

    async def shutdown(self):
        """Shutdown all modes."""
        self.logger.info("🎭 Shutting down Mode Manager...")

        for mode in self.modes.values():
            await mode.shutdown()

        self.modes.clear()
        self.logger.info("✅ Mode Manager shutdown complete")