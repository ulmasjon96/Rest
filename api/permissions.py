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


class IsOwnerOrAdmin(permissions.BasePermission):
    """Foydalanuvchi yozuvi bilan faqat uning egasi yoki admin ishlay oladi."""
    message = 'Bu amal faqat hisob egasi yoki administrator uchun ruxsat etilgan.'

    def has_object_permission(self, request, view, obj):
        return obj == request.user or get_role(request.user) == Profile.ADMIN


class IsSelfOrAdminForWrite(permissions.BasePermission):
    """Superuser hisobini faqat superuserning o'zi o'zgartira oladi.

    Aks holda 'admin' rolidagi oddiy foydalanuvchi superuserning username va emailini
    o'zgartirishi yoki hisobiga aralashishi mumkin edi. O'qishga ta'sir qilmaydi.
    """
    message = 'Superuser hisobini faqat superuser o‘zgartira oladi.'

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS or obj == request.user:
            return True
        return request.user.is_superuser or not obj.is_superuser


class IsProductOwner(permissions.BasePermission):
    """Mahsulotni faqat uni yaratgan foydalanuvchi o'zgartiradi. Rol va superuser ataylab tekshirilmaydi."""
    message = 'Bu mahsulotni faqat uni yaratgan foydalanuvchi o‘zgartira oladi.'

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.created_by == request.user


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
