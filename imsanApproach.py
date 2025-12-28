from PIL import Image
import os
import sys

if len(sys.argv) < 2:
    print("Error: No arguments provided.", file=sys.stderr)
    sys.exit(1)

filename = sys.argv[1]
split_fname = os.path.splitext(filename)
extension = split_fname[1]
root = split_fname[0]

img = Image.open(filename)
pildata = img.getdata()
stripped = Image.new(img.mode, img.size)
stripped.putdata(list(pildata))
stripped.save(f"{root}_stripped{extension}") 
