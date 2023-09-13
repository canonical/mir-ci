import asyncio
import psutil
from typing import Dict, TypedDict, Callable
from abc import ABC, abstractmethod
import pytest
from contextlib import suppress
import os
from cgroups import Cgroup


class ProcessStats(TypedDict):
    name: str
    cpu_time_seconds_total: float
    mem_bytes_total: float
    mem_max: float
    num_data_points: int


class ProcessStatPacket(TypedDict):
    pid: int
    mem_bytes: float
    cpu_time_seconds_total: float


class BenchmarkBackend(ABC):
    """
    Abstract class that aggregates programs together and emits process stats as it is requested
    """
    @abstractmethod
    def add(self, pid: int, name: str) -> bool:
        pass

    @abstractmethod
    def poll(self, cb: Callable[[ProcessStatPacket], None]) -> None:
        pass


class Benchmarker:
    def __init__(self):
        self.data_records: Dict[int, ProcessStats] = {}
        self.running = False
        self.backend = PsutilBackend()
        self.task = None
        self.poll_time_seconds = 1

    def add(self, pid: int, name: str) -> bool:
        self.data_records[pid] = {
            "name": name,
            "cpu_time_seconds_total": 0,
            "mem_bytes_total": 0,
            "mem_max": 0,
            "mem_average": 0,
            "num_data_points": 0
        }
        return self.backend.add(pid, name)

    def _on_packet(self, packet: ProcessStatPacket) -> None:
        pid = packet["pid"]
        cpu_time_seconds_total = packet["cpu_time_seconds_total"]
        mem_bytes = packet["mem_bytes"]
        if pid is None or cpu_time_seconds_total is None or mem_bytes is None:
            # TODO: Error
            return
        
        if not pid in self.data_records:
            # TODO: Error
            return
        
        self.data_records[pid]["cpu_time_seconds_total"] += cpu_time_seconds_total
        self.data_records[pid]["mem_bytes_total"] += mem_bytes

        if self.data_records[pid]["cpu_max"] < cpu_time_seconds_total:
            self.data_records[pid]["cpu_max"] = cpu_time_seconds_total
        if self.data_records[pid]["mem_max"] < mem_bytes:
            self.data_records[pid]["mem_max"] = mem_bytes
        self.data_records[pid]["num_data_points"] += 1

    async def run(self) -> None:
        self.running = True
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

    def get_data(self):
        for pid, item in self.data_records.items():
            item["cpu_average"] = item["cpu_total"] / item["num_data_points"]
            item["mem_average"] = item["mem_bytes_total"] / item["num_data_points"]
        return self.data_records
    
    async def __aenter__(self):
        await self.start()

    async def __aexit__(self, *args):
        await self.stop()


class PsutilBackend(BenchmarkBackend):
    def __init__(self):
        super().__init__()
        self.monitored: list[psutil.Process] = []
    
    def add(self, pid: int, name: str):
        self.monitored.append(psutil.Process(pid))
        return True

    def poll(self, cb: Callable[[ProcessStatPacket], None]):
        for process in self.monitored:
            cb({
                "pid": process.pid,
                "cpu_time_seconds_total": process.cpu_times()[0],
                "mem_bytes": process.memory_info().rss
            })


class CgroupsBackend(BenchmarkBackend):
    def __init__(self) -> None:
        self._cgroup_list: dict[int, Cgroup] = {}

    def add(self, pid: int, name: str) -> bool:
        cgroup = Cgroup(f"mir_ci_{name}")
        cgroup.add_process(pid)
        self._cgroup_list[pid] = cgroup
        return True
    
    def poll(self, cb: Callable[[ProcessStatPacket], None]) -> None:
        for pid, cgroup in self._cgroup_list.items():
            cb({
                "pid": pid,
                "cpu_time_seconds_total": cgroup.get_cpu_time_seconds(),
                "mem_bytes": cgroup.get_current_memory()
            })
    

@pytest.fixture
def benchmarker() -> Benchmarker:
    return Benchmarker()