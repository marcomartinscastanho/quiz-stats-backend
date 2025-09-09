from django.db import models
from django.db.models import Count, Q, QuerySet


class Quiz(models.Model):
    season = models.PositiveSmallIntegerField()
    week = models.CharField(max_length=10)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["season", "week"], name="unique_quiz_season_week")]
        verbose_name_plural = "quizzes"

    def __str__(self):
        return f"Season {self.season} - Week {self.week}"


def ppt_upload_path(instance, filename):  # TODO: move
    season = instance.quiz.season
    week = instance.quiz.week
    part_num = instance.sequence
    ext = filename.split(".")[-1]
    return f"quiz_ppts/S{season}/w{week}_part_{part_num}.{ext}"


class QuizPart(models.Model):
    quiz = models.ForeignKey(to=Quiz, on_delete=models.CASCADE, related_name="parts")
    sequence = models.PositiveSmallIntegerField()
    ppt_file = models.FileField(
        upload_to=ppt_upload_path, blank=True, null=True, help_text="Optional PowerPoint file for this quiz part"
    )

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
    def xT(self):  # XXX: never used
        questions: QuerySet[Question] = self.questions.all()
        if not questions.exists():
            return None
        annotated = questions.annotate(
            total_answers=Count("useranswer"),
            correct_answers=Count("useranswer", filter=Q(useranswer__is_correct=True)),
        ).filter(total_answers__gt=0)
        if not annotated.exists():
            return None
        xps = []
        for q in annotated:
            xp = (q.correct_answers / q.total_answers) * 2
            xps.append(xp)
        if not xps:
            return None
        return sum(xps)


class CategoryGroup(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=1024, null=True)
    group = models.ForeignKey(CategoryGroup, related_name="categories", on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = "categories"
        unique_together = ("name", "group")

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
    def xP(self):  # XXX: never used
        from answers.models import UserAnswer

        qs = UserAnswer.objects.filter(question=self).aggregate(
            total=Count("id"), correct=Count("id", filter=Q(is_correct=True))
        )
        total = qs["total"]
        if total == 0:
            return None
        correct = qs["correct"]
        return (correct / total) * 2

    @property
    def has_category(self):
        return self.categories.exists()
