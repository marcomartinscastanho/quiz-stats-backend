from django.contrib.auth.models import Group
from rest_framework import serializers

from users.serializers import UserShortSerializer


class TeamSerializer(serializers.ModelSerializer):
    users = UserShortSerializer(source="user_set", many=True)

    class Meta:
        model = Group
        fields = ["id", "name", "users"]
