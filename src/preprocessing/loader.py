"""
Data loading utilities for Amazon review datasets.

Provides:
- Streaming JSON loader for large files (1M+ records)
- Batch processing for memory efficiency
- Caching system for 10x faster subsequent loads
- Progress tracking
"""

import json
import pickle
from pathlib import Path
from typing import Iterator, List, Dict, Any, Optional
from tqdm import tqdm

from .cleaner import batch_normalize_reviews


def load_json_reviews(filepath: str,
                     limit: Optional[int] = None,
                     normalize: bool = True,
                     show_progress: bool = True) -> List[Dict[str, Any]]:
    """
    Load reviews from JSON file (line-delimited or array format).

    Automatically detects JSON format and loads efficiently.
    For large files, use batch_loader() instead for memory efficiency.

    Args:
        filepath: Path to JSON file
        limit: Maximum number of reviews to load (None = all)
        normalize: Whether to normalize reviews
        show_progress: Show progress bar

    Returns:
        List of review dictionaries

    Example:
        >>> reviews = load_json_reviews("data/reviews.json", limit=1000)
        >>> len(reviews)
        1000
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    reviews = []
    file_size = filepath.stat().st_size

    with open(filepath, 'r', encoding='utf-8') as f:
        # Try to detect format
        first_char = f.read(1)
        f.seek(0)

        if first_char == '[':
            # JSON array format
            if show_progress:
                print(f"Loading JSON array from {filepath.name}...")
            data = json.load(f)
            reviews = data[:limit] if limit else data

        else:
            # Line-delimited JSON format (one JSON object per line)
            if show_progress:
                # Estimate line count for progress bar
                total_lines = sum(1 for _ in f) if file_size < 100_000_000 else None
                f.seek(0)
                progress = tqdm(total=total_lines or limit, desc=f"Loading {filepath.name}")
            else:
                progress = None

            for i, line in enumerate(f):
                if limit and i >= limit:
                    break

                line = line.strip()
                if line:
                    try:
                        review = json.loads(line)
                        reviews.append(review)
                        if progress:
                            progress.update(1)
                    except json.JSONDecodeError:
                        # Skip malformed lines
                        continue

            if progress:
                progress.close()

    # Normalize if requested
    if normalize:
        if show_progress:
            print("Normalizing reviews...")
        reviews = batch_normalize_reviews(reviews)

    return reviews


def batch_loader(filepath: str,
                batch_size: int = 10000,
                limit: Optional[int] = None,
                normalize: bool = True) -> Iterator[List[Dict[str, Any]]]:
    """
    Load reviews in batches for memory-efficient processing.

    Generator that yields batches of reviews, ideal for processing
    large datasets that don't fit in memory.

    Args:
        filepath: Path to JSON file
        batch_size: Number of reviews per batch
        limit: Maximum total reviews to load
        normalize: Whether to normalize reviews

    Yields:
        Batches of review dictionaries

    Example:
        >>> for batch in batch_loader("data/reviews.json", batch_size=1000):
        ...     process_batch(batch)
        ...     print(f"Processed {len(batch)} reviews")
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    batch = []
    count = 0

    with open(filepath, 'r', encoding='utf-8') as f:
        # Detect format
        first_char = f.read(1)
        f.seek(0)

        if first_char == '[':
            # JSON array format
            data = json.load(f)
            for review in data:
                if limit and count >= limit:
                    break

                batch.append(review)
                count += 1

                if len(batch) >= batch_size:
                    if normalize:
                        batch = batch_normalize_reviews(batch)
                    yield batch
                    batch = []

        else:
            # Line-delimited JSON
            for line in f:
                if limit and count >= limit:
                    break

                line = line.strip()
                if line:
                    try:
                        review = json.loads(line)
                        batch.append(review)
                        count += 1

                        if len(batch) >= batch_size:
                            if normalize:
                                batch = batch_normalize_reviews(batch)
                            yield batch
                            batch = []

                    except json.JSONDecodeError:
                        continue

    # Yield remaining batch
    if batch:
        if normalize:
            batch = batch_normalize_reviews(batch)
        yield batch


def load_cached_reviews(cache_path: str) -> Optional[List[Dict[str, Any]]]:
    """
    Load reviews from preprocessed cache file.

    Cache files are created by save_to_cache() and provide 10x faster
    loading compared to parsing JSON.

    Args:
        cache_path: Path to cache file (.pkl)

    Returns:
        List of reviews if cache exists, None otherwise

    Example:
        >>> reviews = load_cached_reviews("data/cache/reviews.pkl")
        >>> if reviews:
        ...     print(f"Loaded {len(reviews)} from cache")
    """
    cache_path = Path(cache_path)

    if not cache_path.exists():
        return None

    try:
        with open(cache_path, 'rb') as f:
            return pickle.load(f)
    except Exception as e:
        print(f"Warning: Failed to load cache: {e}")
        return None


def save_to_cache(reviews: List[Dict[str, Any]],
                 cache_path: str,
                 create_dirs: bool = True) -> bool:
    """
    Save preprocessed reviews to cache file for fast reloading.

    Args:
        reviews: List of review dictionaries
        cache_path: Path for cache file (.pkl)
        create_dirs: Create parent directories if they don't exist

    Returns:
        True if successful, False otherwise

    Example:
        >>> reviews = load_json_reviews("data/reviews.json")
        >>> save_to_cache(reviews, "data/cache/reviews.pkl")
        True
    """
    cache_path = Path(cache_path)

    if create_dirs:
        cache_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(cache_path, 'wb') as f:
            pickle.dump(reviews, f, protocol=pickle.HIGHEST_PROTOCOL)
        return True
    except Exception as e:
        print(f"Warning: Failed to save cache: {e}")
        return False


def load_with_cache(json_path: str,
                   cache_dir: str = "data/cache",
                   limit: Optional[int] = None,
                   force_reload: bool = False,
                   show_progress: bool = True) -> List[Dict[str, Any]]:
    """
    Load reviews with automatic caching.

    On first load: parses JSON and saves to cache.
    On subsequent loads: loads from cache (10x faster).

    Args:
        json_path: Path to original JSON file
        cache_dir: Directory for cache files
        limit: Maximum reviews to load
        force_reload: Force reload from JSON even if cache exists
        show_progress: Show progress information

    Returns:
        List of review dictionaries

    Example:
        >>> # First call: slow (parses JSON)
        >>> reviews = load_with_cache("data/reviews.json")
        >>> # Second call: fast (loads from cache)
        >>> reviews = load_with_cache("data/reviews.json")
    """
    json_path = Path(json_path)
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Generate cache filename
    cache_name = f"{json_path.stem}_{limit or 'all'}.pkl"
    cache_path = cache_dir / cache_name

    # Try to load from cache
    if not force_reload:
        if show_progress:
            print(f"Checking for cache: {cache_name}")

        cached = load_cached_reviews(cache_path)
        if cached is not None:
            if show_progress:
                print(f"✓ Loaded {len(cached)} reviews from cache")
            return cached

    # Load from JSON
    if show_progress:
        print(f"Loading from JSON (this may take a while)...")

    reviews = load_json_reviews(json_path, limit=limit,
                               normalize=True,
                               show_progress=show_progress)

    # Save to cache for next time
    if show_progress:
        print(f"Saving to cache for faster future loads...")

    save_to_cache(reviews, cache_path)

    if show_progress:
        print(f"✓ Loaded and cached {len(reviews)} reviews")

    return reviews


def get_dataset_info(filepath: str) -> Dict[str, Any]:
    """
    Get information about a dataset without loading it all.

    Args:
        filepath: Path to JSON file

    Returns:
        Dictionary with dataset information

    Example:
        >>> info = get_dataset_info("data/reviews.json")
        >>> print(info["estimated_count"])
        1000000
    """
    filepath = Path(filepath)

    if not filepath.exists():
        return {"error": "File not found"}

    file_size = filepath.stat().st_size

    # Sample first few reviews
    sample_reviews = []
    with open(filepath, 'r', encoding='utf-8') as f:
        first_char = f.read(1)
        f.seek(0)

        if first_char == '[':
            data = json.load(f)
            sample_reviews = data[:10]
            count = len(data)
        else:
            # Line-delimited: count lines
            for i, line in enumerate(f):
                if i < 10:
                    try:
                        sample_reviews.append(json.loads(line.strip()))
                    except json.JSONDecodeError:
                        pass
                if i >= 100000:  # Don't count too many for very large files
                    break
            count = i + 1 if i < 100000 else None

    # Get field info from samples
    fields = set()
    for review in sample_reviews:
        fields.update(review.keys())

    return {
        "filepath": str(filepath),
        "file_size_mb": file_size / (1024 * 1024),
        "estimated_count": count,
        "sample_count": len(sample_reviews),
        "fields": sorted(list(fields))
    }
