"""Utility functions for parsing and manipulating JPEG file structure."""

import sys
import struct


def parse_jpg_segments(jpg):
    """Parse JPEG markers and return dict of {name: {pos, length}} for APP0/APP1/SOS."""
    segments = {}
    pos = 2  # Skip SOI

    while pos < len(jpg) - 1:
        # All markers have form 0xFFXX
        if jpg[pos] != 0xFF:
            raise ValueError(f"Error: expect 0xffXX at offset {pos} but found {jpg[pos:pos+1].hex()}")
        marker = jpg[pos + 1]
        #0x00/0xFF is FF as literal data but we dont parse for FF anyway but jump through the file using length so we did something wrong
        if marker in [0x00, 0xFF]:
            raise ValueError(f"Error parsing ended up in data not a segment beginning")
        if marker == 0xD9: #EOI
                return segments
        # no length field 
        if marker == 0x01 or marker in range(0xD0, 0xD9):
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

def inject_segment(old_jpg, segment, segment_name, offset):
    """Delete existing segment (if any) and insert new one at offset. Returns (bytes, offset)."""
    segments = parse_jpg_segments(old_jpg)
    existing_segment = segments.get(segment_name, None)
    result = bytearray(old_jpg)

    if existing_segment:
        # replace
        pos = existing_segment['pos']
        old_len = existing_segment['length']
        del result[pos : pos + old_len] # we want it at early pos else its bad/unfair for detection as magika only take first 1024 end 1024
        #result[pos:pos+old_len] = segment #bytearray resize
        #segment_offset = pos
    result[offset:offset] = segment
    segment_offset = offset

    return bytes(result), segment_offset