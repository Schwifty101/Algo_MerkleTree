"""
Hash utilities for Merkle Tree implementation.

This module provides SHA-256 hashing functions using raw bytes internally
for optimal performance and memory efficiency. Hex encoding is only used
for display and JSON serialization.

Design principles:
- DRY: Single source of truth for all hashing operations
- Performance: Raw bytes (32 bytes) vs hex strings (64 characters)
- Simplicity: Direct bytes concatenation before hashing
"""

import hashlib


def hash_data(data: str) -> bytes:
    """
    Hash a string using SHA-256 and return raw bytes.

    Args:
        data: String to hash

    Returns:
        32-byte SHA-256 digest as bytes

    Example:
        >>> hash_data("hello")
        b'...' # 32 bytes
    """
    return hashlib.sha256(data.encode('utf-8')).digest()


def hash_pair(left: bytes, right: bytes) -> bytes:
    """
    Hash the concatenation of two hash values.

    Uses direct bytes concatenation (left_bytes + right_bytes) for optimal
    performance, avoiding hex encoding overhead.

    Args:
        left: Left hash value (32 bytes)
        right: Right hash value (32 bytes)

    Returns:
        32-byte SHA-256 digest of concatenated hashes

    Example:
        >>> left = hash_data("a")
        >>> right = hash_data("b")
        >>> hash_pair(left, right)
        b'...' # 32 bytes
    """
    return hashlib.sha256(left + right).digest()


def hash_review(review_dict: dict) -> bytes:
    """
    Hash a review using canonical string representation.

    Canonical format: {reviewerID}|{asin}|{overall}|{unixReviewTime}|{reviewText}
    Fixed field order ensures deterministic hashing.

    Args:
        review_dict: Dictionary containing review fields

    Returns:
        32-byte SHA-256 digest of canonical review string

    Example:
        >>> review = {"reviewerID": "A123", "asin": "B456", ...}
        >>> hash_review(review)
        b'...' # 32 bytes
    """
    canonical = generate_canonical_string(review_dict)
    return hash_data(canonical)


def generate_canonical_string(review_dict: dict) -> str:
    """
    Generate deterministic canonical string representation of a review.

    Format: {reviewerID}|{asin}|{overall}|{unixReviewTime}|{reviewText}
    Missing fields are replaced with empty strings.

    Args:
        review_dict: Dictionary containing review fields

    Returns:
        Canonical string representation
    """
    reviewer_id = str(review_dict.get('reviewerID', ''))
    asin = str(review_dict.get('asin', ''))
    overall = str(review_dict.get('overall', ''))
    timestamp = str(review_dict.get('unixReviewTime', ''))
    text = str(review_dict.get('reviewText', ''))

    return f"{reviewer_id}|{asin}|{overall}|{timestamp}|{text}"


def bytes_to_hex(hash_bytes: bytes) -> str:
    """
    Convert hash bytes to hex string for display/serialization.

    Only use this for:
    - CLI output to user
    - JSON serialization
    - Logging/debugging

    Args:
        hash_bytes: 32-byte hash value

    Returns:
        64-character hex string

    Example:
        >>> hash_bytes = hash_data("hello")
        >>> bytes_to_hex(hash_bytes)
        '2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824'
    """
    return hash_bytes.hex()


def hex_to_bytes(hex_str: str) -> bytes:
    """
    Convert hex string back to bytes when loading from JSON.

    Args:
        hex_str: 64-character hex string

    Returns:
        32-byte hash value

    Example:
        >>> hex_str = '2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824'
        >>> hex_to_bytes(hex_str)
        b'...' # 32 bytes
    """
    return bytes.fromhex(hex_str)
