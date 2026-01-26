"""
Main detection runner for evaluating polyglot files.

Runs all configured detectors on generated polyglot files and their source
monoglots, collecting results into a JSON dataset for analysis.
"""

from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import signal
from .types import DetectionResult
from .fileDetector import FileDetector
from .magikaDetector import MagikaDetector
from .polyFileDetector import PolyFileDetector
from .polyDetDetector import PolyDetDetector


@dataclass
class DetectorConfig:
    """Configuration for a single detector with timeout."""
    detector: object
    name: str
    timeout: int

# ADD HERE TO ADD NEW DETECTOR
ALL_DETECTORS = [
    DetectorConfig(FileDetector(), "file", timeout=10),
    DetectorConfig(MagikaDetector(threshold=0.05), "magika", timeout=30),
    DetectorConfig(PolyFileDetector(require_mimetype=True), "polyfile", timeout=60),
    DetectorConfig(PolyDetDetector(), "polydet", timeout=60),
]

BASE_PATH = Path(__file__).parent.parent #dir containing the git
GENERATED_DIR = BASE_PATH / "generated"

#having actual working timeout on python is quite the rabbit hole cause it cant kill thread and multi process dont work if not pickleable 
#but with signal it works with timeout but on linux/únix only
#using base exception and having old_handler coem from this blog post idea to prevent further issues: https://anonbadger.wordpress.com/2018/12/15/python-signal-handlers-and-exceptions/
# do it like this bcause using using big custom libraries for detect which might use also signal 
class TimeoutException(BaseException):
    """Raised when detector execution exceeds configured timeout."""
    pass

def _timeout_handler(signum, frame):
    raise TimeoutException()

@dataclass
class EvalResult:
    """Detection results for a single file across all detectors."""
    file_path: str
    generator: str
    overt_format: str
    covert_format: str
    is_polyglot: bool
    detectors: dict  #{name(str): DetectionResult}


@dataclass
class EvalDataset:
    """Collection of evaluation results with timestamp and save functionality."""
    timestamp: str
    results: list[EvalResult]

    @staticmethod
    def create():
        return EvalDataset(
            timestamp=datetime.now().isoformat(),
            results=[]
        )

    def add(self, result: EvalResult):
        self.results.append(result)

    def save(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)

        def custom_json(obj):
            #set si not serializable
            if isinstance(obj, set):
                return list(obj)
            # numpy
            if hasattr(obj, 'item'):  # numpy scalars
                return obj.item()
            if hasattr(obj, 'tolist'):  # numpy arrays
                return obj.tolist()
            raise TypeError(f"Failed to sesrialize object of type {type(obj)}")

        with path.open('w') as f:
            json.dump(asdict(self), f, default=custom_json, indent=2)

def run_detector_with_timeout(detector, name, file_path, seconds):
    """Run a detector with Unix SIGALRM-based timeout protection."""
    old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
    try:
        signal.alarm(seconds)
        result = detector.detect(file_path)
        signal.alarm(0)
        return result
    except TimeoutException:
        print(f"{name} timed out after {seconds}s")
        return DetectionResult(
            tool=name,
            detected_types=set(),
            is_polyglot=False,
            raw_output="",
            error=f"timeout after {seconds}s"
        )
    except Exception as e:
        return DetectionResult(
            tool=name,
            detected_types=set(),
            is_polyglot=False,
            raw_output="",
            error=str(e)
        )
    finally:
        signal.signal(signal.SIGALRM, old_handler) #reset in case sth went wrong exception handled in other place
        signal.alarm(0)

def run_detectors(file_path) -> dict:
    """Run all configured detectors on a file and return results dict."""
    results = {}
    for config in ALL_DETECTORS:
        result = run_detector_with_timeout(config.detector, config.name, file_path, config.timeout)
        results[config.name] = result
    return results

def run() -> EvalDataset:
    """Run detection evaluation on all generated polyglots and source files."""
    dataset = EvalDataset.create()
    generation_json_path = GENERATED_DIR / "run.json"
    with open(generation_json_path) as f:
        generation = json.load(f)
    files_to_eval = []
    #get all monoglots (map with its format so no duplicate and easy .items())
    formats = {}  
    for poly in generation['polyglots']:
        if poly['status'] == 'success':
            formats[Path(poly['overt_path'])] = poly['overt_format']
            formats[Path(poly['covert_path'])] = poly['covert_format']
    # add monoglots to eval
    for src_path, src_format in formats.items():
        if src_path.exists():
            files_to_eval.append((src_path, "Monoglot", src_format, "", False))
    # add polyglots to eval
    for poly in generation['polyglots']:
        if poly['status'] == 'success':
            poly_path = Path(poly['output_path'])
            if poly_path.exists():
                files_to_eval.append((
                    poly_path,
                    poly['generator'],
                    poly['overt_format'],
                    poly['covert_format'], 
                    True
                ))

    # eval all files
    total_files = len(files_to_eval)
    for idx, (file_path, generator, overt, covert, is_poly) in enumerate(files_to_eval, 1):
        file_size = file_path.stat().st_size
        file_type = "polyglot" if is_poly else "monoglot"
        file_path_rel = file_path.relative_to(BASE_PATH)
        print(f"[{idx}/{total_files}] {file_type}: {file_path_rel} ({file_size//1024}KB)")

        results = run_detectors(file_path)

        eval_result = EvalResult(
            file_path=str(file_path_rel),
            generator=generator,
            overt_format=overt,
            covert_format=covert,
            is_polyglot=is_poly,
            detectors=results
        )

        dataset.add(eval_result)

    return dataset

if __name__ == "__main__":
    print("Starting polyglot detection evaluation...")
    dataset = run()

    output_file = GENERATED_DIR / "detection_results.json"
    dataset.save(output_file)

    print(f"\nEvaluation complete!")
    print(f"Total files evaluated: {len(dataset.results)}")
    print(f"Results saved to: {output_file}")
