from django.urls import path

from quizzes.views import (
    CategoriesView,
    CategoryUserStatsView,
    ListQuizProgressView,
    PredictedTopicStatsView,
    QuizUnansweredQuestionsView,
    QuizView,
    QuizzesView,
    RandomUnansweredTopicView,
)

urlpatterns = [
    # api/quizzes/
    path("", QuizzesView.as_view(), name="list-all-quizzes"),
    path("<int:pk>/", QuizView.as_view(), name="get-quizzes"),
    path("<int:pk>/unanswered/", QuizUnansweredQuestionsView.as_view(), name="get-unanswered-quiz"),
    path("categories/", CategoriesView.as_view(), name="list-all-categories"),
    path("categories/users/stats/", CategoryUserStatsView.as_view(), name="category-user-stats"),
    path("progress/", ListQuizProgressView.as_view(), name="quiz-progress"),
    path("stats/predict/", PredictedTopicStatsView.as_view(), name="predict-stats"),
    path("topics/random/", RandomUnansweredTopicView.as_view(), name="random-unanswered-topic"),
]
