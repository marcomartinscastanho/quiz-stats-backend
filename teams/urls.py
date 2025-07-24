from django.urls import path

from teams.views import TeamCategoryGroupStatsView, TeamView

urlpatterns = [
    # api/teams/
    path("<int:pk>/", TeamView.as_view(), name="get-team"),
    path("<int:pk>/stats/category-groups/", TeamCategoryGroupStatsView.as_view(), name="category-group-stats-by-team"),
]
