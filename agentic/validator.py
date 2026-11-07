from schemas import TOOL_SCHEMAS
from pathlib import Path


def validate_request(request):

    if not isinstance(request, dict):
        return False, "Invalid request format"

    tool = request.get("tool")
    arguments = request.get("arguments")

    if tool not in TOOL_SCHEMAS:
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
        path = Path(arguments["path"])

        if path.is_absolute() or ".." in path.parts:
            return False, "Path traversal not allowed"

    return True, "Request approved"
