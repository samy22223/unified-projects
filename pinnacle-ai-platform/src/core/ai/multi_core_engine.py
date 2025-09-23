"""
Pinnacle AI Multi-Core Automation Engine

This module implements the high-performance multi-core automation engine that powers
the platform's autonomous operation with parallel processing capabilities for 200+ AI agents.
"""

import asyncio
import logging
import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from enum import Enum
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import deque, defaultdict
import statistics
import json

from src.core.config.settings import settings
from src.core.ai.engine import PinnacleAIEngine, AITask, AIContext, TaskPriority
from src.core.ai.agent_manager import AgentManager, Agent, AgentStatus
from src.core.ai.task_queue import TaskQueueManager, QueueStatus


class ProcessingStatus(Enum):
    """Multi-core processing status enumeration."""
    INITIALIZING = "initializing"
    READY = "ready"
    PROCESSING = "processing"
    SCALING_UP = "scaling_up"
    SCALING_DOWN = "scaling_down"
    OVERLOADED = "overloaded"
    ERROR = "error"
    SHUTDOWN = "shutdown"


class LoadBalancingStrategy(Enum):
    """Load balancing strategy enumeration."""
    ROUND_ROBIN = "round_robin"
    LEAST_LOADED = "least_loaded"
    ADAPTIVE = "adaptive"
    PRIORITY_BASED = "priority_based"


@dataclass
class CoreMetrics:
    """Core performance metrics."""
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    thread_count: int = 0
    active_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    average_task_time: float = 0.0
    throughput: float = 0.0
    queue_size: int = 0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class WorkerThread:
    """Worker thread information."""
    id: str = ""
    executor: ThreadPoolExecutor = None
    is_active: bool = False
    current_load: int = 0
    max_load: int = 10
    average_task_time: float = 0.0
    last_active: datetime = field(default_factory=datetime.now)
    status: str = "idle"
    assigned_tasks: List[str] = field(default_factory=list)


@dataclass
class CircuitBreaker:
    """Circuit breaker for fault tolerance."""
    failure_count: int = 0
    threshold: int = 5
    timeout: int = 60
    last_failure: Optional[datetime] = None
    is_open: bool = False
    recovery_time: Optional[datetime] = None


class MultiCoreAutomationEngine:
    """
    High-performance multi-core automation engine for 200+ AI agents.

    Features:
    - ThreadPoolExecutor-based parallel processing
    - Advanced task distribution and load balancing
    - Resource management and optimization
    - Fault-tolerant parallel processing
    - Real-time performance monitoring
    - Dynamic scaling based on system resources
    - Priority-based task scheduling
    """

    def __init__(self, ai_engine: PinnacleAIEngine):
        """Initialize the multi-core automation engine."""
        self.logger = logging.getLogger(__name__)
        self.ai_engine = ai_engine
        self.status = ProcessingStatus.INITIALIZING

        # Core components
        self.task_queue_manager: Optional[TaskQueueManager] = None
        self.agent_manager: Optional[AgentManager] = None

        # Thread pool management
        self.worker_threads: Dict[str, WorkerThread] = {}
        self.main_executor: Optional[ThreadPoolExecutor] = None
        self.task_executors: Dict[str, ThreadPoolExecutor] = {}

        # Performance tracking
        self.core_metrics: Dict[str, CoreMetrics] = {}
        self.performance_history: deque = deque(maxlen=settings.PERFORMANCE_HISTORY_SIZE)
        self.metrics_lock = threading.Lock()

        # Load balancing
        self.load_balancer = LoadBalancer(self)
        self.current_strategy = LoadBalancingStrategy(settings.LOAD_BALANCING_STRATEGY)

        # Resource management
        self.resource_manager = ResourceManager(self)
        self.circuit_breaker = CircuitBreaker()

        # Task management
        self.active_tasks: Dict[str, AITask] = {}
        self.task_results: Dict[str, Any] = {}
        self.failed_tasks: Dict[str, AITask] = {}
        self.task_lock = threading.Lock()

        # Configuration
        self.max_worker_threads = settings.MAX_WORKER_THREADS
        self.min_worker_threads = settings.MIN_WORKER_THREADS
        self.core_multiplier = settings.CORE_MULTIPLIER
        self.task_batch_size = settings.TASK_BATCH_SIZE
        self.adaptive_scaling = settings.ADAPTIVE_SCALING_ENABLED

        # Background tasks
        self._monitoring_task = None
        self._scaling_task = None
        self._metrics_task = None
        self._shutdown_event = threading.Event()

        # Statistics
        self.stats = {
            "tasks_processed": 0,
            "agents_utilized": 0,
            "threads_created": 0,
            "errors_recovered": 0,
            "scaling_events": 0
        }

        self.start_time = time.time()

    async def initialize(self) -> bool:
        """Initialize the multi-core automation engine."""
        try:
            self.logger.info("🚀 Initializing Multi-Core Automation Engine...")

            # Initialize core components
            if not await self._initialize_components():
                return False

            # Initialize thread pools
            if not await self._initialize_thread_pools():
                return False

            # Start background tasks
            self._monitoring_task = asyncio.create_task(self._monitor_performance())
            self._scaling_task = asyncio.create_task(self._manage_scaling())
            self._metrics_task = asyncio.create_task(self._collect_metrics())

            self.status = ProcessingStatus.READY
            self.logger.info("✅ Multi-Core Automation Engine initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Multi-Core Automation Engine: {e}")
            self.status = ProcessingStatus.ERROR
            return False

    async def _initialize_components(self) -> bool:
        """Initialize core components."""
        try:
            # Get references to existing components
            self.task_queue_manager = self.ai_engine.task_queue_manager
            self.agent_manager = self.ai_engine.agent_manager

            if not self.task_queue_manager or not self.agent_manager:
                self.logger.error("Task queue manager or agent manager not available")
                return False

            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
            return False

    async def _initialize_thread_pools(self) -> bool:
        """Initialize thread pools for parallel processing."""
        try:
            # Calculate optimal thread count based on system resources
            cpu_count = psutil.cpu_count()
            optimal_threads = min(
                cpu_count * self.core_multiplier,
                self.max_worker_threads
            )

            # Create main executor for task coordination
            self.main_executor = ThreadPoolExecutor(
                max_workers=optimal_threads,
                thread_name_prefix="pinnacle-main"
            )

            # Create task-specific executors
            for i in range(min(10, optimal_threads // 5)):
                executor_id = f"task-executor-{i}"
                self.task_executors[executor_id] = ThreadPoolExecutor(
                    max_workers=5,
                    thread_name_prefix=f"pinnacle-task-{i}"
                )

            # Create worker threads
            await self._create_worker_threads(optimal_threads)

            self.logger.info(f"Created {optimal_threads} worker threads across {len(self.task_executors)} executors")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize thread pools: {e}")
            return False

    async def _create_worker_threads(self, count: int):
        """Create worker threads for task processing."""
        for i in range(count):
            worker_id = f"worker-{i}"
            worker = WorkerThread(
                id=worker_id,
                executor=self.main_executor,
                max_load=self.task_batch_size
            )
            self.worker_threads[worker_id] = worker

    async def process_tasks_parallel(self, tasks: List[AITask], contexts: Optional[List[AIContext]] = None) -> Dict[str, Any]:
        """
        Process multiple tasks in parallel using ThreadPoolExecutor.

        Args:
            tasks: List of tasks to process
            contexts: Optional list of contexts for tasks

        Returns:
            Dictionary mapping task IDs to results
        """
        if self.status != ProcessingStatus.READY:
            raise RuntimeError(f"Multi-core engine is not ready (status: {self.status})")

        if not tasks:
            return {}

        self.status = ProcessingStatus.PROCESSING
        task_results = {}

        try:
            # Check circuit breaker
            if self.circuit_breaker.is_open:
                if self._should_attempt_recovery():
                    self.circuit_breaker.is_open = False
                    self.logger.info("Circuit breaker closed, attempting recovery")
                else:
                    raise RuntimeError("Circuit breaker is open, too many recent failures")

            # Group tasks by priority for efficient processing
            priority_groups = self._group_tasks_by_priority(tasks)

            # Process each priority group
            for priority, priority_tasks in priority_groups.items():
                if priority_tasks:
                    group_results = await self._process_priority_group(priority_tasks, contexts)
                    task_results.update(group_results)

            # Update statistics
            self.stats["tasks_processed"] += len(tasks)

            return task_results

        except Exception as e:
            self.logger.error(f"Error in parallel task processing: {e}")
            await self._handle_processing_error(e)
            raise
        finally:
            self.status = ProcessingStatus.READY

    async def _process_priority_group(self, tasks: List[AITask], contexts: Optional[List[AIContext]] = None) -> Dict[str, Any]:
        """Process a group of tasks with the same priority."""
        results = {}

        # Use ThreadPoolExecutor for parallel processing
        loop = asyncio.get_event_loop()

        with self.main_executor as executor:
            # Submit tasks to thread pool
            future_to_task = {}
            for i, task in enumerate(tasks):
                context = contexts[i] if contexts and i < len(contexts) else None

                future = loop.run_in_executor(
                    executor,
                    self._execute_single_task,
                    task,
                    context
                )
                future_to_task[future] = task

            # Collect results as they complete
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    result = await future
                    results[task.id] = result

                    # Update task status
                    with self.task_lock:
                        if task.id in self.active_tasks:
                            del self.active_tasks[task.id]

                except Exception as e:
                    self.logger.error(f"Task {task.id} failed: {e}")
                    await self._handle_task_failure(task, e)

                    with self.task_lock:
                        if task.id in self.active_tasks:
                            del self.active_tasks[task.id]

        return results

    def _execute_single_task(self, task: AITask, context: Optional[AIContext] = None) -> Any:
        """Execute a single task (runs in thread pool)."""
        try:
            # Mark task as active
            with self.task_lock:
                self.active_tasks[task.id] = task

            # Execute task using AI engine
            result = asyncio.run(self.ai_engine.process_task(task, context))

            # Update worker thread metrics
            self._update_worker_metrics(task)

            return result

        except Exception as e:
            self.logger.error(f"Error executing task {task.id}: {e}")
            raise

    async def _handle_task_failure(self, task: AITask, error: Exception):
        """Handle task failure with retry logic."""
        with self.task_lock:
            self.failed_tasks[task.id] = task

        # Update circuit breaker
        self.circuit_breaker.failure_count += 1
        self.circuit_breaker.last_failure = datetime.now()

        if self.circuit_breaker.failure_count >= self.circuit_breaker.threshold:
            self.circuit_breaker.is_open = True
            self.circuit_breaker.recovery_time = datetime.now() + timedelta(seconds=self.circuit_breaker.timeout)
            self.logger.warning(f"Circuit breaker opened after {self.circuit_breaker.failure_count} failures")

        # Attempt retry if enabled
        if settings.FAULT_TOLERANCE_ENABLED and task.retry_count < task.max_retries:
            task.retry_count += 1
            await self.task_queue_manager.enqueue_task(task)
            self.stats["errors_recovered"] += 1

    def _should_attempt_recovery(self) -> bool:
        """Check if circuit breaker should attempt recovery."""
        if not self.circuit_breaker.recovery_time:
            return False

        return datetime.now() >= self.circuit_breaker.recovery_time

    def _group_tasks_by_priority(self, tasks: List[AITask]) -> Dict[TaskPriority, List[AITask]]:
        """Group tasks by priority for efficient processing."""
        groups = defaultdict(list)

        for task in tasks:
            groups[task.priority].append(task)

        return dict(groups)

    def _update_worker_metrics(self, task: AITask):
        """Update worker thread performance metrics."""
        # This would update metrics for the worker thread that processed the task
        pass

    async def _monitor_performance(self):
        """Monitor system performance and resource usage."""
        while not self._shutdown_event.is_set():
            try:
                # Collect system metrics
                metrics = self._collect_system_metrics()

                # Update performance history
                with self.metrics_lock:
                    self.performance_history.append(metrics)

                # Check for scaling needs
                if self.adaptive_scaling:
                    await self._check_scaling_requirements(metrics)

                # Update core metrics
                self._update_core_metrics(metrics)

                await asyncio.sleep(settings.RESOURCE_MONITORING_INTERVAL)

            except Exception as e:
                self.logger.error(f"Error in performance monitoring: {e}")
                await asyncio.sleep(5)

    def _collect_system_metrics(self) -> CoreMetrics:
        """Collect current system performance metrics."""
        try:
            # Get CPU and memory usage
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()

            # Get thread pool statistics
            active_threads = len(self.worker_threads)
            active_tasks = len(self.active_tasks)

            # Calculate throughput
            throughput = 0.0
            if self.performance_history:
                recent_metrics = list(self.performance_history)[-10:]
                if recent_metrics:
                    throughput = statistics.mean([m.throughput for m in recent_metrics if m.throughput > 0])

            return CoreMetrics(
                cpu_usage=cpu_percent,
                memory_usage=memory.percent,
                thread_count=active_threads,
                active_tasks=active_tasks,
                completed_tasks=self.stats["tasks_processed"],
                failed_tasks=len(self.failed_tasks),
                average_task_time=0.0,  # Would calculate from task history
                throughput=throughput,
                queue_size=len(self.active_tasks)
            )

        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
            return CoreMetrics()

    async def _check_scaling_requirements(self, metrics: CoreMetrics):
        """Check if scaling up or down is needed."""
        try:
            # Scale up conditions
            if (metrics.cpu_usage > settings.CPU_THRESHOLD_HIGH or
                metrics.memory_usage > settings.MEMORY_THRESHOLD_HIGH or
                len(self.active_tasks) > len(self.worker_threads) * 2):

                if len(self.worker_threads) < self.max_worker_threads:
                    await self._scale_up()

            # Scale down conditions
            elif (metrics.cpu_usage < settings.CPU_THRESHOLD_LOW and
                  metrics.memory_usage < settings.MEMORY_THRESHOLD_LOW and
                  len(self.active_tasks) < len(self.worker_threads) * 0.5):

                if len(self.worker_threads) > self.min_worker_threads:
                    await self._scale_down()

        except Exception as e:
            self.logger.error(f"Error checking scaling requirements: {e}")

    async def _scale_up(self):
        """Scale up worker threads."""
        try:
            current_count = len(self.worker_threads)
            new_count = min(current_count + 5, self.max_worker_threads)

            for i in range(current_count, new_count):
                worker_id = f"worker-{i}"
                worker = WorkerThread(
                    id=worker_id,
                    executor=self.main_executor,
                    max_load=self.task_batch_size
                )
                self.worker_threads[worker_id] = worker

            self.stats["scaling_events"] += 1
            self.logger.info(f"Scaled up to {new_count} worker threads")

        except Exception as e:
            self.logger.error(f"Error scaling up: {e}")

    async def _scale_down(self):
        """Scale down worker threads."""
        try:
            current_count = len(self.worker_threads)
            new_count = max(current_count - 3, self.min_worker_threads)

            # Remove excess workers
            workers_to_remove = []
            for worker_id in list(self.worker_threads.keys())[new_count:]:
                worker = self.worker_threads[worker_id]
                if worker.current_load == 0:  # Only remove idle workers
                    workers_to_remove.append(worker_id)

            for worker_id in workers_to_remove:
                del self.worker_threads[worker_id]

            self.stats["scaling_events"] += 1
            self.logger.info(f"Scaled down to {new_count} worker threads")

        except Exception as e:
            self.logger.error(f"Error scaling down: {e}")

    def _update_core_metrics(self, metrics: CoreMetrics):
        """Update core performance metrics."""
        with self.metrics_lock:
            self.core_metrics["current"] = metrics

    async def _collect_metrics(self):
        """Collect and store performance metrics."""
        while not self._shutdown_event.is_set():
            try:
                # Collect detailed metrics
                system_status = await self.get_system_status()

                # Store metrics for analytics
                await self._store_metrics(system_status)

                await asyncio.sleep(settings.METRICS_COLLECTION_INTERVAL)

            except Exception as e:
                self.logger.error(f"Error collecting metrics: {e}")
                await asyncio.sleep(5)

    async def _store_metrics(self, metrics: Dict[str, Any]):
        """Store metrics for analytics and monitoring."""
        # This would typically store metrics in a database or metrics service
        pass

    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        uptime = time.time() - self.start_time

        # Get current metrics
        current_metrics = self.core_metrics.get("current", CoreMetrics())

        return {
            "status": self.status.value,
            "uptime_seconds": uptime,
            "worker_threads": len(self.worker_threads),
            "active_tasks": len(self.active_tasks),
            "failed_tasks": len(self.failed_tasks),
            "task_queue_status": await self.task_queue_manager.get_queue_status() if self.task_queue_manager else {},
            "agent_status": await self.agent_manager.get_system_status() if self.agent_manager else {},
            "performance_metrics": {
                "cpu_usage": current_metrics.cpu_usage,
                "memory_usage": current_metrics.memory_usage,
                "throughput": current_metrics.throughput,
                "average_task_time": current_metrics.average_task_time
            },
            "load_balancing": {
                "strategy": self.current_strategy.value,
                "active_workers": len([w for w in self.worker_threads.values() if w.is_active])
            },
            "circuit_breaker": {
                "is_open": self.circuit_breaker.is_open,
                "failure_count": self.circuit_breaker.failure_count,
                "threshold": self.circuit_breaker.threshold
            },
            "statistics": self.stats
        }

    async def shutdown(self):
        """Shutdown the multi-core automation engine."""
        self.logger.info("🛑 Shutting down Multi-Core Automation Engine...")

        self.status = ProcessingStatus.SHUTDOWN
        self._shutdown_event.set()

        # Cancel background tasks
        if self._monitoring_task:
            self._monitoring_task.cancel()
        if self._scaling_task:
            self._scaling_task.cancel()
        if self._metrics_task:
            self._metrics_task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(
            self._monitoring_task,
            self._scaling_task,
            self._metrics_task,
            return_exceptions=True
        )

        # Shutdown thread pools
        if self.main_executor:
            self.main_executor.shutdown(wait=True)

        for executor in self.task_executors.values():
            executor.shutdown(wait=True)

        # Clear data structures
        self.worker_threads.clear()
        self.active_tasks.clear()
        self.failed_tasks.clear()
        self.performance_history.clear()

        self.logger.info("✅ Multi-Core Automation Engine shutdown complete")


class LoadBalancer:
    """Advanced load balancer for task distribution."""

    def __init__(self, engine: MultiCoreAutomationEngine):
        self.engine = engine
        self.round_robin_index = 0
        self.strategy = LoadBalancingStrategy.ROUND_ROBIN

    async def select_worker(self, task: AITask) -> Optional[str]:
        """Select the best worker for a task based on current strategy."""
        if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._round_robin_selection()
        elif self.strategy == LoadBalancingStrategy.LEAST_LOADED:
            return self._least_loaded_selection()
        elif self.strategy == LoadBalancingStrategy.ADAPTIVE:
            return self._adaptive_selection(task)
        else:
            return self._round_robin_selection()

    def _round_robin_selection(self) -> Optional[str]:
        """Select worker using round-robin strategy."""
        workers = list(self.engine.worker_threads.keys())
        if not workers:
            return None

        worker = workers[self.round_robin_index % len(workers)]
        self.round_robin_index += 1
        return worker

    def _least_loaded_selection(self) -> Optional[str]:
        """Select worker with least current load."""
        available_workers = [
            (worker_id, worker.current_load)
            for worker_id, worker in self.engine.worker_threads.items()
            if worker.is_active and worker.current_load < worker.max_load
        ]

        if not available_workers:
            return None

        return min(available_workers, key=lambda x: x[1])[0]

    def _adaptive_selection(self, task: AITask) -> Optional[str]:
        """Select worker using adaptive strategy based on task priority and worker performance."""
        # For high priority tasks, prefer least loaded workers
        if task.priority in [TaskPriority.CRITICAL, TaskPriority.URGENT]:
            return self._least_loaded_selection()
        else:
            return self._round_robin_selection()


class ResourceManager:
    """Resource management and optimization."""

    def __init__(self, engine: MultiCoreAutomationEngine):
        self.engine = engine
        self.cpu_history = deque(maxlen=100)
        self.memory_history = deque(maxlen=100)

    async def optimize_resources(self):
        """Optimize resource allocation based on current usage patterns."""
        try:
            # Analyze resource usage patterns
            if len(self.cpu_history) > 10:
                avg_cpu = statistics.mean(self.cpu_history)
                if avg_cpu > 80:
                    await self._optimize_for_high_cpu()
                elif avg_cpu < 20:
                    await self._optimize_for_low_cpu()

            if len(self.memory_history) > 10:
                avg_memory = statistics.mean(self.memory_history)
                if avg_memory > 85:
                    await self._optimize_for_high_memory()

        except Exception as e:
            self.engine.logger.error(f"Error optimizing resources: {e}")

    async def _optimize_for_high_cpu(self):
        """Optimize for high CPU usage."""
        # Reduce thread count temporarily
        if len(self.engine.worker_threads) > self.engine.min_worker_threads:
            await self.engine._scale_down()

    async def _optimize_for_low_cpu(self):
        """Optimize for low CPU usage."""
        # Can be more aggressive with threading
        if len(self.engine.worker_threads) < self.engine.max_worker_threads:
            await self.engine._scale_up()

    async def _optimize_for_high_memory(self):
        """Optimize for high memory usage."""
        # Reduce batch sizes and thread pools
        self.engine.task_batch_size = max(1, self.engine.task_batch_size - 2)
        await self.engine._scale_down()


# Global multi-core engine instance
multi_core_engine = None

def get_multi_core_engine() -> MultiCoreAutomationEngine:
    """Get the global multi-core automation engine instance."""
    return multi_core_engine