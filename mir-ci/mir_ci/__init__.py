import os
from pathlib import Path

import distro

SLOWDOWN = float(os.environ.get("MIR_CI_SLOWDOWN", 1))
VARIANT = Path(os.environ.get("MIR_CI_VARIANT", distro.codename()))
