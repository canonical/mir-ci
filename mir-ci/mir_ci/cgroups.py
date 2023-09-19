import os
from typing import Iterator, Optional
import pathlib
import logging

class Cgroup:
    def __init__(self, pid: int, name: str) -> None:
        self.name = name
        self.pid = pid
        self.path = Cgroup.get_cgroup_dir(self.pid)

    @staticmethod
    def get_cgroup_dir(pid: int) -> Optional[pathlib.Path]:
        path = None
        directory = f"/proc/{pid}"
        if not os.path.isdir(directory):
            logging.getLogger().error("Process has no directory")
            return None

        cgroup_file = f"{directory}/cgroup"
        if not os.path.isfile(cgroup_file):
            logging.getLogger().error("Process has no cgroup file")
            return None

        with open(cgroup_file, "r") as group_file:
            lines = group_file.readlines()
            if len(lines) == 0:
                logging.getLogger().error(f"Process with pid={pid} lacks a cgroup folder")
                return None
            
            for line in lines:
                if not line.startswith("0::"):
                    continue

                path = pathlib.Path(f"/sys/fs/cgroup/{line[3:]}".strip())

        if not path:
            logging.getLogger().error(f"Process with pid={pid} lacks a path")
        return path

    def _read_file(self, file_name: str) -> Iterator[str]:
        if not self.path:
            return
        
        file_path = f"{self.path}/{file_name}"
        if not os.path.isfile(file_path):
            logging.getLogger().error(f"Requested fiel is not a file: {file_name}")
            return

        try:
            with open(file_path, "r") as file:
                yield file.readline()
        except Exception as e:
            logging.getLogger().error(f"Unable to read file at path: {file_path}")
            return

    def get_cpu_time_microseconds(self) -> int:
        for line in self._read_file("cpu.stat"):
            split_line = line.split(' ')
            if len(split_line) < 2:
                continue

            if split_line[0] == "usage_usec":
                return int(split_line[1])
            
        return 0
    
    def get_cpu_time_seconds(self) -> float:
        return self.get_cpu_time_microseconds() / 1_000_000
    
    def get_current_memory(self) -> int:
        for line in self._read_file("memory.current"):
            return int(line)
        
        return 0
    
    def get_peak_memory(self) -> int:
        for line in self._read_file("memory.peak"):
            return int(line)
        
        return 0
