"""
Base Agent Framework for OmniCore AI Platform
All specialized agents inherit from this base class
"""

import asyncio
import logging
import json
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import uuid

from app.core.config import settings
from app.core.database import get_mongodb, get_redis, get_chroma
from app.services.llm_service import LLMService
from app.services.memory_service import MemoryService

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Base class for all AI agents in OmniCore"""
    
    def __init__(self, agent_id: str, name: str, role: str, department: str):
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.department = department
        self.status = "stopped"
        self.last_active = None
        self.tasks_completed = 0
        self.current_task = None
        self.capabilities = []
        self.memory_context = []
        self.llm_service = None
        self.memory_service = None
        
        # Agent-specific configuration
        self.max_concurrent_tasks = 3
        self.task_timeout = settings.agent_timeout
        self.retry_attempts = settings.agent_retry_attempts
        
    async def initialize(self):
        """Initialize agent services and connections"""
        try:
            # Initialize LLM service
            self.llm_service = LLMService()
            
            # Initialize memory service
            self.memory_service = MemoryService(self.agent_id)
            
            # Load agent state from database
            await self._load_state()
            
            logger.info(f"✅ Agent {self.name} initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize agent {self.name}: {e}")
            raise
    
    async def start(self):
        """Start the agent"""
        if self.status != "stopped":
            return
            
        try:
            await self.initialize()
            self.status = "active"
            self.last_active = datetime.utcnow()
            
            # Start background tasks
            asyncio.create_task(self._health_check_loop())
            asyncio.create_task(self._maintenance_loop())
            
            logger.info(f"🚀 Agent {self.name} started")
            
        except Exception as e:
            logger.error(f"Failed to start agent {self.name}: {e}")
            self.status = "error"
            raise
    
    async def stop(self):
        """Stop the agent"""
        if self.status == "stopped":
            return
            
        try:
            self.status = "stopped"
            
            # Save agent state
            await self._save_state()
            
            logger.info(f"🛑 Agent {self.name} stopped")
            
        except Exception as e:
            logger.error(f"Error stopping agent {self.name}: {e}")
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task with error handling and retries"""
        task_id = task.get("id", str(uuid.uuid4()))
        self.current_task = task
        
        try:
            # Update activity
            self.last_active = datetime.utcnow()
            
            # Execute with retries
            for attempt in range(self.retry_attempts + 1):
                try:
                    result = await self._execute_task_logic(task)
                    
                    # Update metrics
                    self.tasks_completed += 1
                    
                    # Store in memory
                    await self._store_task_memory(task, result)
                    
                    return {
                        "task_id": task_id,
                        "status": "completed",
                        "result": result,
                        "agent_id": self.agent_id,
                        "completed_at": datetime.utcnow().isoformat()
                    }
                    
                except Exception as e:
                    logger.warning(f"Task attempt {attempt + 1} failed for {self.name}: {e}")
                    if attempt == self.retry_attempts:
                        raise
                    await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
            
        except Exception as e:
            logger.error(f"Task execution failed for {self.name}: {e}")
            return {
                "task_id": task_id,
                "status": "failed",
                "error": str(e),
                "agent_id": self.agent_id,
                "failed_at": datetime.utcnow().isoformat()
            }
        finally:
            self.current_task = None
    
    @abstractmethod
    async def _execute_task_logic(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Implement specific task execution logic in subclasses"""
        pass
    
    async def communicate(self, target_agent_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Send message to another agent"""
        try:
            async with get_redis() as redis:
                channel = f"agent:{target_agent_id}:messages"
                await redis.publish(channel, json.dumps({
                    "from": self.agent_id,
                    "message": message,
                    "timestamp": datetime.utcnow().isoformat()
                }))
                
            logger.info(f"Message sent from {self.name} to {target_agent_id}")
            return {"status": "sent"}
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def receive_messages(self) -> List[Dict[str, Any]]:
        """Receive pending messages"""
        try:
            async with get_redis() as redis:
                channel = f"agent:{self.agent_id}:messages"
                # Note: In production, use proper pub/sub handling
                return []
                
        except Exception as e:
            logger.error(f"Failed to receive messages: {e}")
            return []
    
    async def learn_from_experience(self, task: Dict[str, Any], result: Dict[str, Any]):
        """Learn from task execution for continuous improvement"""
        try:
            # Store experience in ChromaDB for RAG
            experience = {
                "task": task,
                "result": result,
                "agent_id": self.agent_id,
                "timestamp": datetime.utcnow().isoformat(),
                "success": result.get("status") == "completed"
            }
            
            async with get_chroma() as chroma:
                collection = await chroma.get_or_create_collection(f"agent_{self.agent_id}_experiences")
                await collection.add(
                    documents=[json.dumps(experience)],
                    metadatas=[{"type": "experience", "timestamp": experience["timestamp"]}],
                    ids=[f"exp_{datetime.utcnow().timestamp()}"]
                )
                
        except Exception as e:
            logger.error(f"Failed to learn from experience: {e}")
    
    async def get_similar_experiences(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieve similar past experiences using semantic search"""
        try:
            async with get_chroma() as chroma:
                collection = await chroma.get_or_create_collection(f"agent_{self.agent_id}_experiences")
                results = await collection.query(
                    query_texts=[query],
                    n_results=limit
                )
                
                experiences = []
                for doc, metadata in zip(results['documents'][0], results['metadatas'][0]):
                    experiences.append(json.loads(doc))
                    
                return experiences
                
        except Exception as e:
            logger.error(f"Failed to retrieve experiences: {e}")
            return []
    
    async def _health_check_loop(self):
        """Periodic health check"""
        while self.status == "active":
            try:
                await self._perform_health_check()
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Health check failed for {self.name}: {e}")
                await asyncio.sleep(5)
    
    async def _maintenance_loop(self):
        """Periodic maintenance tasks"""
        while self.status == "active":
            try:
                await self._perform_maintenance()
                await asyncio.sleep(300)  # Maintenance every 5 minutes
            except Exception as e:
                logger.error(f"Maintenance failed for {self.name}: {e}")
                await asyncio.sleep(60)
    
    async def _perform_health_check(self):
        """Implement health checks in subclasses"""
        # Basic health check - override in subclasses for specific checks
        pass
    
    async def _perform_maintenance(self):
        """Implement maintenance tasks in subclasses"""
        # Clean up old memories, optimize performance, etc.
        pass
    
    async def _load_state(self):
        """Load agent state from database"""
        try:
            async with get_mongodb() as mongo:
                db = mongo.omnicore
                state = await db.agent_states.find_one({"agent_id": self.agent_id})
                
                if state:
                    self.tasks_completed = state.get("tasks_completed", 0)
                    self.capabilities = state.get("capabilities", [])
                    logger.info(f"Loaded state for agent {self.name}")
                    
        except Exception as e:
            logger.warning(f"Failed to load state for {self.name}: {e}")
    
    async def _save_state(self):
        """Save agent state to database"""
        try:
            async with get_mongodb() as mongo:
                db = mongo.omnicore
                await db.agent_states.update_one(
                    {"agent_id": self.agent_id},
                    {
                        "$set": {
                            "name": self.name,
                            "role": self.role,
                            "department": self.department,
                            "tasks_completed": self.tasks_completed,
                            "capabilities": self.capabilities,
                            "last_updated": datetime.utcnow()
                        }
                    },
                    upsert=True
                )
                
        except Exception as e:
            logger.error(f"Failed to save state for {self.name}: {e}")
    
    async def _store_task_memory(self, task: Dict[str, Any], result: Dict[str, Any]):
        """Store task execution in memory"""
        memory_item = {
            "task": task,
            "result": result,
            "timestamp": datetime.utcnow().isoformat(),
            "agent_id": self.agent_id
        }
        
        self.memory_context.append(memory_item)
        
        # Keep only recent memories
        if len(self.memory_context) > 100:
            self.memory_context = self.memory_context[-100:]
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "role": self.role,
            "department": self.department,
            "status": self.status,
            "last_active": self.last_active.isoformat() if self.last_active else None,
            "tasks_completed": self.tasks_completed,
            "current_task": self.current_task.get("id") if self.current_task else None,
            "capabilities": self.capabilities
        }
