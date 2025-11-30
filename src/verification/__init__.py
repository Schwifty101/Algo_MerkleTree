"""
Verification module for Merkle tree integrity checking and tamper detection.

This module provides components for:
- Integrity verification through root hash comparison
- Tamper detection and analysis
- Verification reporting
"""

from verification.integrity_checker import IntegrityChecker
from verification.tamper_detector import TamperDetector

__all__ = ['IntegrityChecker', 'TamperDetector']
