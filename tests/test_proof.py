"""
Unit tests for Merkle proof system.

Tests cover:
- Proof generation from trees of various sizes
- Proof verification (valid and invalid)
- Serialization/deserialization
- Edge cases (single leaf, odd counts, etc.)
- Integration with MerkleTree
- Raw bytes handling
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from merkle.tree import MerkleTree
from merkle.proof import MerkleProof
from utils.hash_utils import hash_data, hash_pair, bytes_to_hex, hex_to_bytes


class TestMerkleProofCreation:
    """Test MerkleProof object creation."""

    def test_create_proof_with_strings(self):
        """Test creating proof with string data."""
        tree = MerkleTree(["a", "b", "c", "d"])
        proof = tree.get_proof(0, "a")

        assert proof.leaf_data == "a"
        assert proof.leaf_index == 0
        assert isinstance(proof.proof_path, list)
        assert len(proof.proof_path) > 0

    def test_create_proof_with_dict(self):
        """Test creating proof with dictionary data."""
        reviews = [
            {"reviewerID": "A123", "asin": "B456", "overall": "5"},
            {"reviewerID": "A789", "asin": "B012", "overall": "4"}
        ]
        tree = MerkleTree(reviews)
        proof = tree.get_proof(0, reviews[0])

        assert proof.leaf_data == reviews[0]
        assert proof.leaf_index == 0

    def test_create_proof_without_data(self):
        """Test creating proof without including data."""
        tree = MerkleTree(["a", "b", "c"])
        proof = tree.get_proof(1)  # No data argument

        assert proof.leaf_data is None
        assert proof.leaf_index == 1

    def test_proof_path_uses_bytes(self):
        """Test that proof path uses raw bytes, not hex strings."""
        tree = MerkleTree(["a", "b", "c", "d"])
        proof = tree.get_proof(2)

        for sibling_hash, is_left in proof.proof_path:
            assert isinstance(sibling_hash, bytes)
            assert len(sibling_hash) == 32
            assert isinstance(is_left, bool)

    def test_proof_path_length(self):
        """Test that proof path length is roughly log₂(n)."""
        # For 8 leaves, expect path length of 3 (log₂(8) = 3)
        tree = MerkleTree([f"item{i}" for i in range(8)])
        proof = tree.get_proof(0)

        assert len(proof.proof_path) == 3

        # For 16 leaves, expect path length of 4 (log₂(16) = 4)
        tree = MerkleTree([f"item{i}" for i in range(16)])
        proof = tree.get_proof(0)

        assert len(proof.proof_path) == 4


class TestProofGeneration:
    """Test proof generation from MerkleTree."""

    def test_generate_proof_for_each_leaf(self):
        """Test generating proofs for all leaves in a tree."""
        data = ["a", "b", "c", "d"]
        tree = MerkleTree(data)

        # Should be able to generate proof for each leaf
        for i in range(len(data)):
            proof = tree.get_proof(i, data[i])
            assert proof.leaf_index == i
            assert proof.verify()

    def test_proof_generation_invalid_index(self):
        """Test that invalid index raises IndexError."""
        tree = MerkleTree(["a", "b", "c"])

        with pytest.raises(IndexError):
            tree.get_proof(10)

        with pytest.raises(IndexError):
            tree.get_proof(-1)

    def test_proof_for_single_leaf_tree(self):
        """Test proof generation for tree with single leaf."""
        tree = MerkleTree(["only"])
        proof = tree.get_proof(0, "only")

        # Single leaf should have empty proof path
        assert len(proof.proof_path) == 0
        assert proof.verify()

    def test_proof_for_two_leaf_tree(self):
        """Test proof generation for tree with two leaves."""
        tree = MerkleTree(["left", "right"])

        # Proof for left leaf
        proof_left = tree.get_proof(0, "left")
        assert len(proof_left.proof_path) == 1
        assert proof_left.verify()

        # Proof for right leaf
        proof_right = tree.get_proof(1, "right")
        assert len(proof_right.proof_path) == 1
        assert proof_right.verify()

    def test_proof_for_odd_number_of_leaves(self):
        """Test proof generation for tree with odd number of leaves."""
        data = ["a", "b", "c", "d", "e"]
        tree = MerkleTree(data)

        # Generate proof for each leaf
        for i, item in enumerate(data):
            proof = tree.get_proof(i, item)
            assert proof.verify()

    def test_proof_for_power_of_two_leaves(self):
        """Test proof generation for trees with power-of-2 leaves."""
        for size in [2, 4, 8, 16, 32]:
            data = [f"item{i}" for i in range(size)]
            tree = MerkleTree(data)

            # Test first, middle, and last leaves
            indices = [0, size // 2, size - 1]
            for idx in indices:
                proof = tree.get_proof(idx, data[idx])
                assert proof.verify()


class TestProofVerification:
    """Test proof verification."""

    def test_verify_valid_proof(self):
        """Test that valid proofs verify successfully."""
        tree = MerkleTree(["a", "b", "c", "d"])
        proof = tree.get_proof(2, "c")

        assert proof.verify() is True

    def test_verify_invalid_data(self):
        """Test that proof fails with wrong data."""
        tree = MerkleTree(["a", "b", "c", "d"])
        proof = tree.get_proof(2, "c")

        # Modify the data
        proof.leaf_data = "wrong"

        assert proof.verify() is False

    def test_verify_tampered_proof_path(self):
        """Test that proof fails if path is tampered."""
        tree = MerkleTree(["a", "b", "c", "d"])
        proof = tree.get_proof(2, "c")

        # Tamper with the proof path
        if len(proof.proof_path) > 0:
            tampered_hash = bytes(32)  # All zeros
            proof.proof_path[0] = (tampered_hash, proof.proof_path[0][1])

            assert proof.verify() is False

    def test_verify_wrong_root_hash(self):
        """Test that proof fails with wrong root hash."""
        tree = MerkleTree(["a", "b", "c", "d"])
        proof = tree.get_proof(2, "c")

        # Change root hash
        proof.root_hash = bytes(32)  # All zeros

        assert proof.verify() is False

    def test_verify_static_method(self):
        """Test static verify_proof method."""
        tree = MerkleTree(["a", "b", "c", "d"])
        proof = tree.get_proof(2, "c")

        # Verify using static method
        is_valid = MerkleProof.verify_proof(
            leaf_data="c",
            proof_path=proof.proof_path,
            root_hash=tree.get_root_hash()
        )

        assert is_valid is True

    def test_verify_static_method_invalid(self):
        """Test static verify_proof with invalid data."""
        tree = MerkleTree(["a", "b", "c", "d"])
        proof = tree.get_proof(2, "c")

        # Verify with wrong data
        is_valid = MerkleProof.verify_proof(
            leaf_data="wrong",
            proof_path=proof.proof_path,
            root_hash=tree.get_root_hash()
        )

        assert is_valid is False


class TestProofSerialization:
    """Test proof serialization and deserialization."""

    def test_to_dict(self):
        """Test converting proof to dictionary."""
        tree = MerkleTree(["a", "b", "c"])
        proof = tree.get_proof(1, "b")
        proof_dict = proof.to_dict()

        assert 'leaf_data' in proof_dict
        assert 'leaf_index' in proof_dict
        assert 'proof_path' in proof_dict
        assert 'root_hash' in proof_dict

        assert proof_dict['leaf_data'] == "b"
        assert proof_dict['leaf_index'] == 1

        # Check that hashes are hex strings
        assert isinstance(proof_dict['root_hash'], str)
        for step in proof_dict['proof_path']:
            assert isinstance(step['sibling_hash'], str)
            assert isinstance(step['is_left'], bool)

    def test_from_dict(self):
        """Test creating proof from dictionary."""
        tree = MerkleTree(["a", "b", "c"])
        original = tree.get_proof(1, "b")
        proof_dict = original.to_dict()

        restored = MerkleProof.from_dict(proof_dict)

        assert restored.leaf_data == original.leaf_data
        assert restored.leaf_index == original.leaf_index
        assert restored.root_hash == original.root_hash
        assert len(restored.proof_path) == len(original.proof_path)

    def test_serialization_roundtrip(self):
        """Test complete serialization roundtrip."""
        tree = MerkleTree([f"item{i}" for i in range(10)])
        original = tree.get_proof(5, "item5")

        # Serialize
        serialized = original.to_dict()

        # Deserialize
        restored = MerkleProof.from_dict(serialized)

        # Verify everything matches
        assert restored == original
        assert restored.verify()

    def test_serialization_preserves_bytes(self):
        """Test that deserialization converts hex back to bytes."""
        tree = MerkleTree(["a", "b", "c", "d"])
        original = tree.get_proof(2, "c")

        restored = MerkleProof.from_dict(original.to_dict())

        # Check that internal representation uses bytes
        assert isinstance(restored.root_hash, bytes)
        for sibling_hash, is_left in restored.proof_path:
            assert isinstance(sibling_hash, bytes)
            assert len(sibling_hash) == 32


class TestProofEdgeCases:
    """Test edge cases and special scenarios."""

    def test_single_leaf_proof(self):
        """Test proof for tree with single leaf."""
        tree = MerkleTree(["only"])
        proof = tree.get_proof(0, "only")

        assert len(proof.proof_path) == 0
        assert proof.verify()

    def test_proof_with_large_data(self):
        """Test proof with large data items."""
        large_text = "x" * 10000
        tree = MerkleTree([large_text, "b", "c"])
        proof = tree.get_proof(0, large_text)

        assert proof.verify()

    def test_proof_with_special_characters(self):
        """Test proof with special characters."""
        data = ["Hello 世界", "Test\x00Data", "Special!@#$%"]
        tree = MerkleTree(data)

        for i, item in enumerate(data):
            proof = tree.get_proof(i, item)
            assert proof.verify()

    def test_proof_with_duplicate_data(self):
        """Test proofs for duplicate data items."""
        data = ["same", "same", "different"]
        tree = MerkleTree(data)

        # Both "same" items should have valid but different proofs
        proof0 = tree.get_proof(0, "same")
        proof1 = tree.get_proof(1, "same")

        assert proof0.verify()
        assert proof1.verify()
        assert proof0.leaf_index != proof1.leaf_index

    def test_large_tree_proof(self):
        """Test proof generation for large tree."""
        # 1000 leaves
        data = [f"review_{i}" for i in range(1000)]
        tree = MerkleTree(data)

        # Test proofs for a few leaves
        for idx in [0, 100, 500, 999]:
            proof = tree.get_proof(idx, data[idx])
            assert proof.verify()

            # Check proof length is roughly log₂(1000) ≈ 10
            assert 8 <= len(proof.proof_path) <= 12


class TestProofIntegration:
    """Test integration between MerkleTree and MerkleProof."""

    def test_proof_matches_tree_root(self):
        """Test that proof root hash matches tree root hash."""
        tree = MerkleTree(["a", "b", "c", "d"])
        proof = tree.get_proof(2)

        assert proof.root_hash == tree.get_root_hash()

    def test_all_proofs_in_tree_verify(self):
        """Test that all proofs in a tree verify successfully."""
        data = [f"item{i}" for i in range(20)]
        tree = MerkleTree(data)

        for i, item in enumerate(data):
            proof = tree.get_proof(i, item)
            assert proof.verify(), f"Proof for index {i} failed"

    def test_proof_with_dict_data(self):
        """Test proof generation and verification with review dicts."""
        reviews = [
            {"reviewerID": "A123", "asin": "B456", "overall": "5"},
            {"reviewerID": "A789", "asin": "B012", "overall": "4"},
            {"reviewerID": "A111", "asin": "B222", "overall": "3"}
        ]
        tree = MerkleTree(reviews)

        for i, review in enumerate(reviews):
            proof = tree.get_proof(i, review)
            assert proof.verify()

    def test_modified_data_fails_verification(self):
        """Test that modified data fails verification."""
        tree = MerkleTree(["a", "b", "c", "d"])
        proof = tree.get_proof(1, "b")

        # Verify original
        assert proof.verify()

        # Modify data
        proof.leaf_data = "modified"

        # Should fail
        assert not proof.verify()

    def test_cross_tree_proof_fails(self):
        """Test that proof from one tree fails on another tree."""
        tree1 = MerkleTree(["a", "b", "c", "d"])
        tree2 = MerkleTree(["w", "x", "y", "z"])

        proof = tree1.get_proof(1, "b")

        # Proof should work on original tree
        assert proof.verify()

        # Modify to use tree2's root hash
        proof.root_hash = tree2.get_root_hash()

        # Should fail
        assert not proof.verify()


class TestProofProperties:
    """Test MerkleProof properties and methods."""

    def test_get_proof_length(self):
        """Test getting proof path length."""
        tree = MerkleTree([f"item{i}" for i in range(16)])
        proof = tree.get_proof(5)

        assert proof.get_proof_length() == len(proof.proof_path)
        assert proof.get_proof_length() == 4  # log₂(16) = 4

    def test_proof_repr(self):
        """Test proof string representation."""
        tree = MerkleTree(["a", "b", "c"])
        proof = tree.get_proof(1, "b")
        repr_str = repr(proof)

        assert "MerkleProof" in repr_str
        assert "index=1" in repr_str
        assert "path_length=" in repr_str
        assert "root=" in repr_str

    def test_proof_equality(self):
        """Test proof equality comparison."""
        tree = MerkleTree(["a", "b", "c"])
        proof1 = tree.get_proof(1, "b")
        proof2 = tree.get_proof(1, "b")

        assert proof1 == proof2

    def test_proof_inequality(self):
        """Test proof inequality for different leaves."""
        tree = MerkleTree(["a", "b", "c"])
        proof1 = tree.get_proof(0, "a")
        proof2 = tree.get_proof(1, "b")

        assert proof1 != proof2


class TestProofValidation:
    """Test proof validation and error handling."""

    def test_invalid_root_hash_raises_error(self):
        """Test that invalid root hash raises ValueError."""
        with pytest.raises(ValueError):
            MerkleProof(
                leaf_data="test",
                leaf_index=0,
                proof_path=[],
                root_hash="not bytes"  # Wrong type
            )

    def test_invalid_sibling_hash_raises_error(self):
        """Test that invalid sibling hash raises ValueError."""
        with pytest.raises(ValueError):
            MerkleProof(
                leaf_data="test",
                leaf_index=0,
                proof_path=[("not bytes", True)],  # Wrong type
                root_hash=bytes(32)
            )

    def test_invalid_is_left_raises_error(self):
        """Test that invalid is_left raises ValueError."""
        with pytest.raises(ValueError):
            MerkleProof(
                leaf_data="test",
                leaf_index=0,
                proof_path=[(bytes(32), "not bool")],  # Wrong type
                root_hash=bytes(32)
            )

    def test_short_root_hash_raises_error(self):
        """Test that short root hash raises ValueError."""
        with pytest.raises(ValueError):
            MerkleProof(
                leaf_data="test",
                leaf_index=0,
                proof_path=[],
                root_hash=bytes(16)  # Too short
            )
