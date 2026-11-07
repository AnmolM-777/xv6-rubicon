TOOL_SCHEMAS = {
    "list_files": {
        "description": "List files in the allowed directory",
        "arguments": {}
    },

    "read_file": {
        "description": "Read the contents of a file",
        "arguments": {
            "path": str
        }
    },

    "summarize": {
        "description": "Summarize the given text",
        "arguments": {
            "text": str
        }
    }
}
