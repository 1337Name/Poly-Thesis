"""
Main generation runner for creating polyglot test files.

Runs all configured generators on sample files to create a dataset of polyglots
for detection evaluation. Also includes Mitra tool integration as baseline.
"""

import argparse
from pathlib import Path
from dataclasses import dataclass
from .generation import PolyDataset, PolyglotKind, launch
from .baseGenerator import BaseGenerator
from .BMPPixelGenerator import BMPPixelGenerator
from .PNGPixelGenerator import PNGPixelGenerator
from .PNGICCGenerator import PNGICCGenerator
from .JPEGAPP0Generator import JPEGAPP0Generator
from .JPEGPixelGenerator import JPEGPixelGenerator
from .PDFInvisTextGenerator import PDFInvisTextGenerator
from .mitra_helper import run_mitra, MITRA_PATH_DEFAULT

BASE_PATH = Path(__file__).parent.parent
SAMPLES_DIR = BASE_PATH / "samples"
OUTPUT_DIR = BASE_PATH / "generated"

COVERT_ALLOWED = ["PHP", "JS", "RAR"]
MITRA_OVERT = ["BMP", "PNG", "JPEG", "PDF"]


@dataclass
class GeneratorConfig:
    """Configuration pairing a generator with its polyglot kind."""
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
        GeneratorConfig(PNGICCGenerator(), PolyglotKind.PARASITE),
    ],
    "JPEG": [
        GeneratorConfig(JPEGPixelGenerator(), PolyglotKind.SEMANTIC),
        GeneratorConfig(JPEGAPP0Generator(), PolyglotKind.PARASITE)
    ],
    "PDF": [
        GeneratorConfig(PDFInvisTextGenerator(), PolyglotKind.SEMANTIC),
    ],
}

def get_files(fmt: str, limit: int | None = None) -> list[Path]:
    """Get sample files for a given format from the samples directory."""
    files = []
    fmt = fmt.lower()
    fmt_dir = SAMPLES_DIR / fmt
    exts = ["*.jpg", "*.jpeg"] if fmt == "jpeg" else [f"*.{fmt}"] #ugly but simple enough
    for ext in exts:
        files.extend(fmt_dir.glob(ext))
    return files[:limit] if limit else files

def run(limit: int | None = None, mitra_path: Path | None = None) -> PolyDataset:
    """Run all generators on sample files and return the complete dataset."""
    polyDataset = PolyDataset.create()
    # run generators
    for overt_fmt, cfgs in ALL_GENERATORS.items():
        overts = get_files(overt_fmt, limit)
        for covert_fmt in COVERT_ALLOWED:
            coverts = get_files(covert_fmt, limit)
            for cfg in cfgs:
                curr_gen = cfg.generator
                print("Running generator: " + curr_gen._get_name() + " on overt: " + overt_fmt + ", covert: " + covert_fmt)
                for overt in overts:
                    for covert in coverts:
                        out_path = OUTPUT_DIR / curr_gen._get_name() / f"{overt.stem}_{covert.stem}_{covert_fmt}.{overt_fmt.lower()}"
                        res = launch(curr_gen, overt, covert, out_path, cfg.kind, covert_fmt.upper())
                        polyDataset.add(res)
                        if res.error:
                            print("Error: " + res.error)
    #run mitra for baseline
    print("\nRunning Mitra generator...")
    for overt_fmt in MITRA_OVERT:
        overts = get_files(overt_fmt, limit)
        for covert_fmt in COVERT_ALLOWED:
            coverts = get_files(covert_fmt, limit)
            for overt in overts:
                print(f"Running Mitra on overt: {overt_fmt}, covert: {covert_fmt}")
                for covert in coverts:
                    #INCLUDE COVERT FMT ELSE  HARD TO FIND BUG COLLISION ON FIELNAME
                    out_path = OUTPUT_DIR / "Mitra" / f"{overt.stem}_{covert.stem}_{covert_fmt}.{overt_fmt.lower()}"
                    res = run_mitra(overt, covert, out_path, covert_fmt.upper(), overt_fmt.upper(), mitra_path)
                    polyDataset.add(res)
                    if res.error:
                        print("Error: " + res.error)

    return polyDataset

def main():
    parser = argparse.ArgumentParser(description="Generate polyglot files")
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=None,
        help="Limit number of sample files per format"
    )
    parser.add_argument(
        "--mitra-path",
        type=Path,
        default=None,
        help=f"Path of mitra.py"
    )
    args = parser.parse_args()

    dataset = run(limit=args.limit, mitra_path=args.mitra_path)
    dataset.save(OUTPUT_DIR / "run.json")
    print("finished generation")

if __name__ == "__main__":
    main()