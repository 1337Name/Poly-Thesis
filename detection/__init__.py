"""
Polyglot file detection framework.

This package provides a unified interface for detecting polyglot files using
multiple detection tools. Polyglot files are files that are valid in multiple
file formats simultaneously, which can be used to bypass security controls.

The package implements a plugin architecture where each detector wraps a
different detection tool (file command, Magika, PolyFile, PolyDet) behind
a common interface defined by :class:`BaseDetector`.

Classes:
    FileType: Enumeration of supported file types for detection.
    DetectionResult: Dataclass containing detection results from a tool.
    BaseDetector: Abstract base class for all detector implementations.
    FileDetector: Wrapper for the Unix ``file`` command.
    MagikaDetector: Wrapper for Google's Magika ML-based file type detector.
    PolyFileDetector: Wrapper for the PolyFile detection library.
    PolyDetDetector: Wrapper for the PolyDet detection library.

Example:
    >>> from detection import FileDetector, MagikaDetector
    >>> detector = FileDetector()
    >>> result = detector.detect(Path("suspicious_file.png"))
    >>> if result.is_polyglot:
    ...     print(f"Polyglot detected: {result.detected_types}")
"""

from .types import FileType, DetectionResult
from .baseDetector import BaseDetector
from .fileDetector import FileDetector
from .magikaDetector import MagikaDetector
from .polyFileDetector import PolyFileDetector
from .polyDetDetector import PolyDetDetector

__all__ = [
    "FileType",
    "DetectionResult",
    "BaseDetector",
    "FileDetector",
    "MagikaDetector",
    "PolyFileDetector",
    "PolyDetDetector",
]
