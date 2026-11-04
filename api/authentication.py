from drf_spectacular.authentication import BasicScheme
from rest_framework.authentication import BasicAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed, Throttled
from rest_framework.throttling import SimpleRateThrottle


class FailedLoginThrottle(SimpleRateThrottle):
    """/api/token/ dagi ScopedRateThrottle bilan bitta hisob: IP bo'yicha 'login' doirasi."""
    scope = 'login'

    def get_cache_key(self, request, view):
        return self.cache_format % {'scope': self.scope, 'ident': self.get_ident(request)}


class ThrottledBasicAuthentication(BasicAuthentication):
    """Noto'g'ri parol bilan urinishlarni cheklaydi.

    DRF autentifikatsiyani throttling'dan oldin bajaradi: noto'g'ri parol 401 bilan
    to'xtaydi va hech qachon sanalmaydi. Usiz /api/token/ dagi cheklovni Basic orqali
    aylanib o'tib, parolni cheksiz tanlash mumkin edi. Faqat xato urinishlar sanaladi,
    to'g'ri parol bilan ishlaydigan mijozga bu cheklov ta'sir qilmaydi.
    """
    def authenticate(self, request):
        header = get_authorization_header(request).split()
        if not header or header[0].lower() != b'basic':
            return None

        throttle = FailedLoginThrottle()
        # Chegaradan o'tilganda to'g'ri parol ham rad etiladi, aks holda tanlash davom etaverardi.
        history = throttle.cache.get(throttle.get_cache_key(request, None), [])
        now = throttle.timer()
        recent = [moment for moment in history if moment > now - throttle.duration]
        if len(recent) >= throttle.num_requests:
            raise Throttled(wait=throttle.duration - (now - recent[-1]))

        try:
            return super().authenticate(request)
        except AuthenticationFailed:
            throttle.allow_request(request, None)
            raise


class ThrottledBasicScheme(BasicScheme):
    """Swagger uchun: spectacular BasicAuthentication vorislarini o'zi tanimaydi."""
    target_class = 'api.authentication.ThrottledBasicAuthentication'
