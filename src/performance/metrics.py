"""
Performance metrics and measurement tools.

This module provides utilities for measuring and analyzing performance:
- Execution time measurement
- Memory usage tracking
- Throughput calculation
- Performance reporting

Used to validate performance targets:
- Tree construction: <10s for 1M records
- Verification: <100ms
- Proof generation: <2ms per proof
- Memory usage: <500MB for 1M records
- Hashing speed: >100K records/second
"""

import time
import sys
from typing import Dict, Any, Callable, Optional, List
from datetime import datetime
from contextlib import contextmanager


class PerformanceTimer:
    """
    High-precision timer for performance measurement.

    Uses time.perf_counter() for accurate timing.
    """

    def __init__(self):
        """Initialize performance timer."""
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.elapsed_ms: Optional[float] = None

    def start(self) -> None:
        """Start the timer."""
        self.start_time = time.perf_counter()
        self.end_time = None
        self.elapsed_ms = None

    def stop(self) -> float:
        """
        Stop the timer and calculate elapsed time.

        Returns:
            Elapsed time in milliseconds
        """
        if self.start_time is None:
            raise RuntimeError("Timer not started")

        self.end_time = time.perf_counter()
        self.elapsed_ms = (self.end_time - self.start_time) * 1000
        return self.elapsed_ms

    def get_elapsed_ms(self) -> float:
        """Get elapsed time in milliseconds."""
        if self.elapsed_ms is None:
            raise RuntimeError("Timer not stopped")
        return self.elapsed_ms

    def get_elapsed_seconds(self) -> float:
        """Get elapsed time in seconds."""
        return self.get_elapsed_ms() / 1000

    @contextmanager
    def measure(self):
        """
        Context manager for timing a block of code.

        Example:
            >>> timer = PerformanceTimer()
            >>> with timer.measure():
            ...     # code to time
            ...     pass
            >>> print(f"Took {timer.get_elapsed_ms():.2f}ms")
        """
        self.start()
        try:
            yield self
        finally:
            self.stop()


class MemoryTracker:
    """
    Memory usage tracker.

    Measures memory consumption of objects and operations.
    """

    @staticmethod
    def get_object_size(obj: Any) -> int:
        """
        Get size of an object in bytes.

        Args:
            obj: Object to measure

        Returns:
            Size in bytes
        """
        return sys.getsizeof(obj)

    @staticmethod
    def format_bytes(size_bytes: int) -> str:
        """
        Format bytes as human-readable string.

        Args:
            size_bytes: Size in bytes

        Returns:
            Formatted string (e.g., "1.5 MB")
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"

    @staticmethod
    def bytes_to_mb(size_bytes: int) -> float:
        """Convert bytes to megabytes."""
        return size_bytes / (1024 * 1024)

    @staticmethod
    def bytes_to_kb(size_bytes: int) -> float:
        """Convert bytes to kilobytes."""
        return size_bytes / 1024


class ThroughputCalculator:
    """
    Calculate throughput for various operations.

    Useful for measuring records/second, hashes/second, etc.
    """

    @staticmethod
    def calculate_throughput(count: int, time_ms: float) -> float:
        """
        Calculate throughput in items per second.

        Args:
            count: Number of items processed
            time_ms: Time taken in milliseconds

        Returns:
            Items per second
        """
        if time_ms <= 0:
            return float('inf')

        time_seconds = time_ms / 1000
        return count / time_seconds

    @staticmethod
    def calculate_avg_time_per_item(count: int, time_ms: float) -> float:
        """
        Calculate average time per item in milliseconds.

        Args:
            count: Number of items
            time_ms: Total time in milliseconds

        Returns:
            Milliseconds per item
        """
        if count <= 0:
            return 0.0

        return time_ms / count


class PerformanceMetrics:
    """
    Collects and reports performance metrics.

    Tracks multiple measurements and generates reports.
    """

    def __init__(self, name: str = "Performance Test"):
        """
        Initialize metrics collector.

        Args:
            name: Name of this performance test
        """
        self.name = name
        self.measurements: Dict[str, Any] = {}
        self.start_timestamp = datetime.now().isoformat()

    def record(self, metric_name: str, value: Any) -> None:
        """
        Record a metric value.

        Args:
            metric_name: Name of the metric
            value: Value to record
        """
        self.measurements[metric_name] = value

    def record_time(self, operation: str, time_ms: float) -> None:
        """
        Record execution time for an operation.

        Args:
            operation: Name of operation
            time_ms: Time in milliseconds
        """
        self.measurements[f"{operation}_time_ms"] = time_ms
        self.measurements[f"{operation}_time_seconds"] = time_ms / 1000

    def record_memory(self, operation: str, size_bytes: int) -> None:
        """
        Record memory usage.

        Args:
            operation: Name of operation
            size_bytes: Memory size in bytes
        """
        self.measurements[f"{operation}_memory_bytes"] = size_bytes
        self.measurements[f"{operation}_memory_mb"] = size_bytes / (1024 * 1024)

    def record_throughput(self, operation: str, count: int, time_ms: float) -> None:
        """
        Record throughput metrics.

        Args:
            operation: Name of operation
            count: Number of items processed
            time_ms: Time taken in milliseconds
        """
        throughput = ThroughputCalculator.calculate_throughput(count, time_ms)
        avg_time = ThroughputCalculator.calculate_avg_time_per_item(count, time_ms)

        self.measurements[f"{operation}_count"] = count
        self.measurements[f"{operation}_throughput_per_sec"] = throughput
        self.measurements[f"{operation}_avg_time_ms"] = avg_time

    def check_threshold(self, metric_name: str, threshold: float,
                       less_is_better: bool = True) -> bool:
        """
        Check if a metric meets a threshold.

        Args:
            metric_name: Name of metric to check
            threshold: Threshold value
            less_is_better: True if lower values are better

        Returns:
            True if threshold is met
        """
        if metric_name not in self.measurements:
            return False

        value = self.measurements[metric_name]

        if less_is_better:
            return value <= threshold
        else:
            return value >= threshold

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of all measurements.

        Returns:
            Dictionary with all metrics
        """
        return {
            'test_name': self.name,
            'timestamp': self.start_timestamp,
            'measurements': self.measurements.copy()
        }

    def generate_report(self) -> str:
        """
        Generate human-readable performance report.

        Returns:
            Formatted report string
        """
        report = f"""
Performance Report: {self.name}
{'=' * 60}
Timestamp: {self.start_timestamp}

Measurements:
"""

        for metric, value in sorted(self.measurements.items()):
            if isinstance(value, float):
                report += f"  {metric}: {value:.4f}\n"
            else:
                report += f"  {metric}: {value}\n"

        report += f"{'=' * 60}\n"
        return report


def measure_function(func: Callable, *args, **kwargs) -> Dict[str, Any]:
    """
    Measure execution time of a function.

    Args:
        func: Function to measure
        *args: Positional arguments for function
        **kwargs: Keyword arguments for function

    Returns:
        Dictionary with result, time, and error (if any)

    Example:
        >>> result = measure_function(my_function, arg1, arg2, kwarg1=value1)
        >>> print(f"Took {result['time_ms']:.2f}ms")
    """
    timer = PerformanceTimer()
    error = None
    result = None

    try:
        timer.start()
        result = func(*args, **kwargs)
        timer.stop()
    except Exception as e:
        timer.stop()
        error = str(e)

    return {
        'result': result,
        'time_ms': timer.get_elapsed_ms(),
        'time_seconds': timer.get_elapsed_seconds(),
        'error': error,
        'success': error is None
    }


def benchmark_iterations(func: Callable, iterations: int,
                        *args, **kwargs) -> Dict[str, Any]:
    """
    Benchmark a function over multiple iterations.

    Args:
        func: Function to benchmark
        iterations: Number of iterations
        *args: Positional arguments for function
        **kwargs: Keyword arguments for function

    Returns:
        Dictionary with timing statistics

    Example:
        >>> stats = benchmark_iterations(my_function, 100, arg1, arg2)
        >>> print(f"Average: {stats['avg_time_ms']:.2f}ms")
    """
    times: List[float] = []

    for _ in range(iterations):
        timer = PerformanceTimer()
        with timer.measure():
            func(*args, **kwargs)
        times.append(timer.get_elapsed_ms())

    return {
        'iterations': iterations,
        'total_time_ms': sum(times),
        'avg_time_ms': sum(times) / iterations,
        'min_time_ms': min(times),
        'max_time_ms': max(times),
        'times': times
    }


class PerformanceValidator:
    """
    Validates performance against target thresholds.

    Used to ensure system meets performance requirements.
    """

    def __init__(self):
        """Initialize performance validator."""
        self.validations: List[Dict[str, Any]] = []

    def validate(self,
                name: str,
                actual_value: float,
                target_value: float,
                less_is_better: bool = True,
                unit: str = "ms") -> bool:
        """
        Validate a performance metric against target.

        Args:
            name: Name of metric
            actual_value: Measured value
            target_value: Target threshold
            less_is_better: True if lower is better
            unit: Unit of measurement

        Returns:
            True if validation passes

        Example:
            >>> validator = PerformanceValidator()
            >>> validator.validate("verification", 8.5, 100, less_is_better=True, unit="ms")
            True
        """
        if less_is_better:
            passed = actual_value <= target_value
            comparison = f"{actual_value:.2f} <= {target_value:.2f}"
        else:
            passed = actual_value >= target_value
            comparison = f"{actual_value:.2f} >= {target_value:.2f}"

        self.validations.append({
            'name': name,
            'actual': actual_value,
            'target': target_value,
            'unit': unit,
            'passed': passed,
            'less_is_better': less_is_better,
            'comparison': comparison
        })

        return passed

    def get_results(self) -> Dict[str, Any]:
        """
        Get validation results.

        Returns:
            Dictionary with all validation results
        """
        total = len(self.validations)
        passed = sum(1 for v in self.validations if v['passed'])

        return {
            'total_validations': total,
            'passed': passed,
            'failed': total - passed,
            'all_passed': passed == total,
            'validations': self.validations
        }

    def generate_report(self) -> str:
        """
        Generate validation report.

        Returns:
            Formatted report string
        """
        results = self.get_results()

        report = f"""
Performance Validation Report
{'=' * 60}
Total Validations: {results['total_validations']}
Passed: {results['passed']}
Failed: {results['failed']}
Status: {'✓ ALL PASSED' if results['all_passed'] else '✗ SOME FAILED'}

Details:
"""

        for v in results['validations']:
            status = '✓' if v['passed'] else '✗'
            report += f"  {status} {v['name']}: {v['comparison']} {v['unit']}\n"

        report += f"{'=' * 60}\n"
        return report
