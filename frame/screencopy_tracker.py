import pywayland
import pywayland.client
from protocols import WlOutput, WlBuffer, WlShm, ZwlrScreencopyManagerV1
from protocols.wlr_screencopy_unstable_v1.zwlr_screencopy_manager_v1 import ZwlrScreencopyManagerV1Proxy
from protocols.wlr_screencopy_unstable_v1.zwlr_screencopy_frame_v1 import ZwlrScreencopyFrameV1Proxy
from protocols.wayland.wl_registry import WlRegistryProxy
from protocols.wayland.wl_output import WlOutputProxy
from protocols.wayland.wl_buffer import WlBufferProxy
from protocols.wayland.wl_shm import WlShmProxy
from typing import Optional, Any
import os
import stat
import ctypes
import mmap
import threading

libc = ctypes.cdll.LoadLibrary(None) # type: ignore
shm_counter = 0

def shm_open() -> int:
    global shm_counter
    shm_counter += 1
    name = f'/frame-test-{os.getpid()}-{shm_counter}'
    c_name = name.encode('utf-8')
    oflag = ctypes.c_int(os.O_RDWR | os.O_CREAT | os.O_EXCL)
    mode = ctypes.c_ushort(stat.S_IRUSR | stat.S_IWUSR)
    open_result: int = libc.shm_open(c_name, oflag, mode)
    assert open_result >= 0, f'Error {open_result} opening SHM file {name}: {os.strerror(ctypes.get_errno())}'
    unlink_result = libc.shm_unlink(c_name)
    assert unlink_result >= 0, f'Error {unlink_result} unlinking SHM file {name}: {os.strerror(ctypes.get_errno())}'
    return open_result

class ScreencopyTracker:
    def __init__(self, display_name: str) -> None:
        self.display_name = display_name
        self.display: Optional[pywayland.client.Display] = None
        self.registry: Optional[WlRegistryProxy] = None
        self.screencopy_manager: Optional[ZwlrScreencopyManagerV1Proxy] = None
        self.output: Optional[WlOutputProxy] = None
        self.shm: Optional[WlShmProxy] = None
        self.frame: Optional[ZwlrScreencopyFrameV1Proxy] = None
        self.buffer: Optional[WlBufferProxy] = None
        self.shm_data: Optional[mmap.mmap] = None
        self.dispatch_thread = threading.Thread(name=f'{display_name}-dispatch', target=self._dispatch)
        self.frame_count = 0
        self.total_damage = 0
        self.buffer_width = 0
        self.buffer_height = 0
        self.buffer_size = 0
        self.pending_damage = 0

    def _dispatch(self) -> None:
        while self.display is not None:
            self.display.dispatch(block=True)

    def _registry_global(self, registry, id_num: int, iface_name: str, version: int) -> None:
        if iface_name == ZwlrScreencopyManagerV1.name:
            self.screencopy_manager = registry.bind(id_num, ZwlrScreencopyManagerV1, version)
        elif iface_name == WlOutput.name:
            self.output = registry.bind(id_num, WlOutput, version)
        elif iface_name == WlShm.name:
            self.shm = shm = registry.bind(id_num, WlShm, version)

    def _frame_buffer(self, frame, format: int, width: int, height: int, stride: int) -> None:
        assert self.buffer_width == 0 or self.buffer_width == width, 'Buffer width changed'
        self.buffer_width = width
        assert self.buffer_height == 0 or self.buffer_height == height, 'Buffer height changed'
        self.buffer_height = height
        buffer_size = stride * height
        assert self.buffer_size == 0 or self.buffer_size == buffer_size, 'Buffer size changed'
        self.buffer_size = buffer_size
        if self.buffer is None:
            assert self.shm is not None, 'SHM not created'
            fd = shm_open()
            os.ftruncate(fd, buffer_size)
            self.shm_data = mmap.mmap(fd, buffer_size)
            shm_pool = self.shm.create_pool(fd, buffer_size)
            libc.close(fd);
            self.buffer = shm_pool.create_buffer(0, width, height, stride, format)
            shm_pool.destroy()

    def _frame_damage(self, frame, x: int, y: int, width: int, height: int) -> None:
        self.pending_damage += width * height

    def _frame_ready(self, frame, tv_sec_hi, tv_sec_lo, tv_nsec) -> None:
        self.frame_count += 1
        self.total_damage += (self.pending_damage
            if self.pending_damage
            else (self.buffer_width * self.buffer_height))
        self.pending_damage = 0
        assert self.frame is not None, 'Frame is None'
        assert self.display is not None, 'No display'
        self.copy_frame(False)
        self.display.flush()

    def copy_frame(self, is_initial: bool) -> None:
        assert self.screencopy_manager is not None, f'{ZwlrScreencopyManagerV1.name} not supported'
        assert self.display is not None, 'No display'
        if self.frame is not None:
            self.frame.destroy()
        self.frame = frame = self.screencopy_manager.capture_output(0, self.output)
        frame.dispatcher['buffer'] = self._frame_buffer
        frame.dispatcher['damage'] = self._frame_damage
        frame.dispatcher['ready'] = self._frame_ready
        self.display.roundtrip()
        assert self.buffer is not None, 'No buffer info given'
        if is_initial:
            frame.copy(self.buffer)
        else:
            frame.copy_with_damage(self.buffer)

    def __enter__(self) -> 'ScreencopyTracker':
        try:
            display = pywayland.client.Display(self.display_name)
            display.connect()
            self.display = display
            self.registry = registry = self.display.get_registry()
            registry.dispatcher['global'] = self._registry_global
            self.display.roundtrip()
            self.copy_frame(True)
            self.dispatch_thread.start()
            return self
        except:
            self.__exit__()
            raise

    def __exit__(self, *args) -> None:
        if self.display is not None:
            display = self.display
            self.display = None
            display.roundtrip()
            display.disconnect()
        if self.shm_data is not None:
            self.shm_data.close()
            self.shm_data = None
        if self.dispatch_thread.is_alive():
            self.dispatch_thread.join()

    def properties(self) -> dict[str, Any]:
        total_possible_pixels = max(
            self.frame_count * self.buffer_width * self.buffer_height,
            self.total_damage,
            1
        )
        return {
            'frame count': self.frame_count,
            'resolution': (self.buffer_width, self.buffer_height),
            'pixels per frame': self.buffer_width * self.buffer_height,
            'total pixels damaged': self.total_damage,
            'percent of pixels damaged per frame': self.total_damage * 100.0 / total_possible_pixels,
        }

if __name__ == '__main__':
    import time
    with ScreencopyTracker(os.environ['WAYLAND_DISPLAY']) as s:
        time.sleep(5)