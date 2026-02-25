import asyncio
from typing import Callable, List, Optional

from .protocols import WlOutput
from .protocols.wayland.wl_output import WlOutputProxy
from .wayland_client import WaylandClient


class OutputWatcher(WaylandClient):
    def __init__(
        self,
        display_name: str,
        on_geometry: Optional[Callable[[WlOutput, int, int, int, int, int, str, str, int], None]] = None,
        on_mode: Optional[Callable[[WlOutput, int, int, int, int], None]] = None,
        on_scale: Optional[Callable[[WlOutput, int], None]] = None,
        on_name: Optional[Callable[[WlOutput, str], None]] = None,
    ):
        super().__init__(display_name)
        self.wl_outputs: List[WlOutputProxy] = []
        self.callbacks = {"geometry": on_geometry, "mode": on_mode, "scale": on_scale, "name": on_name}
        self.mode: Optional[tuple[int, int, int]] = None
        self.done_event = asyncio.Event()

    def registry_global(self, registry, id_num: int, iface_name: str, version: int) -> None:
        if iface_name == WlOutput.name:
            self.wl_outputs.append(registry.bind(id_num, WlOutput, min(WlOutput.version, version)))
            for key in self.callbacks:
                if key == "mode":
                    continue
                self.wl_outputs[-1].dispatcher[key] = self.callbacks[key]
            self.wl_outputs[-1].dispatcher["mode"] = self.on_mode
            self.wl_outputs[-1].dispatcher["done"] = self.on_done
            self.display.roundtrip()

    def connected(self) -> None:
        self.display.roundtrip()

    def disconnected(self) -> None:
        pass

    def on_mode(self, wl_output: WlOutput, flags: int, width: int, height: int, refresh: int) -> None:
        if self.callbacks["mode"] is not None:
            self.callbacks["mode"](wl_output, flags, width, height, refresh)  # type: ignore
        if self.mode is None:
            self.mode = (width, height, refresh)

    def on_done(self, wl_output: WlOutput) -> None:
        self.done_event.set()

    async def wait_done(self) -> None:
        await self.done_event.wait()
