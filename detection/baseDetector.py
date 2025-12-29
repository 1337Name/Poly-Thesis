from .types import FileType, DetectionResult, FILETYPE_NAMES_ALT
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Any, Set, Optional
import re

class BaseDetector(ABC):

    @abstractmethod
    def detect(self, path: Path) -> DetectionResult:
        pass
    
    @abstractmethod
    def _get_name(self) -> str:
        pass

    def _make_result(self, detected_types: Set[FileType], raw_output: str | dict | list) -> DetectionResult:
        return DetectionResult(
            tool=self._get_name(),
            detected_types=detected_types,
            is_polyglot=len(detected_types) > 1,
            raw_output=raw_output,
            error=None
        )
    
    def _make_error(self, error: Exception) -> DetectionResult:
        return DetectionResult(
            tool=self._get_name(),
            detected_types=set(),
            is_polyglot=False,
            raw_output="",
            error=str(error)
        )

    def _normalize(self, types: List[str]) -> Set[FileType | str]:
        normalized = set() # avoids duplication
        for raw_type in types:
            normalized_type = self._normalize_type(raw_type)
            if normalized_type:
                normalized.add(normalized_type)
            else:
                #TODO log for debug becazuse dont know all tool output types 
                normalized.add(raw_type)
        return normalized

    def _normalize_type(self, raw_type: str) -> Optional[FileType]:
        raw_type = raw_type.lower()
        #extra cases TODO add more extra cases
        for name, file_type in FILETYPE_NAMES_ALT.items():
            pattern = r'\b' + re.escape(name) + r'\b' # search for whole word
            if re.search(pattern, raw_type):
                return file_type
        # Autocheck with FileType names TODO eval if there is any problems
        for file_type in FileType:
            pattern = r'\b' + re.escape(file_type.value.lower()) + r'\b'
            if re.search(pattern, raw_type):
                return file_type
            
        return None