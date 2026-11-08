import re
from pathlib import Path
from bridge import XV6Bridge

SCENARIO_DIR = Path(__file__).parent / "scenarios"

bridge = None


def get_safe_path(filename):
    if not isinstance(filename, str):
        raise ValueError("Invalid filename")

    if not re.fullmatch(r"[A-Za-z0-9_.-]+", filename):
        raise ValueError("Invalid filename")

    base = SCENARIO_DIR.resolve()
    path = (base / filename).resolve()

    if path.parent != base:
        raise ValueError("Unsafe file path")

    return path


def get_bridge():
    global bridge

    if bridge is None or bridge.sock is None:
        bridge = XV6Bridge()

    return bridge


def list_files():
    return get_bridge().execute("ls")


def read_file(path):
    get_safe_path(path)
    return get_bridge().execute("cat " + path)


def summarize(text):
    words = text.split()
    return " ".join(words[:20])
