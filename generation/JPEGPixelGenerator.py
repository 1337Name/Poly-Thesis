"""JPEG polyglot generator using progressive scan data embedding."""

import subprocess
from .baseGenerator import BaseGenerator
import tempfile


class JPEGPixelGenerator(BaseGenerator):
    """Embeds payload into progressive JPEG scan data (semantic polyglot). Requires ImageMagick."""

    def _get_name(self) -> str:
        return "JPEGPixelGenerator"

    def _implements_format(self) -> str:
        return "JPEG"
    
    def generate(self, host: bytes, payload: bytes) -> bytes:
        """Convert to progressive JPEG and embed payload before EOI marker."""
        if len(host)<2 or host[0:2] != b'\xFF\xD8':
            raise ValueError("Error: Is not a valid JPEG")
        if b"\xFF" in payload:
            raise ValueError("Error: payload should not contain any FF bytes")
        prog = self._to_progressive(host)
        eoi = prog.rfind(b"\xFF\xD9")
        if eoi == -1:
            eoi = len(prog)-1 #just say at end
        safety_distance = 50
        last_sos = prog.rfind(b'\xFF\xDA')
        if last_sos == -1:
            raise ValueError("Error: Could not find any SOS marker")
        header_size = 20 # estimate
        if eoi-safety_distance-len(payload) <= last_sos+header_size: #with safety distance it should be safe now to inject and not break 
            raise ValueError("Error: Payload doesnt fit, overwrites last Start of Scan")
        
        end = eoi-safety_distance
        start = end-len(payload)
        prog = bytearray(prog)
        prog[start:end] = payload
        return bytes(prog)

    def _to_progressive(self, host : bytes) -> bytes:
        """Convert JPEG to progressive using ImageMagick."""
        with tempfile.NamedTemporaryFile(delete=True) as tmp_in, tempfile.NamedTemporaryFile(delete=True) as tmp_out:
            tmp_in.write(host)
            tmp_in.flush()
            subprocess.run(["convert", tmp_in.name, "-interlace", "JPEG", tmp_out.name], check=True) #create progressive jpeg + raise error if error in subprc
            result = tmp_out.read()
        return result

if __name__ == "__main__":
    JPEGPixelGenerator().main()