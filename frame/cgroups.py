import os

class Cgroup:
    def __init__(self, name: str) -> None:
        self.name = name
        self.path = f"/sys/fs/cgroup/{name}"
        self._mount_if_not_exist()

    def _mount_if_not_exist(self) -> None:
        # On some distros, this might noe even be mounted (e.g. Debian AFAIK)
        if not os.path.isdir("/sys/fs/cgroup"):
            os.mkdir("/sys/fs/cgroup")

        if not os.path.ismount("/sys/fs/cgroup"):
            os.system("mount -t cgroupv2 /sys/fs/cgroup")

        if os.path.isdir(self.path):
            os.rmdir(self.path)

        os.mkdir(self.path)

    def add_process(self, pid: int) -> bool:
        proc_path = f"{self.path}/cgroup.procs"
        with open(proc_path, "a") as proc_file:
            proc_file.write(f"{pid}\n")

    def remove_process(self, pid: int) -> bool:
        proc_path = f"{self.path}/cgroup.procs"
        with open(proc_path, "a") as proc_file:
            proc_file.write(f"{pid}\n")

    def _read_file(self, file_name: str) -> list[str]:
        file_path = f"{self.path}/{file_name}"

        try:
            with open(file_path, "r") as file:
                return file.readlines()
        except:
            return []

    def get_cpu_time_microseconds(self) -> int:
        lines = self._read_file("cpu.stat")
        for line in lines:
            split_line = line.split(' ')
            if len(split_line) < 2:
                continue

            if split_line[0] == "usage_usec":
                return int(split_line[1])
            
        return 0
    
    def get_cpu_time_seconds(self) -> float:
        return self.get_cpu_time_microseconds() / 1_000_000
    
    def get_current_memory(self) -> int:
        lines = self._read_file("memory.current")
        if len(lines) > 0:
            return int(lines[0])
        
        return 0