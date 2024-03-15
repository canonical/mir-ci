import asyncio
import os
import pathlib
from typing import Iterator


class Cgroup:
    def __init__(self, path: pathlib.Path) -> None:
        self.path = path

    @staticmethod
    def create(pid: int) -> asyncio.Task["Cgroup"]:
        async def inner():
            path = await Cgroup.get_cgroup_dir(pid)
            return Cgroup(path)

        task = asyncio.create_task(inner())
        return task

    @staticmethod
    async def get_cgroup_dir(pid: int) -> pathlib.Path:
        MAX_ATTEMPTS = 10
        parent_path = Cgroup._get_cgroup_dir_internal(os.getpid())
        path = Cgroup._get_cgroup_dir_internal(pid)

        for attempt in range(MAX_ATTEMPTS):
            await asyncio.sleep(0.1)
            path = Cgroup._get_cgroup_dir_internal(pid)
            if path != parent_path:
                return path
        else:
            raise RuntimeError(f"Unable to read cgroup directory for pid: {pid}")

    @staticmethod
    def _get_cgroup_dir_internal(pid: int) -> pathlib.Path:
        cgroup_file = f"/proc/{pid}/cgroup"

        with open(cgroup_file, "r") as group_file:
            for line in group_file.readlines():
                assert line.startswith("0::"), f"Line in cgroup file does not start with 0:: for pid: {pid}"
                return pathlib.Path(f"/sys/fs/cgroup/{line[3:]}".strip())
        raise RuntimeError(f"Unable to find path for process with pid: {pid}")

    def _read_file(self, file_name: str) -> Iterator[str]:
        file_path = f"{self.path}/{file_name}"
        with open(file_path, "r") as file:
            yield file.readline()

    def get_cpu_time_microseconds(self) -> int:
        try:
            for line in self._read_file("cpu.stat"):
                split_line = line.split(" ")
                if split_line[0] == "usage_usec":
                    return int(split_line[1])

            raise RuntimeError("usage_usec line not found")
        except Exception as ex:
            raise RuntimeError(f"Unable to get the cpu time for cgroup: {self.path}") from ex

    def get_current_memory(self) -> int:
        try:
            return int(next(self._read_file("memory.current")))
        except Exception as ex:
            raise RuntimeError(f"Unable to get the current memory for cgroup: {self.path}") from ex

    def get_peak_memory(self) -> int:
        try:
            return int(next(self._read_file("memory.peak")))
        except Exception as ex:
            raise RuntimeError(f"Unable to get the peak memory for cgroup: {self.path}") from ex
