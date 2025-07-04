from rest_framework import serializers

from answers.models import UserAnswer
from openai_utils.client import ask_chatgpt
from openai_utils.loaders import get_prompt
from quizzes.models import Question


class UserAnswerSerializer(serializers.ModelSerializer):
    answer = serializers.CharField(required=False, write_only=True)
    is_correct = serializers.BooleanField(required=False)

    class Meta:
        model = UserAnswer
        fields = ["id", "question", "is_correct", "answer", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]

    def validate(self, data):
        if data.get("is_correct") is None and data.get("answer") is None:
            raise serializers.ValidationError("Either 'is_correct' or 'answer' must be provided.")
        return data

    def create(self, validated_data):
        user = self.context["request"].user
        answer = validated_data.pop("answer", None)
        question = validated_data["question"]
        if "is_correct" not in validated_data:
            validated_data["is_correct"] = self.check_answer(answer, question)
        # Update or create the UserAnswer
        user_answer, _ = UserAnswer.objects.update_or_create(
            user=user, question=question, defaults={"is_correct": validated_data["is_correct"]}
        )
        return user_answer

    def check_answer(self, provided_answer: str, question: Question):
        prompt = get_prompt(
            "check_answer", statement=question.statement, correct_answer=question.answer, answer=provided_answer
        )
        result = ask_chatgpt(prompt)
        return result is not None and result.strip().lower() == "true"
