from mir_ci.interfaces.benchmarkable import Benchmarkable
from typing import Dict
from abc import ABC, abstractmethod

class BenchmarkBackend(ABC):
    """
    Abstract class that aggregates programs together and emits process stats as it is requested
    """
    @abstractmethod
    def add(self, name: str, program: Benchmarkable) -> None:
        """
        Add a process to be benchmarked.
        """
        raise NotImplementedError

    @abstractmethod
    async def poll(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def generate_report(self) -> Dict[str, object]:
        raise NotImplementedError
