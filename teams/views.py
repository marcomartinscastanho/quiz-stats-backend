from django.contrib.auth.models import Group
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated

from answers.models import UserAnswer
from quizzes.mixins import CategoryGroupStatsMixin
from teams.permissions import IsGroupMember


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
