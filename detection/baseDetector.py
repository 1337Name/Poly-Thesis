"""
Abstract base class for polyglot file detectors.

This module defines the interface that all detector implementations must follow.
Each detector wraps a specific file type detection tool and normalizes its output
to a common format.
"""

from .types import FileType, DetectionResult, FILETYPE_NAMES_ALT
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Any, Set, Optional
import re


class BaseDetector(ABC):
    """
    Abstract base class for file type detectors.

    Subclasses must implement :meth:`detect` to perform actual detection and
    :meth:`_get_name` to return the detector's identifier. The base class
    provides helper methods for creating result objects and normalizing
    file type names across different detection tools.

    The normalization process maps tool-specific type names to the standard
    :class:`FileType` enumeration, allowing consistent comparison of results
    across different detectors.
    """

    @abstractmethod
    def detect(self, path: Path) -> DetectionResult:
        """
        Detect file types present in the given file.

        Args:
            path: Path to the file to analyze.

        Returns:
            DetectionResult containing detected types, polyglot status,
            and raw tool output.
        """
        pass

    @abstractmethod
    def _get_name(self) -> str:
        """
        Return the unique identifier for this detector.

        Returns:
            String identifier (e.g., 'file', 'magika', 'polyfile').
        """
        pass

    def _make_result(self, detected_types: Set[FileType], raw_output: str | dict | list) -> DetectionResult:
        """
        Create a successful detection result.

        Args:
            detected_types: Set of normalized file types found.
            raw_output: Original output from the detection tool.

        Returns:
            DetectionResult with polyglot flag set based on type count.
        """
        return DetectionResult(
            tool=self._get_name(),
            detected_types=detected_types,
            is_polyglot=len(detected_types) > 1,
            raw_output=raw_output,
            error=None
        )

    def _make_error(self, error: Exception) -> DetectionResult:
        """
        Create an error detection result.

        Args:
            error: The exception that occurred during detection.

        Returns:
            DetectionResult with empty types and error message set.
        """
        return DetectionResult(
            tool=self._get_name(),
            detected_types=set(),
            is_polyglot=False,
            raw_output="",
            error=str(error)
        )

    def _normalize(self, types: List[str]) -> Set[FileType | str]:
        """
        Normalize a list of raw type strings to FileType enums.

        Attempts to map each raw type string to a standard FileType. Types
        that cannot be mapped are kept as raw strings to preserve information.

        Args:
            types: List of raw type strings from the detection tool.

        Returns:
            Set of FileType enums and/or raw strings for unrecognized types.
        """
        normalized = set()  # avoids duplication
        for raw_type in types:
            normalized_type = self._normalize_type(raw_type)
            if normalized_type:
                normalized.add(normalized_type)
            else:
                # TODO log for debug because dont know all tool output types
                normalized.add(raw_type)
        return normalized

    def _normalize_type(self, raw_type: str) -> Optional[FileType]:
        """Map a raw type string to a FileType enum, or None if unrecognized."""
        raw_type = raw_type.lower().strip()
        if "/" in raw_type:
            raw_type = raw_type.split("/")[1].strip()
        #extra cases TODO add more extra cases
        for name, file_type in FILETYPE_NAMES_ALT.items():
            pattern = r'\b' + re.escape(name) + r'\b' # search for whole word
            if re.search(pattern, raw_type):
                return file_type
        # TODO eval if there is any problems
        for file_type in FileType:
            pattern = r'\b' + re.escape(file_type.value.lower()) + r'\b'
            if re.search(pattern, raw_type):
                return file_type

        return None