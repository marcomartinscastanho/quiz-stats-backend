def get_categories_prompt(statement: str, answer: str, categories: list[str]):
    prompt = "I need you to categorize a quiz game question.\n"
    prompt += f"This is the question: '{statement}'\n"
    prompt += f"These are my category options: {categories}\n"
    prompt += "Tell which of my categories better apply to this question/answer.\n"
    prompt += "Up to 2 categories.\n"
    prompt += "If and only if none of my category options fits, you can suggesst other categories yourself.\n"
    prompt += "Be short about the suggested categoy names - max 1 word, in Title Case.\n"
    prompt += "If you suggest categories outside my list, don't be too specific.\n"
    prompt += "Give me just the list of categories, comma separated, nothing else.\n"
    prompt += "Example: `Astronomy,Politics`\n"
    return prompt
