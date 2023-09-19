import asyncio
import psutil
from typing import Dict, Callable, Literal, Iterator, Tuple, List, Optional
from abc import ABC, abstractmethod
from contextlib import suppress
from mir_ci.cgroups import Cgroup
import psutil
import os
import time

class RawInternalProcessInfo:
    pid: int
    name: str
    start_time_seconds: float
    cpu_time_microseconds_total: float
    mem_bytes_total: int
    mem_bytes_max: int
    num_data_points: int

    def __init__(self, pid: int , name: str) -> None:
        self.pid = pid
        self.name = name
        self.start_time_seconds = time.time()
        self.cpu_time_microseconds_total = 0
        self.mem_bytes_total = 0
        self.mem_bytes_max = 0
        self.num_data_points = 0


class ProcessInfo:
    pid: int
    name: str
    cpu_time_microseconds_total: float
    max_mem_bytes: int
    avg_mem_bytes: float

    def __init__(self, info: RawInternalProcessInfo) -> None:
        self.pid = info.pid
        self.name = info.name
        self.cpu_time_microseconds_total = info.cpu_time_microseconds_total
        self.max_mem_bytes = info.mem_bytes_max
        self.avg_mem_bytes = 0 if info.num_data_points == 0 else info.mem_bytes_total / info.num_data_points
        

class ProcessInfoFrame:
    pid: int
    current_memory_bytes: int
    cpu_time_microseconds_total: float

    peak_memory_bytes: Optional[int]
    """
    A frame may contain the peak memory in bytes if it is available.
    This may be more reliable than finding the largest in a sample of
    current memory bytes data points
    """

    def __init__(
            self,
            pid: int,
            current_memory_bytes: int,
            cpu_time_microseconds_total: float,
            peak_memory_bytes: Optional[int] = None) -> None:
        self.pid = pid
        self.current_memory_bytes = current_memory_bytes
        self.cpu_time_microseconds_total = cpu_time_microseconds_total
        self.peak_memory_bytes = peak_memory_bytes


class BenchmarkBackend(ABC):
    """
    Abstract class that aggregates programs together and emits process stats as it is requested
    """
    @abstractmethod
    def add(self, pid: int, name: str) -> None:
        """
        Add a process to be benchmarked.
        """
        pass

    @abstractmethod
    def poll(self, cb: Callable[[ProcessInfoFrame], None]) -> None:
        pass


class Benchmarker:
    def __init__(self, poll_time_seconds: float = 1, backend: Literal["cgroups", "psutil"] = "cgroups"):
        self.data_records: Dict[int, RawInternalProcessInfo] = {}
        self.running = False
        self.backend: BenchmarkBackend = PsutilBackend() if backend == "psutil" else CgroupsBackend()
        self.task: Optional[asyncio.Task[None]] = None
        self.poll_time_seconds = poll_time_seconds

    def add(self, pid: int, name: str) -> None:
        self.data_records[pid] = RawInternalProcessInfo(pid, name)

    def _on_packet(self, packet: ProcessInfoFrame) -> None:
        pid = packet.pid
        cpu_time_microseconds_total = packet.cpu_time_microseconds_total
        current_memory_bytes = packet.current_memory_bytes
        if pid is None:
            print("Frame is lacking pid")
            return
        
        if cpu_time_microseconds_total is None:
            print("Frame is lacking cpu_time_microseconds_total")
            return
        
        if current_memory_bytes is None:
            print("Frame is lacking current_memory_bytes")
            return
        
        if not pid in self.data_records:
            print("PID provided by frame is invalid")
            return
        
        self.data_records[pid].cpu_time_microseconds_total = cpu_time_microseconds_total
        self.data_records[pid].mem_bytes_total += current_memory_bytes

        if packet.peak_memory_bytes is not None:
            self.data_records[pid].mem_bytes_max = packet.peak_memory_bytes
        elif self.data_records[pid].mem_bytes_max < current_memory_bytes:
            self.data_records[pid].mem_bytes_max = current_memory_bytes
        
        self.data_records[pid].num_data_points += 1

    async def _run(self) -> None:
        self.running = True
        while self.running:
            try:
                self.backend.poll(self._on_packet)
            except:
                pass
            await asyncio.sleep(self.poll_time_seconds)

    async def start(self) -> None:
        if self.running is True:
            return

        # This sleep is unfortunate, but necessary. For the cgroups backend,
        # we are waiting for the /proc/PID/cgroup to get written with the
        # correct path. In the beginning, it will briefly have the value
        # of the parent process.
        await asyncio.sleep(self.poll_time_seconds)

        for pid in self.data_records:
            self.backend.add(pid, self.data_records[pid].name)
        
        self.task = asyncio.ensure_future(self._run())

    async def stop(self) -> None:
        if self.running is False:
            return
        
        self.running = False
        if self.task:
            self.task.cancel()
            with suppress(asyncio.CancelledError):
                await self.task

    def get_data(self) -> List[ProcessInfo]:
        process_info_list = []
        for pid, info in self.data_records.items():
            process_info_list.append(ProcessInfo(info))
        return process_info_list
    
    async def __aenter__(self):
        await self.start()

    async def __aexit__(self, *args):
        await self.stop()

    def generate_report(self, record_property: Callable[[str, object], None]):
        idx = 0
        for item in self.get_data():
            record_property(f"{item.name}_cpu_time_microseconds", item.cpu_time_microseconds_total)
            record_property(f"{item.name}_max_mem_bytes", item.max_mem_bytes)
            record_property(f"{item.name}_avg_mem_bytes", item.avg_mem_bytes)
            idx = idx + 1



class PsutilBackend(BenchmarkBackend):
    def __init__(self) -> None:
        self.monitored: List[psutil.Process] = []
    
    def add(self, pid: int, name: str) -> None:
        self.monitored.append(psutil.Process(pid))

    def poll(self, cb: Callable[[ProcessInfoFrame], None]):
        for process in self.monitored:
            cb(ProcessInfoFrame(
                process.pid,
                process.memory_info().rss,
                process.cpu_times()[0] * 1_000_000 # To microseconds
            ))


class CgroupsBackend(BenchmarkBackend):
    def __init__(self) -> None:
        self._cgroup_list: Dict[int, Cgroup] = {}

    def add(self, pid: int, name: str) -> None:
        cgroup = Cgroup(pid, name)
        self._cgroup_list[pid] = cgroup
    
    def poll(self, cb: Callable[[ProcessInfoFrame], None]) -> None:
        for pid, cgroup in self._cgroup_list.items():
            cb(ProcessInfoFrame(
                pid,
                cgroup.get_current_memory(),
                cgroup.get_cpu_time_microseconds(),
                cgroup.get_peak_memory()
            ))
