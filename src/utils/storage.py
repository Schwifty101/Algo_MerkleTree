"""
Storage utilities for persisting Merkle Tree data.

Provides simple JSON-based storage for root hashes, metadata, and cached data.
Follows KISS principle - no external database dependencies.
"""

import json
import os
from pathlib import Path
from typing import Any, Optional


class HashStorage:
    """
    Simple file-based storage for hash data and metadata.

    Stores data as JSON files in a specified directory.
    Used for:
    - Root hash persistence with metadata
    - Verification history
    - Cached preprocessing data
    """

    def __init__(self, storage_dir: str = "data/.merkle_hashes"):
        """
        Initialize storage with specified directory.

        Args:
            storage_dir: Directory path for storing JSON files
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save(self, key: str, data: dict) -> None:
        """
        Save data to JSON file.

        Args:
            key: Identifier for the data (becomes filename)
            data: Dictionary to save

        Example:
            >>> storage = HashStorage()
            >>> storage.save("dataset_1", {"root_hash": "abc123", "count": 1000})
        """
        filepath = self.storage_dir / f"{key}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load(self, key: str) -> Optional[dict]:
        """
        Load data from JSON file.

        Args:
            key: Identifier for the data

        Returns:
            Dictionary if file exists, None otherwise

        Example:
            >>> storage = HashStorage()
            >>> data = storage.load("dataset_1")
            >>> print(data["root_hash"])
        """
        filepath = self.storage_dir / f"{key}.json"
        if not filepath.exists():
            return None

        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def exists(self, key: str) -> bool:
        """
        Check if data exists for given key.

        Args:
            key: Identifier to check

        Returns:
            True if file exists, False otherwise
        """
        filepath = self.storage_dir / f"{key}.json"
        return filepath.exists()

    def delete(self, key: str) -> bool:
        """
        Delete data file.

        Args:
            key: Identifier for data to delete

        Returns:
            True if file was deleted, False if it didn't exist
        """
        filepath = self.storage_dir / f"{key}.json"
        if filepath.exists():
            filepath.unlink()
            return True
        return False

    def list_keys(self) -> list[str]:
        """
        List all stored keys.

        Returns:
            List of key names (without .json extension)

        Example:
            >>> storage = HashStorage()
            >>> storage.list_keys()
            ['dataset_1', 'dataset_2', 'electronics_reviews']
        """
        if not self.storage_dir.exists():
            return []

        return [
            f.stem for f in self.storage_dir.glob("*.json")
        ]
