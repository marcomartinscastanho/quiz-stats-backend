import random

from django.contrib.auth import get_user_model
from django.db.models import Count, F, Q
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from answers.models import UserAnswer
from quizzes.models import Category, Quiz, Topic
from quizzes.serializers import CategorySerializer, QuizSerializer, TopicSerializer

User = get_user_model()


class CategoriesView(ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class QuizzesView(ListAPIView):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer


class CategoryUserStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, *args, **kwargs):
        # Prefetch related questions and their categories upfront
        categories = Category.objects.prefetch_related("questions")
        result = []
        for category in categories:
            # Get all questions for this category
            questions = category.questions.all()
            # Get all UserAnswers for these questions
            user_answers = (
                UserAnswer.objects.filter(question__in=questions)
                .select_related("user")
                .values("user_id", "user__username", "user__first_name", "user__last_name")
                .annotate(correct_count=Count("id", filter=Q(is_correct=True)), total_count=Count("id"))
            )
            # Prepare per-user stats
            user_stats = {}
            for ua in user_answers:
                user_id = ua["user_id"]
                # Compose display name: prefer full name if exists, else username
                full_name = (ua["user__first_name"] + " " + ua["user__last_name"]).strip()
                display_name = full_name if full_name else ua["user__username"]
                user_stats[user_id] = {"user": display_name, "correct": ua["correct_count"], "total": ua["total_count"]}
            # Format response for this category
            users_result = []
            for stat in user_stats.values():
                if stat["total"] > 0:
                    stat["xC"] = round((stat["correct"] / stat["total"]) * 2, 1)
                    users_result.append({"user": stat["user"], "xC": stat["xC"], "answered": stat["total"]})
            # Sort users by xC descending
            users_result.sort(key=lambda u: u["xC"], reverse=True)
            result.append({"category_name": category.name, "users": users_result})
        return Response(result)


class RandomUnansweredTopicView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, *args, **kwargs):
        user = self.request.user
        # Annotate topics with total and answered questions
        topics = Topic.objects.annotate(
            total_questions=Count("questions", distinct=True),
            answered_questions=Count(
                "questions__useranswer", filter=Q(questions__useranswer__user=user), distinct=True
            ),
        ).filter(answered_questions__lt=F("total_questions"))
        if not topics.exists():
            return Response({"message": "No unanswered topics left", "result": None})
        # Pick a random topic from the filtered queryset
        topic = random.choice(list(topics))
        serializer = TopicSerializer(topic)
        return Response({"message": "Random unanswered topic", "result": serializer.data})
