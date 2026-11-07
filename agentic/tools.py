from pathlib import Path

BASE_DIR = Path("scenarios").resolve()


def get_safe_path(path):

    file_path = (BASE_DIR / path).resolve()

    if not file_path.is_relative_to(BASE_DIR):
        raise ValueError("Access outside scenarios directory is not allowed")

    return file_path


def list_files():

    files = []

    for item in BASE_DIR.iterdir():
        if item.is_file():
            files.append(item.name)

    return files


def read_file(path):

    file_path = get_safe_path(path)

    if not file_path.is_file():
        raise FileNotFoundError("File not found")

    return file_path.read_text()


def summarize(text):

    words = text.split()

    return " ".join(words[:20])
