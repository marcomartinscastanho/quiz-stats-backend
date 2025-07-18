from django.contrib.auth import get_user_model
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from answers.models import UserAnswer
from quizzes.models import CategoryGroup
from users.serializers import GroupSerializer, UserDetailSerializer

User = get_user_model()


class CurrentUserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, *args, **kwargs):
        serializer = UserDetailSerializer(self.request.user)
        return Response(serializer.data)


class MyGroupsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, *args, **kwargs):
        groups = self.request.user.groups.all()
        serializer = GroupSerializer(groups, many=True)
        return Response(serializer.data)


class UsersInMyGroupsView(ListAPIView):
    serializer_class = UserDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Get group IDs of the requesting user
        user_groups = self.request.user.groups.all()
        # Get users who share any of those groups
        return User.objects.filter(groups__in=user_groups).distinct()


class UserCategoryStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, *args, **kwargs):
        user = self.request.user
        # Get UserAnswer queryset for the user, select related question and categories for efficiency
        user_answers = (
            UserAnswer.objects.filter(user=user).select_related("question").prefetch_related("question__categories")
        )
        # Prepare a dict to hold category stats
        category_stats = {}
        # Iterate through user answers, categorize and count correct/total
        for ua in user_answers:
            for category in ua.question.categories.all():
                stats = category_stats.setdefault(category.name, {"correct": 0, "total": 0})
                stats["total"] += 1
                if ua.is_correct:
                    stats["correct"] += 1
        # Format response sorted by xC value descending
        response = sorted(
            [
                {
                    "category_name": name,
                    "xC": round((data["correct"] / data["total"]) * 2, 1),
                    "answered": data["total"],
                }
                for name, data in category_stats.items()
            ],
            key=lambda x: x["xC"],
            reverse=True,
        )
        return Response(response)


class UserCategoryGroupStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, *args, **kwargs):
        user = self.request.user

        # Load all category groups
        all_groups = CategoryGroup.objects.all()
        group_stats = {group.name: {"correct": 0, "total": 0} for group in all_groups}

        # Fetch user answers and prefetch related categories and their groups
        user_answers = (
            UserAnswer.objects.filter(user=user)
            .select_related("question")
            .prefetch_related("question__categories__group")
        )

        for ua in user_answers:
            for category in ua.question.categories.all():
                group = category.group
                stats = group_stats[group.name]
                stats["total"] += 1
                if ua.is_correct:
                    stats["correct"] += 1

        # Prepare sorted response
        response = sorted(
            [
                {
                    "group_name": group_name,
                    "xC": round((stats["correct"] / stats["total"]) * 2, 1) if stats["total"] > 0 else 0.0,
                    "answered": stats["total"],
                }
                for group_name, stats in group_stats.items()
            ],
            key=lambda x: x["xC"],
            reverse=True,
        )

        return Response(response)
