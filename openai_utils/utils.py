import hashlib


def get_cache_key(prompt: str):
    prompt_hash = hashlib.md5(prompt.encode("utf-8")).hexdigest()
    print("prompt_hash", prompt_hash)
    return f"ask_chatgpt:{prompt_hash}"
