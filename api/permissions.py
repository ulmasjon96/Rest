from rest_framework import permissions

from restaurant.models import Profile


def get_role(user):
    """Foydalanuvchi roli: anonim uchun None, is_superuser = admin, profili yo'q = customer."""
    if user is None or not user.is_authenticated:
        return None
    if user.is_superuser:
        return Profile.ADMIN
    profile = getattr(user, 'profile', None)
    return profile.role if profile else Profile.CUSTOMER


class IsAdminRole(permissions.BasePermission):
    def has_permission(self, request, view):
        return get_role(request.user) == Profile.ADMIN


class IsAdminOrReadOnly(permissions.BasePermission):
    """O'qish hammaga (anonim ham), yozish faqat adminga."""
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS or get_role(request.user) == Profile.ADMIN


class IsKitchenStaff(permissions.BasePermission):
    def has_permission(self, request, view):
        return get_role(request.user) in (Profile.ADMIN, Profile.WAITER, Profile.CHEF)


class ReservationPermission(permissions.BasePermission):
    """Waiter va admin hammasini boshqaradi; mijoz ko'radi, yaratadi, bekor qiladi; oshpazga yopiq."""
    def has_permission(self, request, view):
        role = get_role(request.user)
        if role in (Profile.ADMIN, Profile.WAITER):
            return True
        if role == Profile.CUSTOMER:
            return request.method in permissions.SAFE_METHODS or view.action in ('create', 'cancel')
        return False


class OrderPermission(permissions.BasePermission):
    """Waiter va admin hammasini boshqaradi; mijoz ko'radi va yaratadi; oshpaz ko'radi va holatni o'zgartiradi."""
    def has_permission(self, request, view):
        role = get_role(request.user)
        if role in (Profile.ADMIN, Profile.WAITER):
            return True
        if role == Profile.CHEF:
            return request.method in permissions.SAFE_METHODS or view.action == 'set_status'
        if role == Profile.CUSTOMER:
            return request.method in permissions.SAFE_METHODS or view.action == 'create'
        return False
