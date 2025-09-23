#!/usr/bin/env python3
"""
Test script for Pinnacle AI System

This script demonstrates the core AI functionality including:
- Database integration
- AI service management
- Mode processing
- Agent management
"""

import asyncio
import logging
import sys
from datetime import datetime

# Add src to path
sys.path.append("src")

from core.ai.database_integration import ai_db_manager
from core.ai.ai_service import ai_service_manager
from core.ai.engine import ai_engine
from core.ai.types import AITask, AIContext, TaskPriority


async def test_database_integration():
    """Test database integration functionality."""
    print("🗄️ Testing Database Integration...")

    try:
        # Initialize database
        success = await ai_db_manager.initialize()
        if not success:
            print("❌ Database initialization failed")
            return False

        # Test creating a sample task
        test_task = AITask(
            type="test_task",
            priority=TaskPriority.NORMAL,
            data={"test": "data", "timestamp": datetime.utcnow().isoformat()},
            mode="auto"
        )

        task_id = await ai_db_manager.create_task(test_task)
        print(f"✅ Created test task: {task_id}")

        # Test retrieving the task
        retrieved_task = await ai_db_manager.get_task(task_id)
        if retrieved_task:
            print(f"✅ Retrieved task: {retrieved_task['id']}")
        else:
            print("❌ Failed to retrieve task")
            return False

        # Test updating task status
        success = await ai_db_manager.mark_task_completed(
            task_id,
            {"result": "Test completed successfully"},
            0.5
        )
        if success:
            print("✅ Updated task status to completed")
        else:
            print("❌ Failed to update task status")
            return False

        print("✅ Database integration test passed!")
        return True

    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False


async def test_ai_services():
    """Test AI service functionality."""
    print("\n🤖 Testing AI Services...")

    try:
        # Get available services
        available_services = await ai_service_manager.get_available_services()
        print(f"✅ Available AI services: {available_services}")

        if not available_services:
            print("❌ No AI services available")
            return False

        # Test text generation
        test_prompt = "Explain the importance of clean architecture in software development."
        print(f"📝 Testing text generation with prompt: {test_prompt[:50]}...")

        response = await ai_service_manager.generate_text(
            test_prompt,
            preferred_service="auto"
        )

        print(f"✅ Generated response ({len(response.text)} chars)")
        print(f"   Model: {response.model_used}")
        print(f"   Confidence: {response.confidence}")
        print(f"   Processing time: {response.processing_time".2f"}s")

        # Test text analysis
        test_text = "Clean architecture promotes separation of concerns and makes software more maintainable."
        print(f"\n📊 Testing text analysis with: {test_text[:50]}...")

        analysis = await ai_service_manager.analyze_text(
            test_text,
            analysis_type="general"
        )

        print(f"✅ Generated analysis ({len(analysis.text)} chars)")
        print(f"   Model: {analysis.model_used}")
        print(f"   Confidence: {analysis.confidence}")

        print("✅ AI services test passed!")
        return True

    except Exception as e:
        print(f"❌ AI services test failed: {e}")
        return False


async def test_ai_engine():
    """Test AI engine functionality."""
    print("\n🚀 Testing AI Engine...")

    try:
        # Initialize AI engine
        success = await ai_engine.initialize()
        if not success:
            print("❌ AI engine initialization failed")
            return False

        print("✅ AI engine initialized successfully")

        # Create a test task
        test_task = AITask(
            type="architectural_analysis",
            priority=TaskPriority.HIGH,
            data={
                "requirement": "Design a scalable web application for e-commerce",
                "constraints": ["high_traffic", "real_time_processing"],
                "technologies": ["python", "fastapi", "postgresql"]
            },
            mode="auto"
        )

        # Create context
        context = AIContext(
            user_id="test_user",
            metadata={"project_type": "ecommerce", "scale": "enterprise"}
        )

        print("📋 Processing test task with AI engine...")

        # Process task
        result = await ai_engine.process_task(test_task, context)

        if result:
            print("✅ Task processed successfully!"            print(f"   Mode used: {result.get('mode', 'unknown')}")
            print(f"   Analysis length: {len(result.get('analysis', ''))} chars")

            # Check if we got AI metadata (indicating real AI processing)
            if 'ai_metadata' in result:
                ai_meta = result['ai_metadata']
                print(f"   AI Model: {ai_meta.get('model_used', 'unknown')}")
                print(f"   Confidence: {ai_meta.get('confidence', 0)".2f"}")
                print(f"   Processing time: {ai_meta.get('processing_time', 0)".2f"}s")
            else:
                print("   ⚠️  No AI metadata found (using fallback)")

        print("✅ AI engine test passed!")
        return True

    except Exception as e:
        print(f"❌ AI engine test failed: {e}")
        return False


async def main():
    """Main test function."""
    print("🧪 Starting Pinnacle AI System Tests")
    print("=" * 50)

    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Run tests
    tests = [
        test_database_integration,
        test_ai_services,
        test_ai_engine
    ]

    results = []
    for test in tests:
        result = await test()
        results.append(result)
        print()

    # Summary
    print("=" * 50)
    print("📊 Test Results Summary:")

    test_names = [
        "Database Integration",
        "AI Services",
        "AI Engine"
    ]

    for name, result in zip(test_names, results):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {name}: {status}")

    all_passed = all(results)
    print(f"\n🎯 Overall Result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")

    # Cleanup
    try:
        await ai_engine.shutdown()
        await ai_db_manager.shutdown()
    except:
        pass

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)