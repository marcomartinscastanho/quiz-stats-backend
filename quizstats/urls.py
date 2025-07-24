from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView

from quizstats.views import CustomTokenObtainPairView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/answers/", include("answers.urls")),
    path("api/quizzes/", include("quizzes.urls")),
    path("api/teams/", include("teams.urls")),
    path("api/users/", include("users.urls")),
]
