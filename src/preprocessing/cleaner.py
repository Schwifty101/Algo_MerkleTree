"""
Data cleaning and normalization for Amazon review datasets.

Provides functions to:
- Normalize review dictionaries
- Generate canonical string representations
- Filter incomplete reviews
- Validate review data
"""

from typing import Dict, List, Optional, Any


def normalize_review(review_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract and normalize key fields from review dictionary.

    Ensures all required fields are present with appropriate defaults.
    Converts field types to strings for consistent hashing.

    Args:
        review_dict: Raw review dictionary from JSON

    Returns:
        Normalized review dictionary with standard fields

    Example:
        >>> review = {"reviewerID": "A123", "overall": 5.0, ...}
        >>> normalized = normalize_review(review)
        >>> normalized["overall"]
        '5.0'
    """
    return {
        'reviewerID': str(review_dict.get('reviewerID', '')),
        'asin': str(review_dict.get('asin', '')),
        'overall': str(review_dict.get('overall', '')),
        'unixReviewTime': str(review_dict.get('unixReviewTime', '')),
        'reviewText': str(review_dict.get('reviewText', '')),
        # Store original dict for reference if needed
        '_original': review_dict
    }


def generate_canonical_string(review_dict: Dict[str, Any]) -> str:
    """
    Generate deterministic canonical string representation of review.

    Format: {reviewerID}|{asin}|{overall}|{unixReviewTime}|{reviewText}
    Fixed field order ensures consistent hashing regardless of dict order.

    Args:
        review_dict: Review dictionary (normalized or raw)

    Returns:
        Canonical string representation

    Example:
        >>> review = {"reviewerID": "A123", "asin": "B456", ...}
        >>> generate_canonical_string(review)
        'A123|B456|5|1234567890|Great product!'
    """
    reviewer_id = str(review_dict.get('reviewerID', ''))
    asin = str(review_dict.get('asin', ''))
    overall = str(review_dict.get('overall', ''))
    timestamp = str(review_dict.get('unixReviewTime', ''))
    text = str(review_dict.get('reviewText', ''))

    return f"{reviewer_id}|{asin}|{overall}|{timestamp}|{text}"


def is_valid_review(review_dict: Dict[str, Any], require_all_fields: bool = False) -> bool:
    """
    Check if review has minimum required fields for hashing.

    Args:
        review_dict: Review dictionary to validate
        require_all_fields: If True, all 5 fields must be present and non-empty

    Returns:
        True if review is valid, False otherwise

    Example:
        >>> review = {"reviewerID": "A123", "asin": "B456"}
        >>> is_valid_review(review)
        True
        >>> is_valid_review(review, require_all_fields=True)
        False
    """
    required_fields = ['reviewerID', 'asin']
    all_fields = ['reviewerID', 'asin', 'overall', 'unixReviewTime', 'reviewText']

    if require_all_fields:
        # All fields must be present and non-empty
        return all(
            field in review_dict and str(review_dict[field]).strip()
            for field in all_fields
        )
    else:
        # At least reviewerID and asin must be present
        return all(
            field in review_dict and str(review_dict[field]).strip()
            for field in required_fields
        )


def filter_incomplete_reviews(reviews: List[Dict[str, Any]],
                              require_all_fields: bool = False) -> List[Dict[str, Any]]:
    """
    Filter out reviews with missing critical fields.

    Args:
        reviews: List of review dictionaries
        require_all_fields: If True, require all 5 fields to be present

    Returns:
        Filtered list of valid reviews

    Example:
        >>> reviews = [
        ...     {"reviewerID": "A123", "asin": "B456"},
        ...     {"reviewerID": ""},  # Invalid
        ...     {"asin": "B789"}     # Missing reviewerID
        ... ]
        >>> valid = filter_incomplete_reviews(reviews)
        >>> len(valid)
        1
    """
    return [r for r in reviews if is_valid_review(r, require_all_fields)]


def extract_review_fields(review_dict: Dict[str, Any]) -> Dict[str, str]:
    """
    Extract only the core fields used for Merkle tree hashing.

    Args:
        review_dict: Full review dictionary

    Returns:
        Dictionary with only core fields (reviewerID, asin, overall,
        unixReviewTime, reviewText)

    Example:
        >>> review = {
        ...     "reviewerID": "A123",
        ...     "helpful": [2, 3],  # Extra field
        ...     "asin": "B456"
        ... }
        >>> core = extract_review_fields(review)
        >>> "helpful" in core
        False
        >>> "reviewerID" in core
        True
    """
    return {
        'reviewerID': str(review_dict.get('reviewerID', '')),
        'asin': str(review_dict.get('asin', '')),
        'overall': str(review_dict.get('overall', '')),
        'unixReviewTime': str(review_dict.get('unixReviewTime', '')),
        'reviewText': str(review_dict.get('reviewText', ''))
    }


def sanitize_review_text(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize review text by removing problematic characters.

    Args:
        text: Review text to sanitize
        max_length: Optional maximum length (for very long reviews)

    Returns:
        Sanitized text

    Example:
        >>> sanitize_review_text("Great\\x00product!\\n")
        'Great product! '
    """
    # Remove null bytes
    text = text.replace('\x00', '')

    # Normalize whitespace
    text = ' '.join(text.split())

    # Truncate if needed
    if max_length and len(text) > max_length:
        text = text[:max_length]

    return text


def batch_normalize_reviews(reviews: List[Dict[str, Any]],
                            filter_invalid: bool = True,
                            sanitize_text: bool = True) -> List[Dict[str, Any]]:
    """
    Normalize a batch of reviews efficiently.

    Args:
        reviews: List of review dictionaries
        filter_invalid: Remove invalid reviews
        sanitize_text: Clean review text

    Returns:
        List of normalized reviews

    Example:
        >>> reviews = [{"reviewerID": "A123", "overall": 5}, ...]
        >>> normalized = batch_normalize_reviews(reviews)
        >>> all('reviewerID' in r for r in normalized)
        True
    """
    normalized = []

    for review in reviews:
        # Skip invalid if requested
        if filter_invalid and not is_valid_review(review):
            continue

        # Normalize
        norm_review = normalize_review(review)

        # Sanitize text if requested
        if sanitize_text:
            norm_review['reviewText'] = sanitize_review_text(
                norm_review['reviewText']
            )

        normalized.append(norm_review)

    return normalized


def get_review_stats(reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Get statistics about a collection of reviews.

    Args:
        reviews: List of review dictionaries

    Returns:
        Dictionary with statistics (count, field completeness, etc.)

    Example:
        >>> reviews = [{"reviewerID": "A123", "asin": "B456"}, ...]
        >>> stats = get_review_stats(reviews)
        >>> stats["total_count"]
        1000
    """
    if not reviews:
        return {
            "total_count": 0,
            "valid_count": 0,
            "field_completeness": {}
        }

    total = len(reviews)
    valid = len([r for r in reviews if is_valid_review(r)])

    # Count field completeness
    fields = ['reviewerID', 'asin', 'overall', 'unixReviewTime', 'reviewText']
    field_counts = {
        field: sum(1 for r in reviews if field in r and str(r[field]).strip())
        for field in fields
    }

    field_completeness = {
        field: (count / total * 100) if total > 0 else 0
        for field, count in field_counts.items()
    }

    return {
        "total_count": total,
        "valid_count": valid,
        "valid_percentage": (valid / total * 100) if total > 0 else 0,
        "field_completeness": field_completeness
    }
