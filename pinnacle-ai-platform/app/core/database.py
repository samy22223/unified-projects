"""
Database initialization and connection management
"""

import logging
from motor.motor_asyncio import AsyncIOMotorClient
from neo4j import AsyncGraphDatabase
import asyncpg
import redis.asyncio as redis
import chromadb
from contextlib import asynccontextmanager

from app.core.config import settings

logger = logging.getLogger(__name__)

# Global database clients
mongodb_client = None
neo4j_driver = None
postgres_pool = None
redis_client = None
chroma_client = None

async def init_databases():
    """Initialize all database connections"""
    global mongodb_client, neo4j_driver, postgres_pool, redis_client, chroma_client
    
    try:
        # MongoDB
        logger.info("Connecting to MongoDB...")
        mongodb_client = AsyncIOMotorClient(settings.mongodb_url)
        await mongodb_client.admin.command('ping')
        logger.info("✅ MongoDB connected")
        
        # PostgreSQL
        logger.info("Connecting to PostgreSQL...")
        postgres_pool = await asyncpg.create_pool(settings.database_url)
        async with postgres_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        logger.info("✅ PostgreSQL connected")
        
        # Redis
        logger.info("Connecting to Redis...")
        redis_client = redis.from_url(settings.redis_url)
        await redis_client.ping()
        logger.info("✅ Redis connected")
        
        # Neo4j
        logger.info("Connecting to Neo4j...")
        neo4j_driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=("neo4j", "omnicore_password")
        )
        async with neo4j_driver.session() as session:
            await session.run("RETURN 1")
        logger.info("✅ Neo4j connected")
        
        # ChromaDB
        logger.info("Connecting to ChromaDB...")
        chroma_client = chromadb.Client()
        chroma_client.heartbeat()
        logger.info("✅ ChromaDB connected")
        
        logger.info("🎉 All databases initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize databases: {e}")
        raise

async def close_databases():
    """Close all database connections"""
    global mongodb_client, neo4j_driver, postgres_pool, redis_client, chroma_client
    
    try:
        if mongodb_client:
            mongodb_client.close()
            logger.info("✅ MongoDB connection closed")
            
        if neo4j_driver:
            await neo4j_driver.close()
            logger.info("✅ Neo4j connection closed")
            
        if postgres_pool:
            await postgres_pool.close()
            logger.info("✅ PostgreSQL connection closed")
            
        if redis_client:
            await redis_client.close()
            logger.info("✅ Redis connection closed")
            
        # ChromaDB doesn't need explicit closing
        logger.info("✅ All database connections closed")
        
    except Exception as e:
        logger.error(f"Error closing databases: {e}")

# Context managers for database access
@asynccontextmanager
async def get_mongodb():
    """Get MongoDB client"""
    if not mongodb_client:
        raise RuntimeError("MongoDB not initialized")
    try:
        yield mongodb_client
    finally:
        pass

@asynccontextmanager
async def get_postgres():
    """Get PostgreSQL connection"""
    if not postgres_pool:
        raise RuntimeError("PostgreSQL not initialized")
    async with postgres_pool.acquire() as conn:
        try:
            yield conn
        finally:
            pass

@asynccontextmanager
async def get_redis():
    """Get Redis client"""
    if not redis_client:
        raise RuntimeError("Redis not initialized")
    try:
        yield redis_client
    finally:
        pass

@asynccontextmanager
async def get_neo4j():
    """Get Neo4j session"""
    if not neo4j_driver:
        raise RuntimeError("Neo4j not initialized")
    async with neo4j_driver.session() as session:
        try:
            yield session
        finally:
            pass

@asynccontextmanager
async def get_chroma():
    """Get ChromaDB client"""
    if not chroma_client:
        raise RuntimeError("ChromaDB not initialized")
    try:
        yield chroma_client
    finally:
        pass
