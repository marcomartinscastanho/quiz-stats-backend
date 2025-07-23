from django.contrib.auth import get_user_model
from django.db.models import Count
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from answers.models import UserAnswer
from quizzes.mixins import CategoryGroupStatsMixin
from users.serializers import UserDetailSerializer, UserListSerializer

User = get_user_model()


class CurrentUserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, *args, **kwargs):
        serializer = UserDetailSerializer(self.request.user)
        return Response(serializer.data)


class UserListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserListSerializer

    def get_queryset(self):
        return (
            User.objects.exclude(is_staff=True).annotate(total_answers=Count("useranswer")).order_by("-total_answers")
        )


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
