from django.urls import path

from answers.views import UserAnswerView

urlpatterns = [
    # api/answers/
    path("", UserAnswerView.as_view(), name="useranswer-create"),
]
