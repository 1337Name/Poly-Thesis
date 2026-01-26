"""PNG polyglot generator using ICC profile embedding."""

import zlib
import struct
from pathlib import Path
from .baseGenerator import BaseGenerator


class PNGICCGenerator(BaseGenerator):
    """Embeds payload into PNG via iCCP chunk with modified ICC profile (parasite polyglot)."""
    _compression_method = zlib.Z_NO_COMPRESSION
    def _get_name(self) -> str:
        return "PNGICCGenerator"

    def _implements_format(self) -> str:
        return "PNG"

    def generate(self, host: bytes, payload: bytes) -> bytes:
        """Inject payload into ICC profile and insert as iCCP chunk after IHDR."""
        parent = Path(__file__).parent
        relative = "data/sRGB2014.icc"
        icc_path = (parent / relative).resolve()
        icc = icc_path.read_bytes()
        icc = self._inject_into_icc(icc, payload)

        #uncompressed deflate block cant be bigger than that
        if len(icc) >65536:
            raise ValueError(f"ICC profile + payload is {len(icc)} bytes, maximum is 65536")

        iccp = self._create_iccp_chunk("sRGB", icc)

        chunks = self._parse_chunks(host)
        host = bytearray(host)
        existing_iccp = False
        for chunk_type, start, end in chunks:
            if chunk_type == b"iCCP":
                del host[start:end] #insert at start for detection so magika can see it
                #host[start:end] = iccp
                #existing_iccp = True
                break
        if not existing_iccp:
            #insert after IHDR sicne iccp doesnt exist yet
            for chunk_type, start, end in chunks:
                if chunk_type == b"IHDR": # NEVER insert after any chunk != IHDR IF deleting before (now offsets wrong)
                    host[end:end] = iccp
                    existing_iccp = True
                    break

        return bytes(host)


    def _inject_into_icc(self, icc, payload):
        """Add payload as 'junk' tag in ICC profile, shifting existing tag offsets."""
        icc = bytearray(icc)
        tag_count = struct.unpack('>I', icc[128:132])[0]
        # OLD end value
        tag_table_end = 132 + (tag_count * 12)
        #need to shift all contents after the entry table as we add new entry 
        for i in range(tag_count):
            offset_pos = 132 + (i * 12) + 4  # offset 4 = position offset 
            old_offset = struct.unpack('>I', icc[offset_pos:offset_pos+4])[0]
            new_offset = old_offset + 12
            icc[offset_pos:offset_pos+4] = struct.pack('>I', new_offset)
        # payload after old icc size + new table entry size
        payload_offset = len(icc) + 12
        # create new entry tag
        new_tag = b'junk' + struct.pack('>II', payload_offset, len(payload)) 
        # add new payload and set fields
        icc = icc[:tag_table_end] + new_tag + icc[tag_table_end:] + payload  
        icc[128:132] = struct.pack('>I', tag_count + 1)   
        icc[0:4] = struct.pack('>I', len(icc)) 
        return bytes(icc)

    def _create_iccp_chunk(self, profile_name, icc_profile):
        """Create iCCP chunk with null-terminated name and zlib-compressed ICC data."""
        chunk_data = profile_name.encode('latin-1') + b'\x00'
        chunk_data += b'\x00'  # compression method = zlib
        chunk_data += zlib.compress(icc_profile, level=self._compression_method)
        return self._create_chunk(b'iCCP', chunk_data)


    def _parse_chunks(self, data : bytes) -> list:
        """Parse PNG into list of (chunk_type, start_pos, end_pos) tuples."""
        chunks = []
        pos = 8 #after magic
        while pos < len(data):
            chunk_len = struct.unpack(">I", data[pos:pos+4])[0]
            chunk_type = data[pos+4:pos+8]
            chunk_start = pos
            chunk_end = chunk_start + chunk_len + 4 + 4 +4 # len + type + len field + crc
            chunks.append((chunk_type, chunk_start, chunk_end))
            pos = chunk_end
        return chunks

    def _create_chunk(self, chunk_type, chunk_data):
        """Build a PNG chunk: length (4B) + type (4B) + data + CRC32 (4B)."""
        length = len(chunk_data)
        chunk = struct.pack('>I', length)
        chunk += chunk_type
        chunk += chunk_data
        crc = zlib.crc32(chunk_type + chunk_data)
        chunk += struct.pack('>I', crc)
        return chunk

if __name__ == "__main__":
    PNGICCGenerator().main()