from pathlib import Path
from typing import Dict

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


def generate_protocol(path: Path, name: str, imports: Dict[str, str]) -> Dict[str, str]:
    import pywayland
    import pywayland.scanner

    input_path = path / "data" / f"{name}.xml"
    proto = pywayland.scanner.Protocol.parse_file(str(input_path))
    proto_imports = {iface.name: proto.name for iface in proto.interface}
    output_dir = path / "protocols"
    proto.output(str(output_dir), dict(proto_imports, **imports))
    return proto_imports


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version, build_data):
        path = Path(__file__).parent / "mir_ci" / "wayland"
        core_imports = generate_protocol(path, "wayland", {})
        generate_protocol(path, "wlr-screencopy-unstable-v1", core_imports)
        generate_protocol(path, "wlr-virtual-pointer-unstable-v1", core_imports)
        generate_protocol(path, "xdg-output-unstable-v1", core_imports)
