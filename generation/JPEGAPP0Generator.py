"""JPEG polyglot generator using APP0 segment embedding."""

import struct
from .baseGenerator import BaseGenerator
from .jpg_utils import inject_segment
import math


class JPEGAPP0Generator(BaseGenerator):
    """Embeds payload into JPEG APP0 (JFIF) segment as thumbnail data (parasite polyglot)."""
    def _get_name(self) -> str:
        return "JPEGAPP0Generator"

    def _implements_format(self) -> str:
        return "JPEG"
    
    def generate(self, host: bytes, payload: bytes) -> bytes:
        """Embed payload in APP0 thumbnail and inject after SOI marker."""
        if len(host)<2 or host[0:2] != b'\xFF\xD8':
            raise ValueError("Error: Is not a valid JPEG")
        app0 = self._create_app0(payload)
        new_jpg, offset = inject_segment(host, app0, "APP0", 2)
        return new_jpg

    def _create_app0(self, payload):
        """Build JFIF APP0 segment with payload as RGB thumbnail data (max 65KB)."""
        mod3 = len(payload) % 3
        if mod3 != 0:
            payload = payload + (b'\x00' * (3-mod3))
        # probably easiest instead of thign i sjust pad it out 
        pixels = len(payload) // 3
        width = 255
        height = math.ceil(pixels / width) 
        totalsize = width * height * 3 
        if totalsize > 65000:
            raise ValueError(f"Jpeg segment cannot be more than 65KB")
        payload = payload + b"\x00" * (totalsize-len(payload))

        magic= b'JFIF\x00'  # jfif magic
        version = b'\x01\x02'  # 1.2
        density_units = b'\x00'  # no units
        x_density = b'\x00\x01'  
        y_density = b'\x00\x01' 
        enc_width = struct.pack('B', width)
        enc_height = struct.pack('B', height)

        content = magic + version + density_units + x_density + y_density + enc_width + enc_height + payload
        length = struct.pack('>H',len(content) + 2) #len field includes itself excludes marker
        marker = b'\xFF\xE0'
        app0 = marker + length + content
        return app0


if __name__ == "__main__":
    JPEGAPP0Generator().main()


