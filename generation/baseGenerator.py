"""Abstract base class for polyglot file generators."""

from abc import ABC, abstractmethod
from pathlib import Path
import argparse


class BaseGenerator(ABC):
    """Base class defining the interface for all polyglot generators."""
    @abstractmethod
    def _get_name(self) -> str:
        pass

    @abstractmethod
    def _implements_format(self) -> str:
        pass
    
    @abstractmethod
    def generate(self, host: bytes, payload: bytes) -> bytes: #pass bytes return bytes so dont have to deal with file io in generate functions = SRP/SOC
        pass
    
    def parse_cli(self):
        """Parse CLI arguments for standalone generator usage."""
        parser = argparse.ArgumentParser(prog=f"{self._get_name()} polyglot generator",
        description = f"Generates Polyglot for {self._implements_format()} host files")
        parser.add_argument("host", type=Path)
        parser.add_argument("payload", type=Path)
        parser.add_argument("output", type=Path)
        return parser.parse_args()

    def main(self):
        """Entry point for standalone CLI execution: read files, generate polyglot, write output."""
        args = self.parse_cli()
        host_data = args.host.read_bytes()
        payload_data = args.payload.read_bytes()
        result = self.generate(host_data, payload_data)
        args.output.write_bytes(result)