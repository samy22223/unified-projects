"""
Memory Service for AI agents
Provides persistent memory, context management, and RAG capabilities
"""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from app.core.database import get_mongodb, get_redis, get_chroma
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

class MemoryService:
    """Service for managing agent memory and context"""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.llm_service = LLMService()
        self.short_term_memory = []
        self.max_short_term_items = 50
    
    async def store_memory(self, content: str, metadata: Dict[str, Any] = None) -> str:
        """Store information in long-term memory"""
        try:
            memory_id = f"mem_{self.agent_id}_{datetime.utcnow().timestamp()}"
            
            memory_item = {
                "id": memory_id,
                "agent_id": self.agent_id,
                "content": content,
                "metadata": metadata or {},
                "timestamp": datetime.utcnow().isoformat(),
                "importance": await self._calculate_importance(content)
            }
            
            # Store in MongoDB
            async with get_mongodb() as mongo:
                db = mongo.omnicore
                await db.agent_memories.insert_one(memory_item)
            
            # Store embedding in ChromaDB for semantic search
            embedding = await self.llm_service.embed_text(content)
            if embedding:
                async with get_chroma() as chroma:
                    collection = await chroma.get_or_create_collection(f"agent_{self.agent_id}_memories")
                    await collection.add(
                        documents=[content],
                        embeddings=[embedding],
                        metadatas=[{
                            "memory_id": memory_id,
                            "timestamp": memory_item["timestamp"],
                            "importance": memory_item["importance"],
                            **memory_item["metadata"]
                        }],
                        ids=[memory_id]
                    )
            
            # Add to short-term memory
            self._add_to_short_term(memory_item)
            
            logger.info(f"Stored memory for agent {self.agent_id}: {memory_id}")
            return memory_id
            
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            return ""
    
    async def retrieve_relevant_memories(
        self, 
        query: str, 
        limit: int = 10,
        time_window_days: int = 30
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant memories using semantic search"""
        try:
            # Search in ChromaDB
            async with get_chroma() as chroma:
                collection = await chroma.get_or_create_collection(f"agent_{self.agent_id}_memories")
                results = await collection.query(
                    query_texts=[query],
                    n_results=limit * 2,  # Get more for filtering
                    where={
                        "timestamp": {
                            "$gte": (datetime.utcnow() - timedelta(days=time_window_days)).isoformat()
                        }
                    }
                )
            
            memories = []
            for doc, metadata, distance in zip(
                results['documents'][0], 
                results['metadatas'][0], 
                results['distances'][0]
            ):
                # Get full memory from MongoDB
                memory_id = metadata["memory_id"]
                full_memory = await self._get_memory_by_id(memory_id)
                if full_memory:
                    full_memory["relevance_score"] = 1.0 - distance  # Convert distance to similarity
                    memories.append(full_memory)
            
            # Sort by relevance and recency
            memories.sort(key=lambda x: (x.get("relevance_score", 0), x.get("importance", 0)), reverse=True)
            
            return memories[:limit]
            
        except Exception as e:
            logger.error(f"Failed to retrieve memories: {e}")
            return []
    
    async def get_context_for_task(self, task_description: str) -> List[Dict[str, Any]]:
        """Get relevant context for a task"""
        # Get relevant memories
        memories = await self.retrieve_relevant_memories(task_description, limit=5)
        
        # Add short-term context
        context = self.short_term_memory[-10:]  # Last 10 items
        
        # Combine and deduplicate
        all_context = memories + context
        seen_ids = set()
        unique_context = []
        
        for item in all_context:
            item_id = item.get("id", str(item))
            if item_id not in seen_ids:
                seen_ids.add(item_id)
                unique_context.append(item)
        
        return unique_context[:15]  # Limit total context
    
    async def update_memory_importance(self, memory_id: str, new_importance: float):
        """Update the importance score of a memory"""
        try:
            async with get_mongodb() as mongo:
                db = mongo.omnicore
                await db.agent_memories.update_one(
                    {"id": memory_id},
                    {"$set": {"importance": new_importance}}
                )
            
            logger.info(f"Updated importance for memory {memory_id}")
            
        except Exception as e:
            logger.error(f"Failed to update memory importance: {e}")
    
    async def forget_old_memories(self, days_old: int = 90):
        """Remove memories older than specified days"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            async with get_mongodb() as mongo:
                db = mongo.omnicore
                result = await db.agent_memories.delete_many({
                    "agent_id": self.agent_id,
                    "timestamp": {"$lt": cutoff_date.isoformat()}
                })
            
            logger.info(f"Forgot {result.deleted_count} old memories for agent {self.agent_id}")
            
        except Exception as e:
            logger.error(f"Failed to forget old memories: {e}")
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        try:
            async with get_mongodb() as mongo:
                db = mongo.omnicore
                pipeline = [
                    {"$match": {"agent_id": self.agent_id}},
                    {"$group": {
                        "_id": None,
                        "total_memories": {"$sum": 1},
                        "avg_importance": {"$avg": "$importance"},
                        "oldest_memory": {"$min": "$timestamp"},
                        "newest_memory": {"$max": "$timestamp"}
                    }}
                ]
                
                result = await db.agent_memories.aggregate(pipeline).to_list(1)
                
                if result:
                    return result[0]
                else:
                    return {
                        "total_memories": 0,
                        "avg_importance": 0.0,
                        "oldest_memory": None,
                        "newest_memory": None
                    }
                    
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            return {}
    
    async def _calculate_importance(self, content: str) -> float:
        """Calculate importance score for content"""
        try:
            # Simple heuristic-based importance calculation
            importance = 0.5  # Base importance
            
            # Increase for certain keywords
            important_keywords = [
                "critical", "urgent", "important", "strategy", "decision",
                "error", "failure", "success", "goal", "objective"
            ]
            
            content_lower = content.lower()
            for keyword in important_keywords:
                if keyword in content_lower:
                    importance += 0.1
            
            # Cap at 1.0
            return min(importance, 1.0)
            
        except Exception as e:
            logger.error(f"Failed to calculate importance: {e}")
            return 0.5
    
    async def _get_memory_by_id(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Get memory by ID from MongoDB"""
        try:
            async with get_mongodb() as mongo:
                db = mongo.omnicore
                memory = await db.agent_memories.find_one({"id": memory_id})
                return memory
                
        except Exception as e:
            logger.error(f"Failed to get memory by ID: {e}")
            return None
    
    def _add_to_short_term(self, memory_item: Dict[str, Any]):
        """Add item to short-term memory"""
        self.short_term_memory.append(memory_item)
        
        # Keep only recent items
        if len(self.short_term_memory) > self.max_short_term_items:
            self.short_term_memory = self.short_term_memory[-self.max_short_term_items:]
    
    def get_short_term_context(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent short-term memory items"""
        return self.short_term_memory[-limit:]
