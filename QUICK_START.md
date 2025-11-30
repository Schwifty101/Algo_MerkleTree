# 🚀 Quick Start Guide - Merkle Tree Verification System

**Get up and running in 5 minutes!**

---

## ⚡ Installation (2 minutes)

```bash
# 1. Navigate to project directory
cd "merkle-tree-verification"

# 2. Create virtual environment
python3 -m venv venv

# 3. Activate it
source venv/bin/activate  # macOS/Linux
# OR: venv\Scripts\activate  # Windows

# 4. Install dependencies
pip install -r requirements.txt

# ✓ Done! Ready to use.
```

---

## 🎯 Running the System (1 minute)

### Option 1: Interactive CLI (Recommended)

```bash
python src/main.py
```

**What you'll see:**
```
╔═══════════════════════════════════════════════════════════╗
║       MERKLE TREE INTEGRITY VERIFICATION SYSTEM          ║
╚═══════════════════════════════════════════════════════════╝

Main Menu:
  1. Load Review Data
  2. Build Merkle Tree
  3. Integrity Verification
  4. Existence Proofs
  5. Tamper Detection
  6. Performance Benchmarks
  7. Exit

Choice:
```

### Option 2: Python API

```python
from src.merkle.tree import MerkleTree

# Create from list of strings
reviews = ["review 1", "review 2", "review 3"]
tree = MerkleTree.build_from_reviews(reviews)

# Get root hash
root = tree.get_root_hash_hex()
print(f"Root: {root}")
```

---

## 📖 Common Workflows

### Workflow 1: Verify Data Integrity

**Scenario**: You have a dataset and want to detect if it's been tampered with.

```python
from src.merkle.tree import MerkleTree
from src.verification.integrity_checker import IntegrityChecker

# Step 1: Build tree from original data
original_reviews = load_your_reviews()
tree = MerkleTree.build_from_reviews(original_reviews)

# Step 2: Save baseline
checker = IntegrityChecker()
checker.save_baseline(tree, "my_baseline")
print("✓ Baseline saved!")

# Step 3: Later, verify current data
current_reviews = load_your_reviews()
current_tree = MerkleTree.build_from_reviews(current_reviews)

result = checker.verify_integrity(current_tree, "my_baseline")

if result['verified']:
    print("✓ Data is intact!")
else:
    print(f"✗ TAMPERING DETECTED!")
    print(f"   Issue: {result['issue_detail']}")
```

**Output:**
```
✓ Baseline saved!
✗ TAMPERING DETECTED!
   Issue: Data modification detected (root hash mismatch, same size)
```

---

### Workflow 2: Prove a Record Exists

**Scenario**: Prove a specific review is part of the dataset.

```python
from src.merkle.tree import MerkleTree

# Build tree
reviews = ["review A", "review B", "review C"]
tree = MerkleTree.build_from_reviews(reviews)

# Generate proof for review B (index 1)
proof = tree.get_proof(1, reviews[1])

# Verify the proof
is_valid = proof.verify(tree.get_root_hash())

print(f"Proof valid: {is_valid}")
print(f"Proof path length: {len(proof.proof_path)}")
```

**Output:**
```
Proof valid: True
Proof path length: 2
```

---

### Workflow 3: Detect What Changed

**Scenario**: Find exactly which records were modified.

```python
from src.merkle.tree import MerkleTree
from src.verification.tamper_detector import TamperDetector

# Original data
original = ["review 1", "review 2", "review 3"]
original_tree = MerkleTree.build_from_reviews(original)

# Modified data (changed review 2)
modified = ["review 1", "TAMPERED!", "review 3"]
modified_tree = MerkleTree.build_from_reviews(modified)

# Detect changes
detector = TamperDetector()
report = detector.detect_tampering(original_tree, modified_tree)

print(f"Tampering detected: {report['tampering_detected']}")
print(f"Modified records: {report['modification_count']}")
print(f"Changed indices: {report['modified_indices']}")
```

**Output:**
```
Tampering detected: True
Modified records: 1
Changed indices: [1]
```

---

### Workflow 4: Benchmark Performance

**Scenario**: Test system performance with your data size.

```bash
# Run benchmark suite
python -m src.performance.benchmark
```

**Output:**
```
Running Merkle Tree Comprehensive Benchmark...

Tree Construction Benchmarks:
  100 records: 0.40ms (250,000 records/sec)
  1,000 records: 3.76ms (266,000 records/sec)
  10,000 records: 47.57ms (210,000 records/sec)

Verification Performance:
  100 records: 0.08ms ✓ PASSED (<100ms target)
  1,000 records: 0.09ms ✓ PASSED
  10,000 records: 0.13ms ✓ PASSED

Results saved to:
  JSON: benchmarks/results/benchmark_results_20241130_164523.json
  Text: benchmarks/results/benchmark_report_20241130_164523.txt
```

---

## 🔧 Common Tasks

### Task: Load Amazon Review Data

```python
from src.preprocessing.loader import ReviewLoader

# Load from file
loader = ReviewLoader()
reviews = loader.load_reviews(
    "data/raw/Electronics.json",
    limit=10000,  # Optional: limit number of records
    use_cache=True  # 10× faster on subsequent loads
)

print(f"Loaded {len(reviews)} reviews")
```

### Task: Download Amazon Dataset

```python
from src.preprocessing.downloader import AmazonDatasetDownloader

# Initialize downloader
downloader = AmazonDatasetDownloader(base_dir="data/raw")

# See available categories
categories = downloader.list_categories()
print(categories[:5])  # ['Books', 'Electronics', 'Movies_and_TV', ...]

# Download a category
downloader.download_category("Electronics")
```

### Task: Save and Load Trees

```python
from src.merkle.tree import MerkleTree

# Build tree
tree = MerkleTree.build_from_reviews(["a", "b", "c"])

# Save to dictionary
tree_dict = tree.to_dict()

# Load from dictionary
loaded_tree = MerkleTree.from_dict(tree_dict)

# Verify they match
assert tree.get_root_hash() == loaded_tree.get_root_hash()
```

### Task: Compare Two Baselines

```python
from src.verification.integrity_checker import IntegrityChecker

checker = IntegrityChecker()

# Compare two saved baselines
comparison = checker.compare_baselines("baseline_v1", "baseline_v2")

if comparison['match']:
    print("Baselines are identical")
else:
    print(f"Baselines differ:")
    print(f"  Root hash 1: {comparison['baseline1']['root_hash']}")
    print(f"  Root hash 2: {comparison['baseline2']['root_hash']}")
```

---

## 🧪 Testing Your Installation

### Quick Test (30 seconds)

```bash
# Run all tests
python -m pytest tests/ -v

# Expected output:
# ============================= 243 passed in 0.18s ==============================
```

### Verify Core Functionality

```python
# Create test script: test_install.py
from src.merkle.tree import MerkleTree
from src.verification.integrity_checker import IntegrityChecker

# Test 1: Build tree
reviews = [f"review_{i}" for i in range(100)]
tree = MerkleTree.build_from_reviews(reviews)
print(f"✓ Built tree with {tree.get_leaf_count()} leaves")

# Test 2: Generate proof
proof = tree.get_proof(50, reviews[50])
assert proof.verify(tree.get_root_hash())
print("✓ Proof generation works")

# Test 3: Integrity check
checker = IntegrityChecker()
checker.save_baseline(tree, "test_baseline")
result = checker.verify_integrity(tree, "test_baseline")
assert result['verified']
print("✓ Integrity verification works")

print("\n🎉 All systems operational!")
```

Run it:
```bash
python test_install.py
```

---

## 📚 Next Steps

### Learning Path

1. **Beginner**: 
   - Run the CLI (`python src/main.py`)
   - Try the examples above
   - Read README.md

2. **Intermediate**:
   - Explore the API with your own data
   - Run benchmarks on different sizes
   - Study the test files

3. **Advanced**:
   - Read CLAUDE.md for architecture details
   - Modify the algorithms
   - Contribute improvements

### Useful Resources

- **README.md**: Complete documentation (650+ lines)
- **PROJECT_SUMMARY.md**: High-level overview
- **WORKDONE.md**: Development history and details
- **tests/**: 243 examples of API usage
- **src/**: Well-documented source code

---

## ❓ Troubleshooting

### Issue: "Module not found"

**Solution**:
```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: "No module named pytest"

**Solution**:
```bash
# Install pytest
pip install pytest pytest-cov

# Or reinstall all dependencies
pip install -r requirements.txt
```

### Issue: "Permission denied" when downloading data

**Solution**:
```bash
# Create data directory
mkdir -p data/raw

# Check permissions
chmod 755 data/raw
```

### Issue: Tests fail

**Solution**:
```bash
# Run tests with verbose output
python -m pytest tests/ -v --tb=short

# Check specific failing test
python -m pytest tests/test_merkle_tree.py::test_name -v
```

---

## 💡 Tips for Best Results

### Performance Tips

1. **Use caching**: Set `use_cache=True` when loading data (10× faster)
2. **Start small**: Test with 1K records before scaling to 1M
3. **Memory conscious**: System uses ~70 bytes per record
4. **Batch operations**: Build tree once, verify many times

### Development Tips

1. **Virtual environment**: Always activate before running
2. **Run tests first**: `pytest tests/ -v` to verify setup
3. **Check coverage**: `pytest tests/ --cov=src` for quality
4. **Use CLI**: Interactive mode is great for exploration

### Data Tips

1. **Clean data**: Use preprocessing module for best results
2. **Canonical format**: System handles field ordering automatically
3. **Cache early**: First load is slow, subsequent loads are 10× faster
4. **Validate input**: Check for missing/invalid fields

---

## 🎓 Example Session

Here's a complete session showing typical usage:

```bash
# Terminal Session
$ cd merkle-tree-verification
$ source venv/bin/activate

(venv) $ python src/main.py

╔═══════════════════════════════════════════════════════════╗
║       MERKLE TREE INTEGRITY VERIFICATION SYSTEM          ║
╚═══════════════════════════════════════════════════════════╝

Choice: 1  # Load Review Data
Choice: 2  # Build Merkle Tree
✓ Built tree with 10,000 leaves in 48ms

Choice: 3  # Integrity Verification
Choice: 1  # Save Baseline
✓ Baseline saved: electronics_jan2024

Choice: 4  # Exit

# ... time passes, data might be modified ...

(venv) $ python src/main.py
Choice: 1  # Load Review Data
Choice: 2  # Build Merkle Tree
Choice: 3  # Integrity Verification
Choice: 2  # Verify Current Tree

✗ TAMPERING DETECTED!
  Root hash mismatch - data has been modified

Choice: 5  # Tamper Detection
✓ Found 3 modifications, 1 deletion, 0 insertions

Choice: 7  # Exit
```

---

## 🚀 You're Ready!

You now know how to:
- ✅ Install and test the system
- ✅ Build Merkle trees
- ✅ Verify data integrity
- ✅ Generate existence proofs
- ✅ Detect tampering
- ✅ Benchmark performance

**Start exploring with the CLI or dive into the API!**

---

**Need help?** Check README.md or create an issue on GitHub.

**Happy verifying!** 🔐
