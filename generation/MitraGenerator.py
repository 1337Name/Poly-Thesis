import subprocess
import tempfile
from pathlib import Path
from .baseGenerator import BaseGenerator

class MitraGenerator(BaseGenerator):
    MITRA_PATH = "" #TODO
    def __init__(self, overt, covert):
        self._overt = overt
        self._covert = covert

    def _get_name(self) -> str:
        return f"MitraGenerator_{self._overt}_{self._covert}"

    def _implements_format(self) -> str:
        return self.overt.upper()

    def generate(self, host: bytes, payload: bytes) -> bytes:
        