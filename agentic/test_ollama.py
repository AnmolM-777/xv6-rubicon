import ollama

response = ollama.chat(
    model="qwen2.5:0.5b",
    messages=[
        {
            "role": "user",
            "content": "Explain demand paging in two simple sentences."
        }
    ]
)

print(response["message"]["content"])
