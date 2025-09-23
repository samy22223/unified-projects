"""
Pinnacle AI Task Queue Manager

This module manages task queues, scheduling, and load balancing for the AI platform.
It handles task distribution across 200+ agents with priority-based processing.
"""

import asyncio
import logging
import time
import heapq
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict
import threading

from src.core.ai.types import AITask, AIContext, TaskPriority
from src.core.ai.engine import PinnacleAIEngine


class QueueStatus(Enum):
    """Task queue status enumeration."""
    ACTIVE = "active"
    PAUSED = "paused"
    OVERLOADED = "overloaded"
    MAINTENANCE = "maintenance"


@dataclass
class QueueMetrics:
    """Queue performance metrics."""
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    average_processing_time: float = 0.0
    current_queue_size: int = 0
    max_queue_size: int = 0
    throughput_per_minute: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class WorkerLoad:
    """Worker load information."""
    worker_id: str = ""
    current_tasks: int = 0
    max_tasks: int = 3
    average_task_time: float = 0.0
    last_active: datetime = field(default_factory=datetime.now)
    status: str = "active"


class PriorityQueue:
    """Priority queue implementation for tasks."""

    def __init__(self):
        """Initialize priority queue."""
        self._queue = []
        self._entry_finder = {}
        self._counter = 0

    def push(self, item: AITask, priority: int = 0):
        """
        Add item to priority queue.

        Args:
            item: Task to add
            priority: Priority value (higher = more priority)
        """
        if item.id in self._entry_finder:
            self.remove(item.id)

        entry = [priority, self._counter, item]
        self._entry_finder[item.id] = entry
        heapq.heappush(self._queue, entry)
        self._counter += 1

    def pop(self) -> Optional[AITask]:
        """Remove and return highest priority task."""
        while self._queue:
            priority, counter, item = heapq.heappop(self._queue)
            if item.id in self._entry_finder:
                del self._entry_finder[item.id]
                return item
        return None

    def remove(self, task_id: str):
        """Remove task from queue."""
        if task_id in self._entry_finder:
            entry = self._entry_finder.pop(task_id)
            entry[-1] = None  # Mark as removed

    def peek(self) -> Optional[AITask]:
        """Get highest priority task without removing."""
        while self._queue:
            priority, counter, item = self._queue[0]
            if item.id in self._entry_finder:
                return item
            heapq.heappop(self._queue)
        return None

    def __len__(self) -> int:
        """Get queue length."""
        return len(self._entry_finder)


class TaskQueueManager:
    """
    Advanced task queue manager for handling 200+ AI agents.

    Features:
    - Priority-based task scheduling
    - Load balancing across agents
    - Queue monitoring and metrics
    - Automatic retry mechanisms
    - Dead letter queue handling
    - Performance optimization
    """

    def __init__(self, engine: PinnacleAIEngine):
        """Initialize the task queue manager."""
        self.engine = engine
        self.logger = logging.getLogger(__name__)

        # Queue management
        self.queues: Dict[str, PriorityQueue] = {
            "high": PriorityQueue(),
            "normal": PriorityQueue(),
            "low": PriorityQueue()
        }

        # Queue status and metrics
        self.status = QueueStatus.ACTIVE
        self.metrics: Dict[str, QueueMetrics] = {
            "high": QueueMetrics(),
            "normal": QueueMetrics(),
            "low": QueueMetrics()
        }

        # Worker management
        self.workers: Dict[str, WorkerLoad] = {}
        self.worker_assignments: Dict[str, List[str]] = defaultdict(list)

        # Task tracking
        self.active_tasks: Dict[str, AITask] = {}
        self.completed_tasks: Dict[str, AITask] = {}
        self.failed_tasks: Dict[str, AITask] = {}

        # Dead letter queue for failed tasks
        self.dead_letter_queue: List[AITask] = []

        # Configuration
        self.max_queue_size = 10000
        self.max_retries = 3
        self.processing_timeout = 300  # 5 minutes
        self.cleanup_interval = 300  # 5 minutes

        # Background tasks
        self._processing_task = None
        self._monitoring_task = None
        self._cleanup_task = None
        self._shutdown_event = threading.Event()

        # Locks for thread safety
        self._queue_lock = asyncio.Lock()
        self._worker_lock = asyncio.Lock()

    async def initialize(self) -> bool:
        """Initialize the task queue manager."""
        self.logger.info("📋 Initializing Task Queue Manager...")

        try:
            # Start background tasks
            self._processing_task = asyncio.create_task(self._process_queues())
            self._monitoring_task = asyncio.create_task(self._monitor_queues())
            self._cleanup_task = asyncio.create_task(self._cleanup_old_tasks())

            self.logger.info("✅ Task Queue Manager initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Task Queue Manager: {e}")
            return False

    async def enqueue_task(self, task: AITask) -> bool:
        """
        Add a task to the appropriate queue.

        Args:
            task: Task to enqueue

        Returns:
            True if task was enqueued successfully
        """
        async with self._queue_lock:
            if self.status != QueueStatus.ACTIVE:
                self.logger.warning(f"Queue is not active (status: {self.status})")
                return False

            # Determine queue based on priority
            queue_name = self._get_queue_for_priority(task.priority)

            # Check queue size limits
            if len(self.queues[queue_name]) >= self.max_queue_size:
                self.logger.warning(f"Queue {queue_name} is at maximum capacity")
                return False

            # Add task to queue
            priority_value = self._get_priority_value(task.priority)
            self.queues[queue_name].push(task, priority_value)

            # Update metrics
            self.metrics[queue_name].total_tasks += 1
            self.metrics[queue_name].current_queue_size = len(self.queues[queue_name])
            self.metrics[queue_name].max_queue_size = max(
                self.metrics[queue_name].max_queue_size,
                len(self.queues[queue_name])
            )

            self.logger.info(f"📥 Enqueued task {task.id} in {queue_name} queue")
            return True

    def _get_queue_for_priority(self, priority: TaskPriority) -> str:
        """Get queue name for task priority."""
        if priority in [TaskPriority.CRITICAL, TaskPriority.URGENT]:
            return "high"
        elif priority == TaskPriority.HIGH:
            return "normal"
        else:
            return "low"

    def _get_priority_value(self, priority: TaskPriority) -> int:
        """Get numeric priority value (higher = more priority)."""
        priority_values = {
            TaskPriority.CRITICAL: 100,
            TaskPriority.URGENT: 90,
            TaskPriority.HIGH: 80,
            TaskPriority.NORMAL: 50,
            TaskPriority.LOW: 20
        }
        return priority_values.get(priority, 50)

    async def dequeue_task(self, queue_name: str = "normal") -> Optional[AITask]:
        """
        Remove and return next task from queue.

        Args:
            queue_name: Queue to dequeue from

        Returns:
            Next task or None if queue is empty
        """
        async with self._queue_lock:
            if queue_name not in self.queues:
                return None

            task = self.queues[queue_name].pop()
            if task:
                # Update metrics
                self.metrics[queue_name].current_queue_size = len(self.queues[queue_name])

            return task

    async def register_worker(self, worker_id: str, max_tasks: int = 3) -> bool:
        """
        Register a worker for task processing.

        Args:
            worker_id: Worker identifier
            max_tasks: Maximum concurrent tasks for this worker

        Returns:
            True if registration successful
        """
        async with self._worker_lock:
            if worker_id in self.workers:
                self.logger.warning(f"Worker {worker_id} already registered")
                return False

            self.workers[worker_id] = WorkerLoad(
                worker_id=worker_id,
                max_tasks=max_tasks
            )

            self.logger.info(f"👷 Registered worker {worker_id}")
            return True

    async def unregister_worker(self, worker_id: str) -> bool:
        """
        Unregister a worker.

        Args:
            worker_id: Worker identifier

        Returns:
            True if unregistration successful
        """
        async with self._worker_lock:
            if worker_id not in self.workers:
                return False

            # Remove worker assignments
            if worker_id in self.worker_assignments:
                del self.worker_assignments[worker_id]

            # Remove worker
            del self.workers[worker_id]

            self.logger.info(f"👷 Unregistered worker {worker_id}")
            return True

    async def assign_task_to_worker(self, task: AITask, worker_id: str) -> bool:
        """
        Assign a task to a specific worker.

        Args:
            task: Task to assign
            worker_id: Worker to assign to

        Returns:
            True if assignment successful
        """
        async with self._worker_lock:
            if worker_id not in self.workers:
                return False

            worker = self.workers[worker_id]

            # Check if worker can accept more tasks
            if worker.current_tasks >= worker.max_tasks:
                return False

            # Assign task
            self.worker_assignments[worker_id].append(task.id)
            worker.current_tasks += 1
            worker.last_active = datetime.now()

            # Mark task as active
            self.active_tasks[task.id] = task
            task.status = "processing"

            self.logger.info(f"📋 Assigned task {task.id} to worker {worker_id}")
            return True

    async def complete_task(self, task_id: str, result: Any, processing_time: float) -> bool:
        """
        Mark a task as completed.

        Args:
            task_id: Task identifier
            result: Task result
            processing_time: Time taken to process task

        Returns:
            True if completion recorded successfully
        """
        async with self._queue_lock:
            if task_id not in self.active_tasks:
                return False

            task = self.active_tasks[task_id]

            # Update task
            task.status = "completed"
            task.result = result

            # Move to completed tasks
            self.completed_tasks[task_id] = task
            del self.active_tasks[task_id]

            # Update worker assignment
            await self._remove_worker_assignment(task_id)

            # Update metrics
            queue_name = self._get_queue_for_priority(task.priority)
            self.metrics[queue_name].completed_tasks += 1
            self.metrics[queue_name].average_processing_time = (
                (self.metrics[queue_name].average_processing_time + processing_time) / 2
            )

            self.logger.info(f"✅ Completed task {task_id}")
            return True

    async def fail_task(self, task_id: str, error: str) -> bool:
        """
        Mark a task as failed.

        Args:
            task_id: Task identifier
            error: Error message

        Returns:
            True if failure recorded successfully
        """
        async with self._queue_lock:
            if task_id not in self.active_tasks:
                return False

            task = self.active_tasks[task_id]

            # Update task
            task.status = "failed"
            task.error = error
            task.retry_count += 1

            # Check if task should be retried
            if task.retry_count < task.max_retries:
                # Re-queue task with lower priority
                task.priority = TaskPriority(task.priority.value - 1) if task.priority.value > 1 else TaskPriority.LOW
                await self.enqueue_task(task)
                self.logger.info(f"🔄 Re-queued failed task {task_id} (attempt {task.retry_count})")
            else:
                # Move to failed tasks or dead letter queue
                self.failed_tasks[task_id] = task
                self.dead_letter_queue.append(task)
                self.logger.warning(f"💀 Task {task_id} moved to dead letter queue after {task.retry_count} failures")

            # Clean up active task
            del self.active_tasks[task_id]
            await self._remove_worker_assignment(task_id)

            # Update metrics
            queue_name = self._get_queue_for_priority(task.priority)
            self.metrics[queue_name].failed_tasks += 1

            return True

    async def _remove_worker_assignment(self, task_id: str):
        """Remove task assignment from worker."""
        async with self._worker_lock:
            for worker_id, tasks in self.worker_assignments.items():
                if task_id in tasks:
                    tasks.remove(task_id)
                    if worker_id in self.workers:
                        self.workers[worker_id].current_tasks = max(0, self.workers[worker_id].current_tasks - 1)
                    break

    async def get_queue_status(self) -> Dict[str, Any]:
        """Get overall queue status."""
        total_queued = sum(len(queue) for queue in self.queues.values())
        total_active = len(self.active_tasks)
        total_completed = len(self.completed_tasks)
        total_failed = len(self.failed_tasks)

        return {
            "status": self.status.value,
            "total_queued": total_queued,
            "total_active": total_active,
            "total_completed": total_completed,
            "total_failed": total_failed,
            "dead_letter_queue_size": len(self.dead_letter_queue),
            "workers": {
                "total": len(self.workers),
                "active": len([w for w in self.workers.values() if w.status == "active"]),
                "overloaded": len([w for w in self.workers.values() if w.current_tasks >= w.max_tasks])
            },
            "queue_sizes": {name: len(queue) for name, queue in self.queues.items()},
            "metrics": {name: {
                "total_tasks": metrics.total_tasks,
                "completed_tasks": metrics.completed_tasks,
                "failed_tasks": metrics.failed_tasks,
                "average_processing_time": metrics.average_processing_time,
                "throughput_per_minute": metrics.throughput_per_minute
            } for name, metrics in self.metrics.items()}
        }

    async def _process_queues(self):
        """Main queue processing loop."""
        while not self._shutdown_event.is_set():
            try:
                if self.status != QueueStatus.ACTIVE:
                    await asyncio.sleep(1)
                    continue

                # Process queues in priority order
                for queue_name in ["high", "normal", "low"]:
                    if self._shutdown_event.is_set():
                        break

                    task = await self.dequeue_task(queue_name)
                    if task:
                        # Find available worker
                        worker_id = await self._find_available_worker()
                        if worker_id:
                            await self.assign_task_to_worker(task, worker_id)
                        else:
                            # No available workers, re-queue task
                            await self.enqueue_task(task)
                            break  # Don't overwhelm the system

                await asyncio.sleep(0.1)  # Small delay to prevent busy waiting

            except Exception as e:
                self.logger.error(f"Error in queue processing: {e}")
                await asyncio.sleep(1)

    async def _find_available_worker(self) -> Optional[str]:
        """Find an available worker for task assignment."""
        async with self._worker_lock:
            available_workers = []

            for worker_id, worker in self.workers.items():
                if (worker.status == "active" and
                    worker.current_tasks < worker.max_tasks):
                    available_workers.append((worker_id, worker.current_tasks))

            if not available_workers:
                return None

            # Return worker with least current tasks
            return min(available_workers, key=lambda x: x[1])[0]

    async def _monitor_queues(self):
        """Monitor queue health and performance."""
        while not self._shutdown_event.is_set():
            try:
                status = await self.get_queue_status()

                # Check for overload conditions
                total_queued = status["total_queued"]
                if total_queued > self.max_queue_size * 0.9:
                    self.status = QueueStatus.OVERLOADED
                    self.logger.warning("Queue overloaded, pausing new task acceptance")
                elif total_queued < self.max_queue_size * 0.5 and self.status == QueueStatus.OVERLOADED:
                    self.status = QueueStatus.ACTIVE
                    self.logger.info("Queue load normalized, resuming normal operation")

                # Update throughput metrics
                for queue_name, metrics in self.metrics.items():
                    if metrics.completed_tasks > 0:
                        # Calculate throughput (tasks per minute)
                        elapsed_minutes = (datetime.now() - metrics.last_updated).total_seconds() / 60
                        if elapsed_minutes > 0:
                            metrics.throughput_per_minute = metrics.completed_tasks / elapsed_minutes

                await asyncio.sleep(30)  # Monitor every 30 seconds

            except Exception as e:
                self.logger.error(f"Error in queue monitoring: {e}")
                await asyncio.sleep(5)

    async def _cleanup_old_tasks(self):
        """Clean up old completed and failed tasks."""
        while not self._shutdown_event.is_set():
            try:
                current_time = datetime.now()
                cutoff_time = current_time - timedelta(hours=24)

                # Clean up old completed tasks
                old_completed = [
                    task_id for task_id, task in self.completed_tasks.items()
                    if task.created_at < cutoff_time
                ]

                for task_id in old_completed:
                    del self.completed_tasks[task_id]

                # Clean up old failed tasks
                old_failed = [
                    task_id for task_id, task in self.failed_tasks.items()
                    if task.created_at < cutoff_time
                ]

                for task_id in old_failed:
                    del self.failed_tasks[task_id]

                # Clean up dead letter queue (keep only recent entries)
                self.dead_letter_queue = [
                    task for task in self.dead_letter_queue
                    if task.created_at >= cutoff_time
                ]

                if old_completed or old_failed:
                    self.logger.info(f"Cleaned up {len(old_completed)} completed and {len(old_failed)} failed tasks")

                await asyncio.sleep(self.cleanup_interval)

            except Exception as e:
                self.logger.error(f"Error in task cleanup: {e}")
                await asyncio.sleep(60)

    async def shutdown(self):
        """Shutdown the task queue manager."""
        self.logger.info("🛑 Shutting down Task Queue Manager...")

        # Stop background tasks
        self._shutdown_event.set()

        if self._processing_task:
            self._processing_task.cancel()
        if self._monitoring_task:
            self._monitoring_task.cancel()
        if self._cleanup_task:
            self._cleanup_task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(
            self._processing_task,
            self._monitoring_task,
            self._cleanup_task,
            return_exceptions=True
        )

        # Clear all queues and data
        for queue in self.queues.values():
            while len(queue) > 0:
                queue.pop()

        self.active_tasks.clear()
        self.completed_tasks.clear()
        self.failed_tasks.clear()
        self.workers.clear()
        self.worker_assignments.clear()

        self.logger.info("✅ Task Queue Manager shutdown complete")</code></edit>
</edit_file>