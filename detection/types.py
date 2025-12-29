
from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Any

class FileType(str, Enum):
   # we only need the filetypes we really use 
   # Design decision here is we convert what we actualy look for in eval i.e. combinations we generate
   # Because if its in the combination it will be converted correctly if not it doesnt really matter anyway
   # dont add a "Other" or default option instead keep the original String for compat with scores dict
    PNG = "PNG"
    JPEG = "JPEG"
    PDF = "PDF"
    BMP = "BMP"
    GIF = "GIF"
    HTML = "HTML"
    HTA = "HTA"
    ZIP = "ZIP"
    JS = "JS"
    
FILETYPE_NAMES_ALT = {
    "jfif": FileType.JPEG,
    "jpg": FileType.JPEG,
    "htm": FileType.HTML,
}

@dataclass
class DetectionResult:
    tool: str
    detected_types: set[str]      
    is_polyglot: bool
    raw_output: dict | str | list #important: need to be json dumpable/serializable
    error: Optional[str] = None