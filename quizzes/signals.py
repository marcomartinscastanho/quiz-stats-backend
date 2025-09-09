import difflib

from django.db.models.signals import post_save
from django.dispatch import receiver

from openai_utils.client import ask_chatgpt
from openai_utils.loaders import get_prompt
from quizzes.models import Category, Question


def format_categories_inline():
    categories = Category.objects.all().order_by("name")
    return "\n".join(cat.name for cat in categories)


@receiver(post_save, sender=Question)
def categorize_question(sender, instance: Question, created, **kwargs):
    if created:
        categories = format_categories_inline()
        prompt = get_prompt(
            "categorize_question", question=instance.statement, answer=instance.answer, categories=categories
        )
        response = ask_chatgpt(prompt)
        if not response or response.strip().lower() == "none":
            return

        valid_categories_qs = Category.objects.all()
        valid_category_names = [cat.name for cat in valid_categories_qs]
        valid_category_names_lower = [name.lower() for name in valid_category_names]

        matched_categories = set()
        suggested_categories_raw = [c.strip() for c in response.split(",") if c.strip()]
        for suggested_raw in suggested_categories_raw:
            suggested_lower = suggested_raw.lower()
            matches = difflib.get_close_matches(suggested_lower, valid_category_names_lower, n=1, cutoff=0.8)
            if matches:
                matched_index = valid_category_names_lower.index(matches[0])
                matched_categories.add(valid_category_names[matched_index])
            else:
                pass

        for cat_name in matched_categories:
            category = valid_categories_qs.get(name=cat_name)
            instance.categories.add(category)
