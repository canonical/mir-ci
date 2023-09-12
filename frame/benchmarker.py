import asyncio
import psutil
from typing import Dict, TypedDict, Callable
from abc import ABC, abstractmethod
import pytest
import time
from contextlib import suppress


class ProcessStats(TypedDict):
    name: str
    cpu_total: float
    cpu_max: float
    mem_total: float
    mem_max: float
    num_data_points: int


class ProcessStatPacket(TypedDict):
    pid: int
    mem: float
    cpu: float


class BenchmarkBackend(ABC):
    """
    Abstract class that aggregates programs together and emits process stats as it is requested
    """
    @abstractmethod
    def add(self, pid: int, name: str) -> bool:
        pass

    @abstractmethod
    def remove(self, pid: int, name: str) -> bool:
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
            "cpu_total": 0,
            "cpu_max": 0,
            "cpu_average": 0,
            "mem_total": 0,
            "mem_max": 0,
            "mem_average": 0,
            "num_data_points": 0
        }
        return self.backend.add(pid, name)

    def remove(self, pid: int, name: str) -> bool:
        return self.backend.remove(pid, name)

    def _on_packet(self, packet: ProcessStatPacket) -> None:
        pid = packet["pid"]
        cpu = packet["cpu"]
        mem = packet["mem"]
        if pid is None or cpu is None or mem is None:
            # TODO: Error
            return
        
        if not pid in self.data_records:
            # TODO: Error
            return
        
        self.data_records[pid]["cpu_total"] += cpu
        self.data_records[pid]["mem_total"] += mem
        if self.data_records[pid]["cpu_max"] < cpu:
            self.data_records[pid]["cpu_max"] = cpu
        if self.data_records[pid]["mem_max"] < mem:
            self.data_records[pid]["mem_max"] = mem
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
        for key, item in self.data_records.items():
            item["cpu_average"] = item["cpu_total"] / item["num_data_points"]
            item["mem_average"] = item["mem_total"] / item["num_data_points"]
        return self.data_records
    
    async def __aenter__(self):
        await self.start()

    async def __aexit__(self, *args):
        await self.stop()


class PsutilBackend(BenchmarkBackend):
    def __init__(self):
        self.monitored = []
    
    def add(self, pid: int, name: str):
        x = psutil.Process(pid)
        x.pid
        
        self.monitored.append(psutil.Process(pid))
        return True

    def remove(self,  pid: int, name: str):
        for process in self.monitored:
            if process.pid == pid:
                self.monitored.remove(process)
                return True;

        return False

    def poll(self, cb: Callable[[ProcessStatPacket], None]):
        for process in self.monitored:
            cpu = process.cpu_percent()
            mem = process.memory_info().rss
            pid = process.pid
            packet: ProcessStatPacket = {
                "cpu": cpu,
                "mem": mem,
                "pid": pid
            }
            cb(packet)


@pytest.fixture
def benchmarker() -> Benchmarker:
    return Benchmarker()