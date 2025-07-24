from django.utils.timezone import now
from rest_framework_simplejwt.views import TokenObtainPairView


class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        self.login_user()
        return response

    def login_user(self):
        serializer = self.get_serializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.user
        user.last_login = now()
        user.save(update_fields=["last_login"])
