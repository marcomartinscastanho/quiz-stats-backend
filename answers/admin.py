from django.contrib import admin

from answers.models import UserAnswer


@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "question__topic__quiz_part__quiz", "question", "is_correct", "updated_at")
    list_filter = ("user", "question__topic__quiz_part__quiz", "is_correct", "created_at")
    search_fields = ("question__statement",)
    ordering = ("-created_at",)
