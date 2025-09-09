from django.db.models.signals import post_save
from django.dispatch import receiver

from quizzes.models import Question
from quizzes.utils import categorize_question


@receiver(post_save, sender=Question)
def categorize_question_signal(sender, instance: Question, created, **kwargs):
    if created:
        categorize_question(instance)
