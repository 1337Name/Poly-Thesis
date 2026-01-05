import re
import sys 

def find_highest_obj_ID(PDF):
    #Copied from rimser thesis raw_pdf.py
    splitPDF = re.findall( b'(\d+[ \t]*\d+[ \t]*obj)', PDF) # split PDF into objects, modified so it match tab too
    max_num = -1
    for split in splitPDF:
        numbers = re.search(b'[0-9]*', split).group()
        if numbers:
            num = int(numbers.decode())
            if num > max_num:
                max_num = num
    return max_num

def find_byte_offset(PDF, content):
    search = re.split(b'(' + content + b')', PDF)[:1]
    offset = len(b''.join(search))
    return offset

    #Copied from rimser thesis raw_pdf.py
def create_xref(PDF):
    xref = b'\nxref\n'
    xref += b'0 '
    xref += str(find_highest_obj_ID(PDF) + 1).encode() + b'\n' # fixed this to correct format and size (size is index+1 if start from 0 and reversed order)
    xref += b'0000000000 65535 f\n'
    objDict = {}
    for objectM in re.findall(b'\d+[ \t\n]*\d+[ \t\n]*obj', PDF):
        objectID = int(re.findall(b'\d+[ \t\n]*', objectM)[0].strip())
        objDict[objectID] = str(find_byte_offset(PDF, objectM)).rjust(10, '0').encode() +b' 00000 n\n'
    sortedList = sorted(objDict.items())
    for key, value in sortedList:
        xref += value

    return xref

#copied from rimser thesis raw_pdf.py
#modified to take bytes not file and to take in a argument for root_ref already given
def create_trailer(PDF, root_ref=None):
    object_count = find_highest_obj_ID(PDF) - 1

    trailer = b'\ntrailer\n'
    trailer += b'<<\n'
    trailer += b'  /Size     ' + str(object_count).encode('ascii') + b'\n'
    if root_ref is None:
        root_ref = re.search(rb'/Root[ \t\n]*\d+[ \t\n]*\d+[ \t\n]*R', PDF).group()
    trailer += b'  ' + root_ref
    trailer += b'\n>>\n'

    return trailer


def parseDictSpan(pdf, start):
    #parse a dictionary from begin to end (begin should be before the first "<<")
    #have to do it like this because its cfg
    count = 0
    i = start
    while i < len(pdf):
        curr = pdf[i:i+2]
        if curr == b"<<":
            count += 1
            i += 2
        elif curr == b">>":
            count -= 1
            i+=2
            if count == 0:
                return i #reached end
        else:
            i += 1
    print("dict parsing fail reached end", file=sys.stderr)
    return None