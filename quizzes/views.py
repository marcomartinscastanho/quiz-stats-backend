import logging
import random
from collections import Counter, defaultdict

import numpy as np
from django.contrib.auth import get_user_model
from django.db.models import Count, Exists, F, OuterRef, Prefetch, Q
from rest_framework import status
from rest_framework.generics import GenericAPIView, ListAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from answers.models import UserAnswer
from quizzes.models import Category, CategoryGroup, Question, Quiz, Topic
from quizzes.serializers import (
    AptitudeSerializer,
    CategoryGroupSerializer,
    CategorySerializer,
    QuestionCategoryUpdateSerializer,
    QuizProgressSerializer,
    QuizSerializer,
    TopicCategorizationSerializer,
    TopicSerializer,
    XTSerializer,
)
from quizzes.utils import classify_topics_list

User = get_user_model()
logger = logging.getLogger(__name__)


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
        topics_qs = topics_with_unanswered.prefetch_related(Prefetch("questions", queryset=unanswered_questions))
        return Quiz.objects.prefetch_related(Prefetch("parts__topics", queryset=topics_qs)).order_by("season", "week")


class CategoriesView(ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class CategoryGroupListView(ListAPIView):
    queryset = CategoryGroup.objects.prefetch_related("categories").all().order_by("id")
    serializer_class = CategoryGroupSerializer
    permission_classes = []


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
                    stat["xC"] = (stat["correct"] / stat["total"]) * 2
                    users_result.append({"user": stat["user"], "xC": stat["xC"], "answered": stat["total"]})
            # Sort users by xC descending
            users_result.sort(key=lambda u: u["xC"], reverse=True)
            result.append({"category_name": category.name, "users": users_result})
        return Response(result)


class ListQuizProgressView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = QuizProgressSerializer

    def get_queryset(self):
        user = self.request.user
        quizzes = (
            Quiz.objects.prefetch_related("parts__topics__questions")
            .annotate(
                total_questions=Count("parts__topics__questions", distinct=True),
                total_answered=Count(
                    "parts__topics__questions__useranswer",
                    filter=Q(parts__topics__questions__useranswer__user=user),
                    distinct=True,
                ),
                total_correct=Count(
                    "parts__topics__questions__useranswer",
                    filter=Q(
                        parts__topics__questions__useranswer__user=user,
                        parts__topics__questions__useranswer__is_correct=True,
                    ),
                    distinct=True,
                ),
            )
            .order_by("season", "week")
        )
        # Add computed fields
        for quiz in quizzes:
            tq = quiz.total_questions
            ta = quiz.total_answered
            tc = quiz.total_correct
            quiz.progress = (ta / tq) * 100 if tq else 0.0
            quiz.correct = (tc / ta) * 100 if ta else 0.0
        return quizzes


class TopicCategorizationView(GenericAPIView):
    serializer_class = TopicCategorizationSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        first_half = serializer.validated_data["first_half_topics"]
        second_half = serializer.validated_data["second_half_topics"]

        first_half_result = classify_topics_list(first_half)
        second_half_result = classify_topics_list(second_half)

        return Response(
            {"first_half_categories": first_half_result, "second_half_categories": second_half_result},
            status=status.HTTP_200_OK,
        )


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


class AptitudeView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AptitudeSerializer

    def post(self, request: Request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_ids = serializer.validated_data["user_ids"]
        category_ids_input = serializer.validated_data["category_ids"]

        # Frequency (weights) of each category
        category_weights = Counter(category_ids_input)
        unique_category_ids = list(category_weights.keys())
        # Pre-fetch all relevant UserAnswers
        answers = (
            UserAnswer.objects.filter(user_id__in=user_ids, question__categories__in=unique_category_ids)
            .select_related("question")
            .prefetch_related("question__categories")
        )

        # Organize answers by user and category
        user_category_scores = {user_id: {} for user_id in user_ids}
        for answer in answers:
            user_id: int = answer.user_id
            question_categories = answer.question.categories.all()
            is_correct = int(answer.is_correct)
            for category in question_categories:
                if category.id in category_weights:
                    cat_scores = user_category_scores[user_id].setdefault(category.id, [])
                    cat_scores.append(is_correct)

        # Prune categories with fewer than 4 answers
        for user_id, categories in user_category_scores.items():
            user_category_scores[user_id] = {
                cat_id: scores for cat_id, scores in categories.items() if len(scores) >= 4
            }

        # Compute weighted medians
        results = []
        for user_id in user_ids:
            per_category_scores = user_category_scores.get(user_id, {})
            weighted_scores = []
            for cat_id, weight in category_weights.items():
                scores = per_category_scores.get(cat_id, [])
                if scores:
                    accuracy = sum(scores) / len(scores)
                    weighted_scores.extend([accuracy] * weight)
            if weighted_scores:
                weighted_scores.sort()
                median = np.median(weighted_scores) * 2
            else:
                median = 0.0  # or None or 'N/A', depending on preference
            results.append({"user_id": user_id, "aptitude": median})
        # Sort ascending by aptitude (None goes last)
        results.sort(key=lambda x: (x["aptitude"] is None, x["aptitude"]))
        serializer = self.get_serializer(instance=results, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class XTView(GenericAPIView):
    serializer_class = XTSerializer

    def post(self, request: Request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_ids = serializer.validated_data["user_ids"]
        topics = serializer.validated_data["topics"]

        results = {"team": {"topics": []}, "users": []}

        # Preload relevant answers only once
        all_category_ids = {cid for t in topics for cid in t["category_ids"]}
        answers = (
            UserAnswer.objects.filter(Q(user_id__in=user_ids), question__categories__in=all_category_ids)
            .select_related("question")
            .prefetch_related("question__categories")
        )

        # Index answers by user and category
        user_category_answers = defaultdict(lambda: defaultdict(list))
        for ans in answers:
            for category in ans.question.categories.all():
                user_category_answers[ans.user_id][category.id].append(int(ans.is_correct))

        # --- Per user ---
        for user_id in user_ids:
            topic_scores = []
            for topic in topics:
                cat_ids = topic["category_ids"]
                scores = []
                for cid in cat_ids:
                    user_scores = user_category_answers[user_id].get(cid, [])
                    scores.extend(user_scores)
                # prune: only include if at least 4 answers
                xt = 2 * (sum(scores) / len(scores)) if len(scores) >= 4 else 0.0
                topic_scores.append({"topic": topic["name"], "xT": xt})
            topic_scores.sort(key=lambda x: x["xT"], reverse=True)
            results["users"].append({"user_id": user_id, "topics": topic_scores})

        # --- Team ---
        team_topic_scores = []
        for topic in topics:
            cat_ids = topic["category_ids"]
            scores = []
            for user_id in user_ids:
                for cid in cat_ids:
                    user_scores = user_category_answers[user_id].get(cid, [])
                    scores.extend(user_scores)
            xt = 2 * (sum(scores) / len(scores)) if len(scores) >= 4 else 0.0
            team_topic_scores.append({"topic": topic["name"], "xT": xt})
        team_topic_scores.sort(key=lambda x: x["xT"], reverse=True)
        results["team"]["topics"] = team_topic_scores

        # Return using the same serializer
        response_serializer = self.get_serializer(instance=results)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
