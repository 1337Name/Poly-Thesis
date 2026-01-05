import re
import sys
import struct
import os
from .baseGenerator import BaseGenerator
from .pdf_utils import find_highest_obj_ID, create_xref, create_trailer, parseDictSpan

class PDFInvisTextGenerator(BaseGenerator):
    """
    insert payload into pdf by adding a new font then adding a stream to a page and putting tr3 (invisible) the payload in the stream

    in hindsight might been easier to just find some font and use its name
    as its very spaghetti especialyl after testing on real corpus pdfs 
     there is stuff like linearized pdf with multiple xref
     some dont put space between then regex matching can be porblematic
    #b9iggest problem in general (every pdf) is that everything can be direct or indirect so blows up to lots of cases to handle
    t"""

    def _get_name(self) -> str:
        return "PDFInvisTextGenerator"

    def _implements_format(self) -> str:
        return "PDF"

    def generate(self, host: bytes, payload: bytes) -> bytes:
        return self._insertHiddenStream(host, payload)

    _font_inner_dict = b" << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"

    def _addToFontDict(self, pdf, page, res_dict, fontname):
        # look for font dict in resource dict and insert new font, very similar to addFontToPage TODO see if can generalize this recursion
        custom_font = b"/" + fontname + self._font_inner_dict
        match = re.search(b"/Font[ \t\n]*", res_dict)

        if not match:
            # no Font dict
            end = res_dict.rfind(b">>") #find end of dict (should already been parsed/no adjacent dicts on same level so just rfind)
            insert = b" /Font << " + custom_font + b" >>"
            new_res_dict = res_dict[:end] + insert + res_dict[end:]
            new_page = page.replace(res_dict, new_res_dict, 1)
            return pdf.replace(page, new_page, 1)

        # look if dictionary follows after /Font
        after_font = res_dict[match.end():]
        direct_dict_match = re.match(b"[ \t\n]*<<", after_font)

        if direct_dict_match:
            #  dictionary come direectly after 
            start = match.end()
            end = parseDictSpan(res_dict, start)
            font_dict = res_dict[start:end]
            new_font_dict = font_dict[:-2] + b" " + custom_font + b">>" #insert at end our font
            new_res_dict = res_dict[:start] + new_font_dict + res_dict[end:] #construct new resource dict
            new_page = page.replace(res_dict, new_res_dict, 1) # first replace in page to avoid replace in wrong place (there can be duplicate for diff page)
            return pdf.replace(page, new_page, 1) 

        #look if indirect ref come after
        indirect_match = re.match(b"[ \t\n]*(\d+)[ \t\n]*\d+[ \t\n]*R", after_font)
        if indirect_match:
            #search this whole font obj in pdf. 
            font_obj_match = re.search(
                b"\n[ \t]*" + indirect_match.group(1) + b"[ \t\n]*\d+[ \t\n]*obj.*?endobj", pdf, re.S)
            font_obj = font_obj_match.group(0) # we match with the obj number so no worry about replacing duplicate dictionaries later
            #extract font dict from obj
            dict_start = font_obj.find(b"<<")
            dict_end = parseDictSpan(font_obj, dict_start)
            font_dict = font_obj[dict_start:dict_end]
            new_font_dict = font_dict[:-2] + b" " + custom_font + b">>" #insert same as above
            return pdf.replace(font_dict, new_font_dict,1)        #replace in whole pdf 

        raise ValueError("Error: malformed Font dictionary")

    def _addFontToPage(self, pdf, page, fontname):
        # kind of complicated either it doesnt exist or it exist as indicrect or as direct reference
        custom_font = fontname + self._font_inner_dict
        match = re.search(b"/Resources[ \t\n]*", page)
        if not match:
            #res dont exist
            insert = b" /Resources << /Font << " + custom_font + b" >> >>"
            dict_end = page.rfind(b">>") # find end of dictionary
            new_page = page[:dict_end] + insert + page[dict_end:]
            return pdf.replace(page, new_page, 1)
        #look if it matches indirect after end of Resources regex match
        #make the obj num findable with .group(1)
        indirect_match = re.search(b"(\d+)[ \t\n]*\d+[ \t\n]*R", page[match.end():])
        if indirect_match:
            #match the whole object with the id found before
            res_obj = re.search(b"\n[ \t]*"+indirect_match.group(1)+b"[ \t\n]*\d+[ \t\n]*obj.*?endobj", pdf, re.S)
            if res_obj:
                res_obj_bytes = res_obj.group(0)
                #extract res dict from res obj
                dict_start = res_obj_bytes.find(b"<<")
                dict_end = parseDictSpan(res_obj_bytes, dict_start)
                res_dict = res_obj_bytes[dict_start:dict_end]
                return self._addToFontDict(pdf, res_obj_bytes, res_dict, fontname)

        # direct ref
        start = match.end() # start of obj dict
        end = parseDictSpan(page, start)
        res_dict = page[start:end]
        return self._addToFontDict(pdf, page, res_dict, fontname)

    def _findPageObject(self, pdf):
        #find the first page object in the pdf (not necessarily the first page)
        # ? important so it only match to the first occurence, re.S so we can go across nl's
        # last match until endobj not >> else we match any >> inside the obj like a font dict
        # iter over every obj now because regex for page object directly was error prone
        for obj_match in re.finditer(rb"(\d+ \d+ obj.*?endobj)", pdf, re.S):
            #we have to parse both header and footer
            #it seems like in PDF /Type/Page its either in beginning or end
            obj = obj_match.group(0)
            dict_start = obj.find(b'<<')
            if dict_start == -1:
                continue
            dict_end = parseDictSpan(obj, dict_start)
            if dict_end == -1:
                continue
            #Find if there is a nested dict
            begin_nested = obj.find(b'<<', dict_start+2)
            #Find last nested dict (dont parseDictSpan we WANT to skip same-level nested)
            end_nested = obj.rfind(b'>>', dict_start, dict_end-2)
            # get header and footer with pos we parsed
            if begin_nested != -1 and begin_nested < dict_end: #2nd is sanity check
                header = obj[dict_start:begin_nested]
            else:
                #theres no nested
                header = obj[dict_start:dict_end]
            if end_nested != -1: #we find a nested dict end
                footer = obj[end_nested+2:dict_end]
            else:
                #theres no nested dict or its corrupt
                footer = b''
            ## search for /Type{0..*(space,tabetc)}/Page{\s or / or >> allwed} so it cant match Pages or sth
            if re.search(rb'/Type\s*/Page(\s|/|>>)', header) or re.search(rb'/Type\s*/Page(\s|/|>>)', footer):
                return obj
        return None #no Page obj found

    def _insertHiddenStream(self, pdf, content):
        fontname = b"Font124573" #no collision
        fontname_str = fontname.decode('ascii')
        old_max_obj_id = find_highest_obj_ID(pdf)
        max_obj_id = old_max_obj_id+1
        stream = f"BT /{fontname_str} 24 Tf 3 Tr 0 0 Td ({content.decode('ascii')}) Tj ET"
        stream_bytes = stream.encode('ascii')
        stream_object = f"{max_obj_id} 0 obj\n<< /Length {len(stream_bytes)} >>\nstream\n{stream}\nendstream\nendobj\n".encode('ascii')
        stream_object_ref = f"{max_obj_id} 0 R".encode()
        page = self._findPageObject(pdf)
        if not page:
            raise ValueError("Error: could not find any page in PDF (might be parser issue rather than of pdf)")

        # sanity check: avoids injecting into wrong places and making a corrupt PDF   
        #/Contents and /Resouces not required by standard (could be empty page) so could delete this but its might worsen correctness                      
        if not (b'/Contents' in page or b'/Resources' in page):
            raise ValueError("Error: weird Page object found does not contain either /Contents or /Resources")
        pdf = self._addFontToPage(pdf, page, fontname)
        # search again to sync
        page = self._findPageObject(pdf)
        if not page: #should not really happen
            raise ValueError("Error: could not find any page in PDF (might be parser issue rather than of pdf)")
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
                    raise ValueError("Error: could not match any obj ref for Contents")

        #  need to handle xref/trailer
        # get root element now because later pdf gets cut
        root = re.search(rb'/Root[ \t\n]*\d+[ \t\n]*\d+[ \t\n]*R', pdf)
        if not root:
            raise ValueError("Error: no /Root in pdf")
        root_bytes = root.group()
        #look for normal xref keyword
        xref_match = re.search(rb'[\r\n]xref[\r\n]', pdf)
        if xref_match:
            #normal case not linearized just cut off and rebuilt at end
            pdf = pdf[:xref_match.start()+1]  #else its off by 1 (we match 1 before)
            pdf = pdf + stream_object       # add new object
            xref = create_xref(pdf)         
            trailer = create_trailer(pdf, root_bytes) # build new trailer with prev saved root
            xref_pos = str(len(pdf) + 1).encode()                  # again offset 1 byte to align 
            pdf = pdf + xref + trailer
            pdf = pdf + b"startxref\n" + xref_pos + b"\n%%EOF"
        else:
            # no normal xref probably linearized pdf
            # 2 options to do 
            # be safe and Raise error
            #raise ValueError("Error: linearized PDF / xref stream is not supported in this generator")
            #just inject content as xref issues do not break pdf viewers
            startxref_match = re.search(rb'[\r\n]startxref[\r\n]', pdf)
            if startxref_match:
                insert_pos = startxref_match.start()+1
                pdf = pdf[:insert_pos] + stream_object + b"\n" + pdf[insert_pos:]
            else:
                raise ValueError("Error: found no xref or startxref")

        return pdf

if __name__ == "__main__":
    PDFInvisTextGenerator().main()