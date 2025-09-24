"""
LLM Service for AI agent interactions
Supports multiple LLM providers (Ollama, OpenAI, Anthropic)
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
import httpx
from openai import AsyncOpenAI
import anthropic
from app.core.config import settings

logger = logging.getLogger(__name__)

class LLMService:
    """Service for interacting with Large Language Models"""
    
    def __init__(self):
        self.ollama_client = None
        self.openai_client = None
        self.anthropic_client = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize LLM clients"""
        try:
            # Ollama (local LLM)
            self.ollama_client = httpx.AsyncClient(
                base_url=settings.ollama_base_url,
                timeout=60.0
            )
            
            # OpenAI (if API key available)
            if hasattr(settings, 'openai_api_key') and settings.openai_api_key:
                self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
            
            # Anthropic (if API key available)
            if hasattr(settings, 'anthropic_api_key') and settings.anthropic_api_key:
                self.anthropic_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
                
        except Exception as e:
            logger.error(f"Failed to initialize LLM clients: {e}")
    
    async def generate_response(
        self, 
        prompt: str, 
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        context: List[Dict[str, str]] = None
    ) -> str:
        """Generate response from LLM"""
        if not model:
            model = settings.default_llm_model
            
        try:
            # Try Ollama first (local, free)
            if self.ollama_client and model in ["llama3", "llama2", "codellama"]:
                return await self._ollama_generate(prompt, model, temperature, max_tokens, context)
            
            # Fallback to OpenAI
            elif self.openai_client:
                return await self._openai_generate(prompt, model, temperature, max_tokens, context)
            
            # Fallback to Anthropic
            elif self.anthropic_client:
                return await self._anthropic_generate(prompt, model, temperature, max_tokens, context)
            
            else:
                raise ValueError("No LLM providers available")
                
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return f"Error: {str(e)}"
    
    async def _ollama_generate(
        self, 
        prompt: str, 
        model: str,
        temperature: float,
        max_tokens: int,
        context: List[Dict[str, str]] = None
    ) -> str:
        """Generate using Ollama (local LLM)"""
        messages = []
        
        # Add context if provided
        if context:
            messages.extend(context)
        
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        response = await self.ollama_client.post("/api/chat", json=payload)
        response.raise_for_status()
        
        result = response.json()
        return result["message"]["content"]
    
    async def _openai_generate(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        context: List[Dict[str, str]] = None
    ) -> str:
        """Generate using OpenAI"""
        messages = []
        
        # Add context if provided
        if context:
            messages.extend(context)
        
        messages.append({"role": "user", "content": prompt})
        
        response = await self.openai_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content
    
    async def _anthropic_generate(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        context: List[Dict[str, str]] = None
    ) -> str:
        """Generate using Anthropic Claude"""
        system_prompt = ""
        user_messages = []
        
        # Separate system messages from user messages
        if context:
            for msg in context:
                if msg.get("role") == "system":
                    system_prompt += msg.get("content", "") + "\n"
                else:
                    user_messages.append(msg)
        
        user_messages.append({"role": "user", "content": prompt})
        
        # Combine all user messages
        combined_prompt = "\n\n".join([msg.get("content", "") for msg in user_messages])
        
        response = await self.anthropic_client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt.strip(),
            messages=[{"role": "user", "content": combined_prompt}]
        )
        
        return response.content[0].text
    
    async def embed_text(self, text: str, model: str = None) -> List[float]:
        """Generate embeddings for text"""
        if not model:
            model = settings.embedding_model
            
        try:
            # Try Ollama embeddings first
            if self.ollama_client and "embed" in model.lower():
                return await self._ollama_embed(text, model)
            
            # Fallback to OpenAI embeddings
            elif self.openai_client:
                return await self._openai_embed(text, model)
            
            else:
                raise ValueError("No embedding providers available")
                
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return []
    
    async def _ollama_embed(self, text: str, model: str) -> List[float]:
        """Generate embeddings using Ollama"""
        payload = {
            "model": model,
            "prompt": text
        }
        
        response = await self.ollama_client.post("/api/embeddings", json=payload)
        response.raise_for_status()
        
        result = response.json()
        return result.get("embedding", [])
    
    async def _openai_embed(self, text: str, model: str) -> List[float]:
        """Generate embeddings using OpenAI"""
        response = await self.openai_client.embeddings.create(
            input=text,
            model=model
        )
        
        return response.data[0].embedding
    
    async def close(self):
        """Close all clients"""
        if self.ollama_client:
            await self.ollama_client.aclose()
