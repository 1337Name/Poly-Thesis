from .types import FileType, DetectionResult
from abc import ABC, abstractmethod

class BaseDetector(ABC):
  @abstractmethod
    def detect(self, filepath: Path) -> DetectionResult:
        pass
    
    @abstractmethod
    def _run(self, filepath: Path) -> str:
        pass

    