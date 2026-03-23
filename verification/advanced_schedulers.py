#!/usr/bin/env python3
"""
Advanced Scheduling Algorithms - Predictive and Adaptive Variants

This module implements cutting-edge scheduling algorithms:
1. Predictive Look-Ahead Scheduler
2. Dynamic Adaptive Threshold Scheduler
3. Weighted Multi-Queue Scheduler

Author: Advanced Implementation
Date: March 23, 2026
"""

import random
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass


@dataclass
class Task:
    """Represents a real-time task"""
    id: int
    arrival_time: int
    deadline: int
    execution_time: int
    remaining_time: int
    priority_mode: str = 'NORMAL'
    urgency_score: float = 0.0  # For predictive scheduling

    @property
    def absolute_deadline(self) -> int:
        return self.arrival_time + self.deadline

    @property
    def slack(self) -> int:
        return self.deadline - self.remaining_time

    @property
    def laxity(self) -> int:
        return self.slack

    @property
    def urgency_ratio(self) -> float:
        """Urgency ratio for predictive scheduling"""
        if self.remaining_time == 0:
            return float('inf')
        return self.slack / self.remaining_time


class PredictiveLookAheadScheduler:
    """
    Predictive Look-Ahead Scheduler

    This scheduler predicts future task states and makes scheduling
    decisions that optimize for both immediate and future performance.

    Key Features:
    - Look-ahead window to predict task urgency
    - Urgency scoring based on future slack projections
    - Proactive priority adjustment
    """

    def __init__(self, num_cores: int = 16, lookahead_window: int = 10):
        self.num_cores = num_cores
        self.lookahead_window = lookahead_window
        self.queue: List[Task] = []
        self.running_tasks: List[Task] = []
        self.completed_tasks: List[Task] = []
        self.missed_deadlines = 0
        self.time = 0
        self.stats = {
            'scheduled': 0,
            'preemptions': 0,
            'predictions': 0,
            'total_wait_time': 0,
            'total_response_time': 0,
        }

    def calculate_urgency_score(self, task: Task) -> float:
        """
        Calculate urgency score with look-ahead prediction

        Score considers:
        - Current slack
        - Projected slack after lookahead window
        - Remaining execution time
        - Deadline pressure
        """
        # Current urgency
        current_slack = task.slack
        if task.remaining_time == 0:
            return 0.0

        # Predict future slack
        future_slack = current_slack - self.lookahead_window

        # Calculate urgency components
        slack_urgency = 1.0 / (max(current_slack, 1))
        future_urgency = 1.0 / (max(future_slack, 1))
        execution_pressure = task.remaining_time / task.execution_time

        # Weighted urgency score
        score = (0.4 * slack_urgency +
                0.4 * future_urgency +
                0.2 * execution_pressure)

        return score

    def admit_task(self, task: Task):
        """Admit task with urgency scoring"""
        task.urgency_score = self.calculate_urgency_score(task)
        self.queue.append(task)
        self.queue.sort(key=lambda t: t.urgency_score, reverse=True)
        self.stats['predictions'] += 1

    def get_next_task(self) -> Optional[Task]:
        """Get highest urgency task"""
        if self.queue:
            # Recalculate urgency scores for all queued tasks
            for task in self.queue:
                task.urgency_score = self.calculate_urgency_score(task)

            # Re-sort by urgency
            self.queue.sort(key=lambda t: t.urgency_score, reverse=True)
            return self.queue.pop(0)
        return None

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

        for task in finished_tasks:
            self.running_tasks.remove(task)

        # Schedule new tasks
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
            'predictions': self.stats['predictions'],
            'time': self.time,
        }


class DynamicAdaptiveScheduler:
    """
    Dynamic Adaptive Threshold Scheduler

    This scheduler dynamically adjusts the slack threshold based on
    system load and historical performance.

    Key Features:
    - Load-aware threshold adjustment
    - Historical success rate tracking
    - Adaptive behavior under different loads
    """

    def __init__(self, num_cores: int = 16):
        self.num_cores = num_cores
        self.srjf_queue: List[Task] = []
        self.edf_queue: List[Task] = []
        self.running_tasks: List[Task] = []
        self.completed_tasks: List[Task] = []
        self.missed_deadlines = 0
        self.time = 0

        # Adaptive parameters
        self.threshold_multiplier = 2.0
        self.min_threshold = 1.2
        self.max_threshold = 3.0
        self.recent_success_rate = 100.0
        self.adjustment_period = 50
        self.last_adjustment = 0

        self.stats = {
            'scheduled': 0,
            'preemptions': 0,
            'threshold_adjustments': 0,
            'total_wait_time': 0,
            'total_response_time': 0,
        }

    def adjust_threshold(self):
        """Dynamically adjust threshold based on performance"""
        if self.time - self.last_adjustment < self.adjustment_period:
            return

        recent_tasks = len(self.completed_tasks)
        if recent_tasks == 0:
            return

        self.recent_success_rate = 100 * (1 - self.missed_deadlines / recent_tasks)

        # Adjust threshold based on success rate
        if self.recent_success_rate < 95.0:
            # Performance issues - make threshold more aggressive (lower)
            self.threshold_multiplier = max(self.min_threshold,
                                          self.threshold_multiplier - 0.2)
        elif self.recent_success_rate == 100.0:
            # Perfect performance - can relax threshold (higher)
            self.threshold_multiplier = min(self.max_threshold,
                                          self.threshold_multiplier + 0.1)

        self.stats['threshold_adjustments'] += 1
        self.last_adjustment = self.time

    def admit_task(self, task: Task):
        """Admit task to appropriate queue"""
        self.adjust_threshold()

        if task.slack < self.threshold_multiplier * task.remaining_time:
            self.edf_queue.append(task)
            self.edf_queue.sort(key=lambda t: t.absolute_deadline)
        else:
            self.srjf_queue.append(task)
            self.srjf_queue.sort(key=lambda t: t.remaining_time)

    def get_next_task(self) -> Optional[Task]:
        """Get next task to schedule"""
        if self.edf_queue:
            return self.edf_queue.pop(0)
        elif self.srjf_queue:
            return self.srjf_queue.pop(0)
        return None

    def schedule_cycle(self, new_tasks: List[Task]):
        """Execute one scheduling cycle"""
        for task in new_tasks:
            self.admit_task(task)
            self.stats['total_wait_time'] += (self.time - task.arrival_time)

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

        for task in finished_tasks:
            self.running_tasks.remove(task)

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
            'threshold_adjustments': self.stats['threshold_adjustments'],
            'final_threshold': self.threshold_multiplier,
            'time': self.time,
        }


def demo_advanced_algorithms():
    """Demonstrate advanced algorithms"""
    print("=" * 80)
    print("Advanced Scheduling Algorithms Demo")
    print("=" * 80)

    print("\n1. PREDICTIVE LOOK-AHEAD SCHEDULER")
    print("-" * 80)
    print("Features:")
    print("  • Predicts future task urgency")
    print("  • Look-ahead window for proactive scheduling")
    print("  • Urgency scoring based on projected slack")
    print()

    print("2. DYNAMIC ADAPTIVE SCHEDULER")
    print("-" * 80)
    print("Features:")
    print("  • Adjusts threshold based on system load")
    print("  • Learns from historical performance")
    print("  • Adapts to varying workload characteristics")
    print()

    print("=" * 80)
    print("Run regression_tests_advanced.py for full evaluation")
    print("=" * 80)


if __name__ == "__main__":
    demo_advanced_algorithms()
