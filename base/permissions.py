from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)


class IsAuthenticatedToCreate(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if user and user.is_staff:
            return True
        if user and user.is_authenticated:
            if request.method in ["POST", "GET"]:
                return True
        return False
