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

    def roundtrip(self) -> None:
        # Use this instead of display.roundtrip()
        # Otherwise there will be multiple dispatchers, which can deadlock
        assert self.display is not None, 'No display'
        callback = self.display.sync()
        event = threading.Event()
        def done(callback, callback_data):
            event.set()
        callback.dispatcher['done'] = done
        self.display.flush()
        assert event.wait(10), 'Roundtrip failed'

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
            self.display = pywayland.client.Display(self.display_name)
            self.display.connect()
            def roundtrip():
                raise NotImplementedError(
                    'Use WaylandClient.roundtrip() instead of Display.roundtrip() to avoid deadlock')
            self.display.roundtrip = roundtrip # type: ignore
            self._dispatch_thread.start()
            self._registry = registry = self.display.get_registry()
            registry.dispatcher['global'] = self.registry_global
            self.roundtrip()
            self.connected()
            return self
        except:
            self.__exit__()
            raise

    def __exit__(self, *args) -> None:
        if self.display is not None:
            display = self.display
            callback = self.display.sync()
            event = threading.Event()
            def done(callback, callback_data):
                self.display = None
                event.set()
            callback.dispatcher['done'] = done
            display.flush()
            assert event.wait(10), 'Shutdown roundtrip failed'
            display.disconnect()
        if self._dispatch_thread.is_alive():
            self._dispatch_thread.join()
        self.disconnected()
