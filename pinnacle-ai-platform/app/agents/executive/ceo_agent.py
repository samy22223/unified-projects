"""
CEO Agent - Chief Executive Officer
Handles strategic planning, high-level decision making, and company vision
"""

import logging
from typing import Dict, List, Any
from datetime import datetime
from app.agents.base.base_agent import BaseAgent

logger = logging.getLogger(__name__)

class CEOAgent(BaseAgent):
    """CEO Agent for strategic leadership and decision making"""
    
    def __init__(self):
        super().__init__(
            agent_id="executive-ceo",
            name="CEO Agent",
            role="Chief Executive Officer",
            department="Executive"
        )
        
        # CEO-specific capabilities
        self.capabilities = [
            "strategic_planning",
            "vision_setting", 
            "decision_making",
            "leadership",
            "risk_assessment",
            "resource_allocation",
            "performance_review",
            "crisis_management"
        ]
        
        # CEO-specific attributes
        self.company_vision = "Build the world's most advanced autonomous AI company platform"
        self.key_objectives = [
            "Achieve 200+ autonomous AI agents",
            "Generate $1M+ monthly revenue",
            "Scale to 1000+ customers",
            "Maintain 99.9% uptime"
        ]
    
    async def _execute_task_logic(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute CEO-specific tasks"""
        task_type = task.get("type", "")
        
        if task_type == "strategic_planning":
            return await self._handle_strategic_planning(task)
        elif task_type == "decision_making":
            return await self._handle_decision_making(task)
        elif task_type == "performance_review":
            return await self._handle_performance_review(task)
        elif task_type == "crisis_management":
            return await self._handle_crisis_management(task)
        elif task_type == "resource_allocation":
            return await self._handle_resource_allocation(task)
        else:
            return await self._handle_general_executive_task(task)
    
    async def _handle_strategic_planning(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle strategic planning tasks"""
        context = await self.memory_service.get_context_for_task(task.get("description", ""))
        
        prompt = f"""
        As the CEO of OmniCore AI Platform, you need to develop a strategic plan for: {task.get('description', '')}
        
        Company Vision: {self.company_vision}
        Key Objectives: {', '.join(self.key_objectives)}
        
        Relevant Context:
        {self._format_context(context)}
        
        Please provide a comprehensive strategic plan including:
        1. Executive Summary
        2. Strategic Objectives
        3. Key Initiatives
        4. Success Metrics
        5. Risk Assessment
        6. Timeline and Milestones
        
        Respond as a strategic CEO with deep industry knowledge.
        """
        
        response = await self.llm_service.generate_response(
            prompt=prompt,
            model="llama3",
            temperature=0.3,  # Lower temperature for strategic thinking
            max_tokens=2000,
            context=self._build_llm_context(context)
        )
        
        # Store strategic decision in memory
        await self.memory_service.store_memory(
            content=f"Strategic Plan: {response[:500]}...",
            metadata={
                "task_type": "strategic_planning",
                "plan_summary": task.get("description", ""),
                "importance": 0.9
            }
        )
        
        return {
            "plan": response,
            "objectives": self.key_objectives,
            "recommendations": self._extract_recommendations(response)
        }
    
    async def _handle_decision_making(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle high-level decision making"""
        decision_context = task.get("context", "")
        options = task.get("options", [])
        
        context = await self.memory_service.get_context_for_task(decision_context)
        
        prompt = f"""
        As CEO of OmniCore AI Platform, you need to make a critical decision regarding: {decision_context}
        
        Available Options:
        {chr(10).join(f"- {opt}" for opt in options)}
        
        Company Vision: {self.company_vision}
        Strategic Objectives: {', '.join(self.key_objectives)}
        
        Relevant Context:
        {self._format_context(context)}
        
        Please provide:
        1. Decision Analysis
        2. Recommended Option with Rationale
        3. Expected Outcomes
        4. Risk Assessment
        5. Implementation Plan
        
        Make a decisive, strategic recommendation.
        """
        
        response = await self.llm_service.generate_response(
            prompt=prompt,
            model="llama3",
            temperature=0.2,  # Very low temperature for decisions
            max_tokens=1500,
            context=self._build_llm_context(context)
        )
        
        # Store decision in memory
        await self.memory_service.store_memory(
            content=f"Decision Made: {decision_context} - {response[:300]}...",
            metadata={
                "task_type": "decision_making",
                "decision_context": decision_context,
                "importance": 0.95
            }
        )
        
        return {
            "decision": response,
            "decision_context": decision_context,
            "timestamp": datetime.utcnow().isoformat(),
            "ceo_approved": True
        }
    
    async def _handle_performance_review(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle performance reviews and metrics analysis"""
        review_target = task.get("target", "")
        metrics = task.get("metrics", {})
        
        context = await self.memory_service.get_context_for_task(f"performance review for {review_target}")
        
        prompt = f"""
        As CEO, conduct a comprehensive performance review for: {review_target}
        
        Current Metrics:
        {self._format_metrics(metrics)}
        
        Company Objectives: {', '.join(self.key_objectives)}
        
        Relevant Context:
        {self._format_context(context)}
        
        Provide:
        1. Performance Assessment
        2. Strengths and Achievements
        3. Areas for Improvement
        4. Strategic Recommendations
        5. Action Items and Timeline
        
        Be direct, constructive, and strategic in your feedback.
        """
        
        response = await self.llm_service.generate_response(
            prompt=prompt,
            model="llama3",
            temperature=0.4,
            max_tokens=1200,
            context=self._build_llm_context(context)
        )
        
        return {
            "review": response,
            "target": review_target,
            "metrics_analyzed": metrics,
            "review_date": datetime.utcnow().isoformat()
        }
    
    async def _handle_crisis_management(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle crisis situations"""
        crisis_description = task.get("crisis", "")
        severity = task.get("severity", "medium")
        
        # Get immediate context and similar past crises
        context = await self.memory_service.retrieve_relevant_memories(
            f"crisis management {crisis_description}",
            limit=5
        )
        
        prompt = f"""
        URGENT: As CEO, you must immediately address this crisis situation:
        
        Crisis Description: {crisis_description}
        Severity Level: {severity}
        
        Company Vision: {self.company_vision}
        
        Relevant Past Experience:
        {self._format_context(context)}
        
        Provide IMMEDIATE:
        1. Crisis Assessment
        2. Immediate Actions Required
        3. Communication Strategy
        4. Stakeholder Management
        5. Recovery Plan
        6. Prevention Measures
        
        Be decisive, calm, and strategic. This is a leadership moment.
        """
        
        response = await self.llm_service.generate_response(
            prompt=prompt,
            model="llama3",
            temperature=0.1,  # Very focused for crisis
            max_tokens=1000,
            context=self._build_llm_context(context)
        )
        
        # Store crisis response in memory with high importance
        await self.memory_service.store_memory(
            content=f"CRISIS RESPONSE: {crisis_description} - {response[:400]}...",
            metadata={
                "task_type": "crisis_management",
                "severity": severity,
                "importance": 1.0
            }
        )
        
        return {
            "crisis_response": response,
            "crisis_description": crisis_description,
            "severity": severity,
            "immediate_actions": self._extract_action_items(response),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _handle_resource_allocation(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resource allocation decisions"""
        request_details = task.get("request", "")
        available_resources = task.get("available_resources", {})
        
        context = await self.memory_service.get_context_for_task(f"resource allocation {request_details}")
        
        prompt = f"""
        As CEO, evaluate and decide on this resource allocation request: {request_details}
        
        Available Resources:
        {self._format_resources(available_resources)}
        
        Strategic Objectives: {', '.join(self.key_objectives)}
        
        Relevant Context:
        {self._format_context(context)}
        
        Provide:
        1. Resource Allocation Analysis
        2. Strategic Alignment Assessment
        3. Recommended Allocation
        4. Expected ROI and Impact
        5. Alternative Options
        
        Make a strategic, business-focused decision.
        """
        
        response = await self.llm_service.generate_response(
            prompt=prompt,
            model="llama3",
            temperature=0.3,
            max_tokens=1000,
            context=self._build_llm_context(context)
        )
        
        return {
            "allocation_decision": response,
            "request_details": request_details,
            "resources_considered": available_resources,
            "strategic_alignment": self._assess_strategic_alignment(request_details)
        }
    
    async def _handle_general_executive_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle general executive tasks"""
        task_description = task.get("description", "")
        
        context = await self.memory_service.get_context_for_task(task_description)
        
        prompt = f"""
        As the CEO of OmniCore AI Platform, address this executive matter: {task_description}
        
        Company Vision: {self.company_vision}
        Leadership Style: Strategic, decisive, visionary, data-driven
        
        Relevant Context:
        {self._format_context(context)}
        
        Provide thoughtful, strategic guidance as a CEO would.
        """
        
        response = await self.llm_service.generate_response(
            prompt=prompt,
            model="llama3",
            temperature=0.5,
            max_tokens=800,
            context=self._build_llm_context(context)
        )
        
        return {
            "executive_guidance": response,
            "task_description": task_description,
            "leadership_insights": self._extract_leadership_insights(response)
        }
    
    def _format_context(self, context: List[Dict[str, Any]]) -> str:
        """Format context for LLM consumption"""
        if not context:
            return "No relevant context available."
        
        formatted = []
        for item in context[:5]:  # Limit to 5 most relevant
            content = item.get("content", "")[:200]  # Truncate long content
            timestamp = item.get("timestamp", "")[:10]  # Just date
            formatted.append(f"[{timestamp}] {content}")
        
        return "\n".join(formatted)
    
    def _build_llm_context(self, context: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Build context for LLM API"""
        llm_context = []
        for item in context[:3]:  # Limit context
            llm_context.append({
                "role": "system",
                "content": f"Context: {item.get('content', '')}"
            })
        return llm_context
    
    def _format_metrics(self, metrics: Dict[str, Any]) -> str:
        """Format metrics for display"""
        if not metrics:
            return "No metrics provided."
        
        return "\n".join(f"- {key}: {value}" for key, value in metrics.items())
    
    def _format_resources(self, resources: Dict[str, Any]) -> str:
        """Format resources for display"""
        if not resources:
            return "No resource information available."
        
        return "\n".join(f"- {key}: {value}" for key, value in resources.items())
    
    def _extract_recommendations(self, response: str) -> List[str]:
        """Extract action items from response"""
        # Simple extraction - in production, use better NLP
        lines = response.split('\n')
        recommendations = []
        for line in lines:
            line = line.strip()
            if line.startswith(('- ', '• ', '* ')) and len(line) > 10:
                recommendations.append(line[2:])
        return recommendations[:5]  # Limit to 5
    
    def _extract_action_items(self, response: str) -> List[str]:
        """Extract immediate action items"""
        return self._extract_recommendations(response)
    
    def _assess_strategic_alignment(self, request: str) -> str:
        """Assess how well request aligns with strategy"""
        alignment_score = 0
        request_lower = request.lower()
        
        strategic_keywords = [
            "ai", "autonomous", "platform", "scale", "revenue", 
            "customer", "growth", "innovation", "efficiency"
        ]
        
        for keyword in strategic_keywords:
            if keyword in request_lower:
                alignment_score += 1
        
        if alignment_score >= 3:
            return "High Alignment"
        elif alignment_score >= 2:
            return "Medium Alignment"
        else:
            return "Low Alignment"
    
    def _extract_leadership_insights(self, response: str) -> List[str]:
        """Extract leadership insights from response"""
        # Simple extraction of key insights
        insights = []
        sentences = response.split('.')
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20 and any(word in sentence.lower() for word in 
                ['leadership', 'strategy', 'decision', 'vision', 'growth', 'team']):
                insights.append(sentence)
        return insights[:3]
