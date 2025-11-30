"""
Unit tests for Merkle tree implementation.

Tests cover:
- Tree construction with various data sizes
- Hybrid storage approach (root + leaves only)
- Hash consistency and determinism
- Serialization/deserialization
- Memory efficiency
- Edge cases (1 node, odd numbers, power of 2, etc.)
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from merkle.node import MerkleNode
from merkle.tree import MerkleTree
from utils.hash_utils import hash_data, hash_pair, bytes_to_hex


class TestMerkleNode:
    """Test MerkleNode class."""

    def test_create_leaf_node(self):
        """Test creating a leaf node."""
        hash_val = hash_data("test")
        node = MerkleNode(hash_val, data="test", index=0)

        assert node.hash == hash_val
        assert node.is_leaf is True
        assert node.data == "test"
        assert node.index == 0

    def test_create_internal_node(self):
        """Test creating an internal node."""
        left = MerkleNode(hash_data("left"), data="left", index=0)
        right = MerkleNode(hash_data("right"), data="right", index=1)
        parent_hash = hash_pair(left.hash, right.hash)
        parent = MerkleNode(parent_hash, left=left, right=right)

        assert parent.is_leaf is False
        assert parent.left == left
        assert parent.right == right

    def test_node_hash_must_be_bytes(self):
        """Test that hash must be bytes."""
        with pytest.raises(TypeError):
            MerkleNode("not bytes")

    def test_node_hash_must_be_32_bytes(self):
        """Test that hash must be exactly 32 bytes."""
        with pytest.raises(ValueError):
            MerkleNode(b"short")

    def test_node_equality(self):
        """Test node equality based on hash."""
        hash1 = hash_data("test")
        node1 = MerkleNode(hash1)
        node2 = MerkleNode(hash1)

        assert node1 == node2

    def test_node_inequality(self):
        """Test nodes with different hashes are not equal."""
        node1 = MerkleNode(hash_data("test1"))
        node2 = MerkleNode(hash_data("test2"))

        assert node1 != node2

    def test_get_hash_hex(self):
        """Test getting hash as hex string."""
        node = MerkleNode(hash_data("test"))
        hex_str = node.get_hash_hex()

        assert isinstance(hex_str, str)
        assert len(hex_str) == 64  # 32 bytes = 64 hex chars


class TestMerkleTreeConstruction:
    """Test Merkle tree construction."""

    def test_create_tree_from_strings(self):
        """Test creating tree from list of strings."""
        data = ["apple", "banana", "cherry"]
        tree = MerkleTree(data)

        assert tree.get_leaf_count() == 3
        assert isinstance(tree.get_root_hash(), bytes)
        assert len(tree.get_root_hash()) == 32

    def test_create_tree_from_dicts(self):
        """Test creating tree from review dictionaries."""
        data = [
            {"reviewerID": "A123", "asin": "B456", "overall": "5"},
            {"reviewerID": "A789", "asin": "B012", "overall": "4"}
        ]
        tree = MerkleTree(data)

        assert tree.get_leaf_count() == 2
        assert isinstance(tree.get_root_hash(), bytes)

    def test_create_tree_single_item(self):
        """Test creating tree with single item."""
        tree = MerkleTree(["only"])

        assert tree.get_leaf_count() == 1
        assert isinstance(tree.get_root_hash(), bytes)

    def test_create_tree_two_items(self):
        """Test creating tree with two items."""
        tree = MerkleTree(["first", "second"])

        assert tree.get_leaf_count() == 2

    def test_create_tree_power_of_two(self):
        """Test creating tree with power of 2 items."""
        for size in [1, 2, 4, 8, 16, 32]:
            data = [f"item{i}" for i in range(size)]
            tree = MerkleTree(data)
            assert tree.get_leaf_count() == size

    def test_create_tree_odd_number(self):
        """Test creating tree with odd number of items."""
        for size in [3, 5, 7, 9, 11]:
            data = [f"item{i}" for i in range(size)]
            tree = MerkleTree(data)
            assert tree.get_leaf_count() == size

    def test_empty_data_raises_error(self):
        """Test that empty data raises ValueError."""
        with pytest.raises(ValueError):
            MerkleTree([])


class TestMerkleTreeDeterminism:
    """Test that Merkle tree is deterministic."""

    def test_same_data_same_root(self):
        """Test that same data produces same root hash."""
        data = ["a", "b", "c"]

        tree1 = MerkleTree(data)
        tree2 = MerkleTree(data)

        assert tree1.get_root_hash() == tree2.get_root_hash()

    def test_different_data_different_root(self):
        """Test that different data produces different root."""
        tree1 = MerkleTree(["a", "b", "c"])
        tree2 = MerkleTree(["a", "b", "d"])  # Last item different

        assert tree1.get_root_hash() != tree2.get_root_hash()

    def test_order_matters(self):
        """Test that order of data affects root hash."""
        tree1 = MerkleTree(["a", "b", "c"])
        tree2 = MerkleTree(["c", "b", "a"])  # Reversed

        assert tree1.get_root_hash() != tree2.get_root_hash()

    def test_rebuild_produces_same_root(self):
        """Test that rebuilding tree produces same root."""
        data = ["item" + str(i) for i in range(10)]

        roots = [MerkleTree(data).get_root_hash() for _ in range(5)]

        # All roots should be identical
        assert all(r == roots[0] for r in roots)


class TestMerkleTreeLeafAccess:
    """Test leaf hash access."""

    def test_get_leaf_hash(self):
        """Test getting individual leaf hash."""
        data = ["a", "b", "c"]
        tree = MerkleTree(data)

        leaf0 = tree.get_leaf_hash(0)
        assert isinstance(leaf0, bytes)
        assert len(leaf0) == 32
        assert leaf0 == hash_data("a")

    def test_get_leaf_hash_out_of_range(self):
        """Test getting leaf with invalid index."""
        tree = MerkleTree(["a", "b"])

        with pytest.raises(IndexError):
            tree.get_leaf_hash(5)

        with pytest.raises(IndexError):
            tree.get_leaf_hash(-1)

    def test_get_all_leaf_hashes(self):
        """Test getting all leaf hashes."""
        data = ["a", "b", "c"]
        tree = MerkleTree(data)

        leaves = tree.get_all_leaf_hashes()

        assert len(leaves) == 3
        assert all(isinstance(h, bytes) for h in leaves)
        assert all(len(h) == 32 for h in leaves)

    def test_leaf_hashes_are_copy(self):
        """Test that get_all_leaf_hashes returns a copy."""
        tree = MerkleTree(["a", "b"])

        leaves1 = tree.get_all_leaf_hashes()
        leaves2 = tree.get_all_leaf_hashes()

        assert leaves1 == leaves2
        assert leaves1 is not leaves2  # Different objects


class TestMerkleTreeVerification:
    """Test data verification."""

    def test_verify_data_in_tree(self):
        """Test verifying data at correct index."""
        data = ["apple", "banana", "cherry"]
        tree = MerkleTree(data)

        assert tree.verify_data_in_tree("apple", 0) is True
        assert tree.verify_data_in_tree("banana", 1) is True
        assert tree.verify_data_in_tree("cherry", 2) is True

    def test_verify_wrong_data(self):
        """Test verifying wrong data returns False."""
        tree = MerkleTree(["apple", "banana"])

        assert tree.verify_data_in_tree("cherry", 0) is False

    def test_verify_wrong_index(self):
        """Test verifying data at wrong index returns False."""
        tree = MerkleTree(["apple", "banana"])

        assert tree.verify_data_in_tree("apple", 1) is False

    def test_verify_out_of_range_index(self):
        """Test verifying with out of range index."""
        tree = MerkleTree(["apple"])

        assert tree.verify_data_in_tree("apple", 5) is False


class TestMerkleTreeSerialization:
    """Test tree serialization and deserialization."""

    def test_to_dict(self):
        """Test converting tree to dictionary."""
        tree = MerkleTree(["a", "b", "c"])
        tree_dict = tree.to_dict()

        assert 'root_hash' in tree_dict
        assert 'leaf_hashes' in tree_dict
        assert 'leaf_count' in tree_dict

        assert isinstance(tree_dict['root_hash'], str)
        assert isinstance(tree_dict['leaf_hashes'], list)
        assert tree_dict['leaf_count'] == 3

    def test_from_dict(self):
        """Test creating tree from dictionary."""
        original = MerkleTree(["a", "b", "c"])
        tree_dict = original.to_dict()

        restored = MerkleTree.from_dict(tree_dict)

        assert restored.get_root_hash() == original.get_root_hash()
        assert restored.get_leaf_count() == original.get_leaf_count()
        assert restored.get_all_leaf_hashes() == original.get_all_leaf_hashes()

    def test_serialization_roundtrip(self):
        """Test complete serialization roundtrip."""
        data = [f"item{i}" for i in range(10)]
        original = MerkleTree(data)

        # Serialize
        serialized = original.to_dict()

        # Deserialize
        restored = MerkleTree.from_dict(serialized)

        # Verify everything matches
        assert restored.get_root_hash() == original.get_root_hash()
        assert restored.get_leaf_count() == original.get_leaf_count()

        for i in range(original.get_leaf_count()):
            assert restored.get_leaf_hash(i) == original.get_leaf_hash(i)


class TestMerkleTreeMemoryEfficiency:
    """Test memory efficiency of hybrid storage."""

    def test_memory_usage_small_tree(self):
        """Test memory usage for small tree."""
        tree = MerkleTree(["a", "b", "c"])
        stats = tree.get_memory_usage()

        assert 'total_bytes' in stats
        assert 'total_mb' in stats
        assert 'bytes_per_leaf' in stats
        assert 'leaf_count' in stats

        assert stats['leaf_count'] == 3

    def test_memory_usage_grows_linearly(self):
        """Test that memory grows linearly with leaf count."""
        tree100 = MerkleTree([f"item{i}" for i in range(100)])
        tree1000 = MerkleTree([f"item{i}" for i in range(1000)])

        mem100 = tree100.get_memory_usage()['total_bytes']
        mem1000 = tree1000.get_memory_usage()['total_bytes']

        # Should be roughly 10x (with some overhead)
        ratio = mem1000 / mem100
        assert 8 < ratio < 12  # Allow some variance for overhead

    def test_hybrid_storage_is_memory_efficient(self):
        """Test that hybrid storage uses minimal memory."""
        # 1000 leaves should use much less than 1MB
        tree = MerkleTree([f"item{i}" for i in range(1000)])
        stats = tree.get_memory_usage()

        # Each leaf hash is 32 bytes, so 1000 leaves ≈ 32KB + overhead
        assert stats['total_mb'] < 0.1  # Should be well under 100KB


class TestMerkleTreeRootHashHex:
    """Test hex representation of root hash."""

    def test_get_root_hash_hex(self):
        """Test getting root hash as hex string."""
        tree = MerkleTree(["test"])
        hex_str = tree.get_root_hash_hex()

        assert isinstance(hex_str, str)
        assert len(hex_str) == 64  # 32 bytes = 64 hex chars
        assert all(c in '0123456789abcdef' for c in hex_str.lower())

    def test_root_hash_hex_is_consistent(self):
        """Test that hex representation is consistent."""
        tree = MerkleTree(["test"])

        hex1 = tree.get_root_hash_hex()
        hex2 = tree.get_root_hash_hex()

        assert hex1 == hex2


class TestMerkleTreeEdgeCases:
    """Test edge cases and special scenarios."""

    def test_large_data_items(self):
        """Test with large data items."""
        large_text = "a" * 10000  # 10KB string
        tree = MerkleTree([large_text] * 10)

        assert tree.get_leaf_count() == 10
        assert isinstance(tree.get_root_hash(), bytes)

    def test_special_characters(self):
        """Test with special characters in data."""
        data = ["Hello 世界", "Test\x00Data", "Special!@#$%"]
        tree = MerkleTree(data)

        assert tree.get_leaf_count() == 3

    def test_tree_with_1000_items(self):
        """Test tree with 1000 items (realistic small dataset)."""
        data = [f"review_{i}" for i in range(1000)]
        tree = MerkleTree(data)

        assert tree.get_leaf_count() == 1000
        assert isinstance(tree.get_root_hash(), bytes)

        # Verify memory is reasonable
        stats = tree.get_memory_usage()
        assert stats['total_mb'] < 1.0  # Should be well under 1MB


class TestMerkleTreeRepr:
    """Test string representation."""

    def test_tree_repr(self):
        """Test tree string representation."""
        tree = MerkleTree(["a", "b", "c"])
        repr_str = repr(tree)

        assert "MerkleTree" in repr_str
        assert "leaves=3" in repr_str
        assert "root=" in repr_str
