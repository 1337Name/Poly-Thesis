
import zlib
import struct
from pathlib import Path
from .baseGenerator import BaseGenerator
import png
import sys


class PNGPixelGenerator(BaseGenerator):
    _compression_method = zlib.Z_NO_COMPRESSION
    def _get_name(self) -> str:
        return "PNGPixelGenerator"

    def _implements_format(self) -> str:
        return "PNG"

    def generate(self, host: bytes, payload: bytes) -> bytes:
        
        reader = png.Reader(bytes=host)
        width, height, pixels, metadata = reader.asRGB()
        pixels = list(pixels)
        nRow = 0
        row = pixels[nRow]
        if len(payload) > len(row):
            raise ValueError("Error: payload does not fit in row")
        row[0:len(payload)] = payload
        pixels[nRow] = row
        bdata = bytearray()
        for row in pixels: 
            bdata.append(0) #every row first byte signal the filtering applied, 0 = none
            bdata.extend(row)
        compressed = zlib.compress(bdata, level=self._compression_method)
        idat_type = b"IDAT"
        idat_chunk = self._create_chunk(idat_type, compressed)

        #https://www.w3.org/TR/PNG-Chunks.html
        height = len(pixels)
        width = int(len(pixels[0])/3)
        bit_depth = 8
        color_type = 2 #only color used
        compression_method = 0 #zlib (note it doesnt specify which zlib level just zlib)
        filter_method = 0
        interlace_method = 0
        ihdr_data = struct.pack('>IIBBBBB', width, height, bit_depth, color_type, compression_method, filter_method, interlace_method)
        ihdr_type = b"IHDR"
        ihdr_chunk = self._create_chunk(ihdr_type, ihdr_data)
        iend_chunk = self._create_chunk(b'IEND', b'')
        magic = b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A'
        full = magic + ihdr_chunk + idat_chunk + iend_chunk
        return full


    def _create_chunk(self, chunk_type, chunk_data):
        #https://www.w3.org/TR/png/#5Chunk-layout
        #duplicate with PNGICC but for a short method dont have to make a abstraction I think.  
        length = len(chunk_data)
        chunk = struct.pack('>I', length)
        chunk += chunk_type
        chunk += chunk_data
        crc = zlib.crc32(chunk_type + chunk_data)
        chunk += struct.pack('>I', crc)
        return chunk

if __name__ == "__main__":
    PNGPixelGenerator().main()