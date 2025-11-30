"""
Unit tests for hash_utils module.

Tests cover:
- Raw bytes hashing operations
- Hex conversion functions
- Canonical string generation
- Deterministic hashing
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils.hash_utils import (
    hash_data,
    hash_pair,
    hash_review,
    generate_canonical_string,
    bytes_to_hex,
    hex_to_bytes
)


class TestHashData:
    """Test hash_data function."""

    def test_hash_data_returns_bytes(self):
        """Test that hash_data returns bytes, not string."""
        result = hash_data("hello")
        assert isinstance(result, bytes)
        assert len(result) == 32  # SHA-256 produces 32 bytes

    def test_hash_data_deterministic(self):
        """Test that same input produces same hash."""
        hash1 = hash_data("test")
        hash2 = hash_data("test")
        assert hash1 == hash2

    def test_hash_data_different_inputs(self):
        """Test that different inputs produce different hashes."""
        hash1 = hash_data("hello")
        hash2 = hash_data("world")
        assert hash1 != hash2

    def test_hash_data_empty_string(self):
        """Test hashing empty string."""
        result = hash_data("")
        assert isinstance(result, bytes)
        assert len(result) == 32

    def test_hash_data_unicode(self):
        """Test hashing unicode characters."""
        result = hash_data("Hello 世界 🌍")
        assert isinstance(result, bytes)
        assert len(result) == 32


class TestHashPair:
    """Test hash_pair function."""

    def test_hash_pair_returns_bytes(self):
        """Test that hash_pair returns bytes."""
        left = hash_data("left")
        right = hash_data("right")
        result = hash_pair(left, right)
        assert isinstance(result, bytes)
        assert len(result) == 32

    def test_hash_pair_deterministic(self):
        """Test that same inputs produce same hash."""
        left = hash_data("a")
        right = hash_data("b")
        hash1 = hash_pair(left, right)
        hash2 = hash_pair(left, right)
        assert hash1 == hash2

    def test_hash_pair_order_matters(self):
        """Test that order of inputs affects result."""
        left = hash_data("a")
        right = hash_data("b")
        hash_ab = hash_pair(left, right)
        hash_ba = hash_pair(right, left)
        assert hash_ab != hash_ba

    def test_hash_pair_identical_inputs(self):
        """Test hashing pair of identical hashes."""
        hash_val = hash_data("same")
        result = hash_pair(hash_val, hash_val)
        assert isinstance(result, bytes)
        assert len(result) == 32


class TestGenerateCanonicalString:
    """Test generate_canonical_string function."""

    def test_canonical_string_format(self):
        """Test canonical string has correct format."""
        review = {
            "reviewerID": "A123",
            "asin": "B456",
            "overall": "5",
            "unixReviewTime": "1234567890",
            "reviewText": "Great product!"
        }
        result = generate_canonical_string(review)
        expected = "A123|B456|5|1234567890|Great product!"
        assert result == expected

    def test_canonical_string_missing_fields(self):
        """Test handling of missing fields."""
        review = {"reviewerID": "A123"}
        result = generate_canonical_string(review)
        assert result.startswith("A123|")
        assert result.count("|") == 4  # Should have 5 fields

    def test_canonical_string_empty_dict(self):
        """Test with empty dictionary."""
        result = generate_canonical_string({})
        assert result == "||||"

    def test_canonical_string_deterministic(self):
        """Test that same review produces same string."""
        review = {"reviewerID": "A123", "asin": "B456"}
        str1 = generate_canonical_string(review)
        str2 = generate_canonical_string(review)
        assert str1 == str2


class TestHashReview:
    """Test hash_review function."""

    def test_hash_review_returns_bytes(self):
        """Test that hash_review returns bytes."""
        review = {"reviewerID": "A123", "asin": "B456"}
        result = hash_review(review)
        assert isinstance(result, bytes)
        assert len(result) == 32

    def test_hash_review_deterministic(self):
        """Test that same review produces same hash."""
        review = {
            "reviewerID": "A123",
            "asin": "B456",
            "overall": "5",
            "unixReviewTime": "1234567890",
            "reviewText": "Great!"
        }
        hash1 = hash_review(review)
        hash2 = hash_review(review)
        assert hash1 == hash2

    def test_hash_review_different_reviews(self):
        """Test that different reviews produce different hashes."""
        review1 = {"reviewerID": "A123", "reviewText": "Good"}
        review2 = {"reviewerID": "A456", "reviewText": "Bad"}
        hash1 = hash_review(review1)
        hash2 = hash_review(review2)
        assert hash1 != hash2

    def test_hash_review_field_order_independent(self):
        """Test that field order in dict doesn't matter."""
        review1 = {"reviewerID": "A123", "asin": "B456"}
        review2 = {"asin": "B456", "reviewerID": "A123"}
        hash1 = hash_review(review1)
        hash2 = hash_review(review2)
        assert hash1 == hash2  # Canonical format ensures same order


class TestBytesToHex:
    """Test bytes_to_hex function."""

    def test_bytes_to_hex_conversion(self):
        """Test conversion from bytes to hex string."""
        hash_bytes = hash_data("test")
        hex_str = bytes_to_hex(hash_bytes)
        assert isinstance(hex_str, str)
        assert len(hex_str) == 64  # 32 bytes = 64 hex characters

    def test_bytes_to_hex_deterministic(self):
        """Test that same bytes produce same hex."""
        hash_bytes = hash_data("test")
        hex1 = bytes_to_hex(hash_bytes)
        hex2 = bytes_to_hex(hash_bytes)
        assert hex1 == hex2

    def test_bytes_to_hex_only_hex_chars(self):
        """Test that output contains only hex characters."""
        hash_bytes = hash_data("test")
        hex_str = bytes_to_hex(hash_bytes)
        assert all(c in '0123456789abcdef' for c in hex_str.lower())


class TestHexToBytes:
    """Test hex_to_bytes function."""

    def test_hex_to_bytes_conversion(self):
        """Test conversion from hex string to bytes."""
        hash_bytes = hash_data("test")
        hex_str = bytes_to_hex(hash_bytes)
        result = hex_to_bytes(hex_str)
        assert isinstance(result, bytes)
        assert len(result) == 32

    def test_hex_to_bytes_roundtrip(self):
        """Test that bytes -> hex -> bytes preserves value."""
        original = hash_data("test")
        hex_str = bytes_to_hex(original)
        recovered = hex_to_bytes(hex_str)
        assert original == recovered


class TestIntegration:
    """Integration tests for hash utilities."""

    def test_complete_hashing_workflow(self):
        """Test complete workflow: review -> hash -> hex -> bytes."""
        review = {
            "reviewerID": "A2VNYWOPJ13AFP",
            "asin": "0000013714",
            "overall": "5.0",
            "unixReviewTime": "1370736000",
            "reviewText": "This is a great product!"
        }

        # Hash the review
        hash_bytes = hash_review(review)
        assert isinstance(hash_bytes, bytes)
        assert len(hash_bytes) == 32

        # Convert to hex for storage/display
        hex_str = bytes_to_hex(hash_bytes)
        assert isinstance(hex_str, str)
        assert len(hex_str) == 64

        # Convert back to bytes
        recovered_bytes = hex_to_bytes(hex_str)
        assert recovered_bytes == hash_bytes

    def test_merkle_tree_parent_hash(self):
        """Test hashing pairs of hashes (simulating Merkle tree)."""
        # Create two leaf hashes
        review1 = {"reviewerID": "A123", "reviewText": "Good"}
        review2 = {"reviewerID": "A456", "reviewText": "Bad"}

        hash1 = hash_review(review1)
        hash2 = hash_review(review2)

        # Create parent hash
        parent_hash = hash_pair(hash1, hash2)

        assert isinstance(parent_hash, bytes)
        assert len(parent_hash) == 32
        assert parent_hash != hash1
        assert parent_hash != hash2

    def test_memory_efficiency(self):
        """Test that bytes are more memory efficient than hex."""
        hash_bytes = hash_data("test")
        hex_str = bytes_to_hex(hash_bytes)

        # bytes should be 32 bytes, hex should be 64 characters (+ string overhead)
        assert len(hash_bytes) == 32
        assert len(hex_str) == 64
        assert sys.getsizeof(hash_bytes) < sys.getsizeof(hex_str)
