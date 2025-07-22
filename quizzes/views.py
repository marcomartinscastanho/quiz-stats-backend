import random
from collections import defaultdict

from django.contrib.auth import get_user_model
from django.db.models import Count, Exists, F, OuterRef, Prefetch, Q, QuerySet
from rest_framework.generics import ListAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from answers.models import UserAnswer
from openai_utils.client import ask_chatgpt
from openai_utils.loaders import get_prompt
from quizzes.models import Category, CategoryGroup, Question, Quiz, Topic
from quizzes.serializers import (
    CategoryGroupSerializer,
    CategorySerializer,
    PredictedTopicStatsInputSerializer,
    QuestionCategoryUpdateSerializer,
    QuizProgressSerializer,
    QuizSerializer,
    TopicSerializer,
)

User = get_user_model()


class CategoryGroupListView(ListAPIView):
    queryset = CategoryGroup.objects.all().order_by("id")
    serializer_class = CategoryGroupSerializer
    permission_classes = []


class CategoriesView(ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class QuizzesView(ListAPIView):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer


class QuizView(RetrieveAPIView):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer


class QuizUnansweredQuestionsView(RetrieveAPIView):
    queryset = Quiz.objects.prefetch_related("parts__topics__questions")
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        answered_qs = UserAnswer.objects.filter(user=user).values_list("question_id", flat=True)
        unanswered_questions = Question.objects.exclude(id__in=answered_qs)
        topic_has_unanswered = Exists(unanswered_questions.filter(topic=OuterRef("pk")))
        topics_with_unanswered = Topic.objects.annotate(has_unanswered=topic_has_unanswered).filter(has_unanswered=True)
        return Quiz.objects.prefetch_related(
            Prefetch(
                "parts__topics",
                queryset=topics_with_unanswered.prefetch_related(Prefetch("questions", queryset=unanswered_questions)),
            )
        ).order_by("season", "week")


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


class PredictedTopicStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, *args, **kwargs):
        serializer = PredictedTopicStatsInputSerializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        user_ids = validated_data["user_ids"]
        topic_names: list[str] = validated_data["topics"]
        users = User.objects.filter(id__in=user_ids).only("id", "username")
        # users_by_id = {u.id: u for u in users}
        # Map: topic_name -> list of Category instances (from your aux function)
        categories = Category.objects.all()
        print("categories", categories)
        topic_to_categories = {
            topic_name: self._get_categories_for_topic(topic_name, categories) for topic_name in topic_names
        }
        print("topic_to_categories", topic_to_categories)
        # Flatten all categories to reduce queries
        all_categories = set(cat.pk for cats in topic_to_categories.values() for cat in cats.all())
        print("all_categories", all_categories)
        # Prefetch all UserAnswers relevant to the users and categories involved
        user_answers = UserAnswer.objects.filter(user_id__in=user_ids, question__categories__in=all_categories).values(
            "user_id", "question__categories", "is_correct"
        )
        # Build lookup table: (user_id, category_id) -> [correct, total]
        category_answer_counts = defaultdict(lambda: {"correct": 0, "total": 0})
        for ua in user_answers:
            category_id = ua["question__categories"]
            key = (ua["user_id"], category_id)
            category_answer_counts[key]["total"] += 1
            if ua["is_correct"]:
                category_answer_counts[key]["correct"] += 1
        results = []
        for topic_name in topic_names:
            categories = topic_to_categories.get(topic_name, [])
            category_ids = [c.pk for c in categories]
            topic_predicted_xT = 0.0
            topic_users_data = []
            for user in users:
                predicted_user_xT = 0
                for category_id in category_ids:
                    stats = category_answer_counts.get((user.pk, category_id))
                    if stats and stats["total"]:
                        predicted_user_xC = (stats["correct"] / stats["total"]) * 2
                        predicted_user_xT += predicted_user_xC
                topic_users_data.append(
                    {"id": user.pk, "username": user.username, "predicted_user_xT": round(predicted_user_xT, 1)}
                )
                topic_predicted_xT += predicted_user_xT
            topic_users_data.sort(key=lambda x: x["predicted_user_xT"], reverse=True)
            results.append(
                {
                    "topic_name": topic_name,
                    "predicted_team_xT": round(topic_predicted_xT, 1),
                    "categories": [c.name for c in categories],
                    "users": topic_users_data,
                }
            )
        results.sort(key=lambda x: x["predicted_team_xT"], reverse=True)
        return Response(results)

    def _get_categories_for_topic(topic_name: str, categories: QuerySet[Category]):
        prompt = get_prompt("categorize_topic", topic=topic_name, categories=categories.values_list("name", flat=True))
        response = ask_chatgpt(prompt)
        category_names = [] if response is None or response == "None" else response.split(",")
        category_names = [c.strip() for c in category_names]
        return categories.filter(name__in=category_names)


class ListQuizProgressView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = QuizProgressSerializer

    def get_queryset(self):
        user = self.request.user
        user_answered_set = set(UserAnswer.objects.filter(user=user).values_list("question_id", flat=True))
        user_correct_set = set(
            UserAnswer.objects.filter(user=user, is_correct=True).values_list("question_id", flat=True)
        )
        quizzes = Quiz.objects.prefetch_related(Prefetch("parts__topics__questions", to_attr="all_questions")).order_by(
            "season", "week"
        )
        for quiz in quizzes:
            # Collect all questions from all quiz parts
            questions = set()
            for part in quiz.parts.all():
                for topic in part.topics.all():
                    for q in topic.questions.all():
                        questions.add(q.id)
            if not questions:
                progress = 0.0
                correctness = 0.0
            else:
                answered = questions & user_answered_set
                correct = questions & user_correct_set
                progress = round((len(answered) / len(questions)) * 100, 1)
                if not answered:
                    correctness = 0.0
                else:
                    correctness = round((len(correct) / len(answered)) * 100, 1)
            quiz.progress = progress
            quiz.correct = correctness
        return quizzes


class UpdateQuestionCategoriesView(UpdateAPIView):
    queryset = Question.objects.all()
    serializer_class = QuestionCategoryUpdateSerializer
    permission_classes = [IsAuthenticated]

    def update(self, *args, **kwargs):
        question = self.get_object()
        serializer = self.get_serializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        category_ids = serializer.validated_data["category_ids"]
        question.categories.set(category_ids)
        return Response({"detail": "Categories updated successfully."})
