from django.urls import path

from users.views import UserCategoryStatsView

urlpatterns = [
    # api/users/
    path("categories/stats/", UserCategoryStatsView.as_view(), name="user-category-stats"),
]
