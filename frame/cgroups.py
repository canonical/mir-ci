import subprocess
import os
import time
import psutil

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
    
cgroup = Cgroup("test")
def add_process():
    cgroup.add_process(os.getpid())
        
process = subprocess.Popen(["/home/matthew/Github/fork_high_cpu/a.out"], preexec_fn=add_process)
psutil_process = psutil.Process(process.pid)
print(psutil_process.pid)
start_time = psutil_process.create_time()

for i in range(0, 100):
    time.sleep(1)
    up_time = time.time() - start_time;
    print(f"cgroups:\n\tCPU Time: {cgroup.get_cpu_time_seconds()}\n\tMemory: {cgroup.get_current_memory()}\n\t")
    print(f"psutil:\n\tCPU Time: {psutil_process.cpu_times()[0]}\n\tMemory:{psutil_process.memory_info()}\n\t")
    print("\n")

process.wait(1000)