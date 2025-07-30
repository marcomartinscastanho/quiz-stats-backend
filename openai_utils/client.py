from django.core.cache import cache
from openai import OpenAI

from openai_utils.utils import get_cache_key

client = OpenAI()


def ask_chatgpt(prompt: str, model="gpt-4.1-nano"):
    if not prompt:
        return

    cache_key = get_cache_key(prompt)
    cached_response = cache.get(cache_key)
    if cached_response:
        return cached_response

    instructions = "You are a quiz assistant that answer with few words"
    response = client.responses.create(model=model, instructions=instructions, input=prompt)

    output = response.output_text
    cache.set(cache_key, output, timeout=7 * 24 * 60 * 60)  # 7 days
    return output
