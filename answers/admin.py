from django.contrib import admin

from answers.models import UserAnswer


@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "question", "is_correct", "created_at", "updated_at")
    list_display_links = ("id", "question")
    list_filter = ("user", "is_correct", "created_at")
    search_fields = ("user__username", "question__statement")
    ordering = ("-created_at",)
