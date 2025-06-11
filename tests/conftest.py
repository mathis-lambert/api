import sys
import types
from pathlib import Path

module = types.ModuleType("mistralai")
module.Mistral = object
sys.modules.setdefault("mistralai", module)

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
