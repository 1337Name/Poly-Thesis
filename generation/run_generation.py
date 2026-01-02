from pathlib import Path
from dataclasses import dataclass
from .generation import PolyDataset, PolyglotKind, launch
from .baseGenerator import BaseGenerator
from .BMPPixelGenerator import BMPPixelGenerator
from .PNGPixelGenerator import PNGPixelGenerator
from .PNGICCGenerator import PNGICCGenerator
from .JPEGPAPP0Generator import JPEGAPP0Generator
from .PDFInvisTextGenerator import PDFInvisTextGenerator

BASE_PATH = Path(__file__).parent.parent
SAMPLES_DIR = BASE_PATH / "samples"
OUTPUT_DIR = BASE_PATH / "generated"

COVERT_ALLOWED = ["PHP", "JS"]
@dataclass
class GeneratorConfig:
    generator: BaseGenerator
    kind: PolyglotKind
    #allowed_covert: List[str] TODO implement if wanted to test maybe zip or sth that dont work i.e need blacklist/whitelist approach

#PUT HERE IF YOU WANT TO ADD A NEW GENERATOR
ALL_GENERATORS: dict[str, list[GeneratorConfig]] = {
    "BMP": [
        GeneratorConfig(BMPPixelGenerator(), PolyglotKind.SEMANTIC),
    ],
    "PNG": [
        GeneratorConfig(PNGPixelGenerator(), PolyglotKind.SEMANTIC),
        GeneratorConfig(PNGICCGenerator(), PolyglotKind.SEMANTIC),
    ],
    "JPEG": [
        #GeneratorConfig(JpgProgressiveGenerator(), PolyglotKind.SEMANTIC), TODO
        GeneratorConfig(JPEGAPP0Generator(), PolyglotKind.PARASITE)
    ],
    "PDF": [
        GeneratorConfig(PDFInvisTextGenerator(), PolyglotKind.SEMANTIC),
    ],
}

def get_files(fmt: str) -> list[Path]:
    files = []
    fmt = fmt.lower()
    fmt_dir = SAMPLES_DIR / fmt
    exts = ["*.jpg", "*.jpeg"] if fmt == "jpeg" else [f"*.{fmt}"] #ugly but simple enough
    for ext in exts:
        files.extend(fmt_dir.glob(ext))
    return files

def run() -> PolyDataset:
    polyDataset = PolyDataset.create()
    for overt_fmt, cfgs in ALL_GENERATORS.items():
        overts = get_files(overt_fmt)
        for covert_fmt in COVERT_ALLOWED:
            coverts = get_files(covert_fmt)
            for cfg in cfgs:
                curr_gen = cfg.generator
                print("Running generator: " + curr_gen._get_name() + " on overt: " + overt_fmt + ", covert: " + covert_fmt)
                #actualy running now
                for overt in overts:
                    for covert in coverts:
                        out_path = OUTPUT_DIR / curr_gen._get_name() / f"{overt.stem}_{covert.stem}.{overt_fmt.lower()}"
                        res = launch(curr_gen, overt, covert, out_path, cfg.kind, covert_fmt.upper())
                        polyDataset.add(res)
                        if res.error:
                            print("Error: " + res.error)
    return polyDataset

if __name__ == "__main__":
    dataset=run()
    dataset.save(OUTPUT_DIR / "run.json")
    print("finished generation")