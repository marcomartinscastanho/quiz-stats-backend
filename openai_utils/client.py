from django.core.cache import cache
from openai import OpenAI

from openai_utils.utils import get_cache_key

client = OpenAI()


def ask_chatgpt(prompt: str):
    if not prompt:
        return

    cache_key = get_cache_key(prompt)
    cached_response = cache.get(cache_key)
    if cached_response:
        return cached_response

    instructions = "You are a quiz assistant that answer with few words"
    response = client.responses.create(model="gpt-4.1-nano", instructions=instructions, input=prompt)

    output = response.output_text
    cache.set(cache_key, output, timeout=60 * 60)
    return output
