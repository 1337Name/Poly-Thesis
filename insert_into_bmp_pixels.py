import sys
import struct
import os

if len(sys.argv) < 2:
    print("Error: No arguments provided.", file=sys.stderr)
    sys.exit(1)

filename = sys.argv[1]
split_fname = os.path.splitext(filename)
extension = split_fname[1]
root = split_fname[0]

payload = b"abc"

payload_offset = 20

with open(filename, "rb") as f:
    bmp = f.read()

if len(bmp) < 30:
    #TODO use actual minimum header size?
    print("Error: BMP has to be minimum 30 bytes (header data)", file=sys.stderr)
    sys.exit(1) 
if  bmp[0:2] != b'BM':
    print("Error: not a valid BMP file", file=sys.stderr)
    sys.exit(1)

img_offset = struct.unpack('<I', bmp[10:14])[0]
width = struct.unpack('<I', bmp[18:22])[0]
length = struct.unpack('<I', bmp[22:26])[0]

bitspp = struct.unpack('<H', bmp[28:30])[0] #bits per pixel 
bytespp = bitspp // 8 # calc bytes per pixel
imgSize = width*length*bytespp
if(len(payload) + offset > imgSize): 
    print("Error: payload size + offset greater than image size", file=sys.stderr)
    sys.exit(1)
if(len(payload) > imgSize // 100):
    print("Warning: payload takes up a significant part of the image")

offset = img_offset + payload_offset
offset_end = offset + len(payload)
bmp_array = bytearray(bmp) # mutable
bmp_array[offset:offset_end] = payload
output_filename = root + "_poly" + extension
with open(output_filename, "wb") as f:
    f.write(bmp_array)
print(f"Payload inserted at byte {offset}")
print(f"output a new file: {output_filename}")
