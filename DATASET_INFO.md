# Amazon Review Dataset Information

## Dataset Source

**Website**: https://nijianmo.github.io/amazon/index.html  
**Citation**: Justifying recommendations using distantly-labeled reviews and fine-grained aspects  
**Authors**: Jianmo Ni, Jiacheng Li, Julian McAuley  
**Conference**: EMNLP 2019

## Available Datasets (2018 Version)

### Large Datasets with 1M+ Reviews (5-core)

| Category                        | 5-core Reviews | Full Reviews | Recommended for Project |
| ------------------------------- | -------------- | ------------ | ----------------------- |
| **Books**                       | 27,164,983     | 51,311,621   | ✓ YES (27M reviews)     |
| **Clothing, Shoes and Jewelry** | 11,285,464     | 32,292,099   | ✓ YES (11M reviews)     |
| **Home and Kitchen**            | 6,898,955      | 21,928,568   | ✓ YES (6.8M reviews)    |
| **Electronics**                 | 6,739,590      | 20,994,353   | ✓ YES (6.7M reviews)    |
| **Movies and TV**               | 3,410,019      | 8,765,568    | ✓ YES (3.4M reviews)    |
| **Sports and Outdoors**         | 2,839,940      | 12,980,837   | ✓ YES (2.8M reviews)    |
| **Kindle Store**                | 2,222,983      | 5,722,988    | ✓ YES (2.2M reviews)    |
| **Pet Supplies**                | 2,098,325      | 6,542,483    | ✓ YES (2M reviews)      |
| **Tools and Home Improvement**  | 2,070,831      | 9,015,203    | ✓ YES (2M reviews)      |
| **Toys and Games**              | 1,828,971      | 8,201,231    | ✓ YES (1.8M reviews)    |
| **Automotive**                  | 1,711,519      | 7,990,166    | ✓ YES (1.7M reviews)    |
| **CDs and Vinyl**               | 1,443,755      | 4,543,369    | ✓ YES (1.4M reviews)    |
| **Cell Phones and Accessories** | 1,128,437      | 10,063,255   | ✓ YES (1.1M reviews)    |
| **Grocery and Gourmet Food**    | 1,143,860      | 5,074,160    | ✓ YES (1.1M reviews)    |

### What is "5-core"?

- **5-core** datasets are k-core subsets where each user and item has at least 5 reviews
- These are smaller but denser subsets, ideal for research and testing
- **Full** datasets include all reviews but are very large (up to 51M reviews)

## Download Instructions

### Method 1: Direct Download (Recommended for 1M+ requirement)

Download any of the large datasets from the website:

```
Books 5-core:                    27M reviews (BEST for testing)
Electronics 5-core:              6.7M reviews
Home and Kitchen 5-core:         6.9M reviews
Clothing, Shoes, Jewelry 5-core: 11M reviews
```

**Download links format**:

```
http://deepyeti.ucsd.edu/jianmo/amazon/categoryFilesSmall/[Category]_5.json.gz
```

### Method 2: Using Our Downloader Script

```bash
# Activate virtual environment
source .venv/bin/activate

# Run the download script
python download_and_test.py

# Or use the preprocessing module directly
python -c "
from src.preprocessing.downloader import download_dataset
download_dataset('Books', '5-core', 'data/raw')
"
```

### Method 3: Alternative Download Methods

If the main server is down, you can:

1. **Use Google Drive/OneDrive links** (often provided by the dataset authors)
2. **Use alternative mirrors** (check the dataset website for updates)
3. **Contact the authors** at jin018@ucsd.edu for access

## Data Format

### Review Data Structure

Each line is a JSON object with the following fields:

```json
{
  "reviewerID": "A2SUAM1J3GNN3B",
  "asin": "0000013714",
  "reviewerName": "J. McDonald",
  "vote": 5,
  "style": {
    "Format:": "Hardcover"
  },
  "reviewText": "I bought this for my husband...",
  "overall": 5.0,
  "summary": "Heavenly Highway Hymns",
  "unixReviewTime": 1252800000,
  "reviewTime": "09 13, 2009",
  "verified": true,
  "image": ["https://images-amazon.com/..."]
}
```

### Required Fields for Merkle Tree

Our implementation requires these fields:

- `reviewerID` - Unique reviewer identifier
- `asin` - Product ASIN (unique product ID)
- `overall` - Rating (1.0 to 5.0)
- `unixReviewTime` - Unix timestamp
- `reviewText` - Review text content

## Dataset Statistics

### File Sizes (5-core versions)

- Books: ~3-4 GB compressed, ~15 GB uncompressed
- Electronics: ~850 MB compressed, ~3.5 GB uncompressed
- Home & Kitchen: ~900 MB compressed, ~3.7 GB uncompressed

### Expected Loading Times

- 1M reviews: ~30-60 seconds (first load)
- 1M reviews: ~3-5 seconds (cached load)
- 6.7M reviews (Electronics): ~3-5 minutes (first load)
- 27M reviews (Books): ~15-20 minutes (first load)

## Project Requirements Met

✅ **Minimum 1 Million Reviews**: Multiple datasets available with 1M+ reviews  
✅ **Diverse Categories**: Books, Electronics, Home, Clothing, etc.  
✅ **Structured Format**: Line-delimited JSON (easy to parse)  
✅ **Complete Metadata**: All required fields present  
✅ **Verified Purchases**: Includes verified purchase flag  
✅ **Timestamps**: Unix timestamps for temporal analysis

## Testing Strategy

### For Development/Testing (Fast)

Use smaller datasets or limit records:

```python
# Load first 100K records for quick testing
dataset = load_json_reviews("data/raw/Electronics_5.json", limit=100000)
```

### For Full Requirement (1M+)

```python
# Load 1M+ records for final evaluation
dataset = load_json_reviews("data/raw/Electronics_5.json", limit=1000000)
# Or use entire dataset (6.7M reviews)
dataset = load_json_reviews("data/raw/Electronics_5.json")
```

### For Maximum Scale Testing

```python
# Books dataset: 27M reviews
dataset = load_json_reviews("data/raw/Books_5.json")
```

## Current Status

### Downloaded Datasets

- [x] Electronics_5.json (10 reviews - sample file, needs re-download)

### Recommended Next Steps

1. Download Electronics_5.json (6.7M reviews) - ~3.5 GB uncompressed
2. Alternative: Download Books_5.json (27M reviews) - ~15 GB uncompressed
3. Test with 1M subset first
4. Scale up to full dataset for final benchmarks

## Performance Targets

Based on project requirements:

- ✅ **Tree Construction**: Handle 1M+ records
- ✅ **Proof Generation**: < 100ms per proof
- ✅ **Memory Usage**: Efficient for large datasets
- ✅ **Tamper Detection**: 100% accuracy
- ✅ **Root Hash Consistency**: Deterministic hashing

## Citation

If using this dataset, cite:

```bibtex
@inproceedings{ni2019justifying,
  title={Justifying recommendations using distantly-labeled reviews and fine-grained aspects},
  author={Ni, Jianmo and Li, Jiacheng and McAuley, Julian},
  booktitle={Empirical Methods in Natural Language Processing (EMNLP)},
  year={2019}
}
```

## Additional Resources

- **Dataset Website**: https://nijianmo.github.io/amazon/index.html
- **Paper**: http://cseweb.ucsd.edu/~jmcauley/pdfs/emnlp19a.pdf
- **Colab Notebook** (data parsing): https://colab.research.google.com/drive/1Zv6MARGQcrBbLHyjPVVMZVnRWsRnVMpV
- **Previous Versions**:
  - 2014 version: http://jmcauley.ucsd.edu/data/amazon/links.html
  - 2013 version: http://snap.stanford.edu/data/web-Amazon-links.html

## Contact

For dataset issues or access problems:

- **Email**: jin018@ucsd.edu
- **Website**: https://nijianmo.github.io/
