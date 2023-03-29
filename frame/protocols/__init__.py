from pathlib import Path
import pywayland
import pywayland.scanner

def generate_protocol(name, imports: dict[str, str]) -> dict[str, str]:
    input_path = Path(__file__).parent.parent / 'data' / f'{name}.xml'
    proto = pywayland.scanner.Protocol.parse_file(str(input_path))
    proto_imports = {iface.name: proto.name for iface in proto.interface}
    output_dir = Path(__file__).parent.parent / 'protocols'
    proto.output(str(output_dir), proto_imports | imports)
    return proto_imports

core_imports = generate_protocol('wayland', {})
generate_protocol('wlr-screencopy-unstable-v1', core_imports)

from .wayland import *
from .wlr_screencopy_unstable_v1 import *
