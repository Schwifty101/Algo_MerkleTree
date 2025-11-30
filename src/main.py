"""
Merkle Tree Integrity Verification System - Main CLI Entry Point

Interactive menu-based interface for managing Amazon review datasets
and performing integrity verification using Merkle Trees.
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Any

# Add src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

from preprocessing.loader import load_with_cache
from merkle.tree import MerkleTree
from merkle.proof import MerkleProof
from verification.integrity_checker import IntegrityChecker
from verification.tamper_detector import TamperDetector
from utils.hash_utils import bytes_to_hex
from utils.storage import HashStorage


def print_header():
    """Display application header."""
    print("\n" + "="*60)
    print("  MERKLE TREE INTEGRITY VERIFICATION SYSTEM")
    print("  Amazon Review Dataset - Cryptographic Verification")
    print("="*60 + "\n")


def print_main_menu():
    """Display main menu options."""
    print("Main Menu:")
    print("  1. Data Management")
    print("  2. Merkle Tree Operations")
    print("  3. Integrity Verification")
    print("  4. Existence Proofs")
    print("  5. Tamper Detection")
    print("  6. Performance Testing")
    print("  7. Test Cases (As Per Spec)")
    print("  0. Exit")
    print()


def print_data_menu():
    """Display data management submenu."""
    print("\nData Management:")
    print("  1.1. Download Amazon Review Dataset")
    print("  1.2. Load Dataset from File")
    print("  1.3. View Dataset Statistics")
    print("  0. Back to Main Menu")
    print()


def print_tree_menu():
    """Display Merkle tree operations submenu."""
    print("\nMerkle Tree Operations:")
    print("  2.1. Build Merkle Tree")
    print("  2.2. View Tree Information")
    print("  2.3. Export Root Hash")
    print("  0. Back to Main Menu")
    print()


def print_verification_menu():
    """Display integrity verification submenu."""
    print("\nIntegrity Verification:")
    print("  3.1. Verify Dataset Integrity")
    print("  3.2. Store Current Root Hash")
    print("  3.3. Compare with Stored Hash")
    print("  0. Back to Main Menu")
    print()


def print_proof_menu():
    """Display existence proof submenu."""
    print("\nExistence Proofs:")
    print("  4.1. Generate Proof for Review")
    print("  4.2. Verify Proof")
    print("  4.3. Batch Proof Generation")
    print("  0. Back to Main Menu")
    print()


def print_tamper_menu():
    """Display tamper detection submenu."""
    print("\nTamper Detection:")
    print("  5.1. Simulate Modification")
    print("  5.2. Simulate Deletion")
    print("  5.3. Simulate Insertion")
    print("  5.4. Generate Tamper Report")
    print("  0. Back to Main Menu")
    print()


def print_performance_menu():
    """Display performance testing submenu."""
    print("\nPerformance Testing:")
    print("  6.1. Measure Hashing Speed")
    print("  6.2. Benchmark Tree Construction")
    print("  6.3. Benchmark Proof Generation")
    print("  6.4. Run Full Performance Suite")
    print("  0. Back to Main Menu")
    print()


def print_test_cases_menu():
    """Display test cases submenu."""
    print("\nTest Cases (As Per Spec):")
    print("  7.1. Run All Required Test Cases")
    print("  0. Back to Main Menu")
    print()


def get_user_choice(prompt="Enter choice: ") -> str:
    """
    Get user input with prompt.

    Args:
        prompt: Prompt string to display

    Returns:
        User input as string
    """
    try:
        return input(prompt).strip()
    except (KeyboardInterrupt, EOFError):
        print("\n\nExiting...")
        sys.exit(0)


def main():
    """Main application loop."""
    print_header()

    # Application state
    dataset = None
    merkle_tree = None
    integrity_checker = IntegrityChecker()
    tamper_detector = TamperDetector()

    while True:
        print_main_menu()
        choice = get_user_choice()

        if choice == '0':
            print("\nThank you for using Merkle Tree Verification System!")
            print("Goodbye!\n")
            break

        elif choice == '1':
            # Data Management
            while True:
                print_data_menu()
                sub_choice = get_user_choice()
                if sub_choice == '0':
                    break
                elif sub_choice == '1.1':
                    print("\n[Download Dataset]")
                    print("Note: Dataset should be placed in data/raw/ directory")
                    print("Recommended: Electronics_5.json from Amazon review dataset")
                    print("Download from: http://jmcauley.ucsd.edu/data/amazon/\n")
                elif sub_choice == '1.2':
                    print("\n[Load Dataset]")
                    limit_str = get_user_choice("Enter number of records to load (or press Enter for all): ")
                    limit = int(limit_str) if limit_str else None

                    try:
                        # Default dataset path
                        json_path = "data/raw/Electronics_5.json"
                        cache_dir = "data/cache"

                        print("Loading dataset...")
                        dataset = load_with_cache(json_path, cache_dir, limit=limit)
                        print(f"\nSuccessfully loaded {len(dataset)} reviews!")

                        # Reset tree when new data is loaded
                        merkle_tree = None
                        print("Note: Merkle tree will need to be rebuilt.\n")
                    except Exception as e:
                        print(f"\nError loading dataset: {e}\n")
                elif sub_choice == '1.3':
                    if dataset is None:
                        print("\nNo dataset loaded. Please load a dataset first.\n")
                    else:
                        print("\n[Dataset Statistics]")
                        print(f"Total reviews: {len(dataset)}")

                        if dataset:
                            # Sample review
                            sample = dataset[0]
                            print(f"\nSample review fields:")
                            for key in sample.keys():
                                print(f"  - {key}")

                            # Rating distribution
                            ratings = {}
                            for review in dataset[:1000]:  # Sample first 1000
                                rating = review.get('overall', 0)
                                ratings[rating] = ratings.get(rating, 0) + 1
                            print(f"\nRating distribution (first 1000):")
                            for rating in sorted(ratings.keys()):
                                print(f"  {rating} stars: {ratings[rating]}")
                        print()
                else:
                    print("\nInvalid choice. Please try again.\n")

        elif choice == '2':
            # Merkle Tree Operations
            while True:
                print_tree_menu()
                sub_choice = get_user_choice()
                if sub_choice == '0':
                    break
                elif sub_choice == '2.1':
                    if dataset is None:
                        print("\nNo dataset loaded. Please load a dataset first.\n")
                    else:
                        print("\n[Build Merkle Tree]")
                        print("Building Merkle tree...")
                        try:
                            import time
                            start_time = time.time()
                            merkle_tree = MerkleTree(dataset)
                            elapsed = (time.time() - start_time) * 1000
                            print(f"Merkle tree built successfully in {elapsed:.2f}ms!")
                            print(f"Root hash: {merkle_tree.get_root_hash_hex()[:32]}...\n")
                        except Exception as e:
                            print(f"\nError building tree: {e}\n")
                elif sub_choice == '2.2':
                    if merkle_tree is None:
                        print("\nNo Merkle tree built. Please build a tree first.\n")
                    else:
                        print("\n[Tree Information]")
                        leaf_count = merkle_tree.get_leaf_count()
                        print(f"Number of leaves: {leaf_count}")
                        print(f"Root hash: {merkle_tree.get_root_hash_hex()}")
                        print(f"Memory usage (leaves): ~{leaf_count * 32 / 1024:.2f} KB\n")
                elif sub_choice == '2.3':
                    if merkle_tree is None:
                        print("\nNo Merkle tree built. Please build a tree first.\n")
                    else:
                        print("\n[Export Root Hash]")
                        name = get_user_choice("Enter a name for this root hash: ")
                        try:
                            storage = HashStorage()
                            storage.save(name, {
                                'root_hash': merkle_tree.get_root_hash_hex(),
                                'num_leaves': merkle_tree.get_leaf_count()
                            })
                            print(f"Root hash saved as '{name}'!\n")
                        except Exception as e:
                            print(f"\nError saving root hash: {e}\n")
                else:
                    print("\nInvalid choice. Please try again.\n")

        elif choice == '3':
            # Integrity Verification
            while True:
                print_verification_menu()
                sub_choice = get_user_choice()
                if sub_choice == '0':
                    break
                elif sub_choice == '3.1':
                    if dataset is None or merkle_tree is None:
                        print("\nPlease load dataset and build tree first.\n")
                    else:
                        print("\n[Verify Dataset Integrity]")
                        try:
                            result = integrity_checker.verify(dataset, merkle_tree.get_root_hash())
                            if result:
                                print("✓ Dataset integrity verified! Data is intact.\n")
                            else:
                                print("✗ Integrity check failed! Data may have been tampered.\n")
                        except Exception as e:
                            print(f"\nError during verification: {e}\n")
                elif sub_choice == '3.2':
                    if merkle_tree is None:
                        print("\nNo Merkle tree built. Please build a tree first.\n")
                    else:
                        print("\n[Store Current Root Hash]")
                        try:
                            integrity_checker.save_baseline(merkle_tree.get_root_hash())
                            print("Baseline root hash saved successfully!\n")
                        except Exception as e:
                            print(f"\nError saving baseline: {e}\n")
                elif sub_choice == '3.3':
                    if merkle_tree is None:
                        print("\nNo Merkle tree built. Please build a tree first.\n")
                    else:
                        print("\n[Compare with Stored Hash]")
                        try:
                            result = integrity_checker.compare_with_baseline(merkle_tree.get_root_hash())
                            if result:
                                print("✓ Root hash matches stored baseline!\n")
                            else:
                                print("✗ Root hash differs from baseline! Data may have changed.\n")
                        except Exception as e:
                            print(f"\nError comparing with baseline: {e}\n")
                else:
                    print("\nInvalid choice. Please try again.\n")

        elif choice == '4':
            # Existence Proofs
            while True:
                print_proof_menu()
                sub_choice = get_user_choice()
                if sub_choice == '0':
                    break
                elif sub_choice == '4.1':
                    if dataset is None or merkle_tree is None:
                        print("\nPlease load dataset and build tree first.\n")
                    else:
                        print("\n[Generate Proof for Review]")
                        index_str = get_user_choice(f"Enter review index (0-{len(dataset)-1}): ")
                        try:
                            index = int(index_str)
                            if index < 0 or index >= len(dataset):
                                print(f"\nInvalid index. Must be between 0 and {len(dataset)-1}.\n")
                            else:
                                proof = merkle_tree.get_proof(index, dataset[index])
                                print(f"\nProof generated for review at index {index}:")
                                print(f"  Proof path length: {len(proof.proof_path)}")
                                print(f"  Leaf index: {proof.leaf_index}")
                                print(f"  Root hash: {bytes_to_hex(proof.root_hash)[:32]}...\n")
                        except ValueError:
                            print("\nInvalid input. Please enter a number.\n")
                        except Exception as e:
                            print(f"\nError generating proof: {e}\n")
                elif sub_choice == '4.2':
                    if dataset is None or merkle_tree is None:
                        print("\nPlease load dataset and build tree first.\n")
                    else:
                        print("\n[Verify Proof]")
                        index_str = get_user_choice(f"Enter review index to verify (0-{len(dataset)-1}): ")
                        try:
                            index = int(index_str)
                            if index < 0 or index >= len(dataset):
                                print(f"\nInvalid index. Must be between 0 and {len(dataset)-1}.\n")
                            else:
                                proof = merkle_tree.get_proof(index, dataset[index])
                                is_valid = proof.verify()
                                if is_valid:
                                    print("✓ Proof verified! Review exists in dataset.\n")
                                else:
                                    print("✗ Proof verification failed!\n")
                        except ValueError:
                            print("\nInvalid input. Please enter a number.\n")
                        except Exception as e:
                            print(f"\nError verifying proof: {e}\n")
                elif sub_choice == '4.3':
                    if dataset is None or merkle_tree is None:
                        print("\nPlease load dataset and build tree first.\n")
                    else:
                        print("\n[Batch Proof Generation]")
                        count_str = get_user_choice("Enter number of proofs to generate: ")
                        try:
                            count = int(count_str)
                            if count <= 0 or count > len(dataset):
                                print(f"\nInvalid count. Must be between 1 and {len(dataset)}.\n")
                            else:
                                import time
                                start_time = time.time()
                                proofs = []
                                for i in range(count):
                                    proof = merkle_tree.get_proof(i, dataset[i])
                                    proofs.append(proof)
                                elapsed = (time.time() - start_time) * 1000
                                print(f"\nGenerated {count} proofs in {elapsed:.2f}ms")
                                print(f"Average: {elapsed/count:.4f}ms per proof\n")
                        except ValueError:
                            print("\nInvalid input. Please enter a number.\n")
                        except Exception as e:
                            print(f"\nError in batch generation: {e}\n")
                else:
                    print("\nInvalid choice. Please try again.\n")

        elif choice == '5':
            # Tamper Detection
            while True:
                print_tamper_menu()
                sub_choice = get_user_choice()
                if sub_choice == '0':
                    break
                elif sub_choice == '5.1':
                    if dataset is None:
                        print("\nNo dataset loaded. Please load a dataset first.\n")
                    else:
                        print("\n[Simulate Modification]")
                        index_str = get_user_choice(f"Enter review index to modify (0-{len(dataset)-1}): ")
                        try:
                            index = int(index_str)
                            if index < 0 or index >= len(dataset):
                                print(f"\nInvalid index. Must be between 0 and {len(dataset)-1}.\n")
                            else:
                                # Modify the review
                                dataset[index]['overall'] = 5.0
                                dataset[index]['reviewText'] = "TAMPERED REVIEW"
                                print(f"Modified review at index {index}")
                                print("Note: Rebuild tree to see the impact on root hash.\n")
                        except ValueError:
                            print("\nInvalid input. Please enter a number.\n")
                        except Exception as e:
                            print(f"\nError during modification: {e}\n")
                elif sub_choice == '5.2':
                    if dataset is None:
                        print("\nNo dataset loaded. Please load a dataset first.\n")
                    else:
                        print("\n[Simulate Deletion]")
                        index_str = get_user_choice(f"Enter review index to delete (0-{len(dataset)-1}): ")
                        try:
                            index = int(index_str)
                            if index < 0 or index >= len(dataset):
                                print(f"\nInvalid index. Must be between 0 and {len(dataset)-1}.\n")
                            else:
                                del dataset[index]
                                print(f"Deleted review at index {index}")
                                print(f"New dataset size: {len(dataset)}")
                                print("Note: Rebuild tree to see the impact on root hash.\n")
                        except ValueError:
                            print("\nInvalid input. Please enter a number.\n")
                        except Exception as e:
                            print(f"\nError during deletion: {e}\n")
                elif sub_choice == '5.3':
                    if dataset is None:
                        print("\nNo dataset loaded. Please load a dataset first.\n")
                    else:
                        print("\n[Simulate Insertion]")
                        fake_review = {
                            'reviewerID': 'FAKE_REVIEWER',
                            'asin': 'FAKE_PRODUCT',
                            'overall': 5.0,
                            'unixReviewTime': 0,
                            'reviewText': 'This is a fake inserted review'
                        }
                        dataset.append(fake_review)
                        print(f"Inserted fake review at end of dataset")
                        print(f"New dataset size: {len(dataset)}")
                        print("Note: Rebuild tree to see the impact on root hash.\n")
                elif sub_choice == '5.4':
                    if dataset is None or merkle_tree is None:
                        print("\nPlease load dataset and build tree first.\n")
                    else:
                        print("\n[Generate Tamper Report]")
                        try:
                            # Build new tree with current (possibly tampered) data
                            current_tree = MerkleTree(dataset)
                            report = tamper_detector.generate_report(
                                merkle_tree.get_root_hash(),
                                current_tree.get_root_hash(),
                                dataset
                            )
                            print(report)
                        except Exception as e:
                            print(f"\nError generating tamper report: {e}\n")
                else:
                    print("\nInvalid choice. Please try again.\n")

        elif choice == '6':
            # Performance Testing
            while True:
                print_performance_menu()
                sub_choice = get_user_choice()
                if sub_choice == '0':
                    break
                elif sub_choice == '6.1':
                    print("\n[Measure Hashing Speed]")
                    if dataset is None:
                        print("No dataset loaded. Using synthetic data...\n")
                        test_data = [{'reviewText': f'Review {i}'} for i in range(100000)]
                    else:
                        test_data = dataset

                    try:
                        from performance.metrics import measure_hashing_speed
                        import time
                        start_time = time.time()
                        speed = measure_hashing_speed(test_data[:100000])
                        elapsed = time.time() - start_time
                        print(f"Hashing speed: {speed:.0f} hashes/second")
                        print(f"Time for 100K hashes: {elapsed:.2f}s\n")
                    except Exception as e:
                        print(f"\nError measuring hashing speed: {e}\n")
                elif sub_choice == '6.2':
                    if dataset is None:
                        print("\nNo dataset loaded. Please load a dataset first.\n")
                    else:
                        print("\n[Benchmark Tree Construction]")
                        try:
                            import time
                            start_time = time.time()
                            test_tree = MerkleTree(dataset)
                            elapsed = (time.time() - start_time) * 1000
                            print(f"Tree construction time: {elapsed:.2f}ms")
                            print(f"Dataset size: {len(dataset)} records")
                            print(f"Average: {elapsed/len(dataset):.6f}ms per record\n")
                        except Exception as e:
                            print(f"\nError benchmarking tree construction: {e}\n")
                elif sub_choice == '6.3':
                    if dataset is None or merkle_tree is None:
                        print("\nPlease load dataset and build tree first.\n")
                    else:
                        print("\n[Benchmark Proof Generation]")
                        count_str = get_user_choice("Enter number of proofs to test (default: 1000): ")
                        count = int(count_str) if count_str else 1000
                        count = min(count, len(dataset))

                        try:
                            import time
                            start_time = time.time()
                            for i in range(count):
                                proof = merkle_tree.get_proof(i, dataset[i])
                            elapsed = (time.time() - start_time) * 1000
                            print(f"\nGenerated {count} proofs in {elapsed:.2f}ms")
                            print(f"Average: {elapsed/count:.4f}ms per proof\n")
                        except Exception as e:
                            print(f"\nError benchmarking proof generation: {e}\n")
                elif sub_choice == '6.4':
                    print("\n[Run Full Performance Suite]")
                    print("Running comprehensive benchmarks...")
                    print("This will test with datasets of sizes: 100, 1K, 10K, 100K")
                    confirm = get_user_choice("This may take a while. Continue? (y/n): ")
                    if confirm.lower() == 'y':
                        try:
                            from performance.benchmark import MerkleTreeBenchmark
                            bench = MerkleTreeBenchmark()
                            sizes = [100, 1000, 10000, 100000]
                            results = bench.benchmark_tree_construction(sizes)
                            print("\nBenchmark complete! Results saved to benchmarks/results/\n")
                        except Exception as e:
                            print(f"\nError running full benchmark: {e}\n")
                    else:
                        print("Benchmark cancelled.\n")
                else:
                    print("\nInvalid choice. Please try again.\n")

        elif choice == '7':
            # Test Cases
            while True:
                print_test_cases_menu()
                sub_choice = get_user_choice()
                if sub_choice == '0':
                    break
                elif sub_choice == '7.1':
                    print("\n[Run All Required Test Cases]")
                    print("Running pytest test suite...\n")
                    try:
                        import subprocess
                        result = subprocess.run(
                            ['pytest', 'tests/', '-v', '--tb=short'],
                            cwd='/Users/sobanahmad/Fast-Nuces/Semester 7/Algo/final',
                            capture_output=True,
                            text=True
                        )
                        print(result.stdout)
                        if result.returncode == 0:
                            print("\n✓ All tests passed!\n")
                        else:
                            print("\n✗ Some tests failed. See output above.\n")
                    except Exception as e:
                        print(f"\nError running tests: {e}")
                        print("Try running: pytest tests/ -v\n")
                else:
                    print("\nInvalid choice. Please try again.\n")

        else:
            print("\nInvalid choice. Please try again.\n")


if __name__ == "__main__":
    main()
