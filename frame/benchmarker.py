import asyncio
from program import Program
from cgroupspy import trees
import psutil
import apps
from typing import Dict, TypedDict, Callable
from abc import ABC, abstractmethod

class ProcessStats(TypedDict):
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
    def add(self, program: Program) -> bool:
        pass

    @abstractmethod
    def remove(self, program: Program) -> bool:
        pass

    @abstractmethod
    def poll(self, cb: Callable[[ProcessStatPacket], None]) -> None:
        pass

class Benchmarker:
    """
    """
    def __init__(self, group_name: str):
        self.data_records: Dict[int, ProcessStats] = {}
        self.running = False
        self.poll_time_seconds = 1
        self.backend = PsutilBackend()

    def add(self, program: Program) -> bool:
        if program.process is None:
            return False

        self.data_records[program.process.pid] = {
            "cpu_total": 0,
            "cpu_max": 0,
            "mem_total": 0,
            "mem_max": 0,
            "num_data_points": 0
        }
        return self.backend.add(program)

    def remove(self, program: Program) -> bool:
        return self.backend.remove(program)

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
        self.data_records[pid]["mem_total"] += cpu
        self.data_records[pid]["num_data_points"] += 1

    async def run(self) -> None:
        self.running = True
        while self.running:
            self.backend.poll(self._on_packet)
            await asyncio.sleep(self.poll_time_seconds)

    def start(self) -> None:
        asyncio.ensure_future(self.run())

    def stop(self) -> None:
        self.running = False

    def get_data(self):
        return self.data_records



class PsutilBackend(BenchmarkBackend):
    def __init__(self):
        self.monitored = []
    
    def add(self, program: Program):
        x = psutil.Process(program.process.pid)
        x.pid
        
        self.monitored.append(psutil.Process(program.process.pid))
        return True

    def remove(self, program: Program):
        if program.process is None:
            return False

        for process in self.monitored:
            if process.pid == program.process.pid:
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



async def main():
    p = Program(['sleep', '60'])
    async with p:
        benchmarker = Benchmarker("test")
        benchmarker.add(p);
        benchmarker.start()
        await asyncio.sleep(2)
        await p.kill(2)
        benchmarker.stop()
    
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
