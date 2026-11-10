from openai import OpenAI

client = OpenAI()

response = client.responses.create(
    model="gpt-6-luna",
    input="Explain what an operating system does in two sentences."
)

print("LLM Response:")
print(response.output_text)
