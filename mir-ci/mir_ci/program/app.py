from typing import Collection, Literal, Optional

AppType = Literal["snap", "deb", "pip"]


class App:
    command: Collection[str]
    app_type: Optional[AppType]

    def __init__(self, command: Collection[str], app_type: Optional[AppType] = None) -> None:
        self.command = command
        self.app_type = app_type
