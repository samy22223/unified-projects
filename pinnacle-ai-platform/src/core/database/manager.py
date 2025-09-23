"""
Pinnacle AI Database Manager

This module manages all database operations for the AI platform including
agents, tasks, users, and system data.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from contextlib import asynccontextmanager
import json

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, Float, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from sqlalchemy.sql import text

from src.core.config.settings import settings
from .ecommerce_models import (
    CategoryModel, ProductModel, ProductVariantModel, CartModel, CartItemModel,
    OrderModel, OrderItemModel, ReviewModel, WishlistModel, WishlistItemModel,
    AddressModel, PromotionModel, InventoryTransactionModel
)

Base = declarative_base()


class AgentModel(Base):
    """Database model for AI agents."""
    __tablename__ = "agents"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    type = Column(String, index=True)
    status = Column(String, default="created")
    config = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    task_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    current_tasks = Column(JSON, default=list)
    memory = Column(JSON, default=dict)
    performance_metrics = Column(JSON, default=dict)
    heartbeat = Column(DateTime, nullable=True)


class TaskModel(Base):
    """Database model for AI tasks."""
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, index=True)
    type = Column(String, index=True)
    priority = Column(String, default="normal")
    data = Column(JSON)
    mode = Column(String, default="auto")
    agent_id = Column(String, ForeignKey("agents.id"), nullable=True)
    user_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    deadline = Column(DateTime, nullable=True)
    max_retries = Column(Integer, default=3)
    retry_count = Column(Integer, default=0)
    status = Column(String, default="pending")
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    processing_time = Column(Float, nullable=True)
    completed_at = Column(DateTime, nullable=True)


class UserModel(Base):
    """Database model for users."""
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    full_name = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    preferences = Column(JSON, default=dict)
    last_login = Column(DateTime, nullable=True)


class SessionModel(Base):
    """Database model for user sessions."""
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    metadata = Column(JSON, default=dict)


class ConversationModel(Base):
    """Database model for conversations."""
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    title = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON, default=dict)


class MessageModel(Base):
    """Database model for messages."""
    __tablename__ = "messages"

    id = Column(String, primary_key=True, index=True)
    conversation_id = Column(String, ForeignKey("conversations.id"))
    user_id = Column(String, ForeignKey("users.id"))
    role = Column(String)  # user, assistant, system
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON, default=dict)


class SystemMetricsModel(Base):
    """Database model for system metrics."""
    __tablename__ = "system_metrics"

    id = Column(String, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    metric_type = Column(String, index=True)
    value = Column(Float)
    metadata = Column(JSON, default=dict)


class DatabaseManager:
    """
    Database manager for the Pinnacle AI Platform.

    Handles all database operations including agents, tasks, users,
    conversations, and system metrics.
    """

    def __init__(self):
        """Initialize the database manager."""
        self.logger = logging.getLogger(__name__)
        self.engine = None
        self.SessionLocal = None
        self._initialized = False

    async def initialize(self) -> bool:
        """Initialize database connection and create tables."""
        try:
            self.logger.info("🗄️ Initializing Database Manager...")

            # Create database engine
            database_url = settings.DATABASE_URL
            if database_url.startswith("sqlite"):
                # Use SQLite for development with connection pooling
                self.engine = create_engine(
                    database_url,
                    connect_args={"check_same_thread": False},
                    poolclass=StaticPool,
                    echo=settings.APP_DEBUG
                )
            else:
                # Use PostgreSQL for production
                self.engine = create_engine(
                    database_url,
                    pool_size=20,
                    max_overflow=30,
                    pool_timeout=30,
                    pool_recycle=1800,
                    echo=settings.APP_DEBUG
                )

            # Create session factory
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

            # Create tables
            Base.metadata.create_all(bind=self.engine)

            # Test connection
            async with self.get_session() as session:
                session.execute(text("SELECT 1"))

            self._initialized = True
            self.logger.info("✅ Database Manager initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Database Manager: {e}")
            return False

    @asynccontextmanager
    async def get_session(self):
        """Get database session context manager."""
        if not self._initialized:
            raise RuntimeError("Database manager not initialized")

        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    async def shutdown(self):
        """Shutdown database connections."""
        self.logger.info("🛑 Shutting down Database Manager...")

        if self.engine:
            self.engine.dispose()

        self.logger.info("✅ Database Manager shutdown complete")

    # Agent operations
    async def create_agent(self, agent_data: Dict[str, Any]) -> str:
        """Create a new agent in the database."""
        async with self.get_session() as session:
            agent = AgentModel(**agent_data)
            session.add(agent)
            await session.flush()  # Get the ID without committing
            return agent.id

    async def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent by ID."""
        async with self.get_session() as session:
            agent = session.query(AgentModel).filter(AgentModel.id == agent_id).first()
            return agent.__dict__ if agent else None

    async def update_agent(self, agent_id: str, updates: Dict[str, Any]) -> bool:
        """Update agent information."""
        async with self.get_session() as session:
            agent = session.query(AgentModel).filter(AgentModel.id == agent_id).first()
            if not agent:
                return False

            for key, value in updates.items():
                if hasattr(agent, key):
                    setattr(agent, key, value)

            return True

    async def list_agents(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """List agents with optional filters."""
        async with self.get_session() as session:
            query = session.query(AgentModel)

            if filters:
                if "type" in filters:
                    query = query.filter(AgentModel.type == filters["type"])
                if "status" in filters:
                    query = query.filter(AgentModel.status == filters["status"])
                if "name" in filters:
                    query = query.filter(AgentModel.name.contains(filters["name"]))

            agents = query.all()
            return [agent.__dict__ for agent in agents]

    async def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent."""
        async with self.get_session() as session:
            agent = session.query(AgentModel).filter(AgentModel.id == agent_id).first()
            if not agent:
                return False

            session.delete(agent)
            return True

    # Task operations
    async def create_task(self, task_data: Dict[str, Any]) -> str:
        """Create a new task in the database."""
        async with self.get_session() as session:
            task = TaskModel(**task_data)
            session.add(task)
            await session.flush()
            return task.id

    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task by ID."""
        async with self.get_session() as session:
            task = session.query(TaskModel).filter(TaskModel.id == task_id).first()
            return task.__dict__ if task else None

    async def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """Update task information."""
        async with self.get_session() as session:
            task = session.query(TaskModel).filter(TaskModel.id == task_id).first()
            if not task:
                return False

            for key, value in updates.items():
                if hasattr(task, key):
                    setattr(task, key, value)

            return True

    async def list_tasks(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """List tasks with optional filters."""
        async with self.get_session() as session:
            query = session.query(TaskModel)

            if filters:
                if "status" in filters:
                    query = query.filter(TaskModel.status == filters["status"])
                if "user_id" in filters:
                    query = query.filter(TaskModel.user_id == filters["user_id"])
                if "agent_id" in filters:
                    query = query.filter(TaskModel.agent_id == filters["agent_id"])
                if "type" in filters:
                    query = query.filter(TaskModel.type == filters["type"])

            tasks = query.order_by(TaskModel.created_at.desc()).all()
            return [task.__dict__ for task in tasks]

    # User operations
    async def create_user(self, user_data: Dict[str, Any]) -> str:
        """Create a new user."""
        async with self.get_session() as session:
            user = UserModel(**user_data)
            session.add(user)
            await session.flush()
            return user.id

    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        async with self.get_session() as session:
            user = session.query(UserModel).filter(UserModel.id == user_id).first()
            return user.__dict__ if user else None

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email."""
        async with self.get_session() as session:
            user = session.query(UserModel).filter(UserModel.email == email).first()
            return user.__dict__ if user else None

    async def update_user(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update user information."""
        async with self.get_session() as session:
            user = session.query(UserModel).filter(UserModel.id == user_id).first()
            if not user:
                return False

            for key, value in updates.items():
                if hasattr(user, key):
                    setattr(user, key, value)

            return True

    # Conversation operations
    async def create_conversation(self, conversation_data: Dict[str, Any]) -> str:
        """Create a new conversation."""
        async with self.get_session() as session:
            conversation = ConversationModel(**conversation_data)
            session.add(conversation)
            await session.flush()
            return conversation.id

    async def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation by ID."""
        async with self.get_session() as session:
            conversation = session.query(ConversationModel).filter(
                ConversationModel.id == conversation_id
            ).first()
            return conversation.__dict__ if conversation else None

    async def list_conversations(self, user_id: str) -> List[Dict[str, Any]]:
        """List conversations for a user."""
        async with self.get_session() as session:
            conversations = session.query(ConversationModel).filter(
                ConversationModel.user_id == user_id
            ).order_by(ConversationModel.updated_at.desc()).all()
            return [conv.__dict__ for conv in conversations]

    # Message operations
    async def create_message(self, message_data: Dict[str, Any]) -> str:
        """Create a new message."""
        async with self.get_session() as session:
            message = MessageModel(**message_data)
            session.add(message)
            await session.flush()
            return message.id

    async def get_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get messages for a conversation."""
        async with self.get_session() as session:
            messages = session.query(MessageModel).filter(
                MessageModel.conversation_id == conversation_id
            ).order_by(MessageModel.created_at.asc()).all()
            return [msg.__dict__ for msg in messages]

    # System metrics operations
    async def store_metric(self, metric_type: str, value: float, metadata: Optional[Dict[str, Any]] = None):
        """Store a system metric."""
        async with self.get_session() as session:
            metric = SystemMetricsModel(
                id=f"{metric_type}_{datetime.utcnow().isoformat()}",
                metric_type=metric_type,
                value=value,
                metadata=metadata or {}
            )
            session.add(metric)

    async def get_metrics(self, metric_type: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get metrics for a specific type."""
        async with self.get_session() as session:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            metrics = session.query(SystemMetricsModel).filter(
                SystemMetricsModel.metric_type == metric_type,
                SystemMetricsModel.timestamp >= cutoff_time
            ).order_by(SystemMetricsModel.timestamp.asc()).all()
            return [metric.__dict__ for metric in metrics]

    # Analytics operations
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get overall system statistics."""
        async with self.get_session() as session:
            # Agent stats
            total_agents = session.query(AgentModel).count()
            active_agents = session.query(AgentModel).filter(
                AgentModel.status.in_(["ready", "busy"])
            ).count()

            # Task stats
            total_tasks = session.query(TaskModel).count()
            completed_tasks = session.query(TaskModel).filter(
                TaskModel.status == "completed"
            ).count()
            failed_tasks = session.query(TaskModel).filter(
                TaskModel.status == "failed"
            ).count()

            # User stats
            total_users = session.query(UserModel).count()
            active_users = session.query(UserModel).filter(
                UserModel.is_active == True
            ).count()

            return {
                "agents": {
                    "total": total_agents,
                    "active": active_agents,
                    "inactive": total_agents - active_agents
                },
                "tasks": {
                    "total": total_tasks,
                    "completed": completed_tasks,
                    "failed": failed_tasks,
                    "success_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
                },
                "users": {
                    "total": total_users,
                    "active": active_users
                }
            }

    async def cleanup_old_data(self, days: int = 30):
        """Clean up old data to prevent database bloat."""
        async with self.get_session() as session:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Clean up old completed tasks
            old_tasks = session.query(TaskModel).filter(
                TaskModel.status == "completed",
                TaskModel.created_at < cutoff_date
            ).all()

            for task in old_tasks:
                session.delete(task)

            # Clean up old system metrics
            old_metrics = session.query(SystemMetricsModel).filter(
                SystemMetricsModel.timestamp < cutoff_date
            ).all()

            for metric in old_metrics:
                session.delete(metric)

            self.logger.info(f"Cleaned up {len(old_tasks)} old tasks and {len(old_metrics)} old metrics")</code></edit>
</edit_file>