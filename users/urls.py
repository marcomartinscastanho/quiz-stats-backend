from django.urls import path

from users.views import (
    CurrentUserDetailView,
    MyGroupsView,
    UserCategoryGroupStatsView,
    UserCategoryStatsView,
    UsersInMyGroupsView,
)

urlpatterns = [
    # api/users/
    path("me/", CurrentUserDetailView.as_view(), name="user-detail"),
    path("groups/", MyGroupsView.as_view(), name="my-groups"),
    path("in-my-groups/", UsersInMyGroupsView.as_view(), name="users-in-my-groups"),
    path("categories/stats/", UserCategoryStatsView.as_view(), name="user-category-stats"),
    path("groups/stats/", UserCategoryGroupStatsView.as_view(), name="user-group-stats"),
]
