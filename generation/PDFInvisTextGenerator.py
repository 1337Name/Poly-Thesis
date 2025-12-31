import re
import sys
import struct
import os
from .baseGenerator import BaseGenerator
from .pdf_utils import find_highest_obj_ID, create_xref, create_trailer, parse_dict_span

class PDFInvisTextGenerator(BaseGenerator):
    def _get_name(self) -> str:
        return "PDFInvisTextGenerator"

    def _implements_format(self) -> str:
        return "PDF"

    def generate(self, host: bytes, payload: bytes) -> bytes:
        return self._insertHiddenStream(host, payload)



    _font_inner_dict = b" << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"

    def _addToFontDict(self, pdf, res_dict, fontname):
        # very similar to addResource TODO see if can generalize this recursion
        custom_font = fontname + self._font_inner_dict
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
            end = parse_dict_span(res_dict, start)
            font_dict = res_dict[start:end]
            new_font_dict = font_dict[:-2] + b" " + custom_font + ">>"

            # replace everythin
            new_res_dict = res_dict.replace(font_dict, new_font_dict)
            return pdf.replace(res_dict, new_res_dict)

    def _addFontToPage(self, pdf, page, fontname):
        # kind of complicated either it doesnt exist or it exist as indicrect or as direct reference
        custom_font = fontname + self._font_inner_dict
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
            return self._addToFontDict(pdf, res_dict, fontname)
        else:
            #direct reference: challenge is to extract the obj dict
            start = match.end() # start of obj dict
            end = parse_dict_span(page, start)
            res_dict = page[start:end]
            return self._addToFontDict(pdf, res_dict, fontname)

    def _insertHiddenStream(self, pdf, content):
        fontname = b"Font124573" #no collision
        old_max_obj_id = find_highest_obj_ID(pdf)
        max_obj_id = old_max_obj_id+1
        stream = f"BT /{fontname} 24 Tf 3 Tr 0 0 Td ({content.decode('ascii')}) Tj ET".encode('ascii')
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
        pdf = self._addFontToPage(pdf, page, fontname)
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
                    raise ValueError("Error: could not match Contents")

        # now its time to actually add the stream
        #find xref (marks end of content typically)
        last_endobj = pdf.rfind(b"endobj")
        pos = last_endobj + len(b"endobj")
        pdf = pdf[:pos]  + b"\n" + stream_object +b"\n"
        xref = create_xref(pdf)
        trailer = create_trailer(pdf)
        pdf = pdf + xref + trailer
        pdf = pdf + b"startxref\n" + str(len(pdf)).encode() + b"\n%%EOF"
        return pdf 