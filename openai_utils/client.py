from openai import OpenAI

client = OpenAI()


def ask_chatgpt(prompt: str):
    if not prompt:
        return

    instructions = "You are a quiz assistant that answer with few words"
    response = client.responses.create(model="gpt-4.1-nano", instructions=instructions, input=prompt)

    return response.output_text
