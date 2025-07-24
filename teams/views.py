from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db.models import Count, Prefetch
from rest_framework.generics import GenericAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated

from answers.models import UserAnswer
from quizzes.mixins import CategoryGroupStatsMixin
from teams.permissions import IsGroupMember
from teams.serializers import TeamSerializer

User = get_user_model()


class TeamView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Group.objects.all().prefetch_related("user_set")
    serializer_class = TeamSerializer

    def get_queryset(self):
        users_qs = (
            User.objects.exclude(is_staff=True).annotate(total_answers=Count("useranswer")).order_by("-total_answers")
        )
        return Group.objects.all().prefetch_related(Prefetch("user_set", queryset=users_qs))


class TeamCategoryGroupStatsView(CategoryGroupStatsMixin, GenericAPIView):
    queryset = Group.objects.all()
    permission_classes = [IsAuthenticated, IsGroupMember]

    def get_user_answers(self):
        team = self.get_object()
        user_ids_in_team = team.user_set.values_list("id", flat=True)
        return (
            UserAnswer.objects.filter(user__id__in=user_ids_in_team)
            .select_related("question")
            .prefetch_related("question__categories__group")
        )
