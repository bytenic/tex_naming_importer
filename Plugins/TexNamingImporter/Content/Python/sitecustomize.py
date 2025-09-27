from pathlib import Path
import sys

_PLUGIN_PY = Path(__file__).resolve().parent
if str(_PLUGIN_PY) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_PY))