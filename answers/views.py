from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from answers.models import UserAnswer
from answers.serializers import UserAnswerSerializer


class UserAnswerView(generics.CreateAPIView):
    queryset = UserAnswer.objects.all()
    serializer_class = UserAnswerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserAnswer.objects.filter(user=self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context
