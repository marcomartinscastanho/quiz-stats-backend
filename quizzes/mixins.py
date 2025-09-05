from django.db.models import QuerySet
from rest_framework.response import Response

from answers.models import UserAnswer
from quizzes.models import Category, CategoryGroup
from quizzes.serializers import CategoryGroupStatsSerializer, CategoryStatsSerializer


class CategoryGroupStatsMixin:
    serializer_class = CategoryGroupStatsSerializer

    def get_user_answers(self):
        """
        Return a queryset of UserAnswer objects for the user(s) relevant to the view.
        Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement get_user_answers()")

    def get_category_group_stats(self, user_answers: QuerySet[UserAnswer]):
        all_category_groups = CategoryGroup.objects.all().order_by("id")
        category_group_stats = {
            group.pk: {"group_name": group.name, "correct": 0, "total": 0} for group in all_category_groups
        }
        for ua in user_answers:
            for category in ua.question.categories.all():
                category_group = category.group
                stats = category_group_stats[category_group.pk]
                stats["total"] += 1
                if ua.is_correct:
                    stats["correct"] += 1
        return category_group_stats

    def get(self, *args, **kwargs):
        user_answers = self.get_user_answers()
        stats = self.get_category_group_stats(user_answers)
        response_data = [
            {
                "group_id": category_group_id,
                "group_name": stats["group_name"],
                "xC": (stats["correct"] / stats["total"]) * 2 if stats["total"] > 0 else 0.0,
                "answered": stats["total"],
            }
            for category_group_id, stats in stats.items()
        ]
        response_data = sorted(response_data, key=lambda x: x["group_id"])
        serializer = self.get_serializer(response_data, many=True)
        return Response(serializer.data)


class CategoryStatsMixin:
    serializer_class = CategoryStatsSerializer

    def get_user_answers(self):
        raise NotImplementedError("Subclasses must implement get_user_answers()")

    def get_category_stats(self, user_answers: QuerySet[UserAnswer]):
        all_categories = Category.objects.select_related("group").all().order_by("group__id", "id")
        category_stats = {
            category.pk: {
                "category_name": category.name,
                "category_group_id": category.group.id if category.group else None,
                "correct": 0,
                "total": 0,
            }
            for category in all_categories
        }

        for ua in user_answers:
            for category in ua.question.categories.all():
                stats = category_stats[category.pk]
                stats["total"] += 1
                if ua.is_correct:
                    stats["correct"] += 1
        return category_stats

    def get(self, *args, **kwargs):
        user_answers = self.get_user_answers()
        stats = self.get_category_stats(user_answers)
        response_data = [
            {
                "category_id": category_id,
                "category_name": stats["category_name"],
                "category_group_id": stats["category_group_id"],
                "xC": (stats["correct"] / stats["total"]) * 2 if stats["total"] > 0 else 0.0,
                "answered": stats["total"],
            }
            for category_id, stats in stats.items()
        ]
        response_data = sorted(response_data, key=lambda x: (x["category_group_id"], x["category_id"]))
        serializer = self.get_serializer(response_data, many=True)
        return Response(serializer.data)
