"""
Polyglot file generation framework.

Provides generators for creating polyglot files that are valid in multiple
formats simultaneously. Each generator implements a specific embedding technique
for a particular host format (BMP, PNG, JPEG, PDF).

The package implements a plugin architecture where each generator extends
:class:`BaseGenerator` and implements a specific polyglot creation technique.

Classes:
    BMPPixelGenerator: Embeds payload into BMP pixel data (semantic polyglot).
    PNGPixelGenerator: Embeds payload into PNG pixel data (semantic polyglot).
    PNGICCGenerator: Embeds payload into PNG via iCCP chunk (parasite polyglot).
    JPEGPixelGenerator: Embeds payload into JPEG pixel data (semantic polyglot).
    JPEGAPP0Generator: Embeds payload into JPEG APP0 segment (parasite polyglot).
    PDFInvisTextGenerator: Embeds payload as invisible text in PDF (semantic polyglot).

Functions:
    run: Execute all generators on sample files and return the dataset.

Example:
    >>> from generation import PNGICCGenerator
    >>> generator = PNGICCGenerator()
    >>> polyglot = generator.generate(host_bytes, payload_bytes)
"""

from .BMPPixelGenerator import BMPPixelGenerator
from .PNGICCGenerator import PNGICCGenerator
from .PNGPixelGenerator import PNGPixelGenerator
from .PDFInvisTextGenerator import PDFInvisTextGenerator
from .JPEGAPP0Generator import JPEGAPP0Generator
from .JPEGPixelGenerator import JPEGPixelGenerator
from .run_generation import run

__all__ = [
    "BMPPixelGenerator",
    "PNGICCGenerator",
    "PNGPixelGenerator",
    "PDFInvisTextGenerator",
    "JPEGAPP0Generator",
    "JPEGPixelGenerator",
    "run",
]
