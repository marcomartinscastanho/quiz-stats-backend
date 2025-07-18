from django.contrib import admin

from quizzes.models import Category, Question, Quiz, QuizPart, Topic


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("season", "week")
    list_filter = ("season",)
    search_fields = ("season", "week")
    ordering = ("-season", "-week")


@admin.register(QuizPart)
class QuizPartAdmin(admin.ModelAdmin):
    list_display = ("quiz", "sequence")
    list_filter = ("quiz__season",)
    search_fields = ("quiz__season", "quiz__week")
    ordering = ("quiz__season", "quiz__week", "sequence")


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("title", "quiz_part")
    list_filter = ("quiz_part__quiz__season",)
    search_fields = ("title",)


class QuestionInline(admin.StackedInline):
    model = Question.categories.through
    extra = 0


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "group"]
    list_filter = ["group"]
    search_fields = ["name"]
    ordering = ["group__name", "name"]
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("short_statement", "answer", "has_category")
    list_filter = ("is_box",)
    search_fields = ("statement", "answer")
    readonly_fields = ["topic", "statement", "answer", "is_box"]

    @admin.display(description="Question")
    def short_statement(self, obj: Question):
        return (obj.statement[:75] + "...") if len(obj.statement) > 75 else obj.statement

    @admin.display(description="Has Category", boolean=True)
    def has_category(self, obj):
        return obj.has_category
