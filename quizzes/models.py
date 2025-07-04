from django.db import models


class Quiz(models.Model):
    season = models.PositiveSmallIntegerField()
    week = models.PositiveSmallIntegerField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=["season", "week"], name="unique_quiz_season_week")]
        verbose_name_plural = "quizzes"

    def __str__(self):
        return f"Season {self.season} - Week {self.week}"


class QuizPart(models.Model):
    quiz = models.ForeignKey(to=Quiz, on_delete=models.CASCADE, related_name="parts")
    sequence = models.PositiveSmallIntegerField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=["quiz", "sequence"], name="unique_part_per_quiz_sequence")]

    def __str__(self):
        return f"{self.quiz} - Part {self.sequence}"


class Topic(models.Model):
    title = models.CharField(max_length=100)
    quiz_part = models.ForeignKey(to=QuizPart, on_delete=models.CASCADE, related_name="topics")

    def __str__(self):
        return self.title

    @property
    def xT(self):
        from answers.models import UserAnswer

        questions = self.questions.all()
        if not questions.exists():
            return None
        # Prefetch all answers for these questions
        answers = UserAnswer.objects.filter(question__in=questions).select_related("question")
        # Group answers by question id
        answer_map = {}
        for ans in answers:
            answer_map.setdefault(ans.question_id, []).append(ans)
        xps = []
        for question in questions:
            q_answers = answer_map.get(question.id, [])
            if not q_answers:
                continue
            correct = sum(1 for a in q_answers if a.is_correct)
            xp = (correct / len(q_answers)) * 2
            xps.append(xp)
        if not xps:
            return None
        return round(sum(xps), 1)


class Category(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Question(models.Model):
    topic = models.ForeignKey(to=Topic, on_delete=models.CASCADE, related_name="questions")
    categories = models.ManyToManyField(to=Category, related_name="questions")
    statement = models.TextField(max_length=1000)
    answer = models.TextField(max_length=255)
    is_box = models.BooleanField(default=False)

    def __str__(self):
        return self.statement

    @property
    def xP(self):
        from answers.models import UserAnswer

        # Get all UserAnswers for this question
        answers = UserAnswer.objects.filter(question=self)
        total = answers.count()
        if total == 0:
            return None
        correct = answers.filter(is_correct=True).count()
        return round((correct / total) * 2, 1)

    @property
    def has_category(self):
        return self.categories.exists()
