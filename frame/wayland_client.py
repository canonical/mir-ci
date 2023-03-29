import pywayland
import pywayland.client
from protocols.wayland.wl_registry import WlRegistryProxy
from typing import Optional
from abc import abstractmethod
import time
import asyncio

class WaylandClient:
    def __init__(self, display_name: str) -> None:
        self.display = pywayland.client.Display(display_name)
        self._registry: Optional[WlRegistryProxy] = None

    def _dispatch(self) -> None:
        try:
            self.display.read()
            self.display.dispatch(block=False)
        except Exception as e:
            asyncio.get_event_loop().remove_writer(self.display.get_fd())
            raise

    def timestamp(self) -> int:
        return int(time.monotonic() * 1000)

    @abstractmethod
    def registry_global(self, registry, id_num: int, iface_name: str, version: int) -> None:
        pass

    @abstractmethod
    def connected(self) -> None:
        pass

    @abstractmethod
    def disconnected(self) -> None:
        pass

    async def __aenter__(self) -> 'WaylandClient':
        try:
            self.display.connect()
            self._registry = registry = self.display.get_registry()
            registry.dispatcher['global'] = self.registry_global
            self.display.roundtrip()
            self.connected()
            asyncio.get_event_loop().add_writer(self.display.get_fd(), self._dispatch)
            return self
        except:
            await self.__aexit__()
            raise

    async def __aexit__(self, *args) -> None:
        asyncio.get_event_loop().remove_writer(self.display.get_fd())
        self.display.roundtrip()
        self.display.disconnect()
        self.disconnected()
