"""Helper module for running the external Mitra polyglot generator tool."""

import subprocess
import hashlib
from pathlib import Path
from .generation import Result, GenStatus, PolyglotKind

MITRA_PATH_DEFAULT = Path.home() / "tools" / "mitra" / "mitra.py"


def sha256(data: bytes) -> str:
    """Compute SHA256 hash of data."""
    return hashlib.sha256(data).hexdigest()


def run_mitra(overt_path: Path, covert_path: Path, output_path: Path, covert_format: str, overt_format: str, mitra_path: Path | None = None) -> Result:
    """Run external Mitra tool, select stack polyglot if multiple outputs, return Result."""
    if mitra_path is None:
        mitra_path = MITRA_PATH_DEFAULT
    overt_data = overt_path.read_bytes()
    covert_data = covert_path.read_bytes()
    status = GenStatus.SUCCESS
    error = None
    out_hash = None

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        # need all files before to see what it generated
        output_dir = output_path.parent
        files_before = set(output_dir.glob("*"))
        # mitra.py overt covert -f -o output_dir
        # -f force with any format
        result = subprocess.run( #need use absolute path for this!
            ["python3", str(mitra_path), str(overt_path.absolute()), str(covert_path.absolute()), "-f", "-o", str(output_dir.absolute())],
            cwd=mitra_path.parent,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            raise Exception(f"Mitra gen failed: {result.stderr.strip()}")
        files_after = set(output_dir.glob("*"))
        new_files = list(files_after - files_before)
        if not new_files:
            raise Exception("No output file created by Mitra")
        # mitra gen multiple files we need to chosoe one and rename to our structure of naming
        if len(new_files) > 1:
            # S( mean its stack polyglot) prefer this due to koch et al say stack is most used
            stack = [f for f in new_files if f.name.startswith('S(')]
            if stack:
                actual_output = stack[0]
            else:
                #use some polyglot
                actual_output = new_files[0]

            #del all files except the we chose
            for f in new_files:
                if f != actual_output:
                    f.unlink()
        else:
            actual_output = new_files[0]
        actual_output.rename(output_path)
        out_hash = sha256(output_path.read_bytes())
    except Exception as e:

        status = GenStatus.ERROR
        error = str(e)
    finally:
        return Result(
            status=status,
            kind=PolyglotKind.PARASITE,
            generator="Mitra",
            overt_format=overt_format,
            covert_format=covert_format,
            overt_path=str(overt_path),
            overt_hash=sha256(overt_data),
            covert_path=str(covert_path),
            covert_hash=sha256(covert_data),
            output_path=str(output_path),
            output_hash=out_hash,
            error=error
        )
