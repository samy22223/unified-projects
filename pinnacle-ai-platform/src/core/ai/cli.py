"""
Pinnacle AI Platform Command Line Interface

This module provides a comprehensive CLI for interacting with the Pinnacle AI Platform,
including agent management, task control, and system monitoring.
"""

import asyncio
import click
import json
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

from src.core.ai.engine import ai_engine, AITask, AIContext, TaskPriority
from src.core.config.settings import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.group()
@click.option('--debug', is_flag=True, help='Enable debug mode')
@click.option('--config', type=click.Path(exists=True), help='Path to config file')
def cli(debug, config):
    """Pinnacle AI Platform Command Line Interface"""
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        click.echo("🐛 Debug mode enabled")

    if config:
        click.echo(f"📁 Using config file: {config}")


@cli.group()
def agents():
    """Agent management commands"""
    pass


@agents.command('list')
@click.option('--type', 'agent_type', help='Filter by agent type')
@click.option('--status', help='Filter by agent status')
@click.option('--json', 'output_json', is_flag=True, help='Output in JSON format')
def list_agents(agent_type, status, output_json):
    """List all AI agents"""
    try:
        filters = {}
        if agent_type:
            filters['type'] = agent_type
        if status:
            filters['status'] = status

        agents = asyncio.run(ai_engine.list_agents(filters))

        if output_json:
            click.echo(json.dumps(agents, indent=2, default=str))
        else:
            click.echo(f"🤖 Found {len(agents)} agents:")
            for agent in agents:
                click.echo(f"  • {agent['name']} ({agent['id'][:8]}...) - {agent['type']} - {agent['status']}")

    except Exception as e:
        click.echo(f"❌ Error listing agents: {e}", err=True)
        sys.exit(1)


@agents.command('create')
@click.argument('name')
@click.argument('agent_type')
@click.option('--capabilities', multiple=True, help='Agent capabilities')
@click.option('--max-tasks', type=int, default=3, help='Maximum concurrent tasks')
def create_agent(name, agent_type, capabilities, max_tasks):
    """Create a new AI agent"""
    try:
        agent_id = asyncio.run(ai_engine.create_agent(agent_type, {
            'name': name,
            'type': agent_type,
            'capabilities': list(capabilities),
            'max_concurrent_tasks': max_tasks
        }))

        click.echo(f"✅ Created agent {name} with ID: {agent_id}")

    except Exception as e:
        click.echo(f"❌ Error creating agent: {e}", err=True)
        sys.exit(1)


@agents.command('info')
@click.argument('agent_id')
def agent_info(agent_id):
    """Get detailed information about an agent"""
    try:
        agent = asyncio.run(ai_engine.get_agent(agent_id))

        if not agent:
            click.echo(f"❌ Agent {agent_id} not found", err=True)
            sys.exit(1)

        click.echo(f"🤖 Agent Information:")
        click.echo(f"  ID: {agent['id']}")
        click.echo(f"  Name: {agent['name']}")
        click.echo(f"  Type: {agent['type']}")
        click.echo(f"  Status: {agent['status']}")
        click.echo(f"  Created: {agent['created_at']}")
        click.echo(f"  Last Active: {agent['last_active']}")
        click.echo(f"  Tasks Completed: {agent['task_count']}")
        click.echo(f"  Success Rate: {agent['success_rate']".2f"}")
        click.echo(f"  Current Tasks: {len(agent['current_tasks'])}")

    except Exception as e:
        click.echo(f"❌ Error getting agent info: {e}", err=True)
        sys.exit(1)


@agents.command('delete')
@click.argument('agent_id')
@click.option('--force', is_flag=True, help='Force deletion without confirmation')
def delete_agent(agent_id, force):
    """Delete an AI agent"""
    try:
        if not force:
            if not click.confirm(f"Are you sure you want to delete agent {agent_id}?"):
                click.echo("❌ Operation cancelled")
                return

        # Check agent status first
        agent = asyncio.run(ai_engine.get_agent(agent_id))
        if not agent:
            click.echo(f"❌ Agent {agent_id} not found", err=True)
            sys.exit(1)

        if agent.get('status') not in ['idle', 'ready']:
            click.echo(f"❌ Cannot delete agent with status: {agent['status']}", err=True)
            sys.exit(1)

        success = asyncio.run(ai_engine.agent_manager.remove_agent(agent_id))

        if success:
            click.echo(f"✅ Deleted agent {agent_id}")
        else:
            click.echo(f"❌ Failed to delete agent {agent_id}", err=True)
            sys.exit(1)

    except Exception as e:
        click.echo(f"❌ Error deleting agent: {e}", err=True)
        sys.exit(1)


@cli.group()
def tasks():
    """Task management commands"""
    pass


@tasks.command('create')
@click.argument('task_type')
@click.option('--priority', type=click.Choice(['low', 'normal', 'high', 'urgent', 'critical']),
              default='normal', help='Task priority')
@click.option('--data', help='Task data as JSON string')
@click.option('--mode', default='auto', help='Processing mode')
@click.option('--agent-id', help='Specific agent ID')
def create_task(task_type, priority, data, mode, agent_id):
    """Create a new task"""
    try:
        # Parse task data
        task_data = {}
        if data:
            try:
                task_data = json.loads(data)
            except json.JSONDecodeError:
                click.echo("❌ Invalid JSON data", err=True)
                sys.exit(1)

        # Convert priority
        priority_map = {
            'critical': TaskPriority.CRITICAL,
            'urgent': TaskPriority.URGENT,
            'high': TaskPriority.HIGH,
            'normal': TaskPriority.NORMAL,
            'low': TaskPriority.LOW
        }

        task = AITask(
            type=task_type,
            priority=priority_map[priority],
            data=task_data,
            mode=mode,
            agent_id=agent_id
        )

        # Process task
        context = AIContext()
        result = asyncio.run(ai_engine.process_task(task, context))

        click.echo(f"✅ Created and processed task {task.id}")
        click.echo(f"Result: {json.dumps(result, indent=2, default=str)}")

    except Exception as e:
        click.echo(f"❌ Error creating task: {e}", err=True)
        sys.exit(1)


@tasks.command('list')
@click.option('--status', help='Filter by task status')
@click.option('--type', 'task_type', help='Filter by task type')
@click.option('--json', 'output_json', is_flag=True, help='Output in JSON format')
def list_tasks(status, task_type, output_json):
    """List tasks"""
    try:
        # Get tasks from database
        from src.core.database.manager import DatabaseManager
        db_manager = DatabaseManager()

        filters = {}
        if status:
            filters['status'] = status
        if task_type:
            filters['type'] = task_type

        tasks = asyncio.run(db_manager.list_tasks(filters))

        if output_json:
            click.echo(json.dumps(tasks, indent=2, default=str))
        else:
            click.echo(f"📋 Found {len(tasks)} tasks:")
            for task in tasks[:10]:  # Show first 10 tasks
                click.echo(f"  • {task['type']} ({task['id'][:8]}...) - {task['status']} - {task['created_at']}")

            if len(tasks) > 10:
                click.echo(f"  ... and {len(tasks) - 10} more tasks")

    except Exception as e:
        click.echo(f"❌ Error listing tasks: {e}", err=True)
        sys.exit(1)


@tasks.command('info')
@click.argument('task_id')
def task_info(task_id):
    """Get detailed information about a task"""
    try:
        # Get task from database
        from src.core.database.manager import DatabaseManager
        db_manager = DatabaseManager()

        task = asyncio.run(db_manager.get_task(task_id))

        if not task:
            click.echo(f"❌ Task {task_id} not found", err=True)
            sys.exit(1)

        click.echo(f"📋 Task Information:")
        click.echo(f"  ID: {task['id']}")
        click.echo(f"  Type: {task['type']}")
        click.echo(f"  Priority: {task['priority']}")
        click.echo(f"  Status: {task['status']}")
        click.echo(f"  Created: {task['created_at']}")
        click.echo(f"  Retries: {task['retry_count']}/{task['max_retries']}")

        if task['result']:
            click.echo(f"  Result: {json.dumps(task['result'], indent=2, default=str)}")

        if task['error']:
            click.echo(f"  Error: {task['error']}")

    except Exception as e:
        click.echo(f"❌ Error getting task info: {e}", err=True)
        sys.exit(1)


@cli.group()
def system():
    """System management commands"""
    pass


@system.command('status')
@click.option('--json', 'output_json', is_flag=True, help='Output in JSON format')
def system_status(output_json):
    """Get system status"""
    try:
        status = asyncio.run(ai_engine.health_check())

        if output_json:
            click.echo(json.dumps(status, indent=2, default=str))
        else:
            click.echo("🔍 System Status:")
            click.echo(f"  Status: {status['status']}")
            click.echo(f"  Ready: {'✅' if status['ready'] else '❌'}")
            click.echo(f"  Active Tasks: {status['metrics']['active_tasks']}")
            click.echo(f"  Total Tasks Processed: {status['metrics']['total_tasks_processed']}")
            click.echo(f"  Total Agents: {status['metrics']['total_agents_created']}")
            click.echo(f"  Errors: {status['metrics']['total_errors']}")

            click.echo("\n📊 Components:")
            for component, healthy in status['components'].items():
                status_icon = '✅' if healthy else '❌'
                click.echo(f"  {status_icon} {component}")

    except Exception as e:
        click.echo(f"❌ Error getting system status: {e}", err=True)
        sys.exit(1)


@system.command('metrics')
@click.option('--json', 'output_json', is_flag=True, help='Output in JSON format')
def system_metrics(output_json):
    """Get system performance metrics"""
    try:
        metrics = asyncio.run(ai_engine.get_performance_metrics())

        if output_json:
            click.echo(json.dumps(metrics, indent=2, default=str))
        else:
            click.echo("📊 Performance Metrics:")
            click.echo(f"  Status: {metrics['status']}")
            click.echo(f"  Uptime: {metrics['uptime_seconds']".1f"} seconds")
            click.echo(f"  Active Tasks: {metrics['active_tasks']}")
            click.echo(f"  Active Contexts: {metrics['active_contexts']}")
            click.echo(f"  Total Tasks Processed: {metrics['total_tasks_processed']}")
            click.echo(f"  Total Agents Created: {metrics['total_agents_created']}")
            click.echo(f"  Total Errors: {metrics['total_errors']}")

            if 'memory_usage' in metrics and 'error' not in metrics['memory_usage']:
                mem = metrics['memory_usage']
                click.echo(f"  Memory Usage: {mem['rss_mb']".1f"} MB RSS, {mem['vms_mb']".1f"} MB VMS")

            if 'cpu_usage' in metrics and 'error' not in metrics['cpu_usage']:
                cpu = metrics['cpu_usage']
                click.echo(f"  CPU Usage: {cpu['percent']".1f"}%")

    except Exception as e:
        click.echo(f"❌ Error getting system metrics: {e}", err=True)
        sys.exit(1)


@system.command('modes')
@click.option('--json', 'output_json', is_flag=True, help='Output in JSON format')
def list_modes(output_json):
    """List available AI modes"""
    try:
        modes = asyncio.run(ai_engine.mode_manager.get_available_modes())

        if output_json:
            click.echo(json.dumps(modes, indent=2, default=str))
        else:
            click.echo("🎭 Available AI Modes:")
            for mode in modes:
                click.echo(f"  • {mode['name']} ({mode['type']}) - {mode['description']}")
                click.echo(f"    Priority: {mode['priority']}, Enabled: {'✅' if mode['enabled'] else '❌'}")

    except Exception as e:
        click.echo(f"❌ Error listing modes: {e}", err=True)
        sys.exit(1)


@system.command('switch-mode')
@click.argument('mode')
def switch_mode(mode):
    """Switch to a different AI mode"""
    try:
        context = AIContext(current_mode=mode)
        success = asyncio.run(ai_engine.switch_mode(mode, context))

        if success:
            click.echo(f"✅ Switched to {mode} mode")
        else:
            click.echo(f"❌ Failed to switch to {mode} mode", err=True)
            sys.exit(1)

    except Exception as e:
        click.echo(f"❌ Error switching mode: {e}", err=True)
        sys.exit(1)


@cli.group()
def multimodal():
    """Multi-modal processing commands"""
    pass


@multimodal.command('process')
@click.option('--text', help='Text to process')
@click.option('--modality', type=click.Choice(['text', 'image', 'audio', 'video']),
              default='text', help='Data modality')
def process_multimodal(text, modality):
    """Process multi-modal data"""
    try:
        if modality == 'text' and text:
            context = AIContext()
            result = asyncio.run(ai_engine.process_multi_modal(text, 'text', context))

            click.echo("📝 Text Processing Result:")
            click.echo(json.dumps(result, indent=2, default=str))
        else:
            click.echo(f"❌ {modality} processing not yet implemented", err=True)

    except Exception as e:
        click.echo(f"❌ Error processing multi-modal data: {e}", err=True)
        sys.exit(1)


@cli.command('init')
def initialize():
    """Initialize the AI platform"""
    try:
        click.echo("🚀 Initializing Pinnacle AI Platform...")

        success = asyncio.run(ai_engine.initialize())

        if success:
            click.echo("✅ Platform initialized successfully")
            click.echo("📊 Use 'pinnacle system status' to check system status")
            click.echo("🤖 Use 'pinnacle agents list' to see available agents")
        else:
            click.echo("❌ Failed to initialize platform", err=True)
            sys.exit(1)

    except Exception as e:
        click.echo(f"❌ Error initializing platform: {e}", err=True)
        sys.exit(1)


@cli.command('health')
def health_check():
    """Perform a health check"""
    try:
        status = asyncio.run(ai_engine.health_check())

        if status['ready']:
            click.echo("✅ System is healthy")
        else:
            click.echo("❌ System is not healthy", err=True)
            sys.exit(1)

    except Exception as e:
        click.echo(f"❌ Health check failed: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()</code></edit>
</edit_file>