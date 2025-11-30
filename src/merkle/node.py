"""
Merkle Tree Node implementation.

Used temporarily during tree construction, then discarded after extracting
root hash and leaf hashes for hybrid storage approach.

Key design decisions:
- Uses __slots__ for memory efficiency
- Stores hash as raw bytes (32 bytes), not hex string
- Minimal class design following KISS principle
"""

from typing import Optional


class MerkleNode:
    """
    A node in the Merkle tree.

    This class is used during tree construction but NOT stored long-term.
    After building the tree, we only keep root hash + leaf hashes.

    Attributes:
        hash: SHA-256 digest as raw bytes (32 bytes, NOT hex string)
        left: Left child node (None for leaf nodes)
        right: Right child node (None for leaf nodes)
        data: Original data for leaf nodes (Optional)
        index: Position in leaf array (for leaf nodes only)
    """

    __slots__ = ['hash', 'left', 'right', 'data', 'index']

    def __init__(self,
                 hash_value: bytes,
                 left: Optional['MerkleNode'] = None,
                 right: Optional['MerkleNode'] = None,
                 data: Optional[str] = None,
                 index: Optional[int] = None):
        """
        Initialize a Merkle tree node.

        Args:
            hash_value: SHA-256 hash as raw bytes (32 bytes)
            left: Left child node
            right: Right child node
            data: Original data (for leaf nodes)
            index: Position in leaf array (for leaf nodes)

        Example:
            >>> # Leaf node
            >>> leaf = MerkleNode(hash_data("review1"), data="review1", index=0)
            >>> leaf.is_leaf
            True

            >>> # Internal node
            >>> parent = MerkleNode(hash_pair(left.hash, right.hash), left, right)
            >>> parent.is_leaf
            False
        """
        if not isinstance(hash_value, bytes):
            raise TypeError(f"hash_value must be bytes, not {type(hash_value)}")
        if len(hash_value) != 32:
            raise ValueError(f"hash_value must be 32 bytes (SHA-256), got {len(hash_value)}")

        self.hash = hash_value
        self.left = left
        self.right = right
        self.data = data
        self.index = index

    @property
    def is_leaf(self) -> bool:
        """
        Check if this is a leaf node.

        Returns:
            True if node has no children, False otherwise
        """
        return self.left is None and self.right is None

    def __repr__(self) -> str:
        """
        String representation for debugging.

        Shows hash in hex format (first 8 characters) and node type.
        """
        hash_preview = self.hash.hex()[:8]
        if self.is_leaf:
            return f"MerkleNode(leaf, hash={hash_preview}..., index={self.index})"
        else:
            return f"MerkleNode(internal, hash={hash_preview}...)"

    def __eq__(self, other) -> bool:
        """
        Check equality based on hash value.

        Two nodes are equal if they have the same hash.
        """
        if not isinstance(other, MerkleNode):
            return False
        return self.hash == other.hash

    def get_hash_hex(self) -> str:
        """
        Get hash as hex string for display purposes.

        Returns:
            64-character hex string

        Example:
            >>> node = MerkleNode(hash_data("test"))
            >>> node.get_hash_hex()
            '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08'
        """
        return self.hash.hex()
