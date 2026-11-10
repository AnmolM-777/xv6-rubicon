import re
from schemas import TOOL_SCHEMAS
from tools import get_safe_path


def validate_request(request):

    if not isinstance(request, dict):
        return False, "Invalid request format"

    tool = request.get("tool")
    arguments = request.get("arguments")

    if not isinstance(tool, str) or tool not in TOOL_SCHEMAS:
        return False, "Tool not allowed"

    if not isinstance(arguments, dict):
        return False, "Invalid arguments format"

    required_args = TOOL_SCHEMAS[tool]["arguments"]

    if set(arguments.keys()) != set(required_args.keys()):
        return False, "Missing or extra arguments"

    for name, expected_type in required_args.items():
        if not isinstance(arguments[name], expected_type):
            return False, f"Invalid type for {name}"

    if "path" in arguments:
        path = arguments["path"]

        if not re.fullmatch(r"[A-Za-z0-9_.-]+", path):
            return False, "Invalid filename"

        try:
            get_safe_path(path)
        except (ValueError, OSError):
            return False, "Invalid or unsafe file path"

    return True, "Request approved"
