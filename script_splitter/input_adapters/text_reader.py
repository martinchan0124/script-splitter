from pathlib import Path
from .models import ScriptInput

def read_script_text(path: str | Path) -> ScriptInput:
    source_path = Path(path)
    text = source_path.read_text(encoding="utf-8")
    return ScriptInput(text=text, source_path=str(source_path))

