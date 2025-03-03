from rest_framework.permissions import SAFE_METHODS, BasePermission


class AdminPermission(BasePermission):
    """Разрешение для пользователя с доступом админ или выше."""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.is_admin

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class UserAnonPermission(BasePermission):
    """
    Права доступа к постам:
    - Анонимный пользователь: только чтение.
    - Пользователь: может изменять только свои записи.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.author == request.user
