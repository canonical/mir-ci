from enum import Enum
from typing import Collection, Optional


class AppType(Enum):
    snap = 0
    deb = 1
    pip = 2


class App:
    command: Collection[str]
    app_type: Optional[AppType]
    extensions: Collection[str]

    def __init__(
        self, command: Collection[str], app_type: Optional[AppType] = None, extensions: Collection[str] = ()
    ) -> None:
        self.command = command
        self.app_type = app_type
        self.extensions = extensions
