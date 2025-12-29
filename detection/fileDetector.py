from .baseDetector import BaseDetector
from .types import DetectionResult
from pathlib import Path
from typing import List
import subprocess

class FileDetector(BaseDetector):

    def detect(self, filepath: Path) -> DetectionResult:
        try:
            raw_out = self._run(filepath)
            types = self._parse(raw_out)
            normalized = self._normalize(types)

            is_polyglot = len(normalized_type) > 1 #if 2 different detected its polyglot

            return DetectionResult(
                tool = "file",
                detected_types = normalized,
                is_polyglot = is_polyglot,
                raw_output = raw_out,
                confidence_scores = NNone,
                error = None
            )
        #some exception occured for error handling we just make it empty but give the error
        #bercause we will put this all in the end in json so its good to know why it failed there not just in the console when running
        except Exception as exception:
            return DetectionResult(
                tool = "file",
                detected_types = set(),
                is_polyglot = False,
                raw_output = "",
                confidence_scores = None,
                error = str(exception)
            )

    def _run(self, filepath: Path) -> str:
        fileRes = subprocess.run(["file", "--keep-going","--mime-type", str(filepath)],
        capture_output=True,
        text=True,#output in text mode not byte
        timeout = 20 #to be safe
        )
        return fileRes.stdout

    def _parse(self, output : str) -> List[str]:
        #07-06.pdf: application/pdf\012- application/octet-stream
        #insert_jpg_metadata.py: text/html\012- text/plain
        types = []
        content = output.split(":", 1)[1].strip() # remove filename
        splits = content.split("\\012-")
        for mime in splits:
            mime = mime.strip()
            if mime and mime not in ["application/octet-stream", "text/plain"]: #these seem to match for any binary/text data
                subtype = mime.split("/")[1] #mime format is type/subtype
                types.append(subtype)
        return types