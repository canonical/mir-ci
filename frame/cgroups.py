import subprocess
import os
import time

CPUACCT="cpuacct"

class Cgroup:
    def __init__(self, type: str, name: str) -> None:
        self.type = type
        self.name = name
        self.path = None

    def _get_type_path(self):
        return f"/sys/fs/cgroup/{self.type}"

    def _mount_if_not_exist(self) -> None:
        path = self._get_type_path()
        if not os.path.isdir(path):
            os.mkdir(path)

        if not os.path.ismount(path):
            os.system(f"mount -t cgroup -o{self.type} none /sys/fs/cgroup/{self.type}/")

    def __enter__(self) -> "Cgroup":
        self._mount_if_not_exist()
        self.path = f"{self._get_type_path()}/{self.name}"
        if not os.path.isdir(self.path):
            os.mkdir(self.path)
        return self
    
    def __exit__(self, *args) -> None:
        if self.path is not None and os.path.isdir(self.path):
            os.rmdir(self.path)

    def add_process(self, pid: int) -> bool:
        if not os.path.isdir(self.path):
            return False
        
        task_file_path = f"{self.path}/tasks"
        if not os.path.isfile(task_file_path):
            return False
        
        with open(task_file_path, "a") as task_file:
            task_file.write(f"{str(pid)}\n")
        return True
    
    def remove_process(self, pid: int) -> bool:
        if not os.path.isdir(self.path):
            return False
        
        task_file_path = f"{self.path}/tasks"
        if not os.path.isfile(task_file_path):
            return False
        
        with open(task_file_path, "r+") as task_file:
            lines = task_file.readlines()
            task_file.seek(0)
            for line in lines:
                if line != str(pid):
                    task_file.write(line)
            task_file.truncate()
    

process = subprocess.Popen(["/home/matthew/Github/fork_high_cpu/a.out"])
process.pid
with Cgroup(CPUACCT, "test") as cgroup:
    cgroup.add_process(process.pid)
    process.wait(1000)