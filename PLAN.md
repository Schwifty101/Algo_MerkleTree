# Merkle Tree Integrity Verification System

## Overview

Build a Python-based Merkle Tree integrity verification system for Amazon review datasets (≥1M records) with <100ms verification performance.

---

## Project Structure

```
final/
 ├── requirements.txt              # Minimal dependencies (pytest, requests, tqdm)
 ├── .gitignore                    # Ignore data/,__pycache__, *.pyc
 │
 ├── src/
 │   ├── __init__.py
 │   ├── main.py                   # CLI entry point with interactive menu
 │   │
 │   ├── preprocessing/
 │   │   ├── __init__.py
 │   │   ├── downloader.py         # Dataset download with progress tracking
 │   │   ├── loader.py             # Streaming JSON loader for large files
 │   │   └── cleaner.py            # Data normalization and canonical format
 │   │
 │   ├── merkle/
 │   │   ├── __init__.py
 │   │   ├── node.py               # MerkleNode class with __slots__
 │   │   ├── tree.py               # MerkleTree with bottom-up construction
 │   │   └── proof.py              # MerkleProof generation and verification
 │   │
 │   ├── verification/
 │   │   ├── __init__.py
 │   │   ├── integrity_checker.py  # Root hash storage and comparison
 │   │   └── tamper_detector.py    # Detect modifications/deletions/insertions
 │   │
 │   ├── performance/
 │   │   ├── __init__.py
 │   │   ├── metrics.py            # Performance measurement utilities
 │   │   └── benchmark.py          # Comprehensive benchmarking suite
 │   │
 │   └── utils/
 │       ├── __init__.py
 │       ├── hash_utils.py         # SHA-256 hashing (DRY principle)
 │       └── storage.py            # JSON-based hash persistence
 │
 ├── tests/
 │   ├── __init__.py
 │   ├── test_preprocessing.py
 │   ├── test_merkle_tree.py
 │   ├── test_verification.py
 │   ├── test_tamper_detection.py
 │   ├── test_performance.py
 │   └── fixtures/
 │       └── sample_reviews.json   # 100 test reviews
 │
 ├── data/                         # .gitignored
 │   ├── raw/                      # Downloaded datasets
 │   ├── processed/                # Cleaned data
 │   └── cache/                    # Preprocessed data for fast reload
 │
 └── benchmarks/
     └── results/                  # Performance test outputs
```

---

## Core Modules

### 1. Data Preprocessing (`src/preprocessing/`)

#### `downloader.py`
- `download_dataset(category, size='5-core')` - Download with progress bar
- `list_available_categories()` - Show available Amazon datasets
- Uses `requests` and `tqdm` for user-friendly downloads

#### `loader.py`
- `load_json_reviews(filepath, limit=None)` - Stream large JSON files
- `batch_loader(filepath, batch_size=10000)` - Memory-efficient generator
- `load_cached_reviews(cache_path)` - Fast load from preprocessed cache
- `save_to_cache(reviews, cache_path)` - Save cleaned data for reuse
- Handles line-delimited JSON format from Amazon dataset
- **Caching**: First load parses JSON and saves to cache (slow), subsequent loads read cache (10x faster)

#### `cleaner.py`
- `normalize_review(review_dict)` - Extract key fields
- `generate_canonical_string(review_dict)` - Deterministic format for hashing
- **Canonical format**: `{reviewerID}|{asin}|{overall}|{unixReviewTime}|{reviewText}`
- Fixed field order ensures consistent hashing

---

### 2. Merkle Tree Core (`src/merkle/`)

#### `node.py`
```python
class MerkleNode:
    __slots__ = ['hash', 'left', 'right', 'data', 'index']
    # hash: bytes (32-byte SHA-256 digest, NOT hex string)
    # Minimalist design with __slots__ for memory efficiency
    # Convert to hex only when displaying to user
```

#### `tree.py`
```python
class MerkleTree:
    def __init__(self, data_items)
    def build_tree()                    # Bottom-up construction O(n)
    def get_root_hash()                 # Return root hash hex digest
    def get_proof(index)                # Generate Merkle proof O(log n)
    def verify_proof(data, proof, root) # Static verification O(log n)
```

**Algorithm**: Bottom-up construction with duplicate last node for odd levels

**Key Implementation Details (HYBRID STORAGE APPROACH)**:
- Build complete binary tree (duplicate last node if odd count using exact byte copy)
- Store root hash + leaf hashes only as raw bytes (not full tree structure)
- Rebuild proof path on demand from leaf hashes using bytes concatenation
- **Memory**: ~32MB for 1M records (raw bytes, not hex) vs 700MB for full tree
- **Proof generation**: ~1-2ms (rebuild path) vs <0.1ms (full tree)
- **Hash operations**: Use `left_bytes + right_bytes` then `sha256()`
- **Rationale**: Balanced trade-off between memory usage and performance

#### `proof.py`
```python
class MerkleProof:
    def __init__(self, leaf_hash: bytes, leaf_index: int, path: list, root_hash: bytes)
    def to_dict()           # Serialize to JSON (convert bytes to hex)
    def from_dict(data)     # Deserialize from JSON (convert hex to bytes)
    def verify(self, data)  # Verify proof validity
```

**Path structure**: List of `(hash_bytes, is_left)` tuples with 32-byte raw hashes  
**Serialization**: Convert bytes to hex only for JSON export/display  
**Memory**: 32 bytes per hash vs 64 characters (2× savings)

---

### 3. Verification System (`src/verification/`)

#### `integrity_checker.py`
```python
class IntegrityChecker:
    def store_root_hash(dataset_id, root_hash, metadata)
    def verify_integrity(dataset_id, current_root_hash)
    def get_stored_hash(dataset_id)
```

**Storage format**: JSON with `{root_hash, timestamp, record_count, dataset_id}`

#### `tamper_detector.py`
```python
class TamperDetector:
    def detect_modifications(original_tree, modified_data)
    def detect_deletions(original_tree, modified_data)
    def detect_insertions(original_tree, modified_data)
    def generate_tamper_report(original_tree, modified_tree)
```

**Detection strategy**:
- **Modifications**: Compare leaf hashes at same indices
- **Deletions**: Check for missing indices
- **Insertions**: Identify new leaves outside original range

---

### 4. Performance Measurement (`src/performance/`)

#### `metrics.py`
- `measure_hashing_speed()` - Records/second throughput
- `measure_tree_construction_time()` - Build time for various sizes
- `measure_proof_generation_latency()` - Average proof gen time
- `measure_verification_latency()` - Must achieve <100ms
- `measure_memory_usage()` - Peak memory for tree

#### `benchmark.py`
- `run_all_benchmarks()` - Test with 100, 1K, 10K, 100K, 1M records
- `generate_performance_report()` - JSON + text output
- `export_results()` - Save to `benchmarks/results/`

---

### 5. Utilities (`src/utils/`)

#### `hash_utils.py` (DRY principle - single source of truth)
```python
def hash_data(data: str) -> bytes            # SHA-256 raw bytes (32 bytes)
def hash_pair(left: bytes, right: bytes) -> bytes  # Hash left_bytes + right_bytes
def hash_review(review_dict: dict) -> bytes  # Hash canonical review string
def bytes_to_hex(hash_bytes: bytes) -> str   # Convert to hex for display only
def hex_to_bytes(hex_str: str) -> bytes      # Convert from hex for loading
```

**Performance Rationale**:
- **Raw bytes internally**: 32 bytes vs 64-character hex (2× memory savings)
- **Direct concatenation**: `left_bytes + right_bytes` then hash (faster)
- **Hex only for display**: Convert to hex only for JSON/CLI output
- **Odd node duplication**: Exact byte copy of last hash (no sentinel)

#### `storage.py`
```python
class HashStorage:
    def save(key, data)     # Store JSON to file
    def load(key)           # Load from file
    def exists(key)         # Check existence
```

---

## Key Algorithms

### Merkle Tree Construction

1. Create leaf nodes by hashing each review's canonical string
2. While more than one node at current level:
   - a. If odd number: duplicate last node
   - b. Pair adjacent nodes
   - c. Create parent with `hash(left.hash + right.hash)`
3. Return root node

**Complexity**: Time: O(n), Space: O(n), Height: O(log n)

### Proof Generation

1. Start at `leaf[index]`
2. Traverse to root, collecting sibling hashes
3. Record `(sibling_hash, is_left_sibling)` for each level
4. Return path

**Complexity**: Time: O(log n), Space: O(log n)

### Proof Verification

1. Hash the data
2. For each `(sibling, is_left)` in proof:
   - If `is_left`: `hash = SHA256(sibling + hash)`
   - Else: `hash = SHA256(hash + sibling)`
3. Compare final hash with `root_hash`

**Complexity**: Time: O(log n), Space: O(1)

---

## CLI Menu Structure

```
=== MERKLE TREE INTEGRITY VERIFICATION SYSTEM ===

1. Data Management
    1.1. Download Amazon Review Dataset
    1.2. Load Dataset from File
    1.3. View Dataset Statistics

2. Merkle Tree Operations
    2.1. Build Merkle Tree
    2.2. View Tree Information
    2.3. Export Root Hash

3. Integrity Verification
    3.1. Verify Dataset Integrity
    3.2. Store Current Root Hash
    3.3. Compare with Stored Hash

4. Existence Proofs
    4.1. Generate Proof for Review
    4.2. Verify Proof
    4.3. Batch Proof Generation

5. Tamper Detection
    5.1. Simulate Modification
    5.2. Simulate Deletion
    5.3. Simulate Insertion
    5.4. Generate Tamper Report

6. Performance Testing
    6.1. Measure Hashing Speed
    6.2. Benchmark Tree Construction
    6.3. Benchmark Proof Generation
    6.4. Run Full Performance Suite

7. Test Cases (As Per Spec)
    7.1. Run All Required Test Cases

0. Exit
```

---

## Performance Optimizations

### Memory Optimization (HYBRID APPROACH)

1. **Streaming data loading**: Process in 10K-record batches
2. **Store root + leaf hashes only**: ~32MB for 1M records (raw bytes, not hex)
3. **Raw bytes internally**: 32 bytes per hash vs 64-char hex (2× savings)
4. **Rebuild proof paths on demand**: Trade slight speed for memory
5. **Preprocessing cache**: Save cleaned data to disk for fast reload
6. **`__slots__` in MerkleNode**: Reduce per-node overhead during path rebuild
7. **Target**: <500MB for 1M records (32MB for hashes + overhead)

### Speed Optimization

1. **Hash caching**: Pre-compute all leaf hashes, never recompute
2. **C-based hashlib**: Use `hashlib.sha256()` directly with bytes
3. **Direct bytes concatenation**: `left_bytes + right_bytes` (no hex encoding overhead)
4. **Hex conversion only for display**: Avoid encoding/decoding in core operations
5. **Index-based lookup**: O(1) proof generation start
6. **Bottom-up construction**: Single pass, no recursion
7. **Target verification**: <10ms (requirement is <100ms)

### Algorithmic Choices

- **Complete binary tree**: Simplifies index calculations
- **Duplicate last node**: Exact byte copy of last hash (no sentinel)
- **Raw bytes internally**: 32-byte hashes, convert to hex only for display/JSON
- **Direct bytes concatenation**: `left_bytes + right_bytes` before hashing
- **Hybrid storage**: Root + leaf hashes only (32MB for 1M records)

---

## Implementation Phases

### Phase 1: Foundation (Priority: CRITICAL) (completed)

1. Project structure setup
2. `utils/hash_utils.py` - Core hashing functions
3. `utils/storage.py` - JSON persistence
4. Basic CLI skeleton in `main.py`
5. Unit tests for utilities

**Validation**: Hash functions work correctly, CLI displays menu

### Phase 2: Data Processing (Priority: HIGH)

1. `preprocessing/loader.py` - Streaming JSON loader + caching system
2. `preprocessing/cleaner.py` - Canonical format generator
3. `preprocessing/downloader.py` - Dataset acquisition
4. Create test fixture with 1K-10K reviews (small dataset for fast iteration)
5. Implement cache save/load functionality
6. Unit tests for preprocessing and caching

**Validation**: Successfully load, cache, and reload test data (verify cache speedup)

### Phase 3: Merkle Tree Core (Priority: CRITICAL)

1. `merkle/node.py` - MerkleNode class (used temporarily during construction)
2. `merkle/tree.py` - Hybrid storage implementation:
   - Build full tree during construction
   - Store only root hash + array of leaf hashes
   - Discard intermediate nodes after construction
3. Test with various sizes (1, 2, 4, 8, odd numbers, 1K-10K)
4. Verify deterministic hashing (same data → same root)

**Validation**: Build tree from test data, verify memory usage ~60-100KB for 1K records

### Phase 4: Proof System (Priority: CRITICAL)

1. `merkle/proof.py` - MerkleProof class
2. Implement `get_proof()` in MerkleTree with path rebuild:
   - Start from stored leaf hash at index
   - Rebuild tree path upward by rehashing pairs
   - Collect sibling hashes along the way
3. Implement `verify_proof()` static method
4. Test all edge cases (first, middle, last leaf)
5. Verify proof generation <2ms (acceptable for hybrid approach)

**Validation**: Generate and verify proofs for test records, measure latency

### Phase 5: Integrity Verification (Priority: HIGH)

1. `verification/integrity_checker.py` - Hash storage/comparison
2. Implement storage with metadata (timestamp, count)
3. CLI integration for verification workflow
4. Test integrity violation detection

**Validation**: Store root, modify data, detect tampering

### Phase 6: Tamper Detection (Priority: MEDIUM)

1. `verification/tamper_detector.py` - All detection types
2. Implement detailed tamper reports
3. CLI simulation options
4. Test all tampering scenarios

**Validation**: Accurately detect modifications, deletions, insertions

### Phase 7: Performance Measurement (Priority: HIGH)

1. `performance/metrics.py` - All measurement functions
2. `performance/benchmark.py` - Full benchmark suite
3. Test with 100, 1K, 10K, 100K, 1M records
4. Verify <100ms verification requirement

**Validation**: All performance requirements met

### Phase 8: Integration & Testing (Priority: HIGH)

1. Complete all unit tests (>90% coverage)
2. Integration tests for full workflows with 1K-10K records
3. Implement all required test cases from spec
4. Scale-up testing: Download and test with 100K, then 1M records
5. Verify cache performance (10x speedup on reload)
6. Verify hybrid storage memory savings

**Validation**: All tests pass, system handles 1M records in <500MB memory

### Phase 9: Polish (Priority: MEDIUM)

1. Add comprehensive docstrings
2. Update README with usage instructions
3. Final performance benchmarking
4. Code cleanup and formatting

**Validation**: Production-ready system

---

## Dependencies (`requirements.txt`)

```txt
# Testing
pytest>=7.4.0
pytest-cov>=4.1.0

# Data download and UX
requests>=2.31.0    # Dataset downloading
tqdm>=4.66.0        # Progress bars
```

Core functionality uses only Python stdlib (`hashlib`, `json`, `sys`, `time`, `os`, `pathlib`)

---

## Design Principles Applied

### KISS (Keep It Simple)
- Minimal class hierarchy (Node, Tree, Proof)
- Straightforward algorithms (bottom-up construction)
- No unnecessary abstractions

### YAGNI (You Aren't Gonna Need It)
- Only implement required features
- No speculative optimizations
- No over-engineered patterns

### DRY (Don't Repeat Yourself)
- Single `hash_utils` module for all hashing
- Centralized storage logic
- Reusable proof verification

### SOLID Principles
- **Single Responsibility**: Each module has one clear purpose
- **Open/Closed**: Tree accepts any data via hashing abstraction
- **Liskov Substitution**: Consistent interfaces throughout
- **Interface Segregation**: Minimal, focused APIs
- **Dependency Inversion**: Modules depend on `hash_utils` abstraction

---

## Critical Files to Implement (in order)

1. `src/utils/hash_utils.py` - Foundation for all hashing operations
2. `src/merkle/node.py` - Basic tree building block
3. `src/merkle/tree.py` - Core Merkle tree logic
4. `src/preprocessing/loader.py` - Data ingestion for large datasets
5. `src/merkle/proof.py` - Existence proof generation/verification
6. `src/verification/integrity_checker.py` - Root hash storage and verification
7. `src/main.py` - CLI orchestration and user interface
8. `tests/` - Comprehensive test coverage

---

## Performance Targets (HYBRID APPROACH)

- **Tree construction**: <10 seconds for 1M records
- **Verification**: <100ms (target: <10ms via root comparison)
- **Proof generation**: <2ms per proof (hybrid rebuild approach)
- **Memory usage**: <500MB for 1M records (32MB for raw byte hashes + overhead)
- **Hashing speed**: >100K records/second (boosted by raw bytes operations)
- **Cache reload**: 10x faster than initial JSON parsing

---

## Success Criteria

✓ Handle ≥1M Amazon review records  
✓ Verification completes in <100ms  
✓ Generate existence proofs for any review ID (<2ms per proof)  
✓ Detect all types of tampering (modify/delete/insert)  
✓ Interactive CLI with all menu options  
✓ Complete test suite with >90% coverage  
✓ Performance benchmarks validate all targets  
✓ Hybrid storage: <500MB memory for 1M records  
✓ Preprocessing cache: 10x faster subsequent loads  
✓ Clean code following KISS, YAGNI, DRY, SOLID

---

## Key Design Decisions (User Confirmed)

### 1. Hybrid Storage Approach
Store root + leaf hashes only, rebuild proof paths on demand
- **Memory**: ~32MB for 1M records using raw bytes (vs 700MB full tree)
- **Proof speed**: ~1-2ms (vs <0.1ms full tree) - acceptable trade-off
- **Raw bytes optimization**: 32-byte hashes internally, hex only for display
- **Direct concatenation**: `left_bytes + right_bytes` before hashing
- Simplifies tree structure, reduces memory footprint by 50% vs hex encoding

### 2. Preprocessing Cache
Implement disk-based cache for cleaned review data
- **First load**: Parse JSON, clean, save to cache (~slow)
- **Subsequent loads**: Read from cache (~10x faster)
- Enables faster iteration during development and testing

### 3. Development Strategy
Start with small dataset (1K-10K records)
- Fast iteration and debugging
- Scale up to 100K, then 1M for final testing
- Validates design at small scale before large-scale testing