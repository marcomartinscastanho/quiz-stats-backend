import json

from django.contrib import admin
from django.db.models import Count, QuerySet
from django.http import HttpResponse

from answers.models import UserAnswer
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
    actions = ["download_json"]

    @admin.action(description="Download as JSON")
    def download_json(self, request, queryset: QuerySet[CategoryGroup]):
        """
        Admin action to download selected CategoryGroups with their Categories as JSON.
        """
        data = []
        for group in queryset.prefetch_related("categories"):
            group_data = {
                "id": group.pk,
                "name": group.name,
                "categories": [
                    {"id": cat.pk, "name": cat.name, "description": cat.description, "# questions": cat._question_count}
                    for cat in group.categories.annotate(_question_count=Count("questions", distinct=True)).all()
                ],
            }
            data.append(group_data)

        response = HttpResponse(json.dumps(data, indent=2), content_type="application/json")
        response["Content-Disposition"] = 'attachment; filename="category_groups.json"'
        return response


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "group", "description", "question_count"]
    list_filter = ["group"]
    search_fields = ["name"]
    ordering = ["group__name", "name"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(_question_count=Count("questions", distinct=True))

    @admin.display(ordering="_question_count", description="# questions")
    def question_count(self, obj):
        return obj._question_count


class UserAnswerInline(admin.TabularInline):
    model = UserAnswer
    extra = 0  # no empty forms
    fields = ("user", "is_correct", "created_at")
    readonly_fields = ("user", "is_correct", "created_at")
    can_delete = False
    show_change_link = True


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("short_statement", "answer", "has_category_display")
    list_filter = ("categories", HasCategoryFilter)
    search_fields = ("statement", "answer")
    readonly_fields = ["topic", "statement", "answer", "is_box"]
    inlines = [UserAnswerInline]

    @admin.display(description="Question")
    def short_statement(self, obj: Question):
        return (obj.statement[:75] + "...") if len(obj.statement) > 75 else obj.statement

    @admin.display(description="Categories")
    def categories_list(self, obj: Question):
        return ", ".join(cat.name for cat in obj.categories.all())

    @admin.display(boolean=True, description="Has category")
    def has_category_display(self, obj):
        return obj.has_category
