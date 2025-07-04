from django.db.models.signals import post_save
from django.dispatch import receiver

from quizstats.utils.openai import ask_chatgpt
from quizzes.models import Category, Question
from quizzes.utils import get_categories_prompt


@receiver(post_save, sender=Question)
def create_user_info(sender, instance: Question, created, **kwargs):
    if created:
        all_categories = list(Category.objects.values_list("name", flat=True))
        prompt = get_categories_prompt(instance.statement, instance.answer, all_categories)
        response = ask_chatgpt(prompt)
        print("response", response)
        if not response or response == "None":
            return
        suggested_categories = response.split(",")
        for suggested_category in suggested_categories:
            category, _ = Category.objects.get_or_create(name=suggested_category)
            instance.categories.add(category)
