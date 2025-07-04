from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from answers.models import UserAnswer
from answers.serializers import UserAnswerSerializer


class UserAnswerView(generics.CreateAPIView):
    queryset = UserAnswer.objects.all()
    serializer_class = UserAnswerSerializer
    permission_classes = [IsAuthenticated]

    def create(self, *args, **kwargs):
        user = self.request.user
        question_id = self.request.data.get("question")
        is_correct = self.request.data.get("is_correct")
        if not question_id or is_correct is None:
            return Response({"detail": "Missing 'question' or 'is_correct' field."}, status=status.HTTP_400_BAD_REQUEST)
        # Update or create UserAnswer
        user_answer, created = UserAnswer.objects.update_or_create(
            user=user, question_id=question_id, defaults={"is_correct": is_correct}
        )
        serializer = self.get_serializer(user_answer)
        return Response(serializer.data, status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED)
