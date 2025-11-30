"""
Integrity Checker for Merkle Tree verification.

This module implements the core integrity verification system that achieves
<100ms verification performance through simple root hash comparison.

Key design:
- Store baseline snapshots (root hash + metadata)
- Verify integrity with O(1) root hash comparison
- Generate detailed verification reports
- Support multiple datasets and snapshots

Performance:
- Baseline save: <1ms (just storing root hash)
- Integrity check: <1ms (single hash comparison) -> enables <100ms total verification
- Works with trees of any size (1K to 1M+ records)
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from merkle.tree import MerkleTree
from utils.storage import HashStorage
from utils.hash_utils import bytes_to_hex, hex_to_bytes


class IntegrityChecker:
    """
    Manages baseline snapshots and integrity verification for Merkle trees.

    This class enables the <100ms verification requirement by storing baseline
    root hashes and comparing them with current tree state in O(1) time.

    Usage:
        >>> checker = IntegrityChecker()
        >>> checker.save_baseline(tree, "reviews_2024", metadata={...})
        >>> result = checker.verify_integrity(tree, "reviews_2024")
        >>> if result['verified']:
        ...     print("Data integrity confirmed!")
    """

    def __init__(self, storage_dir: str = "data/.merkle_hashes"):
        """
        Initialize integrity checker.

        Args:
            storage_dir: Directory for storing baseline snapshots
        """
        self.storage = HashStorage(storage_dir)

    def save_baseline(self,
                     tree: MerkleTree,
                     dataset_name: str,
                     metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Save a baseline snapshot of a Merkle tree.

        Stores the root hash and metadata for later verification.
        This operation is very fast (<1ms) as it only stores the root hash.

        Args:
            tree: MerkleTree to snapshot
            dataset_name: Unique identifier for this dataset
            metadata: Optional metadata (description, source, etc.)

        Returns:
            Dictionary with snapshot information

        Example:
            >>> tree = MerkleTree(reviews)
            >>> checker.save_baseline(tree, "amazon_reviews_jan2024",
            ...                      metadata={"source": "amazon", "category": "electronics"})
        """
        if metadata is None:
            metadata = {}

        # Create snapshot
        snapshot = {
            'root_hash': tree.get_root_hash_hex(),
            'leaf_count': tree.get_leaf_count(),
            'timestamp': datetime.now().isoformat(),
            'dataset_name': dataset_name,
            'metadata': metadata
        }

        # Store snapshot
        self.storage.save(dataset_name, snapshot)

        return {
            'dataset_name': dataset_name,
            'root_hash': snapshot['root_hash'],
            'leaf_count': snapshot['leaf_count'],
            'timestamp': snapshot['timestamp'],
            'status': 'saved'
        }

    def load_baseline(self, dataset_name: str) -> Optional[Dict[str, Any]]:
        """
        Load a baseline snapshot.

        Args:
            dataset_name: Name of the dataset to load

        Returns:
            Snapshot dictionary or None if not found

        Example:
            >>> baseline = checker.load_baseline("amazon_reviews_jan2024")
            >>> if baseline:
            ...     print(f"Root hash: {baseline['root_hash']}")
        """
        return self.storage.load(dataset_name)

    def verify_integrity(self,
                        tree: MerkleTree,
                        dataset_name: str,
                        detailed: bool = True) -> Dict[str, Any]:
        """
        Verify integrity by comparing current tree with baseline.

        This is the <100ms verification operation: just compares root hashes.
        Time complexity: O(1) - single hash comparison!

        Args:
            tree: Current MerkleTree to verify
            dataset_name: Name of baseline to compare against
            detailed: Include detailed information in result

        Returns:
            Verification result dictionary with:
            - verified: True if hashes match
            - current_root_hash: Current tree's root hash
            - baseline_root_hash: Stored baseline root hash
            - match: Whether hashes match
            - timestamp: When verification was performed
            - baseline_timestamp: When baseline was created
            - Additional details if detailed=True

        Example:
            >>> result = checker.verify_integrity(current_tree, "baseline_2024")
            >>> if result['verified']:
            ...     print("✓ Data integrity verified!")
            >>> else:
            ...     print("✗ TAMPERING DETECTED!")
        """
        # Load baseline
        baseline = self.load_baseline(dataset_name)
        if baseline is None:
            return {
                'verified': False,
                'error': 'baseline_not_found',
                'message': f"No baseline found for dataset '{dataset_name}'",
                'dataset_name': dataset_name
            }

        # Get current root hash
        current_root = tree.get_root_hash_hex()
        baseline_root = baseline['root_hash']

        # Compare (O(1) operation - this is the <100ms magic!)
        hashes_match = current_root == baseline_root

        # Build result
        result = {
            'verified': hashes_match,
            'dataset_name': dataset_name,
            'current_root_hash': current_root,
            'baseline_root_hash': baseline_root,
            'match': hashes_match,
            'verification_timestamp': datetime.now().isoformat(),
            'baseline_timestamp': baseline['timestamp']
        }

        if detailed:
            result.update({
                'current_leaf_count': tree.get_leaf_count(),
                'baseline_leaf_count': baseline['leaf_count'],
                'leaf_count_match': tree.get_leaf_count() == baseline['leaf_count'],
                'baseline_metadata': baseline.get('metadata', {})
            })

            # Add status message
            if hashes_match:
                result['status'] = 'verified'
                result['message'] = 'Data integrity verified - no tampering detected'
            else:
                result['status'] = 'failed'
                result['message'] = 'VERIFICATION FAILED - data has been modified'

                # Additional diagnostics
                if tree.get_leaf_count() != baseline['leaf_count']:
                    result['issue'] = 'leaf_count_mismatch'
                    result['issue_detail'] = (
                        f"Record count changed: {baseline['leaf_count']} → "
                        f"{tree.get_leaf_count()}"
                    )
                else:
                    result['issue'] = 'data_modification'
                    result['issue_detail'] = (
                        "Record count unchanged but root hash differs - "
                        "data has been modified"
                    )

        return result

    def list_baselines(self) -> List[str]:
        """
        List all available baseline snapshots.

        Returns:
            List of dataset names

        Example:
            >>> baselines = checker.list_baselines()
            >>> for name in baselines:
            ...     print(f"- {name}")
        """
        return self.storage.list_keys()

    def delete_baseline(self, dataset_name: str) -> bool:
        """
        Delete a baseline snapshot.

        Args:
            dataset_name: Name of baseline to delete

        Returns:
            True if deleted, False if not found

        Example:
            >>> checker.delete_baseline("old_baseline_2023")
        """
        return self.storage.delete(dataset_name)

    def get_baseline_info(self, dataset_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a baseline without loading full snapshot.

        Args:
            dataset_name: Name of baseline

        Returns:
            Summary information or None if not found

        Example:
            >>> info = checker.get_baseline_info("reviews_jan2024")
            >>> print(f"Created: {info['timestamp']}")
            >>> print(f"Records: {info['leaf_count']}")
        """
        baseline = self.load_baseline(dataset_name)
        if baseline is None:
            return None

        return {
            'dataset_name': dataset_name,
            'root_hash_preview': baseline['root_hash'][:16] + '...',
            'leaf_count': baseline['leaf_count'],
            'timestamp': baseline['timestamp'],
            'metadata': baseline.get('metadata', {}),
            'exists': True
        }

    def compare_baselines(self,
                         dataset1: str,
                         dataset2: str) -> Dict[str, Any]:
        """
        Compare two baseline snapshots.

        Args:
            dataset1: First baseline name
            dataset2: Second baseline name

        Returns:
            Comparison result

        Example:
            >>> result = checker.compare_baselines("jan2024", "feb2024")
            >>> if result['identical']:
            ...     print("Datasets are identical")
        """
        baseline1 = self.load_baseline(dataset1)
        baseline2 = self.load_baseline(dataset2)

        if baseline1 is None or baseline2 is None:
            return {
                'error': 'baseline_not_found',
                'dataset1_exists': baseline1 is not None,
                'dataset2_exists': baseline2 is not None
            }

        identical = baseline1['root_hash'] == baseline2['root_hash']

        return {
            'dataset1': dataset1,
            'dataset2': dataset2,
            'identical': identical,
            'root_hash_match': identical,
            'dataset1_root': baseline1['root_hash'],
            'dataset2_root': baseline2['root_hash'],
            'dataset1_leaf_count': baseline1['leaf_count'],
            'dataset2_leaf_count': baseline2['leaf_count'],
            'leaf_count_match': baseline1['leaf_count'] == baseline2['leaf_count'],
            'dataset1_timestamp': baseline1['timestamp'],
            'dataset2_timestamp': baseline2['timestamp']
        }

    def verify_with_tree_dict(self,
                             tree_dict: Dict[str, Any],
                             dataset_name: str) -> Dict[str, Any]:
        """
        Verify integrity using a serialized tree dictionary.

        Useful when you have a stored tree dict but not a MerkleTree object.

        Args:
            tree_dict: Serialized tree (from MerkleTree.to_dict())
            dataset_name: Baseline to compare against

        Returns:
            Verification result

        Example:
            >>> tree_dict = tree.to_dict()
            >>> # Later...
            >>> result = checker.verify_with_tree_dict(tree_dict, "baseline")
        """
        baseline = self.load_baseline(dataset_name)
        if baseline is None:
            return {
                'verified': False,
                'error': 'baseline_not_found',
                'dataset_name': dataset_name
            }

        current_root = tree_dict['root_hash']
        baseline_root = baseline['root_hash']
        hashes_match = current_root == baseline_root

        return {
            'verified': hashes_match,
            'dataset_name': dataset_name,
            'current_root_hash': current_root,
            'baseline_root_hash': baseline_root,
            'match': hashes_match,
            'verification_timestamp': datetime.now().isoformat(),
            'baseline_timestamp': baseline['timestamp']
        }

    def generate_verification_report(self,
                                   verification_result: Dict[str, Any]) -> str:
        """
        Generate a human-readable verification report.

        Args:
            verification_result: Result from verify_integrity()

        Returns:
            Formatted report string

        Example:
            >>> result = checker.verify_integrity(tree, "baseline")
            >>> report = checker.generate_verification_report(result)
            >>> print(report)
        """
        if 'error' in verification_result:
            return f"""
Verification Report - ERROR
{'=' * 60}
Dataset: {verification_result.get('dataset_name', 'Unknown')}
Error: {verification_result['error']}
Message: {verification_result.get('message', 'No details available')}
"""

        verified = verification_result['verified']
        status_symbol = '✓' if verified else '✗'
        status_text = 'VERIFIED' if verified else 'FAILED'

        report = f"""
Integrity Verification Report
{'=' * 60}
Status: {status_symbol} {status_text}
Dataset: {verification_result['dataset_name']}

Root Hash Comparison:
  Current:  {verification_result['current_root_hash']}
  Baseline: {verification_result['baseline_root_hash']}
  Match: {'YES' if verification_result['match'] else 'NO'}

Timestamps:
  Baseline Created: {verification_result['baseline_timestamp']}
  Verified At: {verification_result['verification_timestamp']}
"""

        # Add detailed information if available
        if 'current_leaf_count' in verification_result:
            report += f"""
Record Counts:
  Current:  {verification_result['current_leaf_count']} records
  Baseline: {verification_result['baseline_leaf_count']} records
  Match: {'YES' if verification_result['leaf_count_match'] else 'NO'}
"""

        # Add issue details if verification failed
        if not verified and 'issue_detail' in verification_result:
            report += f"""
Issue Detected:
  Type: {verification_result.get('issue', 'unknown')}
  Detail: {verification_result['issue_detail']}
"""

        report += f"\n{'=' * 60}\n"
        return report
