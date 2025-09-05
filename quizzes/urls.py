from django.urls import path

from quizzes.views import (
    AptitudeView,
    CategoriesView,
    CategoryGroupListView,
    CategoryUserStatsView,
    ListQuizProgressView,
    QuizUnansweredQuestionsView,
    QuizView,
    RandomUnansweredTopicView,
    TopicCategorizationView,
    UpdateQuestionCategoriesView,
    XTView,
)

urlpatterns = [
    # api/quizzes/
    path("<int:pk>/", QuizView.as_view(), name="get-quiz"),
    path("<int:pk>/unanswered/", QuizUnansweredQuestionsView.as_view(), name="get-unanswered-quiz"),
    path("categories/", CategoriesView.as_view(), name="list-all-categories"),
    path("categories/groups/", CategoryGroupListView.as_view(), name="list-all-groups"),
    path("categories/users/stats/", CategoryUserStatsView.as_view(), name="category-user-stats"),
    path("predictor/topics/categorize/", TopicCategorizationView.as_view(), name="categorize-topics"),
    path("predictor/order-of-play/", AptitudeView.as_view(), name="order-of-play"),
    path("predictor/topics/sort/", XTView.as_view(), name="sort-topics-per-user"),
    path("progress/", ListQuizProgressView.as_view(), name="quiz-progress"),
    path("topics/random/", RandomUnansweredTopicView.as_view(), name="random-unanswered-topic"),
    path(
        "questions/<int:pk>/categories/update/",
        UpdateQuestionCategoriesView.as_view(),
        name="update-question-categories",
    ),
]
