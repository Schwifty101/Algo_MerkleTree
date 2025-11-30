"""
Unit tests for IntegrityChecker.

Tests cover:
- Baseline snapshot creation and storage
- Integrity verification (O(1) root hash comparison)
- Verification reporting
- Baseline management (list, delete, compare)
- Edge cases and error handling
"""

import pytest
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from merkle.tree import MerkleTree
from verification.integrity_checker import IntegrityChecker


@pytest.fixture
def temp_storage_dir():
    """Create a temporary directory for test storage."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def checker(temp_storage_dir):
    """Create an IntegrityChecker with temporary storage."""
    return IntegrityChecker(storage_dir=temp_storage_dir)


@pytest.fixture
def sample_tree():
    """Create a sample Merkle tree for testing."""
    return MerkleTree(["a", "b", "c", "d"])


@pytest.fixture
def sample_tree_large():
    """Create a larger sample tree."""
    return MerkleTree([f"item{i}" for i in range(100)])


class TestBaselineSaving:
    """Test baseline snapshot creation and storage."""

    def test_save_baseline_basic(self, checker, sample_tree):
        """Test saving a basic baseline."""
        result = checker.save_baseline(sample_tree, "test_dataset")

        assert result['status'] == 'saved'
        assert result['dataset_name'] == 'test_dataset'
        assert 'root_hash' in result
        assert result['leaf_count'] == 4
        assert 'timestamp' in result

    def test_save_baseline_with_metadata(self, checker, sample_tree):
        """Test saving baseline with metadata."""
        metadata = {
            'source': 'test',
            'category': 'sample',
            'description': 'Test dataset'
        }
        result = checker.save_baseline(sample_tree, "test_with_meta", metadata=metadata)

        assert result['status'] == 'saved'

        # Verify metadata was stored
        loaded = checker.load_baseline("test_with_meta")
        assert loaded['metadata'] == metadata

    def test_save_baseline_overwrites(self, checker, sample_tree):
        """Test that saving with same name overwrites."""
        checker.save_baseline(sample_tree, "dataset1")

        # Create different tree and save with same name
        new_tree = MerkleTree(["x", "y", "z"])
        result = checker.save_baseline(new_tree, "dataset1")

        # Should overwrite
        loaded = checker.load_baseline("dataset1")
        assert loaded['leaf_count'] == 3
        assert loaded['root_hash'] == new_tree.get_root_hash_hex()

    def test_save_baseline_multiple_datasets(self, checker, sample_tree):
        """Test saving multiple different datasets."""
        tree1 = MerkleTree(["a", "b"])
        tree2 = MerkleTree(["x", "y"])
        tree3 = MerkleTree(["1", "2", "3"])

        checker.save_baseline(tree1, "dataset1")
        checker.save_baseline(tree2, "dataset2")
        checker.save_baseline(tree3, "dataset3")

        baselines = checker.list_baselines()
        assert len(baselines) == 3
        assert "dataset1" in baselines
        assert "dataset2" in baselines
        assert "dataset3" in baselines


class TestBaselineLoading:
    """Test baseline loading."""

    def test_load_existing_baseline(self, checker, sample_tree):
        """Test loading an existing baseline."""
        checker.save_baseline(sample_tree, "test_load")

        loaded = checker.load_baseline("test_load")

        assert loaded is not None
        assert loaded['dataset_name'] == 'test_load'
        assert loaded['root_hash'] == sample_tree.get_root_hash_hex()
        assert loaded['leaf_count'] == 4

    def test_load_nonexistent_baseline(self, checker):
        """Test loading a nonexistent baseline."""
        loaded = checker.load_baseline("does_not_exist")
        assert loaded is None

    def test_load_baseline_preserves_data(self, checker, sample_tree):
        """Test that loading preserves all saved data."""
        metadata = {'key': 'value'}
        checker.save_baseline(sample_tree, "preserve_test", metadata=metadata)

        loaded = checker.load_baseline("preserve_test")

        assert loaded['root_hash'] == sample_tree.get_root_hash_hex()
        assert loaded['leaf_count'] == sample_tree.get_leaf_count()
        assert loaded['metadata'] == metadata
        assert 'timestamp' in loaded


class TestIntegrityVerification:
    """Test integrity verification - the core <100ms operation."""

    def test_verify_identical_tree(self, checker, sample_tree):
        """Test verification succeeds with identical tree."""
        # Save baseline
        checker.save_baseline(sample_tree, "baseline1")

        # Verify same tree
        result = checker.verify_integrity(sample_tree, "baseline1")

        assert result['verified'] is True
        assert result['match'] is True
        assert result['current_root_hash'] == result['baseline_root_hash']
        assert result['status'] == 'verified'

    def test_verify_modified_tree(self, checker, sample_tree):
        """Test verification fails with modified tree."""
        # Save baseline
        checker.save_baseline(sample_tree, "baseline2")

        # Create modified tree (different data)
        modified_tree = MerkleTree(["a", "b", "c", "MODIFIED"])

        # Verify - should fail
        result = checker.verify_integrity(modified_tree, "baseline2")

        assert result['verified'] is False
        assert result['match'] is False
        assert result['current_root_hash'] != result['baseline_root_hash']
        assert result['status'] == 'failed'

    def test_verify_different_size_tree(self, checker, sample_tree):
        """Test verification fails when record count changes."""
        # Save baseline
        checker.save_baseline(sample_tree, "baseline3")

        # Create tree with different size
        different_tree = MerkleTree(["a", "b"])

        # Verify - should fail
        result = checker.verify_integrity(different_tree, "baseline3")

        assert result['verified'] is False
        assert result['leaf_count_match'] is False
        assert result['issue'] == 'leaf_count_mismatch'

    def test_verify_nonexistent_baseline(self, checker, sample_tree):
        """Test verification with nonexistent baseline."""
        result = checker.verify_integrity(sample_tree, "does_not_exist")

        assert result['verified'] is False
        assert result['error'] == 'baseline_not_found'

    def test_verify_detailed_mode(self, checker, sample_tree):
        """Test verification with detailed=True."""
        checker.save_baseline(sample_tree, "detailed_test")

        result = checker.verify_integrity(sample_tree, "detailed_test", detailed=True)

        assert 'current_leaf_count' in result
        assert 'baseline_leaf_count' in result
        assert 'leaf_count_match' in result
        assert 'baseline_metadata' in result
        assert 'message' in result

    def test_verify_simple_mode(self, checker, sample_tree):
        """Test verification with detailed=False."""
        checker.save_baseline(sample_tree, "simple_test")

        result = checker.verify_integrity(sample_tree, "simple_test", detailed=False)

        # Should have basic fields
        assert 'verified' in result
        assert 'match' in result

        # Should not have detailed fields
        assert 'message' not in result
        assert 'issue' not in result

    def test_verify_large_tree(self, checker, sample_tree_large):
        """Test verification works with larger trees."""
        checker.save_baseline(sample_tree_large, "large_baseline")

        result = checker.verify_integrity(sample_tree_large, "large_baseline")

        assert result['verified'] is True
        assert result['current_leaf_count'] == 100


class TestBaselineManagement:
    """Test baseline management operations."""

    def test_list_baselines_empty(self, checker):
        """Test listing when no baselines exist."""
        baselines = checker.list_baselines()
        assert baselines == []

    def test_list_baselines_multiple(self, checker, sample_tree):
        """Test listing multiple baselines."""
        checker.save_baseline(sample_tree, "baseline1")
        checker.save_baseline(sample_tree, "baseline2")
        checker.save_baseline(sample_tree, "baseline3")

        baselines = checker.list_baselines()
        assert len(baselines) == 3
        assert "baseline1" in baselines
        assert "baseline2" in baselines
        assert "baseline3" in baselines

    def test_delete_baseline_existing(self, checker, sample_tree):
        """Test deleting an existing baseline."""
        checker.save_baseline(sample_tree, "to_delete")

        deleted = checker.delete_baseline("to_delete")
        assert deleted is True

        # Should not exist anymore
        loaded = checker.load_baseline("to_delete")
        assert loaded is None

    def test_delete_baseline_nonexistent(self, checker):
        """Test deleting a nonexistent baseline."""
        deleted = checker.delete_baseline("does_not_exist")
        assert deleted is False

    def test_get_baseline_info_existing(self, checker, sample_tree):
        """Test getting info about existing baseline."""
        checker.save_baseline(sample_tree, "info_test")

        info = checker.get_baseline_info("info_test")

        assert info is not None
        assert info['dataset_name'] == 'info_test'
        assert info['leaf_count'] == 4
        assert 'timestamp' in info
        assert 'root_hash_preview' in info
        assert info['exists'] is True

    def test_get_baseline_info_nonexistent(self, checker):
        """Test getting info about nonexistent baseline."""
        info = checker.get_baseline_info("does_not_exist")
        assert info is None


class TestBaselineComparison:
    """Test comparing baselines."""

    def test_compare_identical_baselines(self, checker, sample_tree):
        """Test comparing identical baselines."""
        checker.save_baseline(sample_tree, "compare1")
        checker.save_baseline(sample_tree, "compare2")

        result = checker.compare_baselines("compare1", "compare2")

        assert result['identical'] is True
        assert result['root_hash_match'] is True
        assert result['leaf_count_match'] is True

    def test_compare_different_baselines(self, checker):
        """Test comparing different baselines."""
        tree1 = MerkleTree(["a", "b"])
        tree2 = MerkleTree(["x", "y"])

        checker.save_baseline(tree1, "diff1")
        checker.save_baseline(tree2, "diff2")

        result = checker.compare_baselines("diff1", "diff2")

        assert result['identical'] is False
        assert result['root_hash_match'] is False

    def test_compare_nonexistent_baseline(self, checker, sample_tree):
        """Test comparing with nonexistent baseline."""
        checker.save_baseline(sample_tree, "exists")

        result = checker.compare_baselines("exists", "does_not_exist")

        assert 'error' in result
        assert result['error'] == 'baseline_not_found'
        assert result['dataset1_exists'] is True
        assert result['dataset2_exists'] is False


class TestVerificationWithDict:
    """Test verification using serialized tree dictionaries."""

    def test_verify_with_tree_dict(self, checker, sample_tree):
        """Test verification using tree dictionary."""
        # Save baseline
        checker.save_baseline(sample_tree, "dict_test")

        # Get tree dict
        tree_dict = sample_tree.to_dict()

        # Verify using dict
        result = checker.verify_with_tree_dict(tree_dict, "dict_test")

        assert result['verified'] is True
        assert result['match'] is True

    def test_verify_with_modified_dict(self, checker, sample_tree):
        """Test verification fails with modified dict."""
        # Save baseline
        checker.save_baseline(sample_tree, "dict_mod_test")

        # Get tree dict and modify it
        tree_dict = sample_tree.to_dict()
        tree_dict['root_hash'] = 'a' * 64  # Tampered hash

        # Verify - should fail
        result = checker.verify_with_tree_dict(tree_dict, "dict_mod_test")

        assert result['verified'] is False
        assert result['match'] is False


class TestReportGeneration:
    """Test verification report generation."""

    def test_generate_report_verified(self, checker, sample_tree):
        """Test report generation for successful verification."""
        checker.save_baseline(sample_tree, "report_test")
        result = checker.verify_integrity(sample_tree, "report_test")

        report = checker.generate_verification_report(result)

        assert "VERIFIED" in report
        assert "✓" in report
        assert result['current_root_hash'] in report
        assert "report_test" in report

    def test_generate_report_failed(self, checker, sample_tree):
        """Test report generation for failed verification."""
        checker.save_baseline(sample_tree, "report_fail_test")

        modified_tree = MerkleTree(["modified", "data", "here", "!"])
        result = checker.verify_integrity(modified_tree, "report_fail_test")

        report = checker.generate_verification_report(result)

        assert "FAILED" in report
        assert "✗" in report
        assert "NO" in report  # For match status

    def test_generate_report_error(self, checker):
        """Test report generation for error case."""
        result = {
            'error': 'baseline_not_found',
            'dataset_name': 'missing',
            'message': 'Baseline not found'
        }

        report = checker.generate_verification_report(result)

        assert "ERROR" in report
        assert "missing" in report


class TestTimestamps:
    """Test timestamp handling."""

    def test_baseline_has_timestamp(self, checker, sample_tree):
        """Test that saved baselines include timestamps."""
        result = checker.save_baseline(sample_tree, "timestamp_test")

        assert 'timestamp' in result
        # Should be valid ISO format
        datetime.fromisoformat(result['timestamp'])

    def test_verification_has_timestamps(self, checker, sample_tree):
        """Test that verification includes timestamps."""
        checker.save_baseline(sample_tree, "verify_timestamp")
        result = checker.verify_integrity(sample_tree, "verify_timestamp")

        assert 'verification_timestamp' in result
        assert 'baseline_timestamp' in result

        # Should be valid ISO format
        datetime.fromisoformat(result['verification_timestamp'])
        datetime.fromisoformat(result['baseline_timestamp'])


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_single_leaf_tree(self, checker):
        """Test with tree containing single leaf."""
        tree = MerkleTree(["only"])
        checker.save_baseline(tree, "single_leaf")

        result = checker.verify_integrity(tree, "single_leaf")
        assert result['verified'] is True

    def test_large_metadata(self, checker, sample_tree):
        """Test with large metadata."""
        metadata = {
            'description': 'x' * 1000,
            'tags': ['tag' + str(i) for i in range(100)]
        }

        checker.save_baseline(sample_tree, "large_meta", metadata=metadata)
        loaded = checker.load_baseline("large_meta")

        assert loaded['metadata'] == metadata

    def test_special_characters_in_name(self, checker, sample_tree):
        """Test with special characters in dataset name."""
        names = [
            "dataset-with-dashes",
            "dataset_with_underscores",
            "dataset.with.dots"
        ]

        for name in names:
            checker.save_baseline(sample_tree, name)
            loaded = checker.load_baseline(name)
            assert loaded is not None

    def test_verify_same_data_different_order(self, checker):
        """Test that order matters in verification."""
        tree1 = MerkleTree(["a", "b", "c"])
        tree2 = MerkleTree(["c", "b", "a"])  # Same data, different order

        checker.save_baseline(tree1, "order_test")
        result = checker.verify_integrity(tree2, "order_test")

        # Should fail because order creates different tree structure
        assert result['verified'] is False


class TestIntegration:
    """Test integration scenarios."""

    def test_workflow_save_verify_modify_verify(self, checker, sample_tree):
        """Test complete workflow: save -> verify -> modify -> verify."""
        # 1. Save baseline
        checker.save_baseline(sample_tree, "workflow_test")

        # 2. Verify original - should pass
        result1 = checker.verify_integrity(sample_tree, "workflow_test")
        assert result1['verified'] is True

        # 3. Create modified tree
        modified = MerkleTree(["a", "b", "c", "MODIFIED"])

        # 4. Verify modified - should fail
        result2 = checker.verify_integrity(modified, "workflow_test")
        assert result2['verified'] is False

    def test_multiple_datasets_independent(self, checker):
        """Test that multiple datasets are independent."""
        tree1 = MerkleTree(["dataset", "1"])
        tree2 = MerkleTree(["dataset", "2"])
        tree3 = MerkleTree(["dataset", "3"])

        checker.save_baseline(tree1, "ds1")
        checker.save_baseline(tree2, "ds2")
        checker.save_baseline(tree3, "ds3")

        # Each should verify correctly
        assert checker.verify_integrity(tree1, "ds1")['verified'] is True
        assert checker.verify_integrity(tree2, "ds2")['verified'] is True
        assert checker.verify_integrity(tree3, "ds3")['verified'] is True

        # Cross-verification should fail
        assert checker.verify_integrity(tree1, "ds2")['verified'] is False
