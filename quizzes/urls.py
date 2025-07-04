from django.urls import path

from quizzes.views import CategoriesView, CategoryUserStatsView, QuizzesView, RandomUnansweredTopicView

urlpatterns = [
    # api/quizzes/
    path("", QuizzesView.as_view(), name="list-all-quizzes"),
    path("categories/", CategoriesView.as_view(), name="list-all-categories"),
    path("categories/users/stats/", CategoryUserStatsView.as_view(), name="category-user-stats"),
    path("topics/random/", RandomUnansweredTopicView.as_view(), name="random-unanswered-topic"),
]
