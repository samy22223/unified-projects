"""
AI Agent Orchestrator - Manages all AI agents in the system
"""

import asyncio
import logging
from typing import Dict, List, Any
from datetime import datetime
from app.core.config import settings
from app.agents.executive.ceo_agent import CEOAgent

logger = logging.getLogger(__name__)

class AgentOrchestrator:
    """Orchestrates all AI agents in the OmniCore system"""
    
    def __init__(self):
        self.agents: Dict[str, Any] = {}
        self.tasks_queue = asyncio.Queue()
        self.running = False
        
    async def start(self):
        """Start the agent orchestrator"""
        logger.info("🚀 Starting Agent Orchestrator...")
        self.running = True
        
        # Initialize core agents
        await self._initialize_agents()
        
        # Start background tasks
        asyncio.create_task(self._process_tasks())
        asyncio.create_task(self._monitor_agents())
        
        logger.info("✅ Agent Orchestrator started")
    
    async def stop(self):
        """Stop the agent orchestrator"""
        logger.info("🛑 Stopping Agent Orchestrator...")
        self.running = False
        
        # Stop all agents
        for agent_id, agent in self.agents.items():
            try:
                await agent.stop()
                logger.info(f"✅ Agent {agent_id} stopped")
            except Exception as e:
                logger.error(f"Error stopping agent {agent_id}: {e}")
        
        logger.info("✅ Agent Orchestrator stopped")
    
    async def _initialize_agents(self):
        """Initialize all AI agents"""
        # TODO: Load agent configurations from database
        # For now, create mock agents
        
        agent_configs = [
            {
                "id": "executive-ceo",
                "name": "CEO Agent",
                "type": "executive",
                "role": "Chief Executive Officer",
                "capabilities": ["strategic_planning", "decision_making", "leadership"]
            },
            {
                "id": "sales-lead",
                "name": "Sales Lead Agent",
                "type": "sales", 
                "role": "Sales Manager",
                "capabilities": ["lead_generation", "customer_management", "sales_forecasting"]
            },
            {
                "id": "marketing-director",
                "name": "Marketing Director Agent",
                "type": "marketing",
                "role": "Marketing Director", 
                "capabilities": ["campaign_management", "brand_strategy", "analytics"]
            }
        ]
        
        for config in agent_configs:
            if config["id"] == "executive-ceo":
                agent = CEOAgent()
            else:
                agent = MockAgent(config)
            self.agents[config["id"]] = agent
            await agent.start()
            logger.info(f"✅ Agent {config['id']} initialized")
    
    async def _process_tasks(self):
        """Process tasks from the queue"""
        while self.running:
            try:
                task = await self.tasks_queue.get()
                await self._execute_task(task)
                self.tasks_queue.task_done()
            except Exception as e:
                logger.error(f"Error processing task: {e}")
                await asyncio.sleep(1)
    
    async def _execute_task(self, task: Dict[str, Any]):
        """Execute a task using appropriate agent"""
        agent_type = task.get("agent_type", "general")
        agent_id = task.get("agent_id")
        
        if agent_id and agent_id in self.agents:
            agent = self.agents[agent_id]
        else:
            # Find agent by type
            agent = None
            for a in self.agents.values():
                if a.type == agent_type:
                    agent = a
                    break
        
        if agent:
            try:
                result = await agent.execute_task(task)
                logger.info(f"Task {task.get('id')} completed by agent {agent.id}")
                return result
            except Exception as e:
                logger.error(f"Task execution failed: {e}")
                raise
        else:
            raise ValueError(f"No agent available for type: {agent_type}")
    
    async def _monitor_agents(self):
        """Monitor agent health and performance"""
        while self.running:
            try:
                for agent_id, agent in self.agents.items():
                    # Check agent health
                    if not await agent.is_healthy():
                        logger.warning(f"Agent {agent_id} is unhealthy, restarting...")
                        await agent.restart()
                
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Error monitoring agents: {e}")
                await asyncio.sleep(5)
    
    async def submit_task(self, task: Dict[str, Any]) -> str:
        """Submit a task to the orchestrator"""
        task_id = f"task_{datetime.utcnow().timestamp()}"
        task["id"] = task_id
        await self.tasks_queue.put(task)
        logger.info(f"Task {task_id} submitted to queue")
        return task_id
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        return {
            agent_id: {
                "name": agent.name,
                "type": agent.type,
                "status": agent.status,
                "last_active": agent.last_active.isoformat() if agent.last_active else None,
                "tasks_completed": agent.tasks_completed
            }
            for agent_id, agent in self.agents.items()
        }

class MockAgent:
    """Mock AI Agent for development"""
    
    def __init__(self, config: Dict[str, Any]):
        self.id = config["id"]
        self.name = config["name"]
        self.type = config["type"]
        self.role = config["role"]
        self.capabilities = config["capabilities"]
        self.status = "stopped"
        self.last_active = None
        self.tasks_completed = 0
    
    async def start(self):
        """Start the agent"""
        self.status = "active"
        self.last_active = datetime.utcnow()
        logger.info(f"Agent {self.id} started")
    
    async def stop(self):
        """Stop the agent"""
        self.status = "stopped"
        logger.info(f"Agent {self.id} stopped")
    
    async def restart(self):
        """Restart the agent"""
        await self.stop()
        await asyncio.sleep(1)
        await self.start()
    
    async def is_healthy(self) -> bool:
        """Check if agent is healthy"""
        return self.status == "active"
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task"""
        self.last_active = datetime.utcnow()
        self.tasks_completed += 1
        
        # Simulate task execution
        await asyncio.sleep(1)
        
        return {
            "task_id": task["id"],
            "status": "completed",
            "result": f"Task completed by {self.name}",
            "agent_id": self.id
        }
