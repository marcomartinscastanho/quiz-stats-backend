from django.contrib.auth import get_user_model
from rest_framework import serializers

from quizzes.models import Category, Question, Quiz, QuizPart, Topic

User = get_user_model()


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]


class QuestionSerializer(serializers.ModelSerializer):
    categories = serializers.SerializerMethodField()
    xP = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = ["id", "statement", "answer", "categories", "xP"]

    def get_categories(self, obj: Question):
        return list(obj.categories.values_list("name", flat=True))

    def get_xP(self, obj: Question):
        return round(obj.xP, 2) if obj.xP is not None else None


class TopicSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True)
    xT = serializers.SerializerMethodField()

    class Meta:
        model = Topic
        fields = ["title", "questions", "xT"]

    def get_xT(self, obj: Topic):
        return round(obj.xT, 2) if obj.xT is not None else None


class QuizPartSerializer(serializers.ModelSerializer):
    topics = TopicSerializer(many=True)

    class Meta:
        model = QuizPart
        fields = ["topics"]


class QuizSerializer(serializers.ModelSerializer):
    parts = QuizPartSerializer(many=True)

    class Meta:
        model = Quiz
        fields = ["season", "week", "parts"]


class PredictedTopicStatsInputSerializer(serializers.Serializer):
    user_ids = serializers.ListField(child=serializers.IntegerField(min_value=1), allow_empty=False)
    topics = serializers.ListField(child=serializers.CharField(max_length=100), allow_empty=False)

    def validate_user_ids(self, value):
        missing_ids = set(value) - set(User.objects.filter(id__in=value).values_list("id", flat=True))
        if missing_ids:
            raise serializers.ValidationError(f"Invalid user_ids: {list(missing_ids)}")
        return value
