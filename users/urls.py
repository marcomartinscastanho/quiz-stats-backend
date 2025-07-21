from django.urls import path

from users.views import (
    CurrentUserDetailView,
    MyGroupsView,
    UserCategoryGroupStatsView,
    UserCategoryStatsView,
    UserListView,
    UsersInMyGroupsView,
)

urlpatterns = [
    # api/users/
    path("", UserListView.as_view(), name="user-list"),
    path("me/", CurrentUserDetailView.as_view(), name="user-detail"),
    path("me/stats/categories/", UserCategoryStatsView.as_view(), name="user-category-stats"),
    path("<identifier>/stats/groups/", UserCategoryGroupStatsView.as_view(), name="user-group-stats"),
    path("groups/", MyGroupsView.as_view(), name="my-groups"),
    path("in-my-groups/", UsersInMyGroupsView.as_view(), name="users-in-my-groups"),
]
