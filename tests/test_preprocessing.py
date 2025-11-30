"""
Unit tests for preprocessing modules (cleaner and loader).

Tests cover:
- Review normalization
- Canonical string generation
- Review validation and filtering
- JSON loading (line-delimited format)
- Caching functionality
"""

import pytest
import sys
import json
import tempfile
import shutil
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from preprocessing.cleaner import (
    normalize_review,
    generate_canonical_string,
    is_valid_review,
    filter_incomplete_reviews,
    extract_review_fields,
    sanitize_review_text,
    batch_normalize_reviews,
    get_review_stats
)
from preprocessing.loader import (
    load_json_reviews,
    batch_loader,
    load_cached_reviews,
    save_to_cache,
    load_with_cache,
    get_dataset_info
)


# Test data
SAMPLE_REVIEW = {
    "reviewerID": "A2VNYWOPJ13AFP",
    "asin": "0000013714",
    "reviewerName": "J. McDonald",
    "helpful": [0, 0],
    "reviewText": "This is a great product!",
    "overall": 5.0,
    "summary": "Excellent!",
    "unixReviewTime": 1370736000,
    "reviewTime": "06 9, 2013"
}


class TestNormalizeReview:
    """Test normalize_review function."""

    def test_normalize_complete_review(self):
        """Test normalizing review with all fields."""
        result = normalize_review(SAMPLE_REVIEW)

        assert result['reviewerID'] == 'A2VNYWOPJ13AFP'
        assert result['asin'] == '0000013714'
        assert result['overall'] == '5.0'
        assert result['unixReviewTime'] == '1370736000'
        assert result['reviewText'] == 'This is a great product!'

    def test_normalize_missing_fields(self):
        """Test normalizing review with missing fields."""
        minimal_review = {"reviewerID": "A123"}
        result = normalize_review(minimal_review)

        assert result['reviewerID'] == 'A123'
        assert result['asin'] == ''
        assert result['overall'] == ''

    def test_normalize_preserves_original(self):
        """Test that original dict is preserved."""
        result = normalize_review(SAMPLE_REVIEW)
        assert '_original' in result
        assert result['_original'] == SAMPLE_REVIEW

    def test_normalize_converts_to_string(self):
        """Test that all fields are converted to strings."""
        review = {"reviewerID": 123, "overall": 5}
        result = normalize_review(review)

        assert isinstance(result['reviewerID'], str)
        assert isinstance(result['overall'], str)


class TestGenerateCanonicalString:
    """Test generate_canonical_string function."""

    def test_canonical_string_format(self):
        """Test canonical string has correct format."""
        result = generate_canonical_string(SAMPLE_REVIEW)
        expected = "A2VNYWOPJ13AFP|0000013714|5.0|1370736000|This is a great product!"
        assert result == expected

    def test_canonical_string_deterministic(self):
        """Test that same review produces same canonical string."""
        str1 = generate_canonical_string(SAMPLE_REVIEW)
        str2 = generate_canonical_string(SAMPLE_REVIEW)
        assert str1 == str2

    def test_canonical_string_field_order(self):
        """Test that dict field order doesn't matter."""
        review1 = {"reviewerID": "A123", "asin": "B456", "overall": "5"}
        review2 = {"overall": "5", "asin": "B456", "reviewerID": "A123"}

        str1 = generate_canonical_string(review1)
        str2 = generate_canonical_string(review2)
        assert str1 == str2

    def test_canonical_string_missing_fields(self):
        """Test handling of missing fields."""
        review = {"reviewerID": "A123"}
        result = generate_canonical_string(review)
        assert result == "A123||||"


class TestIsValidReview:
    """Test is_valid_review function."""

    def test_valid_complete_review(self):
        """Test that complete review is valid."""
        assert is_valid_review(SAMPLE_REVIEW) is True

    def test_valid_minimal_review(self):
        """Test that review with just reviewerID and asin is valid."""
        review = {"reviewerID": "A123", "asin": "B456"}
        assert is_valid_review(review) is True

    def test_invalid_missing_reviewer_id(self):
        """Test that review without reviewerID is invalid."""
        review = {"asin": "B456"}
        assert is_valid_review(review) is False

    def test_invalid_missing_asin(self):
        """Test that review without asin is invalid."""
        review = {"reviewerID": "A123"}
        assert is_valid_review(review) is False

    def test_invalid_empty_fields(self):
        """Test that empty required fields are invalid."""
        review = {"reviewerID": "", "asin": "B456"}
        assert is_valid_review(review) is False

    def test_require_all_fields(self):
        """Test require_all_fields parameter."""
        review = {"reviewerID": "A123", "asin": "B456"}
        assert is_valid_review(review, require_all_fields=False) is True
        assert is_valid_review(review, require_all_fields=True) is False


class TestFilterIncompleteReviews:
    """Test filter_incomplete_reviews function."""

    def test_filter_keeps_valid(self):
        """Test that valid reviews are kept."""
        reviews = [
            {"reviewerID": "A123", "asin": "B456"},
            {"reviewerID": "A789", "asin": "B012"}
        ]
        result = filter_incomplete_reviews(reviews)
        assert len(result) == 2

    def test_filter_removes_invalid(self):
        """Test that invalid reviews are removed."""
        reviews = [
            {"reviewerID": "A123", "asin": "B456"},  # Valid
            {"reviewerID": ""},  # Invalid
            {"asin": "B789"}  # Missing reviewerID
        ]
        result = filter_incomplete_reviews(reviews)
        assert len(result) == 1
        assert result[0]['reviewerID'] == 'A123'

    def test_filter_empty_list(self):
        """Test filtering empty list."""
        result = filter_incomplete_reviews([])
        assert result == []


class TestExtractReviewFields:
    """Test extract_review_fields function."""

    def test_extract_core_fields(self):
        """Test extracting core fields."""
        result = extract_review_fields(SAMPLE_REVIEW)

        assert 'reviewerID' in result
        assert 'asin' in result
        assert 'overall' in result
        assert 'unixReviewTime' in result
        assert 'reviewText' in result

    def test_extract_excludes_extra_fields(self):
        """Test that extra fields are excluded."""
        result = extract_review_fields(SAMPLE_REVIEW)

        assert 'reviewerName' not in result
        assert 'helpful' not in result
        assert 'summary' not in result


class TestSanitizeReviewText:
    """Test sanitize_review_text function."""

    def test_sanitize_removes_null_bytes(self):
        """Test that null bytes are removed."""
        text = "Great\x00product"
        result = sanitize_review_text(text)
        assert '\x00' not in result

    def test_sanitize_normalizes_whitespace(self):
        """Test that whitespace is normalized."""
        text = "Great  \\n  product"
        result = sanitize_review_text(text)
        assert '  ' not in result

    def test_sanitize_truncates_long_text(self):
        """Test that long text is truncated."""
        text = "a" * 1000
        result = sanitize_review_text(text, max_length=100)
        assert len(result) == 100


class TestBatchNormalizeReviews:
    """Test batch_normalize_reviews function."""

    def test_batch_normalize(self):
        """Test batch normalization."""
        reviews = [SAMPLE_REVIEW, SAMPLE_REVIEW.copy()]
        result = batch_normalize_reviews(reviews)

        assert len(result) == 2
        assert all('reviewerID' in r for r in result)

    def test_batch_normalize_filters_invalid(self):
        """Test that invalid reviews are filtered."""
        reviews = [
            {"reviewerID": "A123", "asin": "B456"},
            {"reviewerID": ""},  # Invalid
        ]
        result = batch_normalize_reviews(reviews, filter_invalid=True)
        assert len(result) == 1


class TestGetReviewStats:
    """Test get_review_stats function."""

    def test_stats_basic(self):
        """Test basic statistics."""
        reviews = [SAMPLE_REVIEW, SAMPLE_REVIEW.copy()]
        stats = get_review_stats(reviews)

        assert stats['total_count'] == 2
        assert stats['valid_count'] == 2

    def test_stats_empty_list(self):
        """Test statistics for empty list."""
        stats = get_review_stats([])
        assert stats['total_count'] == 0
        assert stats['valid_count'] == 0

    def test_stats_field_completeness(self):
        """Test field completeness statistics."""
        reviews = [
            {"reviewerID": "A123", "asin": "B456", "overall": "5"},
            {"reviewerID": "A789", "asin": "B012"}  # Missing overall
        ]
        stats = get_review_stats(reviews)

        assert stats['field_completeness']['reviewerID'] == 100.0
        assert stats['field_completeness']['overall'] == 50.0


@pytest.fixture
def sample_json_file(tmp_path):
    """Create a temporary JSON file with sample reviews."""
    filepath = tmp_path / "reviews.json"

    # Write line-delimited JSON
    with open(filepath, 'w') as f:
        for _ in range(10):
            f.write(json.dumps(SAMPLE_REVIEW) + '\n')

    return filepath


class TestLoadJsonReviews:
    """Test load_json_reviews function."""

    def test_load_line_delimited(self, sample_json_file):
        """Test loading line-delimited JSON."""
        reviews = load_json_reviews(str(sample_json_file), show_progress=False)
        assert len(reviews) == 10

    def test_load_with_limit(self, sample_json_file):
        """Test loading with limit."""
        reviews = load_json_reviews(str(sample_json_file), limit=5, show_progress=False)
        assert len(reviews) == 5

    def test_load_normalizes(self, sample_json_file):
        """Test that reviews are normalized."""
        reviews = load_json_reviews(str(sample_json_file), normalize=True, show_progress=False)
        assert all('reviewerID' in r for r in reviews)

    def test_load_nonexistent_file(self):
        """Test loading nonexistent file raises error."""
        with pytest.raises(FileNotFoundError):
            load_json_reviews("nonexistent.json")


class TestBatchLoader:
    """Test batch_loader function."""

    def test_batch_loader(self, sample_json_file):
        """Test batch loading."""
        batches = list(batch_loader(str(sample_json_file), batch_size=3, normalize=False))

        assert len(batches) == 4  # 10 reviews / 3 per batch = 4 batches
        assert len(batches[0]) == 3
        assert len(batches[-1]) == 1  # Last batch has remainder

    def test_batch_loader_with_limit(self, sample_json_file):
        """Test batch loading with limit."""
        batches = list(batch_loader(str(sample_json_file), batch_size=3, limit=5, normalize=False))

        total = sum(len(b) for b in batches)
        assert total == 5


class TestCaching:
    """Test caching functionality."""

    def test_save_and_load_cache(self, tmp_path):
        """Test saving and loading cache."""
        cache_path = tmp_path / "cache.pkl"
        reviews = [SAMPLE_REVIEW, SAMPLE_REVIEW.copy()]

        # Save
        success = save_to_cache(reviews, str(cache_path))
        assert success is True
        assert cache_path.exists()

        # Load
        loaded = load_cached_reviews(str(cache_path))
        assert loaded is not None
        assert len(loaded) == 2

    def test_load_nonexistent_cache(self):
        """Test loading nonexistent cache returns None."""
        result = load_cached_reviews("nonexistent.pkl")
        assert result is None


class TestLoadWithCache:
    """Test load_with_cache function."""

    def test_load_with_cache_first_time(self, sample_json_file, tmp_path):
        """Test first load creates cache."""
        reviews = load_with_cache(
            str(sample_json_file),
            cache_dir=str(tmp_path / "cache"),
            show_progress=False
        )

        assert len(reviews) == 10

        # Check cache was created
        cache_dir = tmp_path / "cache"
        assert cache_dir.exists()
        assert len(list(cache_dir.glob("*.pkl"))) > 0

    def test_load_with_cache_second_time(self, sample_json_file, tmp_path):
        """Test second load uses cache."""
        cache_dir = str(tmp_path / "cache")

        # First load
        reviews1 = load_with_cache(str(sample_json_file), cache_dir=cache_dir, show_progress=False)

        # Second load (should use cache)
        reviews2 = load_with_cache(str(sample_json_file), cache_dir=cache_dir, show_progress=False)

        assert len(reviews1) == len(reviews2)

    def test_force_reload(self, sample_json_file, tmp_path):
        """Test force reload bypasses cache."""
        cache_dir = str(tmp_path / "cache")

        # First load
        load_with_cache(str(sample_json_file), cache_dir=cache_dir, show_progress=False)

        # Force reload
        reviews = load_with_cache(
            str(sample_json_file),
            cache_dir=cache_dir,
            force_reload=True,
            show_progress=False
        )

        assert len(reviews) == 10


class TestGetDatasetInfo:
    """Test get_dataset_info function."""

    def test_get_dataset_info(self, sample_json_file):
        """Test getting dataset information."""
        info = get_dataset_info(str(sample_json_file))

        assert 'filepath' in info
        assert 'file_size_mb' in info
        assert 'estimated_count' in info
        assert 'fields' in info

        assert info['estimated_count'] == 10

    def test_get_info_nonexistent_file(self):
        """Test getting info for nonexistent file."""
        info = get_dataset_info("nonexistent.json")
        assert 'error' in info
