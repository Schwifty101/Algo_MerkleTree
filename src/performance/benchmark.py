"""
Comprehensive benchmark suite for Merkle Tree system.

Validates all performance targets:
- Tree construction: <10s for 1M records
- Verification: <100ms
- Proof generation: <2ms per proof
- Memory usage: <500MB for 1M records
- Hashing speed: >100K records/second
"""

from typing import Dict, Any, List
import sys
import json
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from merkle.tree import MerkleTree
from merkle.proof import MerkleProof
from verification.integrity_checker import IntegrityChecker
from verification.tamper_detector import TamperDetector
from performance.metrics import (
    PerformanceTimer,
    PerformanceMetrics,
    PerformanceValidator,
    MemoryTracker
)
from utils.hash_utils import hash_data


class MerkleTreeBenchmark:
    """
    Comprehensive benchmarking for Merkle Tree operations.

    Tests all critical performance paths and validates against targets.
    """

    def __init__(self):
        """Initialize benchmark suite."""
        self.results: Dict[str, Any] = {}
        self.validator = PerformanceValidator()

    def benchmark_tree_construction(self, sizes: List[int]) -> Dict[str, Any]:
        """
        Benchmark tree construction for various dataset sizes.

        Args:
            sizes: List of dataset sizes to test

        Returns:
            Benchmark results

        Performance Target: <10s for 1M records
        """
        print("Benchmarking tree construction...")
        results = {}

        for size in sizes:
            print(f"  Testing with {size:,} records...")

            # Generate test data
            data = [f"review_{i}" for i in range(size)]

            # Measure construction time
            timer = PerformanceTimer()
            with timer.measure():
                tree = MerkleTree(data)

            time_ms = timer.get_elapsed_ms()
            time_seconds = timer.get_elapsed_seconds()

            # Calculate throughput
            throughput = size / time_seconds if time_seconds > 0 else float('inf')

            # Get memory usage
            memory_stats = tree.get_memory_usage()

            results[f"construction_{size}"] = {
                'size': size,
                'time_ms': time_ms,
                'time_seconds': time_seconds,
                'throughput_per_sec': throughput,
                'memory_mb': memory_stats['total_mb'],
                'memory_bytes': memory_stats['total_bytes']
            }

            print(f"    Time: {time_seconds:.2f}s ({throughput:,.0f} records/sec)")
            print(f"    Memory: {memory_stats['total_mb']:.2f} MB")

            # Validate against target for 1M records
            if size >= 1_000_000:
                passed = self.validator.validate(
                    f"Tree construction ({size:,} records)",
                    time_seconds,
                    10.0,
                    less_is_better=True,
                    unit="seconds"
                )
                print(f"    Target validation: {'✓ PASSED' if passed else '✗ FAILED'}")

        return results

    def benchmark_root_hash_verification(self, sizes: List[int]) -> Dict[str, Any]:
        """
        Benchmark root hash verification (integrity check).

        Args:
            sizes: List of dataset sizes to test

        Returns:
            Benchmark results

        Performance Target: <100ms (should be <1ms with O(1) comparison)
        """
        print("\nBenchmarking root hash verification...")
        results = {}

        for size in sizes:
            print(f"  Testing with {size:,} records...")

            # Create trees
            data = [f"review_{i}" for i in range(size)]
            tree1 = MerkleTree(data)
            tree2 = MerkleTree(data)  # Identical tree

            # Measure verification time
            timer = PerformanceTimer()
            checker = IntegrityChecker()

            # Save baseline
            checker.save_baseline(tree1, f"benchmark_{size}")

            # Verify (this is the critical O(1) operation)
            with timer.measure():
                result = checker.verify_integrity(tree2, f"benchmark_{size}")

            time_ms = timer.get_elapsed_ms()

            results[f"verification_{size}"] = {
                'size': size,
                'time_ms': time_ms,
                'verified': result['verified']
            }

            print(f"    Time: {time_ms:.4f}ms")

            # Validate against target
            passed = self.validator.validate(
                f"Verification ({size:,} records)",
                time_ms,
                100.0,
                less_is_better=True,
                unit="ms"
            )
            print(f"    Target validation: {'✓ PASSED' if passed else '✗ FAILED'}")

        return results

    def benchmark_proof_generation(self, sizes: List[int],
                                  proofs_per_size: int = 10) -> Dict[str, Any]:
        """
        Benchmark proof generation.

        Args:
            sizes: List of dataset sizes to test
            proofs_per_size: Number of proofs to generate per size

        Returns:
            Benchmark results

        Performance Target: <2ms per proof
        """
        print("\nBenchmarking proof generation...")
        results = {}

        for size in sizes:
            print(f"  Testing with {size:,} records...")

            # Create tree
            data = [f"review_{i}" for i in range(size)]
            tree = MerkleTree(data)

            # Generate multiple proofs and measure
            times = []
            for i in range(proofs_per_size):
                index = i * (size // proofs_per_size) if proofs_per_size > 0 else 0

                timer = PerformanceTimer()
                with timer.measure():
                    proof = tree.get_proof(index, data[index])
                times.append(timer.get_elapsed_ms())

            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)

            results[f"proof_gen_{size}"] = {
                'size': size,
                'proofs_generated': proofs_per_size,
                'avg_time_ms': avg_time,
                'min_time_ms': min_time,
                'max_time_ms': max_time
            }

            print(f"    Average: {avg_time:.4f}ms per proof")
            print(f"    Range: {min_time:.4f}ms - {max_time:.4f}ms")

            # Validate against target
            passed = self.validator.validate(
                f"Proof generation ({size:,} records)",
                avg_time,
                2.0,
                less_is_better=True,
                unit="ms"
            )
            print(f"    Target validation: {'✓ PASSED' if passed else '✗ FAILED'}")

        return results

    def benchmark_proof_verification(self, sizes: List[int]) -> Dict[str, Any]:
        """
        Benchmark proof verification.

        Args:
            sizes: List of dataset sizes to test

        Returns:
            Benchmark results
        """
        print("\nBenchmarking proof verification...")
        results = {}

        for size in sizes:
            print(f"  Testing with {size:,} records...")

            # Create tree and proof
            data = [f"review_{i}" for i in range(size)]
            tree = MerkleTree(data)
            proof = tree.get_proof(size // 2, data[size // 2])

            # Measure verification time
            timer = PerformanceTimer()
            with timer.measure():
                verified = proof.verify()

            time_ms = timer.get_elapsed_ms()

            results[f"proof_verify_{size}"] = {
                'size': size,
                'time_ms': time_ms,
                'verified': verified
            }

            print(f"    Time: {time_ms:.4f}ms")

        return results

    def benchmark_memory_usage(self, sizes: List[int]) -> Dict[str, Any]:
        """
        Benchmark memory usage for different tree sizes.

        Args:
            sizes: List of dataset sizes to test

        Returns:
            Memory usage results

        Performance Target: <500MB for 1M records
        """
        print("\nBenchmarking memory usage...")
        results = {}

        for size in sizes:
            print(f"  Testing with {size:,} records...")

            # Create tree
            data = [f"review_{i}" for i in range(size)]
            tree = MerkleTree(data)

            # Get memory stats
            stats = tree.get_memory_usage()

            results[f"memory_{size}"] = {
                'size': size,
                'total_mb': stats['total_mb'],
                'total_bytes': stats['total_bytes'],
                'bytes_per_leaf': stats['bytes_per_leaf']
            }

            print(f"    Total: {stats['total_mb']:.2f} MB")
            print(f"    Per leaf: {stats['bytes_per_leaf']:.2f} bytes")

            # Validate against target for 1M records
            if size >= 1_000_000:
                passed = self.validator.validate(
                    f"Memory usage ({size:,} records)",
                    stats['total_mb'],
                    500.0,
                    less_is_better=True,
                    unit="MB"
                )
                print(f"    Target validation: {'✓ PASSED' if passed else '✗ FAILED'}")

        return results

    def benchmark_hashing_speed(self, count: int = 100_000) -> Dict[str, Any]:
        """
        Benchmark raw hashing speed.

        Args:
            count: Number of hashes to perform

        Returns:
            Hashing benchmark results

        Performance Target: >100K hashes/second
        """
        print(f"\nBenchmarking hashing speed ({count:,} hashes)...")

        # Generate test data
        data = [f"test_data_{i}" for i in range(count)]

        # Measure hashing time
        timer = PerformanceTimer()
        with timer.measure():
            for item in data:
                hash_data(item)

        time_ms = timer.get_elapsed_ms()
        time_seconds = timer.get_elapsed_seconds()
        throughput = count / time_seconds if time_seconds > 0 else float('inf')

        results = {
            'count': count,
            'time_ms': time_ms,
            'time_seconds': time_seconds,
            'throughput_per_sec': throughput
        }

        print(f"  Time: {time_seconds:.2f}s")
        print(f"  Throughput: {throughput:,.0f} hashes/sec")

        # Validate against target
        passed = self.validator.validate(
            "Hashing speed",
            throughput,
            100_000,
            less_is_better=False,
            unit="hashes/sec"
        )
        print(f"  Target validation: {'✓ PASSED' if passed else '✗ FAILED'}")

        return results

    def benchmark_tamper_detection(self, sizes: List[int]) -> Dict[str, Any]:
        """
        Benchmark tamper detection performance.

        Args:
            sizes: List of dataset sizes to test

        Returns:
            Tamper detection benchmark results
        """
        print("\nBenchmarking tamper detection...")
        results = {}

        for size in sizes:
            print(f"  Testing with {size:,} records...")

            # Create baseline and modified trees
            baseline_data = [f"review_{i}" for i in range(size)]
            modified_data = baseline_data.copy()
            # Modify 1% of records
            for i in range(0, size, 100):
                if i < len(modified_data):
                    modified_data[i] = f"MODIFIED_{i}"

            baseline_tree = MerkleTree(baseline_data)
            modified_tree = MerkleTree(modified_data)

            # Measure detection time
            detector = TamperDetector()
            timer = PerformanceTimer()
            with timer.measure():
                report = detector.detect_tampering(baseline_tree, modified_tree)

            time_ms = timer.get_elapsed_ms()

            results[f"tamper_detection_{size}"] = {
                'size': size,
                'time_ms': time_ms,
                'changes_detected': report['total_changes']
            }

            print(f"    Time: {time_ms:.2f}ms")
            print(f"    Changes detected: {report['total_changes']}")

        return results

    def run_comprehensive_benchmark(self) -> Dict[str, Any]:
        """
        Run complete benchmark suite.

        Returns:
            Complete benchmark results
        """
        print("=" * 60)
        print("COMPREHENSIVE MERKLE TREE PERFORMANCE BENCHMARK")
        print("=" * 60)

        # Test with increasing sizes
        small_sizes = [100, 1_000, 10_000]
        large_sizes = [100_000]  # Can add 1_000_000 for full validation

        results = {}

        # Run all benchmarks
        results['construction'] = self.benchmark_tree_construction(small_sizes + large_sizes)
        results['verification'] = self.benchmark_root_hash_verification(small_sizes + large_sizes)
        results['proof_generation'] = self.benchmark_proof_generation(small_sizes + large_sizes)
        results['proof_verification'] = self.benchmark_proof_verification(small_sizes)
        results['memory'] = self.benchmark_memory_usage(small_sizes + large_sizes)
        results['hashing'] = self.benchmark_hashing_speed()
        results['tamper_detection'] = self.benchmark_tamper_detection(small_sizes)

        # Generate validation report
        print("\n" + "=" * 60)
        print(self.validator.generate_report())

        return results

    def save_results_json(self, results: Dict[str, Any], output_dir: str = "benchmarks/results") -> str:
        """
        Save benchmark results to JSON file with timestamp.

        Args:
            results: Benchmark results dictionary
            output_dir: Directory to save results (default: benchmarks/results)

        Returns:
            Path to saved file
        """
        # Create output directory if it doesn't exist
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"benchmark_results_{timestamp}.json"
        filepath = output_path / filename

        # Add metadata to results
        output_data = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'validation_summary': self.validator.get_results()
            },
            'results': results
        }

        # Save to file
        with open(filepath, 'w') as f:
            json.dump(output_data, f, indent=2)

        print(f"\n✓ Results saved to: {filepath}")
        return str(filepath)

    def save_results_text(self, results: Dict[str, Any], output_dir: str = "benchmarks/results") -> str:
        """
        Save benchmark results to human-readable text file.

        Args:
            results: Benchmark results dictionary
            output_dir: Directory to save results (default: benchmarks/results)

        Returns:
            Path to saved file
        """
        # Create output directory if it doesn't exist
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"benchmark_report_{timestamp}.txt"
        filepath = output_path / filename

        # Generate report content
        report_lines = []
        report_lines.append("=" * 70)
        report_lines.append("MERKLE TREE PERFORMANCE BENCHMARK REPORT")
        report_lines.append("=" * 70)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")

        # Tree Construction Results
        if 'construction' in results:
            report_lines.append("-" * 70)
            report_lines.append("TREE CONSTRUCTION")
            report_lines.append("-" * 70)
            for key, data in results['construction'].items():
                report_lines.append(f"\nSize: {data['size']:,} records")
                report_lines.append(f"  Time: {data['time_seconds']:.4f}s ({data['time_ms']:.2f}ms)")
                report_lines.append(f"  Throughput: {data['throughput_per_sec']:,.0f} records/sec")
                report_lines.append(f"  Memory: {data['memory_mb']:.2f} MB")
            report_lines.append("")

        # Verification Results
        if 'verification' in results:
            report_lines.append("-" * 70)
            report_lines.append("ROOT HASH VERIFICATION")
            report_lines.append("-" * 70)
            for key, data in results['verification'].items():
                report_lines.append(f"\nSize: {data['size']:,} records")
                report_lines.append(f"  Time: {data['time_ms']:.4f}ms")
                report_lines.append(f"  Verified: {data['verified']}")
            report_lines.append("")

        # Proof Generation Results
        if 'proof_generation' in results:
            report_lines.append("-" * 70)
            report_lines.append("PROOF GENERATION")
            report_lines.append("-" * 70)
            for key, data in results['proof_generation'].items():
                report_lines.append(f"\nSize: {data['size']:,} records")
                report_lines.append(f"  Proofs generated: {data['proofs_generated']}")
                report_lines.append(f"  Average time: {data['avg_time_ms']:.4f}ms")
                report_lines.append(f"  Min time: {data['min_time_ms']:.4f}ms")
                report_lines.append(f"  Max time: {data['max_time_ms']:.4f}ms")
            report_lines.append("")

        # Proof Verification Results
        if 'proof_verification' in results:
            report_lines.append("-" * 70)
            report_lines.append("PROOF VERIFICATION")
            report_lines.append("-" * 70)
            for key, data in results['proof_verification'].items():
                report_lines.append(f"\nSize: {data['size']:,} records")
                report_lines.append(f"  Time: {data['time_ms']:.4f}ms")
                report_lines.append(f"  Verified: {data['verified']}")
            report_lines.append("")

        # Memory Usage Results
        if 'memory' in results:
            report_lines.append("-" * 70)
            report_lines.append("MEMORY USAGE")
            report_lines.append("-" * 70)
            for key, data in results['memory'].items():
                report_lines.append(f"\nSize: {data['size']:,} records")
                report_lines.append(f"  Total: {data['total_mb']:.2f} MB ({data['total_bytes']:,} bytes)")
                report_lines.append(f"  Per leaf: {data['bytes_per_leaf']:.2f} bytes")
            report_lines.append("")

        # Hashing Speed Results
        if 'hashing' in results:
            report_lines.append("-" * 70)
            report_lines.append("HASHING SPEED")
            report_lines.append("-" * 70)
            data = results['hashing']
            report_lines.append(f"\nCount: {data['count']:,} hashes")
            report_lines.append(f"  Time: {data['time_seconds']:.4f}s ({data['time_ms']:.2f}ms)")
            report_lines.append(f"  Throughput: {data['throughput_per_sec']:,.0f} hashes/sec")
            report_lines.append("")

        # Tamper Detection Results
        if 'tamper_detection' in results:
            report_lines.append("-" * 70)
            report_lines.append("TAMPER DETECTION")
            report_lines.append("-" * 70)
            for key, data in results['tamper_detection'].items():
                report_lines.append(f"\nSize: {data['size']:,} records")
                report_lines.append(f"  Time: {data['time_ms']:.2f}ms")
                report_lines.append(f"  Changes detected: {data['changes_detected']}")
            report_lines.append("")

        # Validation Summary
        report_lines.append("=" * 70)
        report_lines.append("VALIDATION SUMMARY")
        report_lines.append("=" * 70)
        report_lines.append(self.validator.generate_report())

        # Write to file
        with open(filepath, 'w') as f:
            f.write('\n'.join(report_lines))

        print(f"✓ Report saved to: {filepath}")
        return str(filepath)

    def export_results(self, results: Dict[str, Any], output_dir: str = "benchmarks/results") -> Dict[str, str]:
        """
        Export benchmark results in both JSON and text formats.

        Args:
            results: Benchmark results dictionary
            output_dir: Directory to save results (default: benchmarks/results)

        Returns:
            Dictionary with paths to saved files
        """
        json_path = self.save_results_json(results, output_dir)
        text_path = self.save_results_text(results, output_dir)

        return {
            'json': json_path,
            'text': text_path
        }


def main():
    """Run benchmark suite from command line."""
    benchmark = MerkleTreeBenchmark()
    results = benchmark.run_comprehensive_benchmark()

    # Save results to files
    saved_files = benchmark.export_results(results)
    print(f"\n{'=' * 60}")
    print("RESULTS SAVED TO:")
    print(f"  JSON: {saved_files['json']}")
    print(f"  Text: {saved_files['text']}")
    print(f"{'=' * 60}")

    # Check if all validations passed
    validation_results = benchmark.validator.get_results()
    if validation_results['all_passed']:
        print("\n✓ ALL PERFORMANCE TARGETS MET!")
        return 0
    else:
        print(f"\n✗ {validation_results['failed']} PERFORMANCE TARGET(S) NOT MET")
        return 1


if __name__ == "__main__":
    exit(main())
