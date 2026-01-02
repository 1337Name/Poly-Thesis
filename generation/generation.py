from enum import StrEnum, auto
import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional
from .baseGenerator import BaseGenerator
class GenStatus(StrEnum):
    SUCCESS = auto()
    ERROR = auto()

class PolyglotKind(StrEnum):
    SEMANTIC = auto()
    STACK = auto()
    CAVITY = auto()
    PARASITE = auto()

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

@dataclass
class Result:
    status: GenStatus
    kind: PolyglotKind
    generator: str
    overt_format: str
    covert_format: str

    # metadata for proof / reproduce
    overt_path : str
    overt_hash : str
    covert_path : str
    covert_hash : str 
    #might fail no output
    output_path: str
    output_hash: Optional[str] 
    #might not fail no error
    error: Optional[str]

def launch(generator : BaseGenerator, overt_path: Path, covert_path: Path, out_path: Path, kind: PolyglotKind, covert_format: Optional[str]):
    overt = overt_path.read_bytes()
    covert = covert_path.read_bytes()
    status = GenStatus.SUCCESS
    error = None
    out_hash = None
    if covert_format is None:
        covert_format = covert_path.suffix.rsplit(".",1)[-1].upper()
    try:
        out = generator.generate(overt, covert)
        out_path.parent.mkdir(parents=True, exist_ok=True) # else it fails
        out_path.write_bytes(out)
        out_hash = sha256(out)
    except Exception as e:
        error = str(e)
        status = GenStatus.ERROR
    finally:
        return Result(
            status = status,
            kind = kind ,
            generator = generator._get_name(),
            overt_format = generator._implements_format(),
            covert_format = covert_format,
            overt_path = str(overt_path),
            covert_path = str(covert_path),
            overt_hash = sha256(overt),
            covert_hash = sha256(covert),
            output_path = str(out_path),
            output_hash = out_hash,
            error = error
        )

@dataclass
class PolyDataset:
    timestamp: str
    polyglots: list[Result]

    @staticmethod
    def create():
        return PolyDataset(
            timestamp=datetime.now().isoformat(),
            polyglots=[]
        )

    def add(self, result: Result):
        self.polyglots.append(result)

    def save(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('w') as f:
            json.dump(asdict(self), f)


