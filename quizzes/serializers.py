from django.contrib.auth import get_user_model
from rest_framework import serializers

from quizzes.models import Category, CategoryGroup, Question, Quiz, QuizPart, Topic

User = get_user_model()


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]


class CategoryGroupSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True)

    class Meta:
        model = CategoryGroup
        fields = ["id", "name", "categories"]


class QuestionSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True)

    class Meta:
        model = Question
        fields = ["id", "statement", "answer", "categories"]


class TopicSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True)

    class Meta:
        model = Topic
        fields = ["title", "questions"]


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


class CategorizedTopicSerializer(serializers.Serializer):
    topic = serializers.CharField()
    categories = CategorySerializer(many=True)


class TopicCategorizationSerializer(serializers.Serializer):
    first_half_topics = serializers.ListField(child=serializers.CharField(), allow_empty=False, write_only=True)
    second_half_topics = serializers.ListField(child=serializers.CharField(), allow_empty=False, write_only=True)
    first_half_categories = serializers.ListField(child=CategorizedTopicSerializer(), read_only=True)
    second_half_categories = serializers.ListField(child=CategorizedTopicSerializer(), read_only=True)


class QuizProgressSerializer(serializers.ModelSerializer):
    progress = serializers.FloatField()
    correct = serializers.FloatField()

    class Meta:
        model = Quiz
        fields = ["id", "season", "week", "progress", "correct"]


class QuestionCategoryUpdateSerializer(serializers.Serializer):
    category_ids = serializers.ListField(child=serializers.IntegerField(min_value=1), allow_empty=False)

    def validate_category_ids(self, value):
        existing_ids = set(Category.objects.filter(id__in=value).values_list("id", flat=True))
        if len(existing_ids) != len(set(value)):
            raise serializers.ValidationError("One or more category IDs are invalid.")
        return value


class CategoryGroupStatsSerializer(serializers.Serializer):
    group_id = serializers.IntegerField()
    group_name = serializers.CharField()
    xC = serializers.FloatField()
    answered = serializers.IntegerField()
