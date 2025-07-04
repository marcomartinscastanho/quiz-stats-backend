from rest_framework import serializers

from answers.models import UserAnswer


class UserAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAnswer
        fields = ["id", "question", "is_correct", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]
