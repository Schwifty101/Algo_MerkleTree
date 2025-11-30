"""
Merkle Proof implementation for existence verification.

A Merkle proof allows verification that a specific data item exists in the tree
without needing the entire tree structure. The proof consists of sibling hashes
along the path from leaf to root.

Key design decisions:
- Store proof path as list of (sibling_hash, is_left) tuples using raw bytes
- Raw bytes for 32-byte hashes (not 64-char hex strings)
- Convert to hex only for serialization/display
- O(log n) verification time
"""

from typing import List, Tuple, Dict, Any, Optional
from utils.hash_utils import hash_data, hash_pair, hash_review, bytes_to_hex, hex_to_bytes


class MerkleProof:
    """
    Merkle proof for verifying data existence in a Merkle tree.

    A proof consists of:
    - The leaf data being proven
    - The leaf index in the tree
    - A path of sibling hashes from leaf to root

    Each step in the path is a tuple: (sibling_hash, is_left)
    - sibling_hash: 32-byte hash of the sibling node
    - is_left: True if sibling is on the left, False if on the right

    Memory: ~32 bytes × log₂(n) for the proof path
    """

    def __init__(self,
                 leaf_data: Any,
                 leaf_index: int,
                 proof_path: List[Tuple[bytes, bool]],
                 root_hash: bytes):
        """
        Initialize a Merkle proof.

        Args:
            leaf_data: The data item being proven (string or dict)
            leaf_index: Position of the leaf in the tree (0-based)
            proof_path: List of (sibling_hash, is_left) tuples from leaf to root
                       Each sibling_hash is 32 bytes (raw bytes, not hex)
            root_hash: The tree's root hash (32 bytes) for verification

        Example:
            >>> proof_path = [(sibling1_bytes, True), (sibling2_bytes, False)]
            >>> proof = MerkleProof(data="review", leaf_index=5,
            ...                     proof_path=proof_path, root_hash=root_bytes)
        """
        if not isinstance(root_hash, bytes) or len(root_hash) != 32:
            raise ValueError("root_hash must be 32 bytes")

        # Validate proof path
        for sibling_hash, is_left in proof_path:
            if not isinstance(sibling_hash, bytes) or len(sibling_hash) != 32:
                raise ValueError("Each sibling_hash must be 32 bytes")
            if not isinstance(is_left, bool):
                raise ValueError("is_left must be a boolean")

        self.leaf_data = leaf_data
        self.leaf_index = leaf_index
        self.proof_path = proof_path  # List of (bytes, bool)
        self.root_hash = root_hash

    def verify(self) -> bool:
        """
        Verify that the proof is valid.

        Process:
        1. Hash the leaf data
        2. For each step in the proof path:
           - Combine current hash with sibling hash
           - If sibling is left: hash(sibling + current)
           - If sibling is right: hash(current + sibling)
        3. Compare final hash with root hash

        Returns:
            True if proof is valid (computed root matches stored root)
            False otherwise

        Example:
            >>> proof = MerkleProof(...)
            >>> proof.verify()
            True
        """
        # Step 1: Hash the leaf data
        if isinstance(self.leaf_data, dict):
            current_hash = hash_review(self.leaf_data)
        elif isinstance(self.leaf_data, str):
            current_hash = hash_data(self.leaf_data)
        else:
            current_hash = hash_data(str(self.leaf_data))

        # Step 2: Walk up the tree combining with siblings
        for sibling_hash, is_left in self.proof_path:
            if is_left:
                # Sibling is on the left, we are on the right
                current_hash = hash_pair(sibling_hash, current_hash)
            else:
                # Sibling is on the right, we are on the left
                current_hash = hash_pair(current_hash, sibling_hash)

        # Step 3: Compare with root hash
        return current_hash == self.root_hash

    @staticmethod
    def verify_proof(leaf_data: Any,
                    proof_path: List[Tuple[bytes, bool]],
                    root_hash: bytes) -> bool:
        """
        Static method to verify a proof without creating a MerkleProof object.

        Args:
            leaf_data: The data being verified
            proof_path: List of (sibling_hash, is_left) tuples
            root_hash: Expected root hash (32 bytes)

        Returns:
            True if proof is valid, False otherwise

        Example:
            >>> is_valid = MerkleProof.verify_proof(data, path, root)
        """
        # Hash the leaf
        if isinstance(leaf_data, dict):
            current_hash = hash_review(leaf_data)
        elif isinstance(leaf_data, str):
            current_hash = hash_data(leaf_data)
        else:
            current_hash = hash_data(str(leaf_data))

        # Walk up the tree
        for sibling_hash, is_left in proof_path:
            if is_left:
                current_hash = hash_pair(sibling_hash, current_hash)
            else:
                current_hash = hash_pair(current_hash, sibling_hash)

        # Compare
        return current_hash == root_hash

    def get_proof_length(self) -> int:
        """
        Get the length of the proof path.

        Returns:
            Number of hashes in the proof path (roughly log₂(tree_size))
        """
        return len(self.proof_path)

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize proof to dictionary for storage or transmission.

        Converts raw bytes to hex strings for JSON compatibility.

        Returns:
            Dictionary with leaf_data, leaf_index, proof_path (hex), and root_hash (hex)

        Example:
            >>> proof = MerkleProof(...)
            >>> proof_dict = proof.to_dict()
            >>> import json
            >>> json.dumps(proof_dict)  # Can be serialized to JSON
        """
        return {
            'leaf_data': self.leaf_data,
            'leaf_index': self.leaf_index,
            'proof_path': [
                {
                    'sibling_hash': bytes_to_hex(sibling_hash),
                    'is_left': is_left
                }
                for sibling_hash, is_left in self.proof_path
            ],
            'root_hash': bytes_to_hex(self.root_hash)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MerkleProof':
        """
        Deserialize proof from dictionary.

        Converts hex strings back to raw bytes.

        Args:
            data: Dictionary with proof data (hex format)

        Returns:
            MerkleProof instance

        Example:
            >>> proof_dict = proof.to_dict()
            >>> restored = MerkleProof.from_dict(proof_dict)
            >>> restored.verify()
            True
        """
        # Convert hex proof path back to bytes
        proof_path = [
            (hex_to_bytes(step['sibling_hash']), step['is_left'])
            for step in data['proof_path']
        ]

        return cls(
            leaf_data=data['leaf_data'],
            leaf_index=data['leaf_index'],
            proof_path=proof_path,
            root_hash=hex_to_bytes(data['root_hash'])
        )

    def __repr__(self) -> str:
        """String representation for debugging."""
        root_preview = bytes_to_hex(self.root_hash)[:16]
        return (f"MerkleProof(index={self.leaf_index}, "
                f"path_length={len(self.proof_path)}, "
                f"root={root_preview}...)")

    def __eq__(self, other) -> bool:
        """Check equality based on all components."""
        if not isinstance(other, MerkleProof):
            return False
        return (self.leaf_data == other.leaf_data and
                self.leaf_index == other.leaf_index and
                self.proof_path == other.proof_path and
                self.root_hash == other.root_hash)
