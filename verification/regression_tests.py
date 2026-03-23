#!/usr/bin/env python3
"""
Comprehensive Regression Test Suite for SAFAS Schedulers

This suite tests multiple scheduling algorithms with various scenarios:
1. Hybrid EDF + SRJF (existing)
2. Adaptive Threshold Hybrid (new)
3. Multi-Level Priority (new)
4. LLF Hybrid (new)
5. Pure EDF (baseline)
6. Pure SRJF (baseline)

Author: Advanced Implementation
Date: March 23, 2026
"""

import random
import sys
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum
import json


class SchedulerType(Enum):
    """Types of schedulers to test"""
    HYBRID_EDF_SRJF = "Hybrid EDF+SRJF"
    ADAPTIVE_THRESHOLD = "Adaptive Threshold"
    MULTI_LEVEL = "Multi-Level Priority"
    LLF_HYBRID = "LLF Hybrid"
    PURE_EDF = "Pure EDF"
    PURE_SRJF = "Pure SRJF"


@dataclass
class Task:
    """Represents a real-time task"""
    id: int
    arrival_time: int
    deadline: int
    execution_time: int
    remaining_time: int
    priority_mode: str = 'NORMAL'
    priority_level: int = 0  # For multi-level schedulers

    @property
    def absolute_deadline(self) -> int:
        return self.arrival_time + self.deadline

    @property
    def slack(self) -> int:
        return self.deadline - self.remaining_time

    @property
    def laxity(self) -> int:
        """Laxity = slack (alternate term used in LLF)"""
        return self.slack

    def slack_threshold(self, multiplier: float = 2.0) -> float:
        return multiplier * self.remaining_time

    def is_low_slack(self, multiplier: float = 2.0) -> bool:
        return self.slack < self.slack_threshold(multiplier)


@dataclass
class TestScenario:
    """Represents a test scenario"""
    name: str
    description: str
    num_tasks: int
    num_cores: int
    time_range: int
    utilization: float
    expected_success_rate: float = 0.0  # Minimum expected


@dataclass
class TestResult:
    """Results from running a test"""
    scenario: TestScenario
    scheduler_type: SchedulerType
    completed_tasks: int
    missed_deadlines: int
    success_rate: float
    avg_response_time: float
    avg_wait_time: float
    preemptions: int
    mode_switches: int
    total_time: int
    additional_metrics: Dict = field(default_factory=dict)


class BaseScheduler:
    """Base class for all schedulers"""

    def __init__(self, num_cores: int = 16):
        self.num_cores = num_cores
        self.queues: List[List[Task]] = []
        self.running_tasks: List[Task] = []
        self.completed_tasks: List[Task] = []
        self.missed_deadlines = 0
        self.time = 0
        self.stats = {
            'scheduled': 0,
            'preemptions': 0,
            'mode_switches': 0,
            'total_wait_time': 0,
            'total_response_time': 0,
        }

    def admit_task(self, task: Task):
        """Admit a new task - to be overridden"""
        raise NotImplementedError

    def get_next_task(self) -> Optional[Task]:
        """Get the next task to schedule - to be overridden"""
        raise NotImplementedError

    def schedule_cycle(self, new_tasks: List[Task]):
        """Execute one scheduling cycle"""
        # Admit new tasks
        for task in new_tasks:
            self.admit_task(task)
            self.stats['total_wait_time'] += (self.time - task.arrival_time)

        # Update running tasks
        finished_tasks = []
        for task in self.running_tasks:
            task.remaining_time -= 1
            task.deadline -= 1

            if task.remaining_time <= 0:
                finished_tasks.append(task)
                self.completed_tasks.append(task)
                self.stats['total_response_time'] += (self.time - task.arrival_time)
            elif task.deadline <= 0:
                finished_tasks.append(task)
                self.missed_deadlines += 1

        # Remove finished tasks
        for task in finished_tasks:
            self.running_tasks.remove(task)

        # Try to schedule new tasks on idle cores
        while len(self.running_tasks) < self.num_cores:
            next_task = self.get_next_task()
            if next_task is None:
                break
            self.running_tasks.append(next_task)
            self.stats['scheduled'] += 1

        self.time += 1

    def get_results(self) -> Dict:
        """Get scheduling results"""
        total = len(self.completed_tasks)
        return {
            'completed': total,
            'missed': self.missed_deadlines,
            'success_rate': 100 * (1 - self.missed_deadlines / max(total, 1)),
            'avg_response_time': self.stats['total_response_time'] / max(total, 1),
            'avg_wait_time': self.stats['total_wait_time'] / max(self.stats['scheduled'], 1),
            'preemptions': self.stats['preemptions'],
            'mode_switches': self.stats['mode_switches'],
            'time': self.time,
        }


class HybridEDFSRJFScheduler(BaseScheduler):
    """Original Hybrid EDF+SRJF with 2× threshold"""

    def __init__(self, num_cores: int = 16):
        super().__init__(num_cores)
        self.srjf_queue: List[Task] = []
        self.edf_queue: List[Task] = []
        self.queues = [self.srjf_queue, self.edf_queue]

    def admit_task(self, task: Task):
        if task.is_low_slack(2.0):
            self.edf_queue.append(task)
            self.edf_queue.sort(key=lambda t: t.absolute_deadline)
        else:
            self.srjf_queue.append(task)
            self.srjf_queue.sort(key=lambda t: t.remaining_time)

    def get_next_task(self) -> Optional[Task]:
        if self.edf_queue:
            return self.edf_queue.pop(0)
        elif self.srjf_queue:
            return self.srjf_queue.pop(0)
        return None


class AdaptiveThresholdScheduler(BaseScheduler):
    """Hybrid scheduler with configurable threshold"""

    def __init__(self, num_cores: int = 16, threshold_multiplier: float = 1.5):
        super().__init__(num_cores)
        self.threshold_multiplier = threshold_multiplier
        self.srjf_queue: List[Task] = []
        self.edf_queue: List[Task] = []
        self.queues = [self.srjf_queue, self.edf_queue]

    def admit_task(self, task: Task):
        if task.is_low_slack(self.threshold_multiplier):
            self.edf_queue.append(task)
            self.edf_queue.sort(key=lambda t: t.absolute_deadline)
        else:
            self.srjf_queue.append(task)
            self.srjf_queue.sort(key=lambda t: t.remaining_time)

    def get_next_task(self) -> Optional[Task]:
        if self.edf_queue:
            return self.edf_queue.pop(0)
        elif self.srjf_queue:
            return self.srjf_queue.pop(0)
        return None


class MultiLevelScheduler(BaseScheduler):
    """Multi-level priority scheduler with 3 queues"""

    def __init__(self, num_cores: int = 16):
        super().__init__(num_cores)
        self.critical_queue: List[Task] = []  # Slack < 1× execution
        self.urgent_queue: List[Task] = []     # Slack < 2× execution
        self.normal_queue: List[Task] = []     # Slack >= 2× execution
        self.queues = [self.critical_queue, self.urgent_queue, self.normal_queue]

    def admit_task(self, task: Task):
        if task.slack < task.remaining_time:
            # Critical: slack < 1× execution
            task.priority_level = 0
            self.critical_queue.append(task)
            self.critical_queue.sort(key=lambda t: t.absolute_deadline)
        elif task.is_low_slack(2.0):
            # Urgent: slack < 2× execution
            task.priority_level = 1
            self.urgent_queue.append(task)
            self.urgent_queue.sort(key=lambda t: t.absolute_deadline)
        else:
            # Normal: slack >= 2× execution
            task.priority_level = 2
            self.normal_queue.append(task)
            self.normal_queue.sort(key=lambda t: t.remaining_time)

    def get_next_task(self) -> Optional[Task]:
        if self.critical_queue:
            return self.critical_queue.pop(0)
        elif self.urgent_queue:
            return self.urgent_queue.pop(0)
        elif self.normal_queue:
            return self.normal_queue.pop(0)
        return None


class LLFHybridScheduler(BaseScheduler):
    """Least Laxity First with SRJF fallback"""

    def __init__(self, num_cores: int = 16):
        super().__init__(num_cores)
        self.llf_queue: List[Task] = []    # For tasks with low laxity
        self.srjf_queue: List[Task] = []   # For tasks with high laxity
        self.queues = [self.llf_queue, self.srjf_queue]

    def admit_task(self, task: Task):
        # Use laxity-based switching
        if task.laxity < task.remaining_time * 1.5:
            self.llf_queue.append(task)
            self.llf_queue.sort(key=lambda t: t.laxity)
        else:
            self.srjf_queue.append(task)
            self.srjf_queue.sort(key=lambda t: t.remaining_time)

    def get_next_task(self) -> Optional[Task]:
        if self.llf_queue:
            return self.llf_queue.pop(0)
        elif self.srjf_queue:
            return self.srjf_queue.pop(0)
        return None


class PureEDFScheduler(BaseScheduler):
    """Pure EDF scheduler (baseline)"""

    def __init__(self, num_cores: int = 16):
        super().__init__(num_cores)
        self.queue: List[Task] = []
        self.queues = [self.queue]

    def admit_task(self, task: Task):
        self.queue.append(task)
        self.queue.sort(key=lambda t: t.absolute_deadline)

    def get_next_task(self) -> Optional[Task]:
        return self.queue.pop(0) if self.queue else None


class PureSRJFScheduler(BaseScheduler):
    """Pure SRJF scheduler (baseline)"""

    def __init__(self, num_cores: int = 16):
        super().__init__(num_cores)
        self.queue: List[Task] = []
        self.queues = [self.queue]

    def admit_task(self, task: Task):
        self.queue.append(task)
        self.queue.sort(key=lambda t: t.remaining_time)

    def get_next_task(self) -> Optional[Task]:
        return self.queue.pop(0) if self.queue else None


def generate_task_set(scenario: TestScenario) -> List[List[Task]]:
    """Generate a task set based on scenario parameters"""
    task_schedule = [[] for _ in range(scenario.time_range)]
    task_id = 0

    for _ in range(scenario.num_tasks):
        arrival = random.randint(0, scenario.time_range - 100)
        execution = random.randint(5, 50)

        # Vary slack based on utilization
        if scenario.utilization > 0.8:
            slack_factor = random.choice([1.2, 1.5, 2.0, 2.5])
        else:
            slack_factor = random.choice([2.0, 2.5, 3.0, 4.0])

        deadline = int(execution * slack_factor)

        task = Task(
            id=task_id,
            arrival_time=arrival,
            deadline=deadline,
            execution_time=execution,
            remaining_time=execution,
        )
        task_schedule[arrival].append(task)
        task_id += 1

    return task_schedule


def run_test(scenario: TestScenario, scheduler: BaseScheduler,
             scheduler_type: SchedulerType) -> TestResult:
    """Run a single test scenario"""
    task_schedule = generate_task_set(scenario)

    for time_step in range(len(task_schedule)):
        new_tasks = task_schedule[time_step]
        scheduler.schedule_cycle(new_tasks)

    results = scheduler.get_results()

    return TestResult(
        scenario=scenario,
        scheduler_type=scheduler_type,
        completed_tasks=results['completed'],
        missed_deadlines=results['missed'],
        success_rate=results['success_rate'],
        avg_response_time=results['avg_response_time'],
        avg_wait_time=results['avg_wait_time'],
        preemptions=results['preemptions'],
        mode_switches=results['mode_switches'],
        total_time=results['time'],
    )


def create_test_scenarios() -> List[TestScenario]:
    """Create comprehensive test scenarios"""
    return [
        TestScenario(
            name="Low Load",
            description="Light system load with relaxed deadlines",
            num_tasks=30,
            num_cores=16,
            time_range=500,
            utilization=0.4,
            expected_success_rate=100.0
        ),
        TestScenario(
            name="Medium Load",
            description="Moderate system load",
            num_tasks=50,
            num_cores=16,
            time_range=500,
            utilization=0.7,
            expected_success_rate=95.0
        ),
        TestScenario(
            name="High Load",
            description="High system load with tight deadlines",
            num_tasks=70,
            num_cores=16,
            time_range=500,
            utilization=0.9,
            expected_success_rate=90.0
        ),
        TestScenario(
            name="Extreme Load",
            description="Very high load testing schedulability",
            num_tasks=100,
            num_cores=16,
            time_range=500,
            utilization=1.0,
            expected_success_rate=80.0
        ),
        TestScenario(
            name="Short Tasks",
            description="Many short tasks",
            num_tasks=80,
            num_cores=16,
            time_range=500,
            utilization=0.6,
            expected_success_rate=98.0
        ),
        TestScenario(
            name="Long Tasks",
            description="Fewer long tasks",
            num_tasks=20,
            num_cores=16,
            time_range=500,
            utilization=0.6,
            expected_success_rate=98.0
        ),
    ]


def run_regression_tests():
    """Run comprehensive regression tests"""
    print("=" * 80)
    print("SAFAS Scheduler Regression Test Suite")
    print("=" * 80)
    print()

    scenarios = create_test_scenarios()

    # Define schedulers to test
    scheduler_configs = [
        (SchedulerType.HYBRID_EDF_SRJF, lambda: HybridEDFSRJFScheduler(16)),
        (SchedulerType.ADAPTIVE_THRESHOLD, lambda: AdaptiveThresholdScheduler(16, 1.5)),
        (SchedulerType.MULTI_LEVEL, lambda: MultiLevelScheduler(16)),
        (SchedulerType.LLF_HYBRID, lambda: LLFHybridScheduler(16)),
        (SchedulerType.PURE_EDF, lambda: PureEDFScheduler(16)),
        (SchedulerType.PURE_SRJF, lambda: PureSRJFScheduler(16)),
    ]

    all_results: List[TestResult] = []

    for scenario in scenarios:
        print(f"\n{'=' * 80}")
        print(f"Scenario: {scenario.name}")
        print(f"Description: {scenario.description}")
        print(f"Tasks: {scenario.num_tasks}, Cores: {scenario.num_cores}, "
              f"Utilization: {scenario.utilization:.1%}")
        print(f"{'=' * 80}")

        for scheduler_type, scheduler_factory in scheduler_configs:
            scheduler = scheduler_factory()
            result = run_test(scenario, scheduler, scheduler_type)
            all_results.append(result)

            status = "✓ PASS" if result.success_rate >= scenario.expected_success_rate else "✗ FAIL"
            print(f"\n{scheduler_type.value:25s} {status}")
            print(f"  Success Rate:      {result.success_rate:6.2f}%")
            print(f"  Missed Deadlines:  {result.missed_deadlines:6d}")
            print(f"  Avg Response Time: {result.avg_response_time:6.2f}")

    # Summary comparison
    print("\n" + "=" * 80)
    print("SUMMARY: Average Performance Across All Scenarios")
    print("=" * 80)

    for scheduler_type, _ in scheduler_configs:
        scheduler_results = [r for r in all_results if r.scheduler_type == scheduler_type]
        avg_success = sum(r.success_rate for r in scheduler_results) / len(scheduler_results)
        avg_response = sum(r.avg_response_time for r in scheduler_results) / len(scheduler_results)
        total_missed = sum(r.missed_deadlines for r in scheduler_results)

        print(f"\n{scheduler_type.value:25s}")
        print(f"  Avg Success Rate:  {avg_success:6.2f}%")
        print(f"  Avg Response Time: {avg_response:6.2f}")
        print(f"  Total Missed:      {total_missed:6d}")

    return all_results


if __name__ == "__main__":
    random.seed(42)  # For reproducibility
    results = run_regression_tests()

    print("\n" + "=" * 80)
    print("Regression tests complete!")
    print("=" * 80)

    sys.exit(0)
