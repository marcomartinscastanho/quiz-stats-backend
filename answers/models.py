from django.db import models

from quizzes.models import Question
from users.models import User


class UserAnswer(models.Model):
    user = models.ForeignKey(to=User, on_delete=models.CASCADE)
    question = models.ForeignKey(to=Question, on_delete=models.CASCADE)
    is_correct = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "question"], name="unique_user_question_answer")]
