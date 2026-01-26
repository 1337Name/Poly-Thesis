"""Detector implementation using the PolyDet library."""

from .baseDetector import BaseDetector
from .types import DetectionResult
from pathlib import Path
from typing import List, Any, Dict


class PolyDetDetector(BaseDetector):
    """Wraps the PolyDet library for polyglot file detection."""
    def _get_name(self) -> str:
        return "polydet"

    def detect(self, path : Path) -> DetectionResult:
        try:
            import polydet
            result = polydet.scan(str(path))
            types = list(result.keys())
            #mp3 always give false positive
            types = [t for t in types if t.lower() not in ['mp3']]

            normalized = self._normalize(types)
            return self._make_result(normalized, self._make_serializable(result))
        except Exception as exception:
            return self._make_error(exception)

    def _make_serializable(self, result : dict[str, Any]) -> dict:
        serializable = {
            ftype: polyglotlevel.suspicious_chunks
            for ftype, polyglotlevel in result.items() 
        }
        return serializable