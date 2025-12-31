import struct
from .baseGenerator import BaseGenerator
from .jpg_utils import inject_segment

class JPEGAPP0Generator(BaseGenerator):
    def _get_name(self) -> str:
        return "JPEGAPP0Generator"

    def _implements_format(self) -> str:
        return "JPEG"
    
    def generate(self, host: bytes, payload: bytes) -> bytes:
        if len(host)<2 or host[0:2] != b'\xFF\xD8':
            raise ValueError("Error: Is not a valid JPEG")
        app0 = self._create_app0(payload)
        new_jpg, offset = inject_segment(host, app0, "APP0")
        return new_jpg

    def _create_app0(self, payload):
        max_size = 255*3
        if(len(payload) > max_size):
            raise ValueError(f"Error: maximum supported payload is {max_size}")
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





