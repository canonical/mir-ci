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

    def registry_global(self, registry, id_num: int, iface_name: str, version: int) -> None:
        if iface_name == WlOutput.name:
            self.wl_outputs.append(registry.bind(id_num, WlOutput, min(WlOutput.version, version)))
            for key in self.callbacks:
                self.wl_outputs[-1].dispatcher[key] = self.callbacks[key]
            self.display.roundtrip()

    def connected(self) -> None:
        self.display.roundtrip()

    def disconnected(self) -> None:
        pass
