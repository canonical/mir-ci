import asyncio
import psutil
from typing import Dict, Callable, Literal, Iterator, Tuple
from abc import ABC, abstractmethod
import pytest
from contextlib import suppress
from cgroups import Cgroup
import psutil
import os
import time

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
        total_time_seconds = time.time() - info.start_time_seconds
        self.avg_cpu_percent = 0 if info.start_time_seconds == 0 else info.cpu_time_seconds_total / total_time_seconds
        self.max_mem_bytes = info.mem_bytes_max
        self.avg_mem_bytes = 0 if info.num_data_points == 0 else info.mem_bytes_total / info.num_data_points

    def to_json(self):
        return {
            "pid": self.pid,
            "name": self.name,
            "avg_cpu_percent": self.avg_cpu_percent,
            "max_mem_btyes": self.max_mem_bytes,
            "avg_mem_bytes": self.avg_mem_bytes
        }

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
    @abstractmethod
    def add(self, pid: int, name: str) -> bool:
        """
        Add a process to be benchmarked.
        """
        pass

    @abstractmethod
    def poll(self, cb: Callable[[ProcessInfoFrame], None]) -> None:
        pass


class Benchmarker:
    TMP_FILE_DIRECTORY = "/tmp/mir_ci_psutil_bakend"

    def __init__(self, poll_time_seconds: float = 1, backend: Literal["cgroups", "psutil"] = "cgroups"):
        self.data_records: Dict[int, RawInternalProcessInfo] = {}
        self.running = False
        self.backend: BenchmarkBackend = PsutilBackend() if backend == "psutil" else CgroupsBackend()
        self.task = None
        self.poll_time_seconds = poll_time_seconds

        if not os.path.isdir(Benchmarker.TMP_FILE_DIRECTORY):
            os.mkdir(Benchmarker.TMP_FILE_DIRECTORY)

        with open(Benchmarker._get_tmp_file_path(False), "w"):
            pass

    @staticmethod
    def _get_tmp_file_path(in_new_process: bool):
        pid = os.getpid() if in_new_process is False else os.getppid()
        return f"{Benchmarker.TMP_FILE_DIRECTORY}/{pid}"

    @staticmethod
    def add(pid: int, name: str, in_new_process: bool) -> bool:
        """
        Add a process to be benchmarked.

        WARNING: This function is marked static because it is allowed to run from a forked process. 
        """
        with open(Benchmarker._get_tmp_file_path(in_new_process), "a") as file:
            file.write(f"{pid}:{name}\n")

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
        
        self.data_records[pid].cpu_time_seconds_total = cpu_time_seconds_total
        self.data_records[pid].mem_bytes_total += current_memory_bytes

        if self.data_records[pid].mem_bytes_max < current_memory_bytes:
            self.data_records[pid].mem_bytes_max = current_memory_bytes
        self.data_records[pid].num_data_points += 1

    async def _run(self) -> None:
        self.running = True
        for pid, name in self._aggregate_processes():
            self.data_records[pid] = RawInternalProcessInfo(pid, name)
            self.backend.add(pid, name)

        while self.running:
            try:
                self.backend.poll(self._on_packet)
            except:
                pass
            await asyncio.sleep(self.poll_time_seconds)

    def _aggregate_processes(self)-> Iterator[Tuple[int, str]]:
        with open(Benchmarker._get_tmp_file_path(False), "r") as file:
            while True:
                line = file.readline()
                if not line:
                    break

                split_line = line.split(':')
                if len(split_line) != 2:
                    continue

                pid = int(split_line[0])
                name = split_line[1].strip()
                yield (pid, name)

    async def _start(self) -> None:
        if self.running:
            return
          
        self.task = asyncio.ensure_future(self._run())

    async def _stop(self) -> None:
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
        await self._start()

    async def __aexit__(self, *args):
        await self._stop()


class PsutilBackend(BenchmarkBackend):
    def __init__(self):
        super().__init__()
        self.monitored: list[psutil.Process] = []
    
    def add(self, pid: int, name: str):
        self.monitored.append(psutil.Process(pid))

    def poll(self, cb: Callable[[ProcessInfoFrame], None]):
        for process in self.monitored:
            cb(ProcessInfoFrame(
                process.pid,
                process.memory_info().rss,
                process.cpu_times()[0]
            ))


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

def benchmarker_preexec_fn(name: str) -> None:
    """
    Add the current process to the benchmark with the provided name
    """
    Benchmarker.add(os.getpid(), name, True)
