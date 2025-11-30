"""
Unit tests for TamperDetector.

Tests cover:
- Detection of modifications (changed records)
- Detection of deletions (removed records)
- Detection of insertions (added records)
- Combination scenarios
- Statistical analysis
- Report generation
- Edge cases
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from merkle.tree import MerkleTree
from verification.tamper_detector import TamperDetector


@pytest.fixture
def detector():
    """Create a TamperDetector instance."""
    return TamperDetector()


@pytest.fixture
def baseline_tree():
    """Create a baseline tree for testing."""
    return MerkleTree(["a", "b", "c", "d", "e"])


class TestModificationDetection:
    """Test detection of modified records."""

    def test_detect_single_modification(self, detector, baseline_tree):
        """Test detecting a single modified record."""
        # Modify one record
        current = MerkleTree(["a", "b", "MODIFIED", "d", "e"])

        result = detector.detect_tampering(baseline_tree, current)

        assert result['tampering_detected'] is True
        assert result['total_changes'] == 1
        assert result['modification_count'] == 1
        assert result['modifications'] == [2]
        assert result['deletion_count'] == 0
        assert result['insertion_count'] == 0

    def test_detect_multiple_modifications(self, detector, baseline_tree):
        """Test detecting multiple modified records."""
        current = MerkleTree(["CHANGED", "b", "MODIFIED", "d", "ALTERED"])

        result = detector.detect_tampering(baseline_tree, current)

        assert result['tampering_detected'] is True
        assert result['total_changes'] == 3
        assert result['modification_count'] == 3
        assert set(result['modifications']) == {0, 2, 4}

    def test_detect_all_modified(self, detector):
        """Test when all records are modified."""
        baseline = MerkleTree(["a", "b", "c"])
        current = MerkleTree(["x", "y", "z"])

        result = detector.detect_tampering(baseline, current)

        assert result['tampering_detected'] is True
        assert result['modification_count'] == 3
        assert result['modifications'] == [0, 1, 2]

    def test_no_modifications(self, detector, baseline_tree):
        """Test when no records are modified."""
        # Exact same tree
        current = MerkleTree(["a", "b", "c", "d", "e"])

        result = detector.detect_tampering(baseline_tree, current)

        assert result['tampering_detected'] is False
        assert result['total_changes'] == 0
        assert result['modification_count'] == 0
        assert result['modifications'] == []


class TestDeletionDetection:
    """Test detection of deleted records."""

    def test_detect_single_deletion(self, detector):
        """Test detecting deletion of last record."""
        baseline = MerkleTree(["a", "b", "c", "d"])
        current = MerkleTree(["a", "b", "c"])

        result = detector.detect_tampering(baseline, current)

        assert result['tampering_detected'] is True
        assert result['deletion_count'] == 1
        assert result['deletions'] == [3]
        assert result['size_changed'] is True

    def test_detect_multiple_deletions(self, detector):
        """Test detecting multiple deletions."""
        baseline = MerkleTree(["a", "b", "c", "d", "e", "f"])
        current = MerkleTree(["a", "b"])

        result = detector.detect_tampering(baseline, current)

        assert result['tampering_detected'] is True
        assert result['deletion_count'] == 4
        assert result['deletions'] == [2, 3, 4, 5]

    def test_delete_all_but_one(self, detector):
        """Test deleting all records except one."""
        baseline = MerkleTree(["a", "b", "c", "d"])
        current = MerkleTree(["a"])

        result = detector.detect_tampering(baseline, current)

        assert result['deletion_count'] == 3
        assert result['modification_count'] == 0


class TestInsertionDetection:
    """Test detection of inserted records."""

    def test_detect_single_insertion(self, detector):
        """Test detecting insertion of one record."""
        baseline = MerkleTree(["a", "b", "c"])
        current = MerkleTree(["a", "b", "c", "NEW"])

        result = detector.detect_tampering(baseline, current)

        assert result['tampering_detected'] is True
        assert result['insertion_count'] == 1
        assert result['insertions'] == [3]
        assert result['size_changed'] is True

    def test_detect_multiple_insertions(self, detector):
        """Test detecting multiple insertions."""
        baseline = MerkleTree(["a", "b"])
        current = MerkleTree(["a", "b", "new1", "new2", "new3"])

        result = detector.detect_tampering(baseline, current)

        assert result['insertion_count'] == 3
        assert result['insertions'] == [2, 3, 4]

    def test_insert_to_empty_baseline(self, detector):
        """Test insertions when baseline has minimal data."""
        baseline = MerkleTree(["a"])
        current = MerkleTree(["a", "b", "c", "d"])

        result = detector.detect_tampering(baseline, current)

        assert result['insertion_count'] == 3


class TestCombinationScenarios:
    """Test combinations of modifications, deletions, and insertions."""

    def test_modifications_and_deletions(self, detector):
        """Test combined modifications and deletions."""
        baseline = MerkleTree(["a", "b", "c", "d", "e"])
        current = MerkleTree(["MODIFIED", "b", "CHANGED"])

        result = detector.detect_tampering(baseline, current)

        assert result['tampering_detected'] is True
        assert result['modification_count'] == 2
        assert result['deletion_count'] == 2
        assert result['modifications'] == [0, 2]
        assert result['deletions'] == [3, 4]

    def test_modifications_and_insertions(self, detector):
        """Test combined modifications and insertions."""
        baseline = MerkleTree(["a", "b", "c"])
        current = MerkleTree(["MODIFIED", "b", "c", "new1", "new2"])

        result = detector.detect_tampering(baseline, current)

        assert result['modification_count'] == 1
        assert result['insertion_count'] == 2
        assert result['modifications'] == [0]
        assert result['insertions'] == [3, 4]

    def test_complex_changes(self, detector):
        """Test complex scenario with multiple change types."""
        baseline = MerkleTree(["a", "b", "c", "d", "e", "f"])
        current = MerkleTree(["a", "MODIFIED", "c", "CHANGED"])

        result = detector.detect_tampering(baseline, current)

        assert result['modification_count'] == 2
        assert result['deletion_count'] == 2
        assert result['total_changes'] == 4


class TestRecordComparison:
    """Test comparing specific records."""

    def test_compare_unchanged_record(self, detector, baseline_tree):
        """Test comparing an unchanged record."""
        current = MerkleTree(["a", "b", "c", "d", "e"])

        result = detector.compare_records(baseline_tree, current, 1)

        assert result['status'] == 'unchanged'
        assert result['modified'] is False
        assert result['match'] is True

    def test_compare_modified_record(self, detector, baseline_tree):
        """Test comparing a modified record."""
        current = MerkleTree(["a", "MODIFIED", "c", "d", "e"])

        result = detector.compare_records(baseline_tree, current, 1)

        assert result['status'] == 'modified'
        assert result['modified'] is True
        assert result['match'] is False

    def test_compare_deleted_record(self, detector):
        """Test comparing a deleted record."""
        baseline = MerkleTree(["a", "b", "c", "d"])
        current = MerkleTree(["a", "b"])

        result = detector.compare_records(baseline, current, 3)

        assert result['status'] == 'deleted'
        assert result['modified'] is True
        assert result['current_hash'] is None

    def test_compare_inserted_record(self, detector):
        """Test comparing an inserted record."""
        baseline = MerkleTree(["a", "b"])
        current = MerkleTree(["a", "b", "NEW"])

        result = detector.compare_records(baseline, current, 2)

        assert result['status'] == 'inserted'
        assert result['modified'] is True
        assert result['baseline_hash'] is None

    def test_compare_out_of_range(self, detector, baseline_tree):
        """Test comparing index out of range."""
        current = MerkleTree(["a", "b", "c", "d", "e"])

        result = detector.compare_records(baseline_tree, current, 100)

        assert result['status'] == 'index_out_of_range'
        assert result['modified'] is False


class TestUnchangedRecords:
    """Test finding unchanged records."""

    def test_find_unchanged_no_changes(self, detector, baseline_tree):
        """Test finding unchanged when nothing changed."""
        current = MerkleTree(["a", "b", "c", "d", "e"])

        unchanged = detector.find_unchanged_records(baseline_tree, current)

        assert len(unchanged) == 5
        assert unchanged == [0, 1, 2, 3, 4]

    def test_find_unchanged_some_changes(self, detector, baseline_tree):
        """Test finding unchanged with some modifications."""
        current = MerkleTree(["a", "MODIFIED", "c", "CHANGED", "e"])

        unchanged = detector.find_unchanged_records(baseline_tree, current)

        assert len(unchanged) == 3
        assert set(unchanged) == {0, 2, 4}

    def test_find_unchanged_all_changed(self, detector):
        """Test finding unchanged when everything changed."""
        baseline = MerkleTree(["a", "b", "c"])
        current = MerkleTree(["x", "y", "z"])

        unchanged = detector.find_unchanged_records(baseline, current)

        assert len(unchanged) == 0

    def test_find_unchanged_different_sizes(self, detector):
        """Test finding unchanged with different tree sizes."""
        baseline = MerkleTree(["a", "b", "c", "d", "e"])
        current = MerkleTree(["a", "b", "c"])

        unchanged = detector.find_unchanged_records(baseline, current)

        assert len(unchanged) == 3
        assert unchanged == [0, 1, 2]


class TestStatistics:
    """Test statistical analysis."""

    def test_statistics_no_tampering(self, detector, baseline_tree):
        """Test statistics when no tampering."""
        current = MerkleTree(["a", "b", "c", "d", "e"])

        stats = detector.get_tampering_statistics(baseline_tree, current)

        assert stats['tampering_detected'] is False
        assert stats['integrity_percentage'] == 100.0
        assert stats['modification_rate'] == 0.0
        assert stats['deletion_rate'] == 0.0
        assert stats['unchanged_records'] == 5

    def test_statistics_partial_tampering(self, detector):
        """Test statistics with partial tampering."""
        baseline = MerkleTree(["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"])
        current = MerkleTree(["a", "b", "MODIFIED", "d", "e", "CHANGED", "g", "h", "i", "j"])

        stats = detector.get_tampering_statistics(baseline, current)

        assert stats['tampering_detected'] is True
        assert stats['modified_records'] == 2
        assert stats['integrity_percentage'] == 80.0  # 8 out of 10 unchanged
        assert stats['modification_rate'] == 20.0

    def test_statistics_with_deletions(self, detector):
        """Test statistics with deletions."""
        baseline = MerkleTree(["a", "b", "c", "d", "e"])
        current = MerkleTree(["a", "b", "c"])

        stats = detector.get_tampering_statistics(baseline, current)

        assert stats['deleted_records'] == 2
        assert stats['deletion_rate'] == 40.0
        assert stats['unchanged_records'] == 3


class TestReportGeneration:
    """Test report generation."""

    def test_generate_report_no_tampering(self, detector, baseline_tree):
        """Test report when no tampering detected."""
        current = MerkleTree(["a", "b", "c", "d", "e"])

        result = detector.detect_tampering(baseline_tree, current)
        report = detector.generate_tampering_report(result)

        assert "NO TAMPERING DETECTED" in report
        assert "✓" in report

    def test_generate_report_with_modifications(self, detector):
        """Test report with modifications."""
        baseline = MerkleTree(["a", "b", "c", "d"])
        current = MerkleTree(["a", "MODIFIED", "c", "CHANGED"])

        result = detector.detect_tampering(baseline, current)
        report = detector.generate_tampering_report(result)

        assert "TAMPERING DETECTED" in report
        assert "✗" in report
        assert "2" in report  # 2 modifications

    def test_generate_report_with_deletions(self, detector):
        """Test report with deletions."""
        baseline = MerkleTree(["a", "b", "c", "d"])
        current = MerkleTree(["a", "b"])

        result = detector.detect_tampering(baseline, current)
        report = detector.generate_tampering_report(result)

        assert "Deletions:" in report
        assert "2" in report

    def test_generate_report_with_insertions(self, detector):
        """Test report with insertions."""
        baseline = MerkleTree(["a", "b"])
        current = MerkleTree(["a", "b", "NEW1", "NEW2"])

        result = detector.detect_tampering(baseline, current)
        report = detector.generate_tampering_report(result)

        assert "Insertions:" in report
        assert "2" in report


class TestModifiedRanges:
    """Test identification of modified ranges."""

    def test_single_modified_record(self, detector):
        """Test range for single modified record."""
        baseline = MerkleTree(["a", "b", "c", "d"])
        current = MerkleTree(["a", "MODIFIED", "c", "d"])

        ranges = detector.identify_modified_ranges(baseline, current)

        assert len(ranges) == 1
        assert ranges[0] == (1, 1)

    def test_contiguous_modified_range(self, detector):
        """Test contiguous range of modifications."""
        baseline = MerkleTree(["a", "b", "c", "d", "e", "f"])
        current = MerkleTree(["a", "M1", "M2", "M3", "e", "f"])

        ranges = detector.identify_modified_ranges(baseline, current)

        assert len(ranges) == 1
        assert ranges[0] == (1, 3)

    def test_multiple_separate_ranges(self, detector):
        """Test multiple separate modified ranges."""
        baseline = MerkleTree(["a", "b", "c", "d", "e", "f", "g", "h"])
        current = MerkleTree(["a", "M1", "M2", "d", "e", "M3", "M4", "h"])

        ranges = detector.identify_modified_ranges(baseline, current)

        assert len(ranges) == 2
        assert ranges[0] == (1, 2)
        assert ranges[1] == (5, 6)

    def test_no_modifications_no_ranges(self, detector, baseline_tree):
        """Test no ranges when no modifications."""
        current = MerkleTree(["a", "b", "c", "d", "e"])

        ranges = detector.identify_modified_ranges(baseline_tree, current)

        assert len(ranges) == 0


class TestDetailedMode:
    """Test detailed reporting mode."""

    def test_detailed_mode_includes_summary(self, detector, baseline_tree):
        """Test that detailed mode includes summary."""
        current = MerkleTree(["a", "MODIFIED", "c", "d", "e"])

        result = detector.detect_tampering(baseline_tree, current, detailed=True)

        assert 'summary' in result
        assert 'change_details' in result

    def test_detailed_mode_change_details(self, detector):
        """Test that detailed mode includes change details."""
        baseline = MerkleTree(["a", "b", "c", "d"])
        current = MerkleTree(["a", "MODIFIED", "c", "CHANGED"])

        result = detector.detect_tampering(baseline, current, detailed=True)

        assert 'change_details' in result
        assert 'modifications' in result['change_details']
        assert len(result['change_details']['modifications']) == 2

    def test_simple_mode_excludes_details(self, detector, baseline_tree):
        """Test that simple mode excludes details."""
        current = MerkleTree(["a", "MODIFIED", "c", "d", "e"])

        result = detector.detect_tampering(baseline_tree, current, detailed=False)

        assert 'summary' not in result
        assert 'change_details' not in result


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_single_leaf_trees(self, detector):
        """Test with single-leaf trees."""
        baseline = MerkleTree(["only"])
        current = MerkleTree(["modified"])

        result = detector.detect_tampering(baseline, current)

        assert result['modification_count'] == 1

    def test_empty_to_populated(self, detector):
        """Test transition from minimal to populated dataset."""
        baseline = MerkleTree(["a"])
        current = MerkleTree(["a", "b", "c", "d", "e"])

        result = detector.detect_tampering(baseline, current)

        assert result['insertion_count'] == 4

    def test_large_dataset(self, detector):
        """Test with larger dataset."""
        baseline_data = [f"item{i}" for i in range(100)]
        current_data = baseline_data.copy()
        # Modify some records
        current_data[25] = "MODIFIED"
        current_data[50] = "CHANGED"
        current_data[75] = "ALTERED"

        baseline = MerkleTree(baseline_data)
        current = MerkleTree(current_data)

        result = detector.detect_tampering(baseline, current)

        assert result['modification_count'] == 3
        assert set(result['modifications']) == {25, 50, 75}

    def test_special_characters(self, detector):
        """Test with special characters in data."""
        baseline = MerkleTree(["Hello 世界", "Test\x00Data", "Special!@#$%"])
        current = MerkleTree(["Hello 世界", "Modified", "Special!@#$%"])

        result = detector.detect_tampering(baseline, current)

        assert result['modification_count'] == 1
        assert result['modifications'] == [1]


class TestIntegration:
    """Test integration scenarios."""

    def test_workflow_detect_then_analyze(self, detector):
        """Test complete workflow: detect then analyze specific changes."""
        baseline = MerkleTree(["a", "b", "c", "d", "e"])
        current = MerkleTree(["a", "MODIFIED", "c", "CHANGED", "e"])

        # First detect
        result = detector.detect_tampering(baseline, current)
        assert result['tampering_detected'] is True

        # Then analyze specific records
        for idx in result['modifications']:
            comparison = detector.compare_records(baseline, current, idx)
            assert comparison['modified'] is True

    def test_find_unchanged_after_detection(self, detector):
        """Test finding unchanged records after detection."""
        baseline = MerkleTree(["a", "b", "c", "d", "e"])
        current = MerkleTree(["a", "MODIFIED", "c", "d", "e"])

        # Detect changes
        result = detector.detect_tampering(baseline, current)

        # Find what's still valid
        unchanged = detector.find_unchanged_records(baseline, current)

        # Total should match
        assert len(unchanged) + result['modification_count'] == baseline.get_leaf_count()

    def test_statistics_match_detection(self, detector):
        """Test that statistics match detection results."""
        baseline = MerkleTree(["a", "b", "c", "d", "e", "f"])
        current = MerkleTree(["a", "MODIFIED", "c", "CHANGED"])

        result = detector.detect_tampering(baseline, current)
        stats = detector.get_tampering_statistics(baseline, current)

        assert stats['modified_records'] == result['modification_count']
        assert stats['deleted_records'] == result['deletion_count']
        assert stats['tampering_detected'] == result['tampering_detected']
