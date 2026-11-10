def plan_request(command):

    command = command.strip()

    if not command:
        return None

    if command == "list":
        return {
            "tool": "list_files",
            "arguments": {}
        }

    if command.startswith("read "):
        path = command[5:].strip()

        if not path:
            return None

        return {
            "tool": "read_file",
            "arguments": {"path": path}
        }

    if command.startswith("summarize "):
        text = command[10:].strip()

        if not text:
            return None

        return {
            "tool": "summarize",
            "arguments": {"text": text}
        }

    return None
