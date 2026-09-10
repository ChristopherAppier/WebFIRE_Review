from openai import OpenAI

client = OpenAI(
    api_key="secret_api_key",
    base_url="http://localhost:11436/v1",
)

response = client.responses.create(
    model="gemma4:26b",
    instructions="You are a coding assistant that talks like a pirate.",
    input="How do I check if a Python object is an instance of a class?",
)

print(response.output_text)