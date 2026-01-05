from .baseDetector import BaseDetector
from .types import DetectionResult
from pathlib import Path
from typing import List

class PolyFileDetector(BaseDetector):

    def __init__(self, require_mimetype: bool = True):
        """
        require_mimetype: True: count only matches with mimetype; False: counts one match with empty mimetype
        """

        super().__init__()
        self._require_mimetype = require_mimetype

    def _get_name(self) -> str:
        return "polyfile"
    
    def detect(self, path : Path) -> DetectionResult:
        try:
            from polyfile.magic import MagicMatcher
            with open(path, "rb") as f:
                data = f.read()
            matches =  MagicMatcher.DEFAULT_INSTANCE.match(data)
            # only take the first mimetype of the match to prevent eventual false polyglots after normalize
            types = []
            if self._require_mimetype:
                types = [match.mimetypes[0] for match in matches if match.mimetypes] 
            else:
                for match in matches:
                    if match.mimetypes:
                        types.append(match.mimetypes[0])
                    else:
                        types.append("unknown")
            normalized = self._normalize(types)
            # BMP all monoglots it finds text/x-diff so remove it as it doesnt tell anything
            if "BMP" in normalized and "text/x-diff" in normalized:
                normalized = [t for t in normalized if t != "text/x-diff"]
            return self._make_result(normalized, types)
        except Exception as exception:
            return self._make_error(exception)