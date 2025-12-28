import os
import sys
import re

if len(sys.argv) < 3:
    print("Error: No arguments provided.", file=sys.stderr)
    sys.exit(1)

filename = sys.argv[1]
parasite = sys.argv[2]

split_fname = os.path.splitext(filename)
extension = split_fname[1]
root = split_fname[0]

#TODO tried fitz dont work do manual 


objregex = b'(\d+[ \t]*\d+[ \t]*obj)' # modified so it also matches tab too


def find_highest_obj_ID(PDF):
    #Copied from rimser thesis raw_pdf.py
    splitPDF = re.findall(objregex, PDF) # split PDF into objects
    max_num = -1
    for split in splitPDF:
        numbers = re.search(b'[0-9]*', split).group()
        if numbers:
            num = int(numbers.decode())
            if num > max_num:
                max_num = num
    return max_num

def create_xref(PDF):
    #Copied from rimser thesis raw_pdf.py
    xref = b'\nxref\n'
    xref += str(find_highest_obj_ID(PDF)).encode() + b' 0\n'
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
#modified to take bytes not file
def create_trailer(PDF):
    object_count = find_highest_obj_ID(PDF) - 1

    trailer = b'\ntrailer\n'
    trailer += b'<<\n'
    trailer += b'  /Size     ' + str(object_count).encode('ascii') + b'\n'
    trailer += b'  ' + re.search(b'/Root[ \t\n]*\d+[ \t\n]*\d+[ \t\n]*R', PDF).group()
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

font_inner_dict = b" << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"

def addToFontDict(pdf, res_dict, fontname):
    # very similar to addResource TODO see if can generalize this recursion
    custom_font = fontname + font_inner_dict
    match = re.search(b"/Font[ \t\n]*", res_dict)

    if not match:
        # no Font dict
        end = res_dict.rfind(b">>") #find end of dict
        insert = b" /Font << " + custom_font + b" >>"
        new_res_dict = res_dict[:end] + insert + res_dict[end:]
        return pdf.replace(res_dict, new_res_dict)

    # check if indirect 
    indirect_match = re.search(b"(\d+)[ \t\n]*\d+[ \t\n]*R", res_dict[match.end():])

    if indirect_match:
        font_obj_match = re.search(
            b"\n[ \t]*" + indirect_match.group(1) + b"[ \t\n]*\d+[ \t\n]*obj.*?endobj", pdf, re.S)
        font_obj = font_obj_match.group(0)
        #extract dict
        font_dict = font_obj[font_obj.find(b"<<"):font_obj.rfind(b">>")] # dont do +2 now because we need to cut before the >>
        new_font_dict = font_dict + b" " + custom_font + b">>" 
        # Replace in PDF
        return pdf.replace(font_dict, new_font_dict)

    else:
        # direct ref 
        start = match.end()
        end = parseDictSpan(res_dict, start)
        font_dict = res_dict[start:end]
        new_font_dict = font_dict[:-2] + b" " + custom_font + ">>"

        # replace everythin
        new_res_dict = res_dict.replace(font_dict, new_font_dict)
        return pdf.replace(res_dict, new_res_dict)

def addFontToPage(pdf, page, fontname):
    # kind of complicated either it doesnt exist or it exist as indicrect or as direct reference
    custom_font = fontname + font_inner_dict
    match = re.search(b"/Resources[ \t\n]*", page)
    if not match:
        #res dont exist
        insert = b" << /Resources << /Font << " + custom_font + b" >> >>"
        dict_end = page.rfind(b">>") # find end of dictionary
        new_page = page[:dict_end] + insert + page[dict_end:]
        return pdf.replace(page, new_page)
    #look if it matches indirect after end of Resources regex match
    #make the obj num findable with .group(1)
    indirect_match = re.search(b"(\d+)[ \t\n]*\d+[ \t\n]*R", page[match.end():])
    if indirect_match:
        #we have indirect reference to the Resources = they are its own obj
        #match the whole object with the id found before
        res_obj = re.search(b"\n[ \t]*"+indirect_match.group(1)+b"[ \t\n]*\d+[ \t\n]*obj.*?endobj", pdf, re.S)
        #again really res_dict can reference both direct or indirect so pass to function
        # to pass the same from direct and indirect case -> use common resource dict
        res_dict = res_obj[res_obj.find(b"<<"):res_obj.rfind(b">>"+2)] #get the biggest dict = res dict
        return addToFontDict(pdf, res_dict, fontname)
    else:
        #direct reference: challenge is to extract the obj dict
        start = match.end() # start of obj dict
        end = parseDictSpan(page, start)
        res_dict = page[start:end]
        return addToFontDict(pdf, res_dict, fontname)

def insertHiddenStream(inFile, outFile, content):
    fontname = b"Font124573" #no collision
    with open(inFile, 'rb') as f:
        pdf = f.read()

    old_max_obj_id = find_highest_obj_ID(pdf)
    max_obj_id = old_max_obj_id+1
    stream = f"BT /{fontname} 24 Tf 3 Tr 0 0 Td ({content}) Tj ET".encode('ascii')
    stream_object = f"""
{max_obj_id} 0 obj
<< /Length {len(stream)} >>
stream
{stream}
endstream
endobj
""".encode('ascii')
    stream_object_ref = f"{max_obj_id} 0 R".encode()
    #find the first page object in the pdf (not necessarily the first page)
    # ? important so it only match to the first occurence
    # last match until endobj not >> else we match any >> inside the obj like a font dict
    p_match = re.search(b"<<.*?/Type[ \t\n]*/Page.*?endobj",pdf,re.S) #re.S so the . in Page. matches \n
    page = p_match.group(0)
    pdf = addFontToPage(pdf, page, fontname)
    # search again to sync
    p_match = re.search(b"<<.*?/Type[ \t\n]*/Page.*?endobj",pdf,re.S) #re.S so the . in Page. matches \n
    page = p_match.group(0)
    contents_match = re.search(b".*?/Contents[ \t\n]*", page, re.S)
    if not contents_match:
        # there is no contents
        insert = b' /Contents ' + stream_object_ref
        end = page.rfind(b">>") # find end
        new_page = page[:end] + insert + page[end:]
        pdf = pdf.replace(page, new_page)
    else:
        # now we need check is it just one ref or array..
        rest = page[contents_match.end():]
        arr_match = re.match(b"\[.*?\]", rest, re.S) # match from begin
        if arr_match:
            pos = contents_match.end() + arr_match.end() -1 #pos before ]
            new_page = page[:pos] + b" " + stream_object_ref + page[pos:]
            pdf = pdf.replace(page, new_page)
        else:
            # no array we need create array and insert now the old and our ref
            ref_match = re.match(b"\d+[ \t\n]*\d+[ \t\n]*R", rest)
           
            if ref_match:
                old_content_ref = ref_match.group(0)
                start = contents_match.end()
                end = start + ref_match.end()
                new_contents = b"[" + old_content_ref + b" " + stream_object_ref +b"]"
                new_page = page[:start] + new_contents + page[end:]
                pdf = pdf.replace(page, new_page)
            else:
                print("error could not match Contents", file=sys.stderr)
                sys.exit(1)

    # now its time to actually add the stream
    #find xref (marks end of content typically)
    last_endobj = pdf.rfind(b"endobj")
    pos = last_endobj + len(b"endobj")
    pdf = pdf[:pos]  + b"\n" + stream_object +b"\n"
    xref = create_xref(pdf)
    trailer = create_trailer(pdf)
    pdf = pdf + xref + trailer
    pdf = pdf + b"startxref\n" + str(len(pdf)).encode() + b"\n%%EOFd"
    # Write the modified PDF to output file
    with open(outFile, 'wb') as f:
        f.write(pdf)
