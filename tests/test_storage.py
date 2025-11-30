"""
Unit tests for storage module.

Tests cover:
- JSON file storage and retrieval
- Key existence checking
- File deletion
- Edge cases
"""

import pytest
import sys
import tempfile
import shutil
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils.storage import HashStorage


@pytest.fixture
def temp_storage():
    """Create temporary storage directory for tests."""
    temp_dir = tempfile.mkdtemp()
    storage = HashStorage(storage_dir=temp_dir)
    yield storage
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestHashStorageInit:
    """Test HashStorage initialization."""

    def test_init_creates_directory(self):
        """Test that initialization creates storage directory."""
        temp_dir = tempfile.mkdtemp()
        storage_path = Path(temp_dir) / "test_storage"

        storage = HashStorage(storage_dir=str(storage_path))

        assert storage_path.exists()
        assert storage_path.is_dir()

        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_init_with_existing_directory(self):
        """Test initialization with existing directory."""
        temp_dir = tempfile.mkdtemp()

        storage1 = HashStorage(storage_dir=temp_dir)
        storage2 = HashStorage(storage_dir=temp_dir)

        assert storage1.storage_dir == storage2.storage_dir

        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)


class TestHashStorageSave:
    """Test save functionality."""

    def test_save_creates_file(self, temp_storage):
        """Test that save creates a JSON file."""
        data = {"test": "value"}
        temp_storage.save("test_key", data)

        filepath = temp_storage.storage_dir / "test_key.json"
        assert filepath.exists()

    def test_save_correct_content(self, temp_storage):
        """Test that saved content is correct."""
        data = {"root_hash": "abc123", "count": 1000}
        temp_storage.save("dataset_1", data)

        loaded = temp_storage.load("dataset_1")
        assert loaded == data

    def test_save_overwrites_existing(self, temp_storage):
        """Test that save overwrites existing file."""
        temp_storage.save("key", {"value": 1})
        temp_storage.save("key", {"value": 2})

        loaded = temp_storage.load("key")
        assert loaded["value"] == 2

    def test_save_with_special_characters(self, temp_storage):
        """Test saving data with special characters."""
        data = {"text": "Hello 世界 🌍", "special": "!@#$%"}
        temp_storage.save("unicode_test", data)

        loaded = temp_storage.load("unicode_test")
        assert loaded == data


class TestHashStorageLoad:
    """Test load functionality."""

    def test_load_existing_file(self, temp_storage):
        """Test loading existing file."""
        data = {"test": "value"}
        temp_storage.save("key", data)

        loaded = temp_storage.load("key")
        assert loaded == data

    def test_load_nonexistent_file(self, temp_storage):
        """Test loading nonexistent file returns None."""
        result = temp_storage.load("nonexistent")
        assert result is None

    def test_load_complex_data(self, temp_storage):
        """Test loading complex nested data."""
        data = {
            "root_hash": "abc123",
            "metadata": {
                "timestamp": "2024-01-01",
                "record_count": 1000,
                "categories": ["Books", "Electronics"]
            }
        }
        temp_storage.save("complex", data)

        loaded = temp_storage.load("complex")
        assert loaded == data
        assert loaded["metadata"]["categories"] == ["Books", "Electronics"]


class TestHashStorageExists:
    """Test exists functionality."""

    def test_exists_true(self, temp_storage):
        """Test exists returns True for existing file."""
        temp_storage.save("key", {"test": "value"})
        assert temp_storage.exists("key") is True

    def test_exists_false(self, temp_storage):
        """Test exists returns False for nonexistent file."""
        assert temp_storage.exists("nonexistent") is False

    def test_exists_after_delete(self, temp_storage):
        """Test exists returns False after deletion."""
        temp_storage.save("key", {"test": "value"})
        temp_storage.delete("key")
        assert temp_storage.exists("key") is False


class TestHashStorageDelete:
    """Test delete functionality."""

    def test_delete_existing_file(self, temp_storage):
        """Test deleting existing file."""
        temp_storage.save("key", {"test": "value"})

        result = temp_storage.delete("key")
        assert result is True
        assert not temp_storage.exists("key")

    def test_delete_nonexistent_file(self, temp_storage):
        """Test deleting nonexistent file."""
        result = temp_storage.delete("nonexistent")
        assert result is False

    def test_delete_multiple_times(self, temp_storage):
        """Test deleting same key multiple times."""
        temp_storage.save("key", {"test": "value"})

        assert temp_storage.delete("key") is True
        assert temp_storage.delete("key") is False


class TestHashStorageListKeys:
    """Test list_keys functionality."""

    def test_list_keys_empty(self, temp_storage):
        """Test listing keys in empty storage."""
        keys = temp_storage.list_keys()
        assert keys == []

    def test_list_keys_single(self, temp_storage):
        """Test listing single key."""
        temp_storage.save("key1", {"test": "value"})

        keys = temp_storage.list_keys()
        assert len(keys) == 1
        assert "key1" in keys

    def test_list_keys_multiple(self, temp_storage):
        """Test listing multiple keys."""
        temp_storage.save("key1", {"test": "value1"})
        temp_storage.save("key2", {"test": "value2"})
        temp_storage.save("key3", {"test": "value3"})

        keys = temp_storage.list_keys()
        assert len(keys) == 3
        assert set(keys) == {"key1", "key2", "key3"}

    def test_list_keys_after_delete(self, temp_storage):
        """Test listing keys after deletion."""
        temp_storage.save("key1", {"test": "value1"})
        temp_storage.save("key2", {"test": "value2"})

        temp_storage.delete("key1")

        keys = temp_storage.list_keys()
        assert len(keys) == 1
        assert "key2" in keys
        assert "key1" not in keys


class TestHashStorageIntegration:
    """Integration tests for storage."""

    def test_workflow_save_load_delete(self, temp_storage):
        """Test complete workflow."""
        # Save data
        data = {
            "root_hash": "a1b2c3d4",
            "timestamp": "2024-01-01T00:00:00",
            "record_count": 1000000
        }
        temp_storage.save("dataset_electronics", data)

        # Verify it exists
        assert temp_storage.exists("dataset_electronics")

        # Load and verify
        loaded = temp_storage.load("dataset_electronics")
        assert loaded == data

        # Delete
        temp_storage.delete("dataset_electronics")

        # Verify deletion
        assert not temp_storage.exists("dataset_electronics")
        assert temp_storage.load("dataset_electronics") is None

    def test_multiple_datasets(self, temp_storage):
        """Test storing multiple datasets."""
        datasets = {
            "books": {"root_hash": "hash1", "count": 1000},
            "electronics": {"root_hash": "hash2", "count": 2000},
            "clothing": {"root_hash": "hash3", "count": 1500}
        }

        # Save all
        for key, data in datasets.items():
            temp_storage.save(key, data)

        # Verify all exist
        keys = temp_storage.list_keys()
        assert len(keys) == 3

        # Load and verify each
        for key, expected_data in datasets.items():
            loaded = temp_storage.load(key)
            assert loaded == expected_data

    def test_concurrent_access_simulation(self, temp_storage):
        """Test simulated concurrent access (same key overwrite)."""
        temp_storage.save("shared", {"version": 1})
        temp_storage.save("shared", {"version": 2})
        temp_storage.save("shared", {"version": 3})

        loaded = temp_storage.load("shared")
        assert loaded["version"] == 3
