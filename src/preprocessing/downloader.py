"""
Dataset downloader for Amazon review datasets.

Downloads datasets from: https://nijianmo.github.io/amazon/index.html

Provides:
- Category listing
- Progress tracking during download
- Automatic decompression
- Error handling and retries
"""

import requests
from pathlib import Path
from typing import List, Dict, Optional
from tqdm import tqdm
import gzip
import shutil


# Amazon Review Dataset categories and their URLs
DATASET_CATEGORIES = {
    # Main categories with 5-core versions (reviews with at least 5 reviews per user/item)
    "All_Beauty": {
        "5-core": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFilesSmall/All_Beauty_5.json.gz",
        "full": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFiles/All_Beauty.json.gz"
    },
    "Amazon_Fashion": {
        "5-core": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFilesSmall/Amazon_Fashion_5.json.gz",
        "full": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFiles/AMAZON_FASHION.json.gz"
    },
    "Appliances": {
        "5-core": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFilesSmall/Appliances_5.json.gz",
        "full": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFiles/Appliances.json.gz"
    },
    "Arts_Crafts_and_Sewing": {
        "5-core": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFilesSmall/Arts_Crafts_and_Sewing_5.json.gz",
        "full": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFiles/Arts_Crafts_and_Sewing.json.gz"
    },
    "Automotive": {
        "5-core": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFilesSmall/Automotive_5.json.gz",
        "full": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFiles/Automotive.json.gz"
    },
    "Books": {
        "5-core": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFilesSmall/Books_5.json.gz",
        "full": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFiles/Books.json.gz"
    },
    "CDs_and_Vinyl": {
        "5-core": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFilesSmall/CDs_and_Vinyl_5.json.gz",
        "full": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFiles/CDs_and_Vinyl.json.gz"
    },
    "Cell_Phones_and_Accessories": {
        "5-core": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFilesSmall/Cell_Phones_and_Accessories_5.json.gz",
        "full": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFiles/Cell_Phones_and_Accessories.json.gz"
    },
    "Clothing_Shoes_and_Jewelry": {
        "5-core": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFilesSmall/Clothing_Shoes_and_Jewelry_5.json.gz",
        "full": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFiles/Clothing_Shoes_and_Jewelry.json.gz"
    },
    "Digital_Music": {
        "5-core": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFilesSmall/Digital_Music_5.json.gz",
        "full": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFiles/Digital_Music.json.gz"
    },
    "Electronics": {
        "5-core": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFilesSmall/Electronics_5.json.gz",
        "full": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFiles/Electronics.json.gz"
    },
    "Gift_Cards": {
        "5-core": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFilesSmall/Gift_Cards_5.json.gz",
        "full": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFiles/Gift_Cards.json.gz"
    },
    "Grocery_and_Gourmet_Food": {
        "5-core": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFilesSmall/Grocery_and_Gourmet_Food_5.json.gz",
        "full": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFiles/Grocery_and_Gourmet_Food.json.gz"
    },
    "Home_and_Kitchen": {
        "5-core": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFilesSmall/Home_and_Kitchen_5.json.gz",
        "full": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFiles/Home_and_Kitchen.json.gz"
    },
    "Industrial_and_Scientific": {
        "5-core": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFilesSmall/Industrial_and_Scientific_5.json.gz",
        "full": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFiles/Industrial_and_Scientific.json.gz"
    },
    "Kindle_Store": {
        "5-core": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFilesSmall/Kindle_Store_5.json.gz",
        "full": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFiles/Kindle_Store.json.gz"
    },
    "Luxury_Beauty": {
        "5-core": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFilesSmall/Luxury_Beauty_5.json.gz",
        "full": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFiles/Luxury_Beauty.json.gz"
    },
    "Magazine_Subscriptions": {
        "5-core": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFilesSmall/Magazine_Subscriptions_5.json.gz",
        "full": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFiles/Magazine_Subscriptions.json.gz"
    },
    "Movies_and_TV": {
        "5-core": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFilesSmall/Movies_and_TV_5.json.gz",
        "full": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFiles/Movies_and_TV.json.gz"
    },
    "Musical_Instruments": {
        "5-core": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFilesSmall/Musical_Instruments_5.json.gz",
        "full": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFiles/Musical_Instruments.json.gz"
    },
    "Office_Products": {
        "5-core": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFilesSmall/Office_Products_5.json.gz",
        "full": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFiles/Office_Products.json.gz"
    },
    "Patio_Lawn_and_Garden": {
        "5-core": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFilesSmall/Patio_Lawn_and_Garden_5.json.gz",
        "full": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFiles/Patio_Lawn_and_Garden.json.gz"
    },
    "Pet_Supplies": {
        "5-core": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFilesSmall/Pet_Supplies_5.json.gz",
        "full": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFiles/Pet_Supplies.json.gz"
    },
    "Prime_Pantry": {
        "5-core": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFilesSmall/Prime_Pantry_5.json.gz",
        "full": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFiles/Prime_Pantry.json.gz"
    },
    "Software": {
        "5-core": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFilesSmall/Software_5.json.gz",
        "full": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFiles/Software.json.gz"
    },
    "Sports_and_Outdoors": {
        "5-core": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFilesSmall/Sports_and_Outdoors_5.json.gz",
        "full": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFiles/Sports_and_Outdoors.json.gz"
    },
    "Tools_and_Home_Improvement": {
        "5-core": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFilesSmall/Tools_and_Home_Improvement_5.json.gz",
        "full": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFiles/Tools_and_Home_Improvement.json.gz"
    },
    "Toys_and_Games": {
        "5-core": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFilesSmall/Toys_and_Games_5.json.gz",
        "full": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFiles/Toys_and_Games.json.gz"
    },
    "Video_Games": {
        "5-core": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFilesSmall/Video_Games_5.json.gz",
        "full": "http://deepyeti.ucsd.edu/jianmo/amazon/categoryFiles/Video_Games.json.gz"
    }
}


def list_available_categories() -> List[str]:
    """
    List all available dataset categories.

    Returns:
        List of category names

    Example:
        >>> categories = list_available_categories()
        >>> print(categories[:3])
        ['All_Beauty', 'Amazon_Fashion', 'Appliances']
    """
    return sorted(list(DATASET_CATEGORIES.keys()))


def get_download_url(category: str, size: str = '5-core') -> Optional[str]:
    """
    Get download URL for a specific category and size.

    Args:
        category: Dataset category name
        size: '5-core' or 'full'

    Returns:
        Download URL if category exists, None otherwise

    Example:
        >>> url = get_download_url("Electronics", "5-core")
        >>> print(url)
        http://...Electronics_5.json.gz
    """
    if category not in DATASET_CATEGORIES:
        return None

    return DATASET_CATEGORIES[category].get(size)


def download_dataset(category: str,
                    size: str = '5-core',
                    output_dir: str = 'data/raw',
                    decompress: bool = True,
                    chunk_size: int = 8192) -> Optional[str]:
    """
    Download Amazon review dataset for a specific category.

    Args:
        category: Dataset category name
        size: '5-core' (smaller) or 'full' (complete dataset)
        output_dir: Directory to save downloaded file
        decompress: Automatically decompress .gz file
        chunk_size: Download chunk size in bytes

    Returns:
        Path to downloaded (and optionally decompressed) file, or None if failed

    Example:
        >>> filepath = download_dataset("Electronics", "5-core")
        Downloading Electronics (5-core)...
        100%|████████| 50.2MB/50.2MB [00:30<00:00]
        Decompressing...
        ✓ Downloaded to: data/raw/Electronics_5.json
    """
    url = get_download_url(category, size)
    if not url:
        print(f"Error: Category '{category}' not found.")
        print(f"Available categories: {', '.join(list_available_categories()[:5])}...")
        return None

    # Create output directory
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Determine filename
    filename = f"{category}_{size.replace('-', '_')}.json.gz"
    filepath = output_dir / filename

    print(f"\nDownloading {category} ({size})...")
    print(f"URL: {url}")

    try:
        # Stream download with progress bar
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))

        with open(filepath, 'wb') as f:
            with tqdm(total=total_size, unit='B', unit_scale=True, unit_divisor=1024) as pbar:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))

        print(f"✓ Downloaded: {filepath}")

        # Decompress if requested
        if decompress:
            print("Decompressing...")
            decompressed_path = filepath.with_suffix('')  # Remove .gz

            with gzip.open(filepath, 'rb') as f_in:
                with open(decompressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

            # Remove compressed file to save space
            filepath.unlink()

            print(f"✓ Decompressed to: {decompressed_path}")
            return str(decompressed_path)

        return str(filepath)

    except requests.exceptions.RequestException as e:
        print(f"Error downloading dataset: {e}")
        return None
    except Exception as e:
        print(f"Error processing dataset: {e}")
        return None


def get_category_info(category: str) -> Optional[Dict[str, str]]:
    """
    Get information about a category.

    Args:
        category: Dataset category name

    Returns:
        Dictionary with URLs for different sizes

    Example:
        >>> info = get_category_info("Electronics")
        >>> print(info["5-core"])
        http://...Electronics_5.json.gz
    """
    if category not in DATASET_CATEGORIES:
        return None

    return DATASET_CATEGORIES[category]


def print_categories_table():
    """
    Print a formatted table of available categories.

    Example:
        >>> print_categories_table()
        Available Amazon Review Dataset Categories:
        ============================================
        1. All_Beauty
        2. Amazon_Fashion
        ...
    """
    categories = list_available_categories()

    print("\nAvailable Amazon Review Dataset Categories:")
    print("=" * 50)

    for i, category in enumerate(categories, 1):
        print(f"{i:2d}. {category}")

    print("=" * 50)
    print(f"Total: {len(categories)} categories")
    print("\nSizes available for each category:")
    print("  - 5-core: Reviews with at least 5 reviews per user/item (smaller)")
    print("  - full: Complete dataset (larger)")
