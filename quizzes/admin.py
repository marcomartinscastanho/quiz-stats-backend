from django.contrib import admin
from django.db.models import Count

from quizzes.models import Category, CategoryGroup, Question, Quiz, QuizPart, Topic


class HasCategoryFilter(admin.SimpleListFilter):
    title = "Has category"
    parameter_name = "has_category"

    def lookups(self, request, model_admin):
        return [
            ("yes", "Yes"),
            ("no", "No"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(categories__isnull=False).distinct()
        if self.value() == "no":
            return queryset.filter(categories__isnull=True)
        return queryset


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


@admin.register(CategoryGroup)
class CategoryGroupAdmin(admin.ModelAdmin):
    list_display = ["name"]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "group", "question_count"]
    list_filter = ["group"]
    search_fields = ["name"]
    ordering = ["group__name", "name"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(_question_count=Count("questions", distinct=True))

    @admin.display(ordering="_question_count", description="# questions")
    def question_count(self, obj):
        return obj._question_count


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("short_statement", "answer", "has_category_display")
    list_filter = (
        "categories",
        HasCategoryFilter,
    )
    search_fields = ("statement", "answer")
    readonly_fields = ["topic", "statement", "answer", "is_box"]

    @admin.display(description="Question")
    def short_statement(self, obj: Question):
        return (obj.statement[:75] + "...") if len(obj.statement) > 75 else obj.statement

    @admin.display(description="Categories")
    def categories_list(self, obj: Question):
        return ", ".join(cat.name for cat in obj.categories.all())

    @admin.display(boolean=True, description="Has category")
    def has_category_display(self, obj):
        return obj.has_category
