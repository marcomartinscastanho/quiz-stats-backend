from rest_framework import serializers

from quizzes.models import Category, Question, Quiz, QuizPart, Topic


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
