from rest_framework import permissions


class IsGroupMember(permissions.BasePermission):
    def has_permission(self, request, view):
        # Allow access only if user is authenticated and group pk is provided
        return request.user and request.user.is_authenticated and "pk" in view.kwargs

    def has_object_permission(self, request, view, obj):
        # obj here is the Group instance
        return request.user in obj.user_set.all()
