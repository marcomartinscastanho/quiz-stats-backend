from django.urls import path

from teams.views import TeamCategoryGroupStatsView

urlpatterns = [
    # api/teams/
    path("<int:pk>/stats/category-groups/", TeamCategoryGroupStatsView.as_view(), name="category-group-stats-by-team"),
]
