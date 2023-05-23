from protocols import ZwlrVirtualPointerManagerV1
from protocols.wlr_virtual_pointer_unstable_v1.zwlr_virtual_pointer_manager_v1 import ZwlrVirtualPointerManagerV1Proxy
from protocols.wlr_virtual_pointer_unstable_v1.zwlr_virtual_pointer_v1 import ZwlrVirtualPointerV1Proxy
from wayland_client import WaylandClient
from typing import Optional
from enum import IntEnum

# Codes taken from input-event-codes.h
class Button(IntEnum):
    LEFT = 0x110
    RIGHT = 0x111
    MIDDLE = 0x112

class VirtualPointer(WaylandClient):
    required_extensions = (ZwlrVirtualPointerManagerV1.name,)

    def __init__(self, display_name: str) -> None:
        super().__init__(display_name)
        self.pointer_manager: Optional[ZwlrVirtualPointerManagerV1Proxy] = None
        self.pointer: Optional[ZwlrVirtualPointerV1Proxy] = None

    def registry_global(self, registry, id_num: int, iface_name: str, version: int) -> None:
        if iface_name == ZwlrVirtualPointerManagerV1.name:
            self.pointer_manager = manager = registry.bind(
                id_num,
                ZwlrVirtualPointerManagerV1,
                min(ZwlrVirtualPointerManagerV1.version, version))
            self.pointer = manager.create_virtual_pointer(None)

    def connected(self) -> None:
        pass

    def disconnected(self) -> None:
        pass

    def move_to_proportional(self, x: float, y: float) -> None:
        assert x >= 0 and x <= 1, 'x not in range 0-1'
        assert y >= 0 and y <= 1, 'y not in range 0-1'
        assert self.pointer is not None, 'No pointer'
        assert self.display is not None, 'No display'
        self.pointer.motion_absolute(self.timestamp(), int(x * 1000), int(y * 1000), 1000, 1000)
        self.pointer.frame()
        self.display.roundtrip()

    def button(self, button: Button, state: bool) -> None:
        assert self.pointer is not None, 'No pointer'
        assert self.display is not None, 'No display'
        self.pointer.button(self.timestamp(), button, 1 if state else 0)
        self.pointer.frame()
        self.display.roundtrip()

    async def __aenter__(self) -> 'VirtualPointer':
        return await super().__aenter__() # type: ignore
