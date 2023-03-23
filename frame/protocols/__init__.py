import os
import pywayland
import pywayland.scanner

def generate_protocol(name, imports: dict[str, str]) -> dict[str, str]:
    input_path = os.path.join(os.path.dirname(__file__), '../data', name + '.xml')
    proto = pywayland.scanner.Protocol.parse_file(input_path)
    proto_imports = {iface.name: proto.name for iface in proto.interface}
    output_dir = os.path.join(os.path.dirname(__file__), '../protocols')
    proto.output(output_dir, proto_imports | imports)
    return proto_imports

core_imports = generate_protocol('wayland', {})
generate_protocol('wlr-screencopy-unstable-v1', core_imports)

from .wayland import *
from .wlr_screencopy_unstable_v1 import *
