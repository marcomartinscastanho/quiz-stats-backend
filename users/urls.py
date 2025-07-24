from django.urls import path

from users.views import MeView, MyTeamsView, UserCategoryGroupStatsView, UserListView

urlpatterns = [
    # api/users/
    path("", UserListView.as_view(), name="user-list"),
    path("me/", MeView.as_view(), name="user-detail"),
    path("me/teams/", MyTeamsView.as_view(), name="my-teams-list"),
    path("<int:pk>/stats/category-groups/", UserCategoryGroupStatsView.as_view(), name="category-group-stats-by-user"),
]
