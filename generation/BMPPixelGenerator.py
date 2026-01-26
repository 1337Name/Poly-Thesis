"""BMP polyglot generator using pixel data embedding."""

import sys
import struct
import os
from .baseGenerator import BaseGenerator


class BMPPixelGenerator(BaseGenerator):
    """Embeds payload into BMP pixel data (semantic polyglot)."""
    def _get_name(self) -> str:
        return "BMPPixelPolyglotGenerator"

    def _implements_format(self) -> str:
        return "BMP"
    
    def generate(self, host: bytes, payload: bytes) -> bytes:
        """Embed payload into BMP pixel data at a fixed offset after the image data start."""
        payload_offset = 20
        bmp = host
        if len(bmp) < 30:
            #TODO use actual minimum header size?
            raise ValueError("File Too Small to be a BMP File")
        if  bmp[0:2] != b'BM':
            raise ValueError("Not a valid BMP File (Invalid Magic)")

        img_offset = struct.unpack('<I', bmp[10:14])[0]
        width = struct.unpack('<I', bmp[18:22])[0]
        length = struct.unpack('<I', bmp[22:26])[0]
        bitspp = struct.unpack('<H', bmp[28:30])[0] #bits per pixel 
        bytespp = bitspp // 8 # calc bytes per pixel
        imgSize = width*length*bytespp
        if(len(payload) + payload_offset > imgSize): 
            raise ValueError("payload size + offset greater than image size")
        offset = img_offset + payload_offset
        offset_end = offset + len(payload)
        bmp_array = bytearray(bmp) # mutable
        bmp_array[offset:offset_end] = payload
        return bytes(bmp_array)

if __name__ == "__main__":
    BMPPixelGenerator().main()