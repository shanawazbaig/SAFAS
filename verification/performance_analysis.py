#!/usr/bin/env python3
"""
Performance Comparison and Analysis Framework

This framework provides detailed analysis and comparison of different
scheduling algorithms with statistical metrics and insights.

Author: Advanced Implementation
Date: March 23, 2026
"""

import random
import sys
from typing import List, Dict, Tuple
from dataclasses import dataclass
import json


@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics"""
    scheduler_name: str
    success_rate: float
    avg_response_time: float
    avg_wait_time: float
    throughput: float
    missed_deadlines: int
    total_tasks: int
    cpu_utilization: float
    preemptions: int

    def to_dict(self):
        return {
            'scheduler': self.scheduler_name,
            'success_rate': round(self.success_rate, 2),
            'avg_response_time': round(self.avg_response_time, 2),
            'avg_wait_time': round(self.avg_wait_time, 2),
            'throughput': round(self.throughput, 2),
            'missed_deadlines': self.missed_deadlines,
            'total_tasks': self.total_tasks,
            'cpu_utilization': round(self.cpu_utilization, 2),
            'preemptions': self.preemptions,
        }


def generate_ascii_bar_chart(data: Dict[str, float], title: str, max_width: int = 50):
    """Generate ASCII bar chart"""
    print(f"\n{title}")
    print("=" * (max_width + 30))

    max_value = max(data.values()) if data else 1

    for label, value in sorted(data.items(), key=lambda x: x[1], reverse=True):
        bar_length = int((value / max_value) * max_width)
        bar = "█" * bar_length
        print(f"{label:25s} {bar} {value:.2f}")

    print()


def generate_comparison_table(metrics_list: List[PerformanceMetrics]):
    """Generate detailed comparison table"""
    print("\n" + "=" * 120)
    print("DETAILED PERFORMANCE COMPARISON")
    print("=" * 120)

    # Header
    print(f"{'Scheduler':25s} {'Success %':>10s} {'Resp Time':>10s} {'Wait Time':>10s} "
          f"{'Throughput':>12s} {'Missed':>8s} {'Util %':>8s}")
    print("-" * 120)

    # Sort by success rate, then response time
    sorted_metrics = sorted(metrics_list,
                           key=lambda m: (-m.success_rate, m.avg_response_time))

    for metrics in sorted_metrics:
        print(f"{metrics.scheduler_name:25s} "
              f"{metrics.success_rate:10.2f} "
              f"{metrics.avg_response_time:10.2f} "
              f"{metrics.avg_wait_time:10.2f} "
              f"{metrics.throughput:12.2f} "
              f"{metrics.missed_deadlines:8d} "
              f"{metrics.cpu_utilization:8.2f}")

    print("=" * 120)


def analyze_ranking(metrics_list: List[PerformanceMetrics]):
    """Analyze and rank schedulers by different criteria"""
    print("\n" + "=" * 80)
    print("SCHEDULER RANKINGS")
    print("=" * 80)

    # Rank by success rate
    print("\n📊 By Success Rate (Higher is Better):")
    ranked = sorted(metrics_list, key=lambda m: m.success_rate, reverse=True)
    for i, m in enumerate(ranked, 1):
        medal = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else f"{i}."
        print(f"  {medal} {m.scheduler_name:25s} {m.success_rate:.2f}%")

    # Rank by response time
    print("\n⚡ By Response Time (Lower is Better):")
    ranked = sorted(metrics_list, key=lambda m: m.avg_response_time)
    for i, m in enumerate(ranked, 1):
        medal = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else f"{i}."
        print(f"  {medal} {m.scheduler_name:25s} {m.avg_response_time:.2f} cycles")

    # Rank by throughput
    print("\n🚀 By Throughput (Higher is Better):")
    ranked = sorted(metrics_list, key=lambda m: m.throughput, reverse=True)
    for i, m in enumerate(ranked, 1):
        medal = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else f"{i}."
        print(f"  {medal} {m.scheduler_name:25s} {m.throughput:.2f} tasks/cycle")

    # Overall score
    print("\n🏆 Overall Performance Score:")
    print("   (Weighted: 50% success rate, 30% response time, 20% throughput)")

    max_resp = max(m.avg_response_time for m in metrics_list)
    scored = []
    for m in metrics_list:
        # Normalize metrics (0-100 scale)
        success_score = m.success_rate  # Already 0-100
        response_score = 100 * (1 - m.avg_response_time / max_resp)  # Lower is better
        throughput_score = 100 * (m.throughput / max(me.throughput for me in metrics_list))

        # Weighted average
        overall = (0.5 * success_score + 0.3 * response_score + 0.2 * throughput_score)
        scored.append((m.scheduler_name, overall))

    for i, (name, score) in enumerate(sorted(scored, key=lambda x: x[1], reverse=True), 1):
        medal = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else f"{i}."
        print(f"  {medal} {name:25s} {score:.2f}/100")


def generate_insights(metrics_list: List[PerformanceMetrics]):
    """Generate insights and recommendations"""
    print("\n" + "=" * 80)
    print("INSIGHTS AND RECOMMENDATIONS")
    print("=" * 80)

    # Find best performers
    best_success = max(metrics_list, key=lambda m: m.success_rate)
    best_response = min(metrics_list, key=lambda m: m.avg_response_time)
    best_throughput = max(metrics_list, key=lambda m: m.throughput)

    print(f"\n✓ Best Success Rate: {best_success.scheduler_name} ({best_success.success_rate:.2f}%)")
    print(f"✓ Best Response Time: {best_response.scheduler_name} ({best_response.avg_response_time:.2f} cycles)")
    print(f"✓ Best Throughput: {best_throughput.scheduler_name} ({best_throughput.throughput:.2f} tasks/cycle)")

    # Analyze hybrid vs pure schedulers
    hybrid_schedulers = [m for m in metrics_list if 'Hybrid' in m.scheduler_name or 'Multi' in m.scheduler_name or 'LLF' in m.scheduler_name or 'Adaptive' in m.scheduler_name]
    pure_schedulers = [m for m in metrics_list if 'Pure' in m.scheduler_name]

    if hybrid_schedulers and pure_schedulers:
        avg_hybrid_success = sum(m.success_rate for m in hybrid_schedulers) / len(hybrid_schedulers)
        avg_pure_success = sum(m.success_rate for m in pure_schedulers) / len(pure_schedulers)

        print(f"\n📈 Hybrid Schedulers Avg Success: {avg_hybrid_success:.2f}%")
        print(f"📈 Pure Schedulers Avg Success: {avg_pure_success:.2f}%")

        if avg_hybrid_success > avg_pure_success:
            print("✓ Hybrid schedulers show better overall success rates")
        else:
            print("✓ Pure schedulers remain competitive")

    # Recommendations
    print("\n💡 RECOMMENDATIONS:")

    if all(m.success_rate == 100.0 for m in metrics_list):
        print("\n  ✓ All schedulers achieved 100% success rate!")
        print("  ✓ For this workload, choose based on response time optimization")
        print(f"  → Recommended: {best_response.scheduler_name}")
    else:
        # Find schedulers with perfect success
        perfect = [m for m in metrics_list if m.success_rate == 100.0]
        if perfect:
            best_of_perfect = min(perfect, key=lambda m: m.avg_response_time)
            print(f"\n  ✓ For deadline-critical systems: {best_of_perfect.scheduler_name}")
            print(f"    (100% success rate with {best_of_perfect.avg_response_time:.2f} avg response)")

    # Performance insights
    print("\n📊 PERFORMANCE INSIGHTS:")

    # Check if adaptive threshold helps
    hybrid = next((m for m in metrics_list if m.scheduler_name == "Hybrid EDF+SRJF"), None)
    adaptive = next((m for m in metrics_list if m.scheduler_name == "Adaptive Threshold"), None)

    if hybrid and adaptive:
        if adaptive.avg_response_time < hybrid.avg_response_time:
            improvement = ((hybrid.avg_response_time - adaptive.avg_response_time) / hybrid.avg_response_time) * 100
            print(f"\n  ✓ Adaptive threshold improved response time by {improvement:.1f}%")

    # Check multi-level performance
    multi = next((m for m in metrics_list if m.scheduler_name == "Multi-Level Priority"), None)
    if multi and multi.success_rate == 100.0:
        print(f"  ✓ Multi-level priority shows excellent deadline guarantees")

    # LLF analysis
    llf = next((m for m in metrics_list if m.scheduler_name == "LLF Hybrid"), None)
    if llf and llf.avg_response_time < best_response.avg_response_time * 1.1:
        print(f"  ✓ LLF Hybrid balances laxity awareness with performance")


def export_results(metrics_list: List[PerformanceMetrics], filename: str = "performance_results.json"):
    """Export results to JSON"""
    data = {
        'results': [m.to_dict() for m in metrics_list],
        'summary': {
            'total_schedulers': len(metrics_list),
            'best_success_rate': max(m.success_rate for m in metrics_list),
            'best_response_time': min(m.avg_response_time for m in metrics_list),
            'avg_success_rate': sum(m.success_rate for m in metrics_list) / len(metrics_list),
        }
    }

    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"\n📁 Results exported to {filename}")


def main():
    """Run performance comparison"""
    # This would typically be called from regression_tests.py
    # Here we show example usage

    print("=" * 80)
    print("SAFAS Scheduler Performance Analysis Framework")
    print("=" * 80)
    print("\nThis framework provides comprehensive analysis of scheduler performance.")
    print("Run regression_tests.py to generate full comparison data.")
    print()

    # Example metrics (would come from actual tests)
    example_metrics = [
        PerformanceMetrics("Hybrid EDF+SRJF", 100.0, 28.67, 15.2, 0.95, 0, 300, 87.5, 12),
        PerformanceMetrics("Adaptive Threshold", 100.0, 28.07, 14.8, 0.96, 0, 300, 88.2, 15),
        PerformanceMetrics("Multi-Level Priority", 100.0, 28.77, 15.5, 0.94, 0, 300, 86.8, 18),
        PerformanceMetrics("LLF Hybrid", 100.0, 27.43, 14.2, 0.97, 0, 300, 89.1, 14),
        PerformanceMetrics("Pure EDF", 100.0, 26.45, 13.8, 0.98, 0, 300, 90.3, 10),
        PerformanceMetrics("Pure SRJF", 100.0, 27.62, 14.5, 0.96, 0, 300, 88.7, 8),
    ]

    generate_comparison_table(example_metrics)
    analyze_ranking(example_metrics)
    generate_insights(example_metrics)

    # Bar charts
    success_data = {m.scheduler_name: m.success_rate for m in example_metrics}
    generate_ascii_bar_chart(success_data, "Success Rate Comparison (%)")

    response_data = {m.scheduler_name: m.avg_response_time for m in example_metrics}
    generate_ascii_bar_chart(response_data, "Average Response Time (cycles)")

    export_results(example_metrics)

    print("\n" + "=" * 80)
    print("Analysis complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
