import asyncio
import psutil
from typing import Dict, Callable, Literal, Iterator, Tuple
from abc import ABC, abstractmethod
import pytest
from contextlib import suppress
from cgroups import Cgroup
import psutil
import tempfile
import os


class RawInternalProcessInfo:
    pid: int
    name: str
    start_time_seconds: float
    cpu_time_seconds_total: float
    mem_bytes_total: float
    mem_bytes_max: float
    num_data_points: int

    def __init__(self, pid: int , name: str) -> None:
        self.pid = pid
        self.name = name
        process = psutil.Process(self.pid)
        self.start_time_seconds = process.create_time()
        self.cpu_time_seconds_total = 0
        self.mem_bytes_total = 0
        self.mem_bytes_max = 0
        self.num_data_points = 0


class ProcessInfo:
    pid: int
    name: str
    avg_cpu_percent: float
    max_mem_bytes: int
    avg_mem_bytes: int

    def __init__(self, info: RawInternalProcessInfo) -> None:
        self.pid = info.pid
        self.name = info.name
        self.avg_cpu_percent = 0 if info.start_time_seconds == 0 else info.cpu_time_seconds_total / info.start_time_seconds
        self.max_mem_bytes = info.mem_bytes_max
        self.avg_mem_bytes = 0 if info.num_data_points == 0 else info.mem_bytes_total / info.num_data_points

class ProcessInfoFrame:
    pid: int
    current_memory_bytes: float
    cpu_time_seconds_total: float

    def __init__(self, pid: int,
                 current_memory_bytes: float,
                 cpu_time_seconds_total: float) -> None:
        self.pid = pid
        self.current_memory_bytes = current_memory_bytes
        self.cpu_time_seconds_total = cpu_time_seconds_total


class BenchmarkBackend(ABC):
    """
    Abstract class that aggregates programs together and emits process stats as it is requested
    """
    @staticmethod
    @abstractmethod
    def add(pid: int, name: str) -> bool:
        """
        Add a process to be benchmarked.

        WARNING: This function is marked static because it is allowed to run from a forked process.
        It is the job of "aggregate_processes" to add the processes into memory before benchmarking
        starts.
        """
        pass

    @abstractmethod
    def aggregate_processes(self) -> Iterator[Tuple[int, str]]:
        return

    @abstractmethod
    def poll(self, cb: Callable[[ProcessInfoFrame], None]) -> None:
        pass


class Benchmarker:
    def __init__(self, poll_time_seconds: float = 1, backend: Literal["cgroups", "psutil"] = "cgroups"):
        self.data_records: Dict[int, RawInternalProcessInfo] = {}
        self.running = False
        self.backend: BenchmarkBackend = PsutilBackend() if backend == "psutil" else CgroupsBackend()
        self.task = None
        self.poll_time_seconds = poll_time_seconds

    @staticmethod
    def add(pid: int, name: str, backend: Literal["cgroups", "psutil"] = "cgroups") -> bool:
        """
        Add a process to be benchmarked.

        WARNING: This function is marked static because it is allowed to run from a forked process. 
        """
        backend: BenchmarkBackend.__class__ = PsutilBackend if backend == "psutil" else CgroupsBackend
        return backend.add(pid, name)

    def _on_packet(self, packet: ProcessInfoFrame) -> None:
        pid = packet.pid
        cpu_time_seconds_total = packet.cpu_time_seconds_total
        current_memory_bytes = packet.current_memory_bytes
        if pid is None:
            print("Frame is lacking pid")
            return
        
        if cpu_time_seconds_total is None:
            print("Frame is lacking cpu_time_seconds_total")
            return
        
        if current_memory_bytes is None:
            print("Frame is lacking current_memory_bytes")
            return
        
        if not pid in self.data_records:
            print("PID provided by frame is invalid")
            return
        
        self.data_records[pid].cpu_time_seconds_total += cpu_time_seconds_total
        self.data_records[pid].mem_bytes_total += current_memory_bytes

        if self.data_records[pid].mem_bytes_max < current_memory_bytes:
            self.data_records[pid].mem_bytes_max = current_memory_bytes
        self.data_records[pid].num_data_points += 1

    async def run(self) -> None:
        self.running = True
        for pid, name in self.backend.aggregate_processes():
            self.data_records[pid] = RawInternalProcessInfo(pid, name)
        while self.running:
            try:
                self.backend.poll(self._on_packet)
            except:
                pass
            await asyncio.sleep(self.poll_time_seconds)

    async def start(self) -> None:
        if self.running:
            return
          
        self.task = asyncio.ensure_future(self.run())

    async def stop(self) -> None:
        if self.running is False:
            return
        
        self.running = False
        self.task.cancel()
        with suppress(asyncio.CancelledError):
            await self.task

    def get_data(self) -> list[ProcessInfo]:
        process_info_list = []
        for pid, info in self.data_records.items():
            process_info_list.append(ProcessInfo(info))
        return process_info_list
    
    async def __aenter__(self):
        await self.start()

    async def __aexit__(self, *args):
        await self.stop()


PSUTIL_BACKEND_TMP_FILE_LOCATION = "/tmp/mir_ci_psutil_bakend.dat"

class PsutilBackend(BenchmarkBackend):
    def __init__(self):
        super().__init__()
        self.monitored: list[psutil.Process] = []
        with open(PSUTIL_BACKEND_TMP_FILE_LOCATION, "w"):
            pass
    
    @staticmethod
    def add(pid: int, name: str):
        with open(PSUTIL_BACKEND_TMP_FILE_LOCATION, "a") as file:
            file.write(f"{pid}:{name}\n")

    def poll(self, cb: Callable[[ProcessInfoFrame], None]):
        for process in self.monitored:
            cb(ProcessInfoFrame(
                process.pid,
                process.memory_info().rss,
                process.cpu_times()[0]
            ))

    def aggregate_processes(self)-> Iterator[Tuple[int, str]]:
        with open(PSUTIL_BACKEND_TMP_FILE_LOCATION, "r") as file:
            while True:
                line = file.readline()
                if not line:
                    break

                split_line = line.split(':')
                if len(split_line) != 2:
                    continue

                pid = int(split_line[0])
                name = split_line[1]
                self.monitored.append(psutil.Process(pid))
                yield (pid, name)


class CgroupsBackend(BenchmarkBackend):
    def __init__(self) -> None:
        self._cgroup_list: dict[int, Cgroup] = {}

    def add(self, pid: int, name: str) -> bool:
        cgroup = Cgroup(f"mir_ci_{name}")
        cgroup.add_process(pid)
        self._cgroup_list[pid] = cgroup
        return True
    
    def poll(self, cb: Callable[[ProcessInfoFrame], None]) -> None:
        for pid, cgroup in self._cgroup_list.items():
            cb(ProcessInfoFrame(
                pid,
                cgroup.get_current_memory(),
                cgroup.get_cpu_time_seconds()
            ))

    def aggregate_processes(self) -> None:
        return super().aggregate_processes()
    

@pytest.fixture
def benchmarker() -> Benchmarker:
    return Benchmarker()