import pywayland
import pywayland.client
from protocols.wayland.wl_registry import WlRegistryProxy
from typing import Optional
from abc import abstractmethod
import asyncio

class WaylandClient:
    def __init__(self, display_name: str) -> None:
        self.display = pywayland.client.Display(display_name)
        self._registry: Optional[WlRegistryProxy] = None

    def _dispatch(self) -> None:
        self.display.read()
        self.display.dispatch(block=False)

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
            self.display.connect()
            self._registry = registry = self.display.get_registry()
            registry.dispatcher['global'] = self.registry_global
            self.display.roundtrip()
            self.connected()
            asyncio.get_event_loop().add_writer(self.display.get_fd(), self._dispatch)
            return self
        except:
            self.__exit__()
            raise

    def __exit__(self, *args) -> None:
        asyncio.get_event_loop().remove_writer(self.display.get_fd())
        self.display.roundtrip()
        self.display.disconnect()
        self.disconnected()
