from pathlib import Path

from django.conf import settings

PROMPTS_DIR = Path(settings.BASE_DIR) / "openai_utils" / "prompts"


def get_prompt(name: str, **kwargs) -> str:
    path = PROMPTS_DIR / f"{name}.prompt"
    with open(path, "r", encoding="utf-8") as f:
        template = f.read()
    return template.format(**kwargs)
