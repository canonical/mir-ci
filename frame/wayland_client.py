import pywayland
import pywayland.client
from protocols.wayland.wl_registry import WlRegistryProxy
from typing import Optional
from abc import abstractmethod
import threading

class WaylandClient:
    def __init__(self, display_name: str) -> None:
        self.display_name = display_name
        self.display: Optional[pywayland.client.Display] = None
        self._registry: Optional[WlRegistryProxy] = None
        self._dispatch_thread = threading.Thread(name=f'{display_name}-dispatch', target=self._dispatch)

    def _dispatch(self) -> None:
        while self.display is not None:
            self.display.dispatch(block=True)

    @abstractmethod
    def registry_global(self, registry, id_num: int, iface_name: str, version: int) -> None:
        pass

    @abstractmethod
    def connected(self) -> None:
        pass

    @abstractmethod
    def disconnected(self) -> None:
        pass

    def __enter__(self) -> 'WaylandClient':
        try:
            display = pywayland.client.Display(self.display_name)
            display.connect()
            self.display = display
            self._registry = registry = self.display.get_registry()
            registry.dispatcher['global'] = self.registry_global
            self.display.roundtrip()
            self.connected()
            self._dispatch_thread.start()
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
        if self._dispatch_thread.is_alive():
            self._dispatch_thread.join()
        self.disconnected()
