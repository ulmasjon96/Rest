import math
import re

from rest_framework.exceptions import Throttled
from rest_framework.views import exception_handler

# simplejwt va DRF'ning o'zbekchaga tarjima qilinmagan autentifikatsiya xabarlari.
TRANSLATIONS = {
    # simplejwt: token
    'Token is invalid or expired': 'Token noto‘g‘ri yoki muddati o‘tgan.',
    'Token is invalid': 'Token noto‘g‘ri.',
    'Token is expired': 'Token muddati o‘tgan.',
    'Token is blacklisted': 'Token bekor qilingan.',
    'Token has no id': 'Tokenda identifikator yo‘q.',
    'Token has no type': 'Tokenda tur ko‘rsatilmagan.',
    'Token has wrong type': 'Token turi noto‘g‘ri.',
    'Given token not valid for any token type': 'Token hech qaysi token turiga mos kelmaydi.',
    'Invalid algorithm specified': 'Token algoritmi noto‘g‘ri.',
    'Authorization header must contain two space-delimited values':
        'Authorization sarlavhasi probel bilan ajratilgan ikki qismdan iborat bo‘lsin.',
    # simplejwt: foydalanuvchi
    'Token contained no recognizable user identification': 'Tokendan foydalanuvchini aniqlab bo‘lmadi.',
    'User not found': 'Foydalanuvchi topilmadi.',
    'User is inactive': 'Foydalanuvchi faol emas.',
    "The user's password has been changed.": 'Foydalanuvchi paroli o‘zgartirilgan.',
    'No active account found with the given credentials': 'Login yoki parol noto‘g‘ri, yoki hisob faol emas.',
    'No active account found for the given token.': 'Bu token uchun faol hisob topilmadi.',
    # DRF
    'Authentication credentials were not provided.': 'Login ma’lumotlari yuborilmagan.',
    'Invalid username/password.': 'Login yoki parol noto‘g‘ri.',
    'User inactive or deleted.': 'Foydalanuvchi faol emas yoki o‘chirilgan.',
    'Invalid basic header. No credentials provided.': 'Basic sarlavhasi noto‘g‘ri: login ma’lumotlari yo‘q.',
    'Invalid basic header. Credentials string should not contain spaces.': 'Basic sarlavhasi noto‘g‘ri: qiymatda probel bo‘lmasin.',
    'Invalid basic header. Credentials not correctly base64 encoded.': 'Basic sarlavhasi noto‘g‘ri: base64 kodlash xato.',
}

# Ichida o'zgaruvchan qism bor xabarlar.
PATTERNS = [
    (re.compile(r"^Token has no '(.+)' claim$"), r'Tokenda «\1» maydoni yo‘q.'),
    (re.compile(r"^Token '(.+)' claim has expired$"), r'Tokenning «\1» maydoni muddati o‘tgan.'),
    (re.compile(r'^No .+ matches the given query\.$'), 'Yozuv topilmadi.'),
    (re.compile(r'^Method "(.+)" not allowed\.$'), r'«\1» metodi ruxsat etilmagan.'),
    (re.compile(r'^Ensure this value is greater than or equal to (.+)\.$'), r'Qiymat \1 dan kichik bo‘lmasin.'),
]


def translate(text):
    key = str(text)
    if key in TRANSLATIONS:
        return TRANSLATIONS[key]
    for pattern, replacement in PATTERNS:
        if pattern.match(key):
            return pattern.sub(replacement, key)
    return text


def translate_data(data):
    """Javob tuzilmasini saqlagan holda ichidagi matnlarni tarjima qiladi. Kalitlar va `code` o'zgarmaydi."""
    if isinstance(data, dict):
        return {key: value if key == 'code' else translate_data(value) for key, value in data.items()}
    if isinstance(data, list):
        return [translate_data(item) for item in data]
    if isinstance(data, str):
        return translate(data)
    return data


def uzbek_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None
    if isinstance(exc, Throttled):
        message = 'So‘rovlar soni chegaradan oshdi.'
        if exc.wait is not None:
            message += f' {math.ceil(exc.wait)} soniyadan keyin urinib ko‘ring.'
        response.data = {'detail': message}
    else:
        response.data = translate_data(response.data)
    return response
