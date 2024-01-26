import asyncio
import time
from abc import abstractmethod
from typing import Optional

import pywayland
import pywayland.client
from mir_ci.protocols.wayland.wl_registry import WlRegistryProxy


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
            raise e

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

    async def connect(self) -> "WaylandClient":
        try:
            self.display.connect()
            self._registry = registry = self.display.get_registry()
            registry.dispatcher["global"] = self.registry_global
            self.display.roundtrip()
            self.connected()
            asyncio.get_event_loop().add_writer(self.display.get_fd(), self._dispatch)
            return self
        except Exception as e:
            await self.disconnect()
            raise e

    async def disconnect(self) -> None:
        asyncio.get_event_loop().remove_writer(self.display.get_fd())
        self.display.roundtrip()
        self.display.disconnect()
        self.disconnected()

    async def __aenter__(self) -> "WaylandClient":
        return await self.connect()

    async def __aexit__(self, *args) -> None:
        await self.disconnect()
