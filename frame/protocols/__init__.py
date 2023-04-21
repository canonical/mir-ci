from pathlib import Path

from typing import Dict

import pywayland
import pywayland.scanner

def generate_protocol(name, imports: Dict[str, str]) -> Dict[str, str]:
    input_path = Path(__file__).parents[1] / 'data' / f'{name}.xml'
    proto = pywayland.scanner.Protocol.parse_file(str(input_path))
    proto_imports = {iface.name: proto.name for iface in proto.interface}
    output_dir = Path(__file__).parents[1] / 'protocols'
    proto.output(str(output_dir), dict(proto_imports, **imports))
    return proto_imports

core_imports = generate_protocol('wayland', {})
generate_protocol('wlr-screencopy-unstable-v1', core_imports)
generate_protocol('wlr-virtual-pointer-unstable-v1', core_imports)

from .wayland import *
from .wlr_screencopy_unstable_v1 import *
from .wlr_virtual_pointer_unstable_v1 import *
