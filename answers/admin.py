from django.contrib import admin

from answers.models import UserAnswer


@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ("user", "short_question", "is_correct", "created_at", "updated_at")
    list_filter = ("is_correct", "created_at")
    search_fields = ("user__username", "question__statement")
    ordering = ("-created_at",)

    @admin.display(description="Question")
    def short_question(self, obj: UserAnswer):
        return (obj.question.statement[:50] + "...") if len(obj.question.statement) > 50 else obj.question.statement
