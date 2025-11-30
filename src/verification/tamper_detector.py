"""
Tamper Detector for identifying specific data modifications.

This module analyzes differences between baseline and current data to identify:
- Modified records (same position, different content)
- Deleted records (removed from dataset)
- Inserted records (added to dataset)

Key design:
- Compare leaf hashes between trees for efficiency
- Generate detailed reports with affected record indices
- Support for both same-size and different-size datasets
- O(n) analysis time for comprehensive detection

Usage:
    >>> detector = TamperDetector()
    >>> report = detector.detect_tampering(baseline_tree, current_tree)
    >>> if report['tampering_detected']:
    ...     print(f"Found {report['total_changes']} changes")
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from merkle.tree import MerkleTree
from utils.hash_utils import bytes_to_hex


class TamperDetector:
    """
    Detects and analyzes tampering in Merkle trees.

    Compares baseline and current trees to identify specific changes:
    - Modifications: Same index, different hash
    - Deletions: In baseline but not in current
    - Insertions: In current but not in baseline

    This provides detailed forensics when integrity verification fails.
    """

    def __init__(self):
        """Initialize tamper detector."""
        pass

    def detect_tampering(self,
                        baseline_tree: MerkleTree,
                        current_tree: MerkleTree,
                        detailed: bool = True) -> Dict[str, Any]:
        """
        Detect tampering by comparing baseline and current trees.

        Analyzes leaf hashes to identify all changes between the trees.
        Time complexity: O(n) where n = max(baseline_size, current_size)

        Args:
            baseline_tree: The trusted baseline tree
            current_tree: The current tree to analyze
            detailed: Include detailed change information

        Returns:
            Dictionary with tampering analysis:
            - tampering_detected: True if any changes found
            - total_changes: Total number of changes
            - modifications: List of modified record indices
            - deletions: List of deleted record indices
            - insertions: List of inserted record indices
            - summary: Human-readable summary

        Example:
            >>> report = detector.detect_tampering(baseline, current)
            >>> if report['tampering_detected']:
            ...     print(f"Modified: {len(report['modifications'])}")
            ...     print(f"Deleted: {len(report['deletions'])}")
            ...     print(f"Inserted: {len(report['insertions'])}")
        """
        baseline_leaves = baseline_tree.get_all_leaf_hashes()
        current_leaves = current_tree.get_all_leaf_hashes()

        baseline_size = len(baseline_leaves)
        current_size = len(current_leaves)

        # Detect changes
        modifications = []
        deletions = []
        insertions = []

        if baseline_size == current_size:
            # Same size - direct comparison
            for i in range(baseline_size):
                if baseline_leaves[i] != current_leaves[i]:
                    modifications.append(i)
        else:
            # Different sizes - more complex analysis
            min_size = min(baseline_size, current_size)

            # Check modifications in overlapping range
            for i in range(min_size):
                if baseline_leaves[i] != current_leaves[i]:
                    modifications.append(i)

            # Identify deletions/insertions
            if baseline_size > current_size:
                # Records were deleted
                deletions = list(range(current_size, baseline_size))
            else:
                # Records were inserted
                insertions = list(range(baseline_size, current_size))

        total_changes = len(modifications) + len(deletions) + len(insertions)
        tampering_detected = total_changes > 0

        # Build report
        report = {
            'tampering_detected': tampering_detected,
            'total_changes': total_changes,
            'baseline_size': baseline_size,
            'current_size': current_size,
            'size_changed': baseline_size != current_size,
            'modifications': modifications,
            'deletions': deletions,
            'insertions': insertions,
            'modification_count': len(modifications),
            'deletion_count': len(deletions),
            'insertion_count': len(insertions),
            'analysis_timestamp': datetime.now().isoformat()
        }

        if detailed:
            # Add detailed information
            report['summary'] = self._generate_summary(report)

            # Add change details if requested
            report['change_details'] = {
                'modifications': [
                    {
                        'index': idx,
                        'baseline_hash': bytes_to_hex(baseline_leaves[idx]),
                        'current_hash': bytes_to_hex(current_leaves[idx])
                    }
                    for idx in modifications[:10]  # Limit to first 10
                ],
                'deletions': [
                    {
                        'index': idx,
                        'baseline_hash': bytes_to_hex(baseline_leaves[idx])
                    }
                    for idx in deletions[:10]
                ],
                'insertions': [
                    {
                        'index': idx,
                        'current_hash': bytes_to_hex(current_leaves[idx])
                    }
                    for idx in insertions[:10]
                ]
            }

        return report

    def compare_records(self,
                       baseline_tree: MerkleTree,
                       current_tree: MerkleTree,
                       index: int) -> Dict[str, Any]:
        """
        Compare a specific record between baseline and current trees.

        Args:
            baseline_tree: Baseline tree
            current_tree: Current tree
            index: Record index to compare

        Returns:
            Comparison result

        Example:
            >>> result = detector.compare_records(baseline, current, 42)
            >>> if result['modified']:
            ...     print("Record 42 was modified!")
        """
        try:
            baseline_hash = baseline_tree.get_leaf_hash(index)
        except IndexError:
            baseline_hash = None

        try:
            current_hash = current_tree.get_leaf_hash(index)
        except IndexError:
            current_hash = None

        if baseline_hash is None and current_hash is None:
            status = 'index_out_of_range'
            modified = False
        elif baseline_hash is None:
            status = 'inserted'
            modified = True
        elif current_hash is None:
            status = 'deleted'
            modified = True
        elif baseline_hash == current_hash:
            status = 'unchanged'
            modified = False
        else:
            status = 'modified'
            modified = True

        return {
            'index': index,
            'status': status,
            'modified': modified,
            'baseline_hash': bytes_to_hex(baseline_hash) if baseline_hash else None,
            'current_hash': bytes_to_hex(current_hash) if current_hash else None,
            'match': baseline_hash == current_hash if baseline_hash and current_hash else False
        }

    def find_unchanged_records(self,
                              baseline_tree: MerkleTree,
                              current_tree: MerkleTree) -> List[int]:
        """
        Find all records that have NOT been modified.

        Args:
            baseline_tree: Baseline tree
            current_tree: Current tree

        Returns:
            List of indices that are unchanged

        Example:
            >>> unchanged = detector.find_unchanged_records(baseline, current)
            >>> print(f"{len(unchanged)} records are still valid")
        """
        baseline_leaves = baseline_tree.get_all_leaf_hashes()
        current_leaves = current_tree.get_all_leaf_hashes()

        unchanged = []
        min_size = min(len(baseline_leaves), len(current_leaves))

        for i in range(min_size):
            if baseline_leaves[i] == current_leaves[i]:
                unchanged.append(i)

        return unchanged

    def get_tampering_statistics(self,
                                baseline_tree: MerkleTree,
                                current_tree: MerkleTree) -> Dict[str, Any]:
        """
        Get statistical summary of tampering.

        Args:
            baseline_tree: Baseline tree
            current_tree: Current tree

        Returns:
            Statistical summary

        Example:
            >>> stats = detector.get_tampering_statistics(baseline, current)
            >>> print(f"Integrity: {stats['integrity_percentage']:.1f}%")
        """
        report = self.detect_tampering(baseline_tree, current_tree, detailed=False)

        baseline_size = report['baseline_size']
        unchanged_count = baseline_size - report['modification_count'] - report['deletion_count']

        if baseline_size > 0:
            integrity_percentage = (unchanged_count / baseline_size) * 100
            modification_rate = (report['modification_count'] / baseline_size) * 100
            deletion_rate = (report['deletion_count'] / baseline_size) * 100
        else:
            integrity_percentage = 100.0
            modification_rate = 0.0
            deletion_rate = 0.0

        return {
            'baseline_records': baseline_size,
            'current_records': report['current_size'],
            'unchanged_records': unchanged_count,
            'modified_records': report['modification_count'],
            'deleted_records': report['deletion_count'],
            'inserted_records': report['insertion_count'],
            'integrity_percentage': integrity_percentage,
            'modification_rate': modification_rate,
            'deletion_rate': deletion_rate,
            'tampering_detected': report['tampering_detected']
        }

    def _generate_summary(self, report: Dict[str, Any]) -> str:
        """
        Generate human-readable summary of tampering report.

        Args:
            report: Tampering detection report

        Returns:
            Summary string
        """
        if not report['tampering_detected']:
            return "No tampering detected - all records unchanged"

        parts = []

        if report['modification_count'] > 0:
            parts.append(f"{report['modification_count']} record(s) modified")

        if report['deletion_count'] > 0:
            parts.append(f"{report['deletion_count']} record(s) deleted")

        if report['insertion_count'] > 0:
            parts.append(f"{report['insertion_count']} record(s) inserted")

        summary = ", ".join(parts)

        # Add size change note
        if report['size_changed']:
            summary += f" (size: {report['baseline_size']} → {report['current_size']})"

        return summary

    def generate_tampering_report(self,
                                 tampering_result: Dict[str, Any]) -> str:
        """
        Generate detailed human-readable tampering report.

        Args:
            tampering_result: Result from detect_tampering()

        Returns:
            Formatted report string

        Example:
            >>> result = detector.detect_tampering(baseline, current)
            >>> report = detector.generate_tampering_report(result)
            >>> print(report)
        """
        if not tampering_result['tampering_detected']:
            return """
Tamper Detection Report
{'=' * 60}
Status: ✓ NO TAMPERING DETECTED

All records match the baseline.
Dataset integrity verified.
{'=' * 60}
"""

        report = f"""
Tamper Detection Report
{'=' * 60}
Status: ✗ TAMPERING DETECTED

Dataset Size:
  Baseline: {tampering_result['baseline_size']} records
  Current:  {tampering_result['current_size']} records
  Changed:  {'YES' if tampering_result['size_changed'] else 'NO'}

Changes Detected:
  Total Changes:     {tampering_result['total_changes']}
  Modifications:     {tampering_result['modification_count']}
  Deletions:         {tampering_result['deletion_count']}
  Insertions:        {tampering_result['insertion_count']}

Summary:
  {tampering_result.get('summary', 'See details above')}
"""

        # Add sample details if available
        if 'change_details' in tampering_result:
            details = tampering_result['change_details']

            if details['modifications']:
                report += f"\nSample Modified Records (first 10):\n"
                for change in details['modifications']:
                    report += f"  Index {change['index']}: hash changed\n"

            if details['deletions']:
                report += f"\nSample Deleted Records (first 10):\n"
                for change in details['deletions']:
                    report += f"  Index {change['index']}: removed from dataset\n"

            if details['insertions']:
                report += f"\nSample Inserted Records (first 10):\n"
                for change in details['insertions']:
                    report += f"  Index {change['index']}: added to dataset\n"

        report += f"\n{'=' * 60}\n"
        return report

    def identify_modified_ranges(self,
                                baseline_tree: MerkleTree,
                                current_tree: MerkleTree) -> List[Tuple[int, int]]:
        """
        Identify contiguous ranges of modified records.

        Useful for finding large-scale modifications.

        Args:
            baseline_tree: Baseline tree
            current_tree: Current tree

        Returns:
            List of (start_index, end_index) tuples for modified ranges

        Example:
            >>> ranges = detector.identify_modified_ranges(baseline, current)
            >>> for start, end in ranges:
            ...     print(f"Modified: records {start}-{end}")
        """
        report = self.detect_tampering(baseline_tree, current_tree, detailed=False)
        modifications = report['modifications']

        if not modifications:
            return []

        # Find contiguous ranges
        ranges = []
        start = modifications[0]
        end = modifications[0]

        for idx in modifications[1:]:
            if idx == end + 1:
                # Contiguous
                end = idx
            else:
                # Gap found, save current range and start new one
                ranges.append((start, end))
                start = idx
                end = idx

        # Add final range
        ranges.append((start, end))

        return ranges
