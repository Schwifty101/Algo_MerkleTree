"""
Merkle Tree implementation with hybrid storage approach.

HYBRID STORAGE DESIGN:
- During construction: Build complete binary tree in memory
- After construction: Store only root hash + array of leaf hashes (32 bytes each)
- For proofs: Rebuild tree path on demand from leaf hashes
- Memory: ~32MB for 1M records (vs 700MB for full tree storage)

Key optimizations:
- Raw bytes for all hash values (32 bytes vs 64-char hex)
- Direct bytes concatenation: left_bytes + right_bytes
- Duplicate last node for odd counts (exact byte copy)
"""

from typing import List, Optional, Dict, Any
import sys

from merkle.node import MerkleNode
from utils.hash_utils import hash_data, hash_pair, hash_review, bytes_to_hex, hex_to_bytes


class MerkleTree:
    """
    Merkle Tree with hybrid storage for memory efficiency.

    Stores only root hash + leaf hashes after construction.
    Intermediate nodes are discarded to save memory.

    Memory usage: ~32MB for 1M records (32 bytes per leaf hash)
    """

    def __init__(self, data_items: List[Any]):
        """
        Initialize and build Merkle tree from data items.

        Args:
            data_items: List of data items (can be strings or dicts)
                       - If dict with review fields: hashed using hash_review()
                       - If string: hashed using hash_data()

        Example:
            >>> reviews = [{"reviewerID": "A123", ...}, {...}]
            >>> tree = MerkleTree(reviews)
            >>> root = tree.get_root_hash()
        """
        if not data_items:
            raise ValueError("Cannot create Merkle tree from empty data")

        self._leaf_count = len(data_items)
        self._root_hash: Optional[bytes] = None
        self._leaf_hashes: List[bytes] = []

        # Build tree and extract what we need
        self._build_tree(data_items)

    def _build_tree(self, data_items: List[Any]) -> None:
        """
        Build complete Merkle tree and extract root + leaf hashes.

        Process:
        1. Create leaf nodes from data items
        2. Build tree bottom-up with parent nodes
        3. Extract root hash and leaf hashes
        4. Discard intermediate nodes (garbage collected)

        Args:
            data_items: List of data to build tree from
        """
        # Step 1: Create leaf nodes
        leaves = []
        for i, item in enumerate(data_items):
            # Hash the data
            if isinstance(item, dict):
                # Assume it's a review dict
                leaf_hash = hash_review(item)
            elif isinstance(item, str):
                leaf_hash = hash_data(item)
            else:
                # Convert to string and hash
                leaf_hash = hash_data(str(item))

            # Create leaf node
            leaf_node = MerkleNode(
                hash_value=leaf_hash,
                data=item if isinstance(item, str) else None,
                index=i
            )
            leaves.append(leaf_node)

        # Store leaf hashes (HYBRID STORAGE: keep leaves)
        self._leaf_hashes = [leaf.hash for leaf in leaves]

        # Step 2: Build tree bottom-up
        current_level = leaves

        while len(current_level) > 1:
            next_level = []

            # Process pairs
            for i in range(0, len(current_level), 2):
                left = current_level[i]

                # If odd number, duplicate last node
                if i + 1 >= len(current_level):
                    right = current_level[i]  # Duplicate (same object reference is fine)
                else:
                    right = current_level[i + 1]

                # Create parent node with combined hash
                parent_hash = hash_pair(left.hash, right.hash)
                parent = MerkleNode(
                    hash_value=parent_hash,
                    left=left,
                    right=right
                )
                next_level.append(parent)

            current_level = next_level

        # Step 3: Extract root hash (HYBRID STORAGE: keep root only)
        if current_level:
            self._root_hash = current_level[0].hash
        # After this, current_level and all intermediate nodes are garbage collected

    def get_root_hash(self) -> bytes:
        """
        Get the Merkle root hash as raw bytes.

        Returns:
            32-byte SHA-256 root hash

        Example:
            >>> tree = MerkleTree(["data1", "data2"])
            >>> root = tree.get_root_hash()
            >>> len(root)
            32
        """
        if self._root_hash is None:
            raise RuntimeError("Tree not built yet")
        return self._root_hash

    def get_root_hash_hex(self) -> str:
        """
        Get the Merkle root hash as hex string for display.

        Returns:
            64-character hex string

        Example:
            >>> tree = MerkleTree(["data1", "data2"])
            >>> root_hex = tree.get_root_hash_hex()
            >>> print(root_hex)
            'a1b2c3d4...'
        """
        return bytes_to_hex(self.get_root_hash())

    def get_leaf_count(self) -> int:
        """
        Get the number of leaf nodes in the tree.

        Returns:
            Number of original data items
        """
        return self._leaf_count

    def get_leaf_hash(self, index: int) -> bytes:
        """
        Get the hash of a specific leaf node.

        Args:
            index: Leaf index (0-based)

        Returns:
            32-byte SHA-256 hash of the leaf

        Raises:
            IndexError: If index is out of range

        Example:
            >>> tree = MerkleTree(["data1", "data2", "data3"])
            >>> leaf_hash = tree.get_leaf_hash(0)
            >>> len(leaf_hash)
            32
        """
        if index < 0 or index >= len(self._leaf_hashes):
            raise IndexError(f"Leaf index {index} out of range [0, {len(self._leaf_hashes)})")
        return self._leaf_hashes[index]

    def get_all_leaf_hashes(self) -> List[bytes]:
        """
        Get all leaf hashes.

        Returns:
            List of 32-byte SHA-256 hashes

        Example:
            >>> tree = MerkleTree(["a", "b", "c"])
            >>> leaves = tree.get_all_leaf_hashes()
            >>> len(leaves)
            3
        """
        return self._leaf_hashes.copy()

    def verify_data_in_tree(self, data: Any, index: int) -> bool:
        """
        Verify that data at a given index matches the stored leaf hash.

        Args:
            data: Data item to verify (string or dict)
            index: Index where data should be located

        Returns:
            True if data hash matches leaf hash at index

        Example:
            >>> tree = MerkleTree(["data1", "data2"])
            >>> tree.verify_data_in_tree("data1", 0)
            True
            >>> tree.verify_data_in_tree("wrong", 0)
            False
        """
        if index < 0 or index >= len(self._leaf_hashes):
            return False

        # Hash the data
        if isinstance(data, dict):
            data_hash = hash_review(data)
        elif isinstance(data, str):
            data_hash = hash_data(data)
        else:
            data_hash = hash_data(str(data))

        # Compare with stored leaf hash
        return data_hash == self._leaf_hashes[index]

    def get_memory_usage(self) -> Dict[str, Any]:
        """
        Get memory usage statistics for the tree.

        Returns:
            Dictionary with memory usage information

        Example:
            >>> tree = MerkleTree(["data"] * 1000)
            >>> stats = tree.get_memory_usage()
            >>> print(stats['total_mb'])
            0.032  # ~32KB for 1000 leaves
        """
        # Calculate sizes
        root_size = sys.getsizeof(self._root_hash) if self._root_hash else 0
        leaves_size = sum(sys.getsizeof(h) for h in self._leaf_hashes)
        list_overhead = sys.getsizeof(self._leaf_hashes)

        total_bytes = root_size + leaves_size + list_overhead

        return {
            'leaf_count': self._leaf_count,
            'root_hash_bytes': root_size,
            'leaf_hashes_bytes': leaves_size,
            'list_overhead_bytes': list_overhead,
            'total_bytes': total_bytes,
            'total_kb': total_bytes / 1024,
            'total_mb': total_bytes / (1024 * 1024),
            'bytes_per_leaf': total_bytes / self._leaf_count if self._leaf_count > 0 else 0
        }

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize tree to dictionary for storage.

        Returns:
            Dictionary with root hash and leaf hashes in hex format

        Example:
            >>> tree = MerkleTree(["a", "b"])
            >>> tree_dict = tree.to_dict()
            >>> 'root_hash' in tree_dict
            True
        """
        return {
            'root_hash': bytes_to_hex(self._root_hash),
            'leaf_hashes': [bytes_to_hex(h) for h in self._leaf_hashes],
            'leaf_count': self._leaf_count
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MerkleTree':
        """
        Deserialize tree from dictionary.

        Args:
            data: Dictionary with root_hash and leaf_hashes (hex format)

        Returns:
            MerkleTree instance

        Example:
            >>> tree = MerkleTree(["a", "b"])
            >>> tree_dict = tree.to_dict()
            >>> restored = MerkleTree.from_dict(tree_dict)
            >>> restored.get_root_hash() == tree.get_root_hash()
            True
        """
        # Create empty tree (bypass __init__)
        tree = cls.__new__(cls)

        # Restore from dict
        tree._root_hash = hex_to_bytes(data['root_hash'])
        tree._leaf_hashes = [hex_to_bytes(h) for h in data['leaf_hashes']]
        tree._leaf_count = data['leaf_count']

        return tree

    def __repr__(self) -> str:
        """String representation for debugging."""
        root_preview = self.get_root_hash_hex()[:16] if self._root_hash else "None"
        return f"MerkleTree(leaves={self._leaf_count}, root={root_preview}...)"
