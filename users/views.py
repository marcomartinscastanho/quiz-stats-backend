from django.contrib.auth import get_user_model
from django.db.models import Count, Prefetch
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from answers.models import UserAnswer
from quizzes.mixins import CategoryGroupStatsMixin, CategoryStatsMixin
from teams.serializers import TeamSerializer
from users.serializers import UserDetailSerializer, UserShortSerializer

User = get_user_model()


class UserListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserShortSerializer

    def get_queryset(self):
        return (
            User.objects.exclude(is_staff=True).annotate(total_answers=Count("useranswer")).order_by("-total_answers")
        )


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, *args, **kwargs):
        serializer = UserDetailSerializer(self.request.user)
        return Response(serializer.data)


class MyTeamsView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TeamSerializer

    def get_queryset(self):
        users_qs = (
            User.objects.exclude(is_staff=True).annotate(total_answers=Count("useranswer")).order_by("-total_answers")
        )
        return self.request.user.groups.prefetch_related(Prefetch("user_set", queryset=users_qs))


class UserCategoryGroupStatsView(CategoryGroupStatsMixin, GenericAPIView):
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()

    def get_user_answers(self):
        user = self.get_object()
        return (
            UserAnswer.objects.filter(user=user)
            .select_related("question")
            .prefetch_related("question__categories__group")
        )


class UserCategoryStatsView(CategoryStatsMixin, GenericAPIView):
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()

    def get_user_answers(self):
        user = self.get_object()
        return UserAnswer.objects.filter(user=user).select_related("question").prefetch_related("question__categories")
