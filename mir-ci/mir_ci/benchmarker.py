import asyncio
import logging
from typing import Dict, Callable, Optional
from contextlib import suppress

from mir_ci.interfaces.benchmarkable import Benchmarkable
from mir_ci.interfaces.benchmarker_backend import BenchmarkBackend


logger = logging.getLogger(__name__)


class Benchmarker:
    def __init__(self, programs: Dict[str, Benchmarkable], poll_time_seconds: float = 1.0):
        self.programs = programs
        self.backend: BenchmarkBackend = CgroupsBackend()
        self.poll_time_seconds = poll_time_seconds
        self.task: Optional[asyncio.Task[None]] = None
        self.running: bool = False

    async def _run(self) -> None:
        while self.running:
            await self.backend.poll()
            await asyncio.sleep(self.poll_time_seconds)

    async def __aenter__(self):
        if self.running is True:
            return self

        self.running = True
        for program_id, program in self.programs.items():
            await program.__aenter__()
            self.backend.add(program_id, program)

        self.task = asyncio.ensure_future(self._run())
        return self

    async def __aexit__(self, *args):
        if self.running is False:
            return
        
        self.running = False
        if self.task:
            self.task.cancel()
            with suppress(asyncio.CancelledError):
                await self.task

        for program_id, program in self.programs.items():
            await program.__aexit__()

    def generate_report(self, record_property: Callable[[str, object], None]) -> None:
        report = self.backend.generate_report()
        for key, value in report.items():
            record_property(key, value)


class CgroupsBackend(BenchmarkBackend):
    class ProcessInfo:
        program: Benchmarkable
        cpu_time_microseconds: int = 0
        mem_bytes_accumulator: int = 0
        mem_bytes_max: int = 0
        num_data_points: int = 0

        def __init__(self, program: Benchmarkable) -> None:
            self.program = program
        
    def __init__(self) -> None:
        self.data_records: Dict[str, CgroupsBackend.ProcessInfo] = {}

    def add(self, name: str, program: Benchmarkable) -> None:
        self.data_records[name] = CgroupsBackend.ProcessInfo(program)
    
    async def poll(self) -> None:
        for name, info in self.data_records.items():
            cgroup = await info.program.get_cgroup()
            self.data_records[name].cpu_time_microseconds = cgroup.get_cpu_time_microseconds()
            self.data_records[name].mem_bytes_accumulator += cgroup.get_current_memory()
            self.data_records[name].mem_bytes_max = cgroup.get_peak_memory()
            self.data_records[name].num_data_points += 1

    def generate_report(self) -> Dict[str, object]:
        result: Dict[str, object] = {}
        for name, info in self.data_records.items():
            result[f"{name}_cpu_time_microseconds"] = info.cpu_time_microseconds
            result[f"{name}_max_mem_bytes"] = info.mem_bytes_max
            result[f"{name}_avg_mem_bytes"] = 0 if info.num_data_points == 0 else info.mem_bytes_accumulator / info.num_data_points
        return result