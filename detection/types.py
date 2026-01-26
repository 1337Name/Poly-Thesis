"""
Types and data structures for polyglot file detection.

This module defines the core types used throughout the detection system,
including file type enumerations and detection result structures.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional


class FileType(str, Enum):
    """
    Enumeration of supported file types for polyglot detection.

    Only includes file types relevant for polyglot generation and evaluation.
    Types not in this enum are kept as raw strings for compatibility with
    detection tool outputs.
    """
    PNG = "PNG"
    JPEG = "JPEG"
    PDF = "PDF"
    BMP = "BMP"
    GIF = "GIF"
    HTML = "HTML"
    HTA = "HTA"
    ZIP = "ZIP"
    JS = "JS"
    PHP = "PHP"
    RAR = "RAR"


FILETYPE_NAMES_ALT: dict[str, FileType] = {
    """
    Mapping of alternative file type names to FileType enum values.

    Used to normalize various naming conventions from different detection tools
    to a consistent FileType enum.
    """
    "jfif": FileType.JPEG,
    "jpg": FileType.JPEG,
    "htm": FileType.HTML,
    "javascript": FileType.JS,
    "x-php": FileType.PHP
}


@dataclass
class DetectionResult:
    """
    Result of a file type detection operation.
    """
    tool: str
    detected_types: set[str]
    is_polyglot: bool
    raw_output: dict | str | list
    error: Optional[str] = None