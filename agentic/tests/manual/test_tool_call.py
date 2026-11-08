import ollama

tools = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files in the xv6 filesystem",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]

response = ollama.chat(
    model="qwen2.5:0.5b",
    messages=[
        {
            "role": "user",
            "content": "Show me the files available in xv6. Use the list_files tool."
        }
    ],
    tools=tools
)

print("Model response:")
print(response.message.content)

print("\nTool calls:")
print(response.message.tool_calls)
