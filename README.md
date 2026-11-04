# Rest — Restoran API (Django REST Framework)

Bu hujjatda loyihani noldan ishga tushirishgacha qilingan barcha ishlar bor: har bir buyruq, har bir kod qatori, o'rnatilgan paketlar, chiqqan xatolar va ularning qanday tuzatilgani tushuntirib yozilgan.

**Hozirgi holat:** restoran API'si: menyu, stollar, bron, buyurtma, rollar va kunlik hisobot (17–24-bo'limlar). Foydalanuvchi API va JWT (26-bo'lim), mahsulotlar (27-bo'lim). `Book` API o'quv namunasi sifatida qolgan.

---

## Mundarija

1. [Umumiy ma'lumot](#1-umumiy-malumot)
2. [Asosiy tushunchalar](#2-asosiy-tushunchalar)
3. [Papka va virtual muhit](#3-papka-va-virtual-muhit)
4. [Paketlarni o'rnatish](#4-paketlarni-ornatish)
5. [Django loyihasi va app yaratish](#5-django-loyihasi-va-app-yaratish)
6. [Sozlamalar — settings.py](#6-sozlamalar--configsettingspy)
7. [Asosiy URL'lar — config/urls.py](#7-asosiy-urllar--configurlspy)
8. [API kodi — api app](#8-api-kodi--api-app)
9. [Migratsiya, superuser va server](#9-migratsiya-superuser-va-server)
10. [Chiqqan xatolar va yechimlari](#10-chiqqan-xatolar-va-yechimlari)
11. [Tekshirish](#11-tekshirish)
12. [Loyiha tuzilishi](#12-loyiha-tuzilishi)
13. [Boshqa kompyuterda ishga tushirish](#13-boshqa-kompyuterda-ishga-tushirish)
14. [Buyruqlar qisqa jadvali](#14-buyruqlar-qisqa-jadvali)
15. [Xulosa va tavsiyalar](#15-xulosa-va-tavsiyalar)
16. [.env sozlamalari](#16-env-sozlamalari)
17. [Restoran: modellar va bog'lanishlar](#17-restoran-modellar-va-boglanishlar)
18. [Rollar jadvali](#18-rollar-jadvali)
19. [Endpointlar](#19-endpointlar)
20. [Validatsiyalar](#20-validatsiyalar)
21. [Buyurtma holatlari](#21-buyurtma-holatlari)
22. [Misol so'rov va javoblar](#22-misol-sorov-va-javoblar)
23. [Namuna ma'lumot (seed)](#23-namuna-malumot-seed)
24. [Testlarni ishga tushirish](#24-testlarni-ishga-tushirish)
25. [Tarix: klinikadan restoranga o'tish](#25-tarix-klinikadan-restoranga-otish)
26. [Foydalanuvchi va JWT](#26-foydalanuvchi-va-jwt)
27. [Mahsulotlar API](#27-mahsulotlar-api)

---

## 1. Umumiy ma'lumot

| Narsa              | Qiymati                                           |
| ------------------ | ------------------------------------------------- |
| Loyiha papkasi     | `C:\Users\user\Desktop\Rest`                      |
| Operatsion tizim   | Windows, CMD terminali                            |
| Python versiyasi   | **3.13** (dastlab 3.15 edi, 10.1-bo'limga qarang) |
| Virtual muhit      | `env`                                             |
| Django loyihasi    | `config`                                          |
| Django app'lar     | `api` (API kodi), `restaurant` (modellar, admin)  |
| Ma'lumotlar bazasi | SQLite (`db.sqlite3`)                             |
| Superuser          | `admin`                                           |

**Windows yoki WSL?** Django Windows'da to'liq ishlaydi, shuning uchun mashq loyihalari uchun WSL shart emas. Agar loyiha keyin Ubuntu serverga (masalan, Hetzner VPS) deploy qilinadigan bo'lsa yoki PostgreSQL, Docker, Redis va gunicorn ishlatilsa, WSL qulayroq. WSL'da ishlaganda loyihani `/mnt/c/...` ichida emas, `~/projects/` ichida saqlash kerak, aks holda u juda sekin ishlaydi. Windows'da yaratilgan `env` WSL'da ishlamaydi, u yerda muhitni qaytadan yaratish kerak.

---

## 2. Asosiy tushunchalar

| Atama                    | Ma'nosi                                                                                                                                                                 |
| ------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **API**                  | Application Programming Interface: dasturlar bir-biri bilan ma'lumot almashadigan interfeys. Frontend (React) yoki mobil ilova backend'dan ma'lumotni API orqali oladi. |
| **REST**                 | API qurish uslubi. Har bir resursning o'z URL manzili bo'ladi (masalan, `/api/books/`), unga HTTP metodlari orqali murojaat qilinadi.                                   |
| **JSON**                 | Ma'lumot almashish formati, masalan `{"title": "Kitob", "price": "25000.00"}`.                                                                                          |
| **HTTP metodlar**        | `GET` o'qish, `POST` yaratish, `PUT` to'liq tahrirlash, `PATCH` qisman tahrirlash, `DELETE` o'chirish.                                                                  |
| **CRUD**                 | Create, Read, Update, Delete: ma'lumot ustidagi 4 ta asosiy amal.                                                                                                       |
| **Django**               | Python veb-freymvorki.                                                                                                                                                  |
| **DRF**                  | Django REST Framework: Django ustiga REST API qurish uchun kutubxona.                                                                                                   |
| **Virtual muhit (venv)** | Loyihaga xos alohida Python muhiti.                                                                                                                                     |
| **Migratsiya**           | Model o'zgarishlarini ma'lumotlar bazasiga qo'llash uchun yaratiladigan fayl.                                                                                           |
| **Wheel (`.whl`)**       | Oldindan yig'ilgan, o'rnatishga tayyor Python paketi.                                                                                                                   |

---

## 3. Papka va virtual muhit

### 3.1. Papka yaratish

```cmd
cd Desktop
mkdir Rest
cd Rest
```

| Buyruq       | Vazifasi                                                                             |
| ------------ | ------------------------------------------------------------------------------------ |
| `cd Desktop` | **cd** (change directory) joriy papkani o'zgartiradi. Bu yerda Ish stoliga o'tiladi. |
| `cd ..`      | Bir pog'ona yuqoridagi papkaga qaytaradi.                                            |
| `mkdir Rest` | **mkdir** (make directory) `Rest` nomli yangi papka yaratadi.                        |
| `cd Rest`    | Yangi papka ichiga kiradi.                                                           |

### 3.2. Virtual muhit

```cmd
py -3.13 -m venv env
env\Scripts\activate
```

**Virtual muhit nima uchun kerak:** paketlar butun kompyuterga emas, faqat shu loyihaga o'rnatiladi. Shu sababli bir loyihada Django 6, boshqasida Django 4 ishlatilsa ham, ular bir-biriga xalaqit bermaydi.

| Buyruq                       | Vazifasi                                                                                                                                                                             |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `python -m venv env`         | Standart Python bilan `env` nomli virtual muhit yaratadi. `-m` bayrog'i Python modulini (`venv`) dastur sifatida ishga tushiradi, `env` esa muhit papkasining nomi.                  |
| `py -3.13 -m venv env`       | Xuddi shu ishni qiladi, lekin **aniq Python 3.13** ni tanlaydi. `py` Windows'dagi Python launcher bo'lib, kompyuterda bir nechta Python bo'lsa, keraklisini tanlash imkonini beradi. |
| `env\Scripts\activate`       | Muhitni faollashtiradi. Satr boshida `(env)` paydo bo'ladi, shundan keyin `python` va `pip` buyruqlari shu muhitga tegishli bo'ladi. CMD uchun shu buyruq ishlatiladi.               |
| `.\env\Scripts\Activate.ps1` | PowerShell uchun faollashtirish buyrug'i.                                                                                                                                            |
| `source env/bin/activate`    | Linux va WSL uchun faollashtirish buyrug'i.                                                                                                                                          |
| `deactivate`                 | Muhitdan chiqadi.                                                                                                                                                                    |
| `rmdir /s /q env`            | `env` papkasini to'liq o'chiradi. `/s` ichki papkalarni ham o'chiradi, `/q` esa tasdiq so'ramaydi.                                                                                   |

> Eslatma: `env` faol turganida `py -3.13 -m venv env` ni qayta ishga tushirish shart emas. Bu hech narsani buzmaydi, lekin ortiqcha amal.

---

## 4. Paketlarni o'rnatish

### 4.1. Buyruqlar

```cmd
pip install django djangorestframework markdown django-filter djangorestframework-simplejwt django-cors-headers drf-spectacular python-dotenv Pillow "psycopg[binary]"
pip freeze > requirements.txt
python.exe -m pip install --upgrade pip
```

| Buyruq                                    | Vazifasi                                                                                                                                           |
| ----------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `pip install <paket>`                     | **pip** Python paket menejeri. U paketni PyPI'dan yuklab o'rnatadi va paketga kerakli boshqa paketlarni (bog'liqliklarni) ham avtomatik o'rnatadi. |
| `"psycopg[binary]"`                       | Kvadrat qavs ichidagi `binary` qo'shimcha variantni tanlaydi. Qo'shtirnoq terminal qavslarni noto'g'ri tushunmasligi uchun qo'yiladi.              |
| `pip freeze > requirements.txt`           | O'rnatilgan paketlarni versiyalari bilan `requirements.txt` ga yozadi. `>` belgisi buyruq natijasini faylga yo'naltiradi.                          |
| `pip install -r requirements.txt`         | Fayldagi barcha paketlarni bir buyruq bilan o'rnatadi.                                                                                             |
| `pip list`                                | O'rnatilgan paketlarni ko'rsatadi.                                                                                                                 |
| `python.exe -m pip install --upgrade pip` | pip'ning o'zini yangilaydi (26.2.1 dan 26.2.2 ga).                                                                                                 |

### 4.2. Asosiy paketlar

| Paket                             | Versiya | Vazifasi                                                                                                                                             |
| --------------------------------- | ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Django**                        | 6.1.2   | Veb-freymvork: model, URL, admin panel, autentifikatsiya.                                                                                            |
| **djangorestframework**           | 3.18.3  | REST API: Serializer, ViewSet, Router va brauzerdagi API sahifasi.                                                                                   |
| **markdown**                      | 3.11.2  | DRF'ning brauzer sahifasida tavsiflarni formatlab ko'rsatadi.                                                                                        |
| **django-filter**                 | 26.2    | URL orqali filtrlash, masalan `?author=Ali`.                                                                                                         |
| **djangorestframework-simplejwt** | 5.5.1   | JWT token bilan login. Foydalanuvchi token oladi va har bir so'rovda uni yuboradi. React va mobil ilovalar uchun mos.                                |
| **django-cors-headers**           | 4.9.0   | Boshqa domendagi frontend (masalan, `localhost:5173` dagi React) API'ga murojaat qilishiga ruxsat beradi. Usiz brauzer bunday so'rovlarni bloklaydi. |
| **drf-spectacular**               | 0.30.0  | Avtomatik OpenAPI sxemasi va Swagger hujjat sahifasini yaratadi.                                                                                     |
| **python-dotenv**                 | 1.2.4   | Maxfiy ma'lumotlarni (`SECRET_KEY`, parollar) `.env` faylidan o'qiydi.                                                                               |
| **Pillow**                        | 13.0.0  | Rasmlar bilan ishlash; modelda `ImageField` uchun kerak.                                                                                             |
| **psycopg[binary]**               | 3.3.6   | PostgreSQL drayveri.                                                                                                                                 |

### 4.3. Avtomatik o'rnatilgan bog'liqliklar

| Paket                                                                                               | Kim uchun kerak                              |
| --------------------------------------------------------------------------------------------------- | -------------------------------------------- |
| asgiref, sqlparse, tzdata                                                                           | Django                                       |
| PyJWT                                                                                               | simplejwt: tokenlarni yaratish va tekshirish |
| PyYAML, jsonschema, jsonschema-specifications, referencing, rpds-py, attrs, uritemplate, inflection | drf-spectacular                              |
| psycopg-binary                                                                                      | psycopg                                      |

### 4.4. Zararsiz ogohlantirishlar

| Xabar                                                        | Ma'nosi                                                                      |
| ------------------------------------------------------------ | ---------------------------------------------------------------------------- |
| `WARNING: Cache entry deserialization failed, entry ignored` | pip keshdagi eski yozuvni o'qiy olmadi va faylni qaytadan yukladi. Zararsiz. |
| `Requirement already satisfied`                              | Paket avvaldan o'rnatilgan.                                                  |
| `[notice] A new release of pip is available`                 | pip'ning yangi versiyasi chiqqani haqida xabar.                              |

---

## 5. Django loyihasi va app yaratish

```cmd
django-admin startproject config .
python manage.py startapp api
```

| Buyruq                               | Vazifasi                                                                                                                                                                                                                              |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `django-admin startproject config .` | `config` nomli loyiha yaratadi. Unda `settings.py`, `urls.py`, `wsgi.py` va `asgi.py` bo'ladi. Oxiridagi **nuqta (`.`)** loyihani joriy papkaning o'zida yaratadi, shuning uchun `manage.py` to'g'ridan-to'g'ri `Rest` ichida turadi. |
| `python manage.py startapp api`      | `api` nomli app yaratadi. Unda `models.py`, `views.py`, `admin.py`, `apps.py`, `tests.py` va `migrations/` bo'ladi. **`urls.py` va `serializers.py` avtomatik yaratilmaydi**, ularni qo'lda qo'shish kerak.                           |

**Loyiha va app farqi:** loyiha (`config`) butun saytning sozlamalarini saqlaydi. App (`api`) esa ma'lum bir vazifani bajaruvchi mustaqil modul. Bitta loyihada bir nechta app bo'lishi mumkin, masalan `users`, `books`, `orders`.

**`manage.py`** loyihani boshqarish uchun buyruqlar fayli. Unga `migrate`, `runserver`, `createsuperuser` kabi buyruqlar beriladi.

---

## 6. Sozlamalar — `config/settings.py`

> Yangilanish (2026-11-02): `SECRET_KEY`, `DEBUG` va `ALLOWED_HOSTS` endi `.env` faylidan o'qiladi, `LANGUAGE_CODE = 'uz'`, `TIME_ZONE = 'Asia/Tashkent'`. 16-bo'limga qarang.

### 6.1. INSTALLED_APPS

```python
INSTALLED_APPS = [
    'django.contrib.admin',          # admin panel
    'django.contrib.auth',           # foydalanuvchilar va autentifikatsiya
    'django.contrib.contenttypes',   # modellar haqida meta-ma'lumot
    'django.contrib.sessions',       # sessiyalar (brauzerda login holati)
    'django.contrib.messages',       # xabarlar tizimi
    'django.contrib.staticfiles',    # CSS, JS va rasmlar
    'rest_framework',                # DRF
    'rest_framework_simplejwt',      # JWT
    'rest_framework_simplejwt.token_blacklist',  # bekor qilingan refresh tokenlar
    'django_filters',                # filtrlash
    'corsheaders',                   # CORS
    'drf_spectacular',               # Swagger
    'api',                           # bizning app
    'restaurant',                    # restoran modellari
]
```

**Vazifasi:** Django faqat shu ro'yxatdagi app'larni "ko'radi", ya'ni ularning modellari, shablonlari va migratsiyalarini ishlatadi. Paketni faqat o'rnatish yetarli emas, uni shu ro'yxatga ham qo'shish kerak.

> Diqqat: pip'dagi nom bilan Python'dagi nom ba'zan farq qiladi. Masalan, pip'da `django-filter`, ro'yxatda esa `django_filters` deb yoziladi.

### 6.2. MIDDLEWARE

```python
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',   # eng yuqorida bo'lishi shart
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

**Middleware** har bir so'rov va javob o'tadigan qatlam. `CorsMiddleware` javobga CORS sarlavhalarini qo'shadi. U boshqa middleware'lardan oldin, ayniqsa `CommonMiddleware` dan oldin ishlashi kerak, shuning uchun eng yuqoriga qo'yiladi.

### 6.3. REST_FRAMEWORK

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'api.authentication.ThrottledBasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'login': '5/minute',
        'register': '5/minute',
        'change_password': '5/minute',
    },
    'NUM_PROXIES': 0,
    'EXCEPTION_HANDLER': 'api.exceptions.uzbek_exception_handler',
}
```

| Kalit                                                               | Vazifasi                                                                                                                                                                                                                                                                                                                                                             |
| ------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `DEFAULT_AUTHENTICATION_CLASSES`                                    | So'rov kimdan kelganini aniqlash usullari. **JWTAuthentication** `Authorization: Bearer <token>` sarlavhasini tekshiradi (React va mobil uchun). **SessionAuthentication** brauzerdagi login sessiyasini tekshiradi (DRF sahifasi va admin uchun). **ThrottledBasicAuthentication** login va parolni sarlavhadan oladi va xato urinishlarni cheklaydi (26.7-bo'lim). |
| `DEFAULT_PERMISSION_CLASSES`                                        | Kimga nimaga ruxsat berilishi. **IsAuthenticatedOrReadOnly** bo'yicha o'qish (GET) hammaga ochiq, yozish (POST, PUT, DELETE) esa faqat login qilganlarga.                                                                                                                                                                                                            |
| `DEFAULT_FILTER_BACKENDS`                                           | **DjangoFilterBackend** maydon bo'yicha filtrlaydi (`?author=Ali`). **SearchFilter** matn bo'yicha qidiradi (`?search=python`). **OrderingFilter** saralaydi (`?ordering=-price`, minus kamayish tartibini bildiradi).                                                                                                                                               |
| `DEFAULT_PAGINATION_CLASS`                                          | Natijalarni sahifalarga bo'ladi (`?page=2`).                                                                                                                                                                                                                                                                                                                         |
| `PAGE_SIZE`                                                         | Bir sahifadagi yozuvlar soni: 10 ta.                                                                                                                                                                                                                                                                                                                                 |
| `DEFAULT_THROTTLE_CLASSES`, `DEFAULT_THROTTLE_RATES`, `NUM_PROXIES` | So'rovlar sonini cheklash (26.7-bo'lim).                                                                                                                                                                                                                                                                                                                             |
| `EXCEPTION_HANDLER`                                                 | Xato javoblarini o'zbekchaga o'giradi (26.8-bo'lim).                                                                                                                                                                                                                                                                                                                 |
| `DEFAULT_SCHEMA_CLASS`                                              | Swagger uchun API sxemasini drf-spectacular yaratishini bildiradi.                                                                                                                                                                                                                                                                                                   |

### 6.4. CORS

```python
CORS_ALLOWED_ORIGINS = ["http://localhost:5173"]
```

API'ga qaysi frontend manzillaridan so'rov yuborishga ruxsat berilishini belgilaydi. `5173` Vite (React) ning standart porti.

---

## 7. Asosiy URL'lar — `config/urls.py`

```python
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from api.views import LoginView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('api-auth/', include('rest_framework.urls')),
    path('api/token/', LoginView.as_view()),
    path('api/token/refresh/', TokenRefreshView.as_view()),
    path('api/token/verify/', TokenVerifyView.as_view()),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema')),
]
```

| Qator                                               | Vazifasi                                                                                                                                |
| --------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| `from django.urls import path, include`             | `path` URL manzilini view'ga bog'laydi. `include` boshqa fayldagi URL ro'yxatini ulaydi.                                                |
| `path('admin/', admin.site.urls)`                   | `/admin/` manzilida admin panel ochiladi.                                                                                               |
| `path('api/', include('api.urls'))`                 | `/api/` bilan boshlanadigan barcha so'rovlar `api/urls.py` ga yo'naltiriladi. **Bu fayl mavjud bo'lishi shart** (10.2-bo'limga qarang). |
| `path('api-auth/', include('rest_framework.urls'))` | DRF brauzer sahifasida **Log in** va **Log out** tugmalarini ishlatadi.                                                                 |
| `LoginView`                                         | `/api/token/` ga username va parol yuborilsa, `access` va `refresh` tokenlar qaytariladi.                                               |
| `TokenRefreshView`                                  | `/api/token/refresh/` ga `refresh` token yuborilsa, yangi `access` token beriladi. Access token qisqa muddatli bo'lgani uchun kerak.    |
| `SpectacularAPIView`                                | `/api/schema/` manzilida API'ning OpenAPI (YAML) sxemasi ochiladi.                                                                      |
| `SpectacularSwaggerView`                            | `/api/docs/` manzilida Swagger sahifasi ochiladi. `url_name='schema'` sxemani qayerdan olishni ko'rsatadi.                              |
| `.as_view()`                                        | Klass ko'rinishidagi view'ni URL'ga ulash uchun funksiyaga aylantiradi.                                                                 |
| `name='schema'`                                     | URL'ga nom beradi, shunda unga boshqa joydan nomi orqali murojaat qilish mumkin.                                                        |

---

## 8. API kodi — `api` app

DRF'da bitta API resursi odatda 4 qismdan iborat bo'ladi:

```
Model  →  Serializer  →  ViewSet  →  Router (urls)
(baza)    (JSON)         (mantiq)    (manzillar)
```

### 8.1. `api/models.py` — Model

```python
from django.db import models

class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
```

| Qator                                           | Vazifasi                                                                                                                                                                        |
| ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `from django.db import models`                  | Django'ning model vositalarini import qiladi.                                                                                                                                   |
| `class Book(models.Model)`                      | `Book` modeli. Bazada `api_book` nomli jadval yaratiladi. `id` maydoni avtomatik qo'shiladi.                                                                                    |
| `CharField(max_length=200)`                     | Matn maydoni, ko'pi bilan 200 ta belgi.                                                                                                                                         |
| `DecimalField(max_digits=10, decimal_places=2)` | Aniq o'nli son, pul uchun mos: jami 10 ta raqam, shundan 2 tasi verguldan keyin (masalan, `25000.00`). Pul uchun `FloatField` ishlatilmaydi, chunki u yaxlitlashda xato qiladi. |
| `DateTimeField(auto_now_add=True)`              | Sana va vaqt. `auto_now_add=True` bo'lsa, yozuv yaratilgan vaqt avtomatik saqlanadi.                                                                                            |
| `def __str__`                                   | Obyektning matn ko'rinishi. Admin panelda `Book object (1)` o'rniga kitob nomi chiqadi.                                                                                         |

### 8.2. `api/serializers.py` — Serializer (yangi fayl)

```python
from rest_framework import serializers
from .models import Book

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'
```

**Serializer nima qiladi:**

- **Serializatsiya:** Python obyektini (`Book`) JSON'ga o'giradi. Bu javob qaytarishda ishlatiladi.
- **Deserializatsiya:** kelgan JSON'ni tekshiradi (validatsiya) va Python obyektiga aylantiradi. Bu POST va PUT so'rovlarida ishlatiladi.

| Qator                      | Vazifasi                                                                                       |
| -------------------------- | ---------------------------------------------------------------------------------------------- |
| `from .models import Book` | Nuqta (`.`) "shu app ichidan" degani.                                                          |
| `ModelSerializer`          | Model asosida maydonlar va validatsiyani avtomatik yaratadi.                                   |
| `class Meta`               | Serializer sozlamalari.                                                                        |
| `model = Book`             | Qaysi model uchun ekanini bildiradi.                                                           |
| `fields = '__all__'`       | Barcha maydonlar JSON'ga kiradi. Faqat ba'zilarini olish uchun `['id', 'title']` deb yoziladi. |

Natija JSON ko'rinishida:

```json
{
	"id": 1,
	"title": "Python asoslari",
	"author": "Ali Valiyev",
	"price": "25000.00",
	"created_at": "2026-10-29T09:50:00Z"
}
```

### 8.3. `api/views.py` — ViewSet

```python
from rest_framework import viewsets
from .models import Book
from .serializers import BookSerializer

class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    filterset_fields = ['author']
    search_fields = ['title', 'author']
    ordering_fields = ['price', 'created_at']
```

| Qator                                       | Vazifasi                                                                                                              |
| ------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `viewsets.ModelViewSet`                     | CRUD amallarining hammasini tayyor holda beradi: `list`, `create`, `retrieve`, `update`, `partial_update`, `destroy`. |
| `queryset = Book.objects.all()`             | Qaysi ma'lumotlar bilan ishlashni bildiradi: barcha kitoblar.                                                         |
| `serializer_class`                          | Qaysi serializer ishlatilishini bildiradi.                                                                            |
| `filterset_fields = ['author']`             | `?author=Ali` bilan aniq moslik bo'yicha filtrlash.                                                                   |
| `search_fields = ['title', 'author']`       | `?search=python` bilan nom yoki muallif bo'yicha qidirish.                                                            |
| `ordering_fields = ['price', 'created_at']` | `?ordering=price` (o'sish) yoki `?ordering=-price` (kamayish) bilan saralash.                                         |

### 8.4. `api/urls.py` — Router (yangi fayl)

```python
from rest_framework.routers import DefaultRouter
from .views import BookViewSet

router = DefaultRouter()
router.register('books', BookViewSet)

urlpatterns = router.urls
```

| Qator                                   | Vazifasi                                                                                                          |
| --------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `DefaultRouter()`                       | ViewSet uchun URL'larni avtomatik yaratuvchi obyekt. U `/api/` manzilida API'ning asosiy sahifasini ham qo'shadi. |
| `router.register('books', BookViewSet)` | `books` manzilini `BookViewSet` ga bog'laydi.                                                                     |
| `urlpatterns = router.urls`             | Yaratilgan URL ro'yxatini Django'ga beradi. Bu o'zgaruvchining nomi aynan `urlpatterns` bo'lishi shart.           |

Router yaratgan endpointlar:

| Metod  | URL             | ViewSet metodi   | Amal                 |
| ------ | --------------- | ---------------- | -------------------- |
| GET    | `/api/books/`   | `list`           | Ro'yxatni olish      |
| POST   | `/api/books/`   | `create`         | Yangi kitob qo'shish |
| GET    | `/api/books/1/` | `retrieve`       | Bitta kitobni olish  |
| PUT    | `/api/books/1/` | `update`         | To'liq tahrirlash    |
| PATCH  | `/api/books/1/` | `partial_update` | Qisman tahrirlash    |
| DELETE | `/api/books/1/` | `destroy`        | O'chirish            |

### 8.5. `api/admin.py` — Admin panel

```python
from django.contrib import admin
from .models import Book

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'author', 'price', 'created_at']
    search_fields = ['title', 'author']
```

| Qator                   | Vazifasi                                                |
| ----------------------- | ------------------------------------------------------- |
| `@admin.register(Book)` | Dekorator: `Book` modelini admin panelga qo'shadi.      |
| `admin.ModelAdmin`      | Admin sahifasining ko'rinishini sozlash klassi.         |
| `list_display`          | Ro'yxatda qaysi ustunlar chiqishini belgilaydi.         |
| `search_fields`         | Admin sahifasining yuqorisida qidiruv maydoni qo'shadi. |

Faylni saqlagandan keyin `runserver` o'zi qayta yuklanadi.

---

## 9. Migratsiya, superuser va server

### 9.1. makemigrations

```cmd
python manage.py makemigrations
```

Natija:

```
Migrations for 'api':
  api\migrations\0001_initial.py
    + Create model Book
```

**Vazifasi:** `models.py` dagi o'zgarishlarni o'qiydi va `api\migrations\0001_initial.py` faylini yaratadi. Bu faylda `Book` jadvalini qanday yaratish kerakligi yozilgan. Bu bosqichda baza **hali o'zgarmaydi**. Har safar model o'zgartirilganda bu buyruq qayta ishga tushiriladi va keyingi raqamli fayl yaratiladi (`0002_...`).

### 9.2. migrate

```cmd
python manage.py migrate
```

**Vazifasi:** barcha migratsiyalarni bazaga qo'llaydi, ya'ni jadvallar haqiqatda yaratiladi. Birinchi marta ishga tushirilganda `db.sqlite3` fayli paydo bo'ladi.

Natijadagi yozuvlar:

| Yozuv              | Nima yaratildi                                     |
| ------------------ | -------------------------------------------------- |
| `contenttypes.*`   | Modellar ro'yxati jadvali                          |
| `auth.*`           | Foydalanuvchilar, guruhlar va ruxsatlar jadvallari |
| `admin.*`          | Admin paneldagi amallar tarixi                     |
| `api.0001_initial` | **Bizning `Book` jadvalimiz**                      |
| `sessions.*`       | Login sessiyalari jadvali                          |

Har bir qator oxiridagi `OK` muvaffaqiyatli bajarilganini bildiradi.

### 9.3. createsuperuser

```cmd
python manage.py createsuperuser
```

Bu buyruq admin panelga kira oladigan, barcha huquqlarga ega foydalanuvchi yaratadi. U **interaktiv** ishlaydi, ya'ni savollar beradi:

```
Username (leave blank to use 'user'): admin
Email address:
Password:
Password (again):
This password is too short. It must contain at least 8 characters.
This password is too common.
This password is entirely numeric.
Bypass password validation and create user anyway? [y/N]: y
Superuser created successfully.
```

| Savol              | Izoh                                                                           |
| ------------------ | ------------------------------------------------------------------------------ |
| `Username`         | Login nomi. Bo'sh qoldirilsa, Windows foydalanuvchi nomi (`user`) olinadi.     |
| `Email address`    | Ixtiyoriy, bo'sh qoldirib Enter bosish mumkin.                                 |
| `Password`         | **Yozilayotgan belgilar ekranda ko'rinmaydi.** Bu xavfsizlik uchun, xato emas. |
| `Password (again)` | Tasdiqlash uchun parol qayta kiritiladi.                                       |

**Parol validatsiyasi ogohlantirishlari:**

| Xabar              | Ma'nosi                                                                                                                                |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------------------- |
| `too short`        | Parol 8 belgidan kam.                                                                                                                  |
| `too common`       | Parol mashhur parollar ro'yxatida bor.                                                                                                 |
| `entirely numeric` | Parol faqat raqamlardan iborat.                                                                                                        |
| `Bypass ... [y/N]` | `y` javobi ogohlantirishga qaramay foydalanuvchini yaratadi, `N` yoki Enter bekor qiladi. Katta harf (`N`) standart javobni bildiradi. |

> Mashq loyihasida oddiy parol bo'lishi mumkin. **Real loyiha va serverda albatta kuchli parol qo'ying.**

### 9.4. runserver

```cmd
python manage.py runserver
```

`http://127.0.0.1:8000/` manzilida ishlab chiqish serverini ishga tushiradi. Kod saqlanganda server avtomatik qayta yuklanadi (`StatReloader`). To'xtatish uchun `Ctrl + C` bosiladi.

| Variant                  | Vazifasi                                               |
| ------------------------ | ------------------------------------------------------ |
| `runserver 8080`         | Boshqa portda ishga tushiradi.                         |
| `runserver 0.0.0.0:8000` | Mahalliy tarmoqdagi boshqa qurilmalar ham ulana oladi. |

> `runserver` faqat ishlab chiqish uchun. Serverda (production) gunicorn yoki uvicorn ishlatiladi.

---

## 10. Chiqqan xatolar va yechimlari

### 10.1. 1-xato: PyYAML o'rnatilmadi

**Xato matni:**

```
Building wheel for PyYAML (pyproject.toml) ... error
error: Microsoft Visual C++ 14.0 or greater is required.
ERROR: Failed building wheel for PyYAML
```

**Sababi, bosqichma-bosqich:**

1. Kompyuterda **Python 3.15** bor edi. pip yuklagan fayl nomlaridagi `cp315` belgisi shuni ko'rsatadi.
2. `drf-spectacular` paketi o'z ishi uchun **PyYAML** paketini talab qiladi.
3. PyYAML ichida C tilida yozilgan qism bor. Odatda pip Python versiyasiga mos tayyor wheel yuklaydi, lekin Python 3.15 uchun Windows'ga mo'ljallangan PyYAML wheel hali chiqmagan edi.
4. Shuning uchun pip PyYAML'ni manba kodidan (`pyyaml-6.0.3.tar.gz`) yig'ishga urindi. Buning uchun C++ kompilyatori (Microsoft C++ Build Tools) kerak, u esa kompyuterda yo'q edi.
5. **Muhim natija:** bitta paket o'rnatilmasa, pip butun buyruqni bekor qiladi. Shu sababli simplejwt, cors, spectacular va boshqa paketlar **ham o'rnatilmay qoldi**.

**Wheel fayl nomini o'qish:**

```
pyyaml-6.0.3-cp313-cp313-win_amd64.whl
│       │     │            │
│       │     │            └── tizim: Windows 64-bit
│       │     └── Python versiyasi: 3.13
│       └── paket versiyasi
└── paket nomi
```

**Yechim:** virtual muhit barqaror Python 3.13 bilan qayta yaratildi.

```cmd
deactivate
rmdir /s /q env
py -3.13 -m venv env
env\Scripts\activate
pip install django djangorestframework markdown django-filter djangorestframework-simplejwt django-cors-headers drf-spectacular python-dotenv Pillow "psycopg[binary]"
pip freeze > requirements.txt
```

**Natija:** pip `pyyaml-6.0.3-cp313-cp313-win_amd64.whl` tayyor faylini yukladi, kompilyatsiya kerak bo'lmadi va barcha paketlar o'rnatildi. `config` va `api` papkalari o'zgarmadi, faqat `env` qayta yaratildi.

**Boshqa mumkin bo'lgan yechimlar:**

| Yechim                              | Izoh                                        |
| ----------------------------------- | ------------------------------------------- |
| Microsoft C++ Build Tools o'rnatish | Ishlaydi, lekin bir necha GB joy egallaydi. |
| `drf-spectacular` siz ishlash       | Swagger bo'lmaydi.                          |
| WSL (Ubuntu) da ishlash             | Linux'da bunday muammolar kam uchraydi.     |

### 10.2. 2-xato: `No module named 'api.urls'`

**Xato matni:**

```
File "C:\Users\user\Desktop\Rest\config\urls.py", line 24, in <module>
    path('api/', include('api.urls')),
ModuleNotFoundError: No module named 'api.urls'
```

**Sababi:** `config/urls.py` ning 24-qatorida `include('api.urls')` yozilgan, ya'ni Django `api/urls.py` faylini qidiradi. Lekin `startapp` buyrug'i `urls.py` ni **avtomatik yaratmaydi**, shuning uchun fayl yo'q edi. Django ishga tushishdan oldin barcha URL'larni tekshiradi, shu sababli `migrate` ham, `runserver` ham shu xato bilan to'xtadi.

**Traceback qanday o'qiladi:** xato xabarini pastdan yuqoriga o'qiladi. Eng pastdagi qator xatoning turini ko'rsatadi (`ModuleNotFoundError`). Uning ustida loyiha papkasidagi (`C:\Users\user\Desktop\Rest\...`) birinchi fayl xato qayerdan kelganini ko'rsatadi: `config\urls.py`, 24-qator. `env\Lib\site-packages` ichidagi qatorlar Django'ning ichki kodi, ularga odatda e'tibor berish shart emas.

**Yechim:** `api` papkasida `urls.py`, `serializers.py` yaratildi, `models.py` va `views.py` to'ldirildi (8-bo'limga qarang). Shundan keyin `makemigrations` va `migrate` muvaffaqiyatli o'tdi.

> Windows'da fayl yaratganda u `urls.py.txt` bo'lib qolmasligiga e'tibor bering. Buni `dir api` buyrug'i bilan tekshirish mumkin.

### 10.3. 3-xato: `createsuperuser` da noto'g'ri kiritish

**Nima bo'ldi:**

```
Username (leave blank to use 'user'): python manage.py runserver
```

**Sababi:** `createsuperuser` interaktiv buyruq, u javob kutib turadi. Username so'ralgan joyga keyingi buyruq (`python manage.py runserver`) yozib yuborildi. Probel bo'lgani uchun Django buni username sifatida qabul qilmaydi va qayta so'raydi.

**Yechim:** savollarga birma-bir javob berildi: username `admin`, email bo'sh, parol ikki marta kiritildi. Shundan keyin `runserver` alohida ishga tushirildi.

> Qoida: buyruq savol berayotgan bo'lsa, avval unga javob bering. Chalkashib ketsa, `Ctrl + C` bilan chiqib, buyruqni qaytadan ishga tushiring.

### 10.4. Xatolar jadvali

| №   | Xato                               | Sababi                                                     | Yechim                                                       |
| --- | ---------------------------------- | ---------------------------------------------------------- | ------------------------------------------------------------ |
| 1   | `Failed building wheel for PyYAML` | Python 3.15 uchun tayyor wheel yo'q, C++ kompilyatori yo'q | Python 3.13 bilan `env` qayta yaratildi                      |
| 2   | `No module named 'api.urls'`       | `api/urls.py` fayli yaratilmagan edi                       | `urls.py`, `serializers.py`, `views.py`, `models.py` yozildi |
| 3   | Username o'rniga buyruq yozildi    | Interaktiv savolga noto'g'ri javob berildi                 | Savollarga to'g'ri javob berildi                             |

---

## 11. Tekshirish

### 11.1. Manzillar

| Manzil                               | Nima ochiladi                           |
| ------------------------------------ | --------------------------------------- |
| `http://127.0.0.1:8000/admin/`       | Admin panel (`admin` va parol)          |
| `http://127.0.0.1:8000/api/`         | API asosiy sahifasi (DefaultRouter)     |
| `http://127.0.0.1:8000/api/books/`   | Kitoblar ro'yxati, DRF brauzer sahifasi |
| `http://127.0.0.1:8000/api/books/1/` | Bitta kitob                             |
| `http://127.0.0.1:8000/api/menu/`    | Restoran menyusi (ochiq)                |
| `http://127.0.0.1:8000/api/docs/`    | Swagger hujjatlari                      |
| `http://127.0.0.1:8000/api/schema/`  | OpenAPI sxemasi (YAML)                  |
| `http://127.0.0.1:8000/api/token/`   | JWT token olish                         |

### 11.2. Kitob qo'shish

1. `/api/books/` sahifasini oching.
2. O'ng yuqoridagi **Log in** tugmasini bosib, `admin` bilan kiring.
3. Pastdagi formani to'ldirib, **POST** tugmasini bosing.

> Permission `IsAuthenticatedOrReadOnly` bo'lgani uchun login qilinmasa, POST formasi ko'rinmaydi.

### 11.3. Filtrlash, qidiruv, saralash va sahifalash

| URL                                | Natija                                     |
| ---------------------------------- | ------------------------------------------ |
| `/api/books/?author=Ali`           | Muallifi aynan `Ali` bo'lgan kitoblar      |
| `/api/books/?search=python`        | Nomi yoki muallifida `python` bor kitoblar |
| `/api/books/?ordering=price`       | Narx bo'yicha o'sish tartibida             |
| `/api/books/?ordering=-created_at` | Eng yangi qo'shilganlari birinchi          |
| `/api/books/?page=2`               | 2-sahifa (har sahifada 10 tadan)           |

### 11.4. JWT tokenni tekshirish

`/api/token/` ga POST so'rov yuboriladi:

```json
{ "username": "admin", "password": "parolingiz" }
```

Javob:

```json
{ "refresh": "eyJ...", "access": "eyJ..." }
```

Keyingi so'rovlarda sarlavhaga quyidagi qo'shiladi:

```
Authorization: Bearer eyJ...access_token...
```

Buni Swagger (`/api/docs/`) yoki Postman orqali sinab ko'rish mumkin.

---

## 12. Loyiha tuzilishi

```
Rest/
├── env/                     # virtual muhit (GitHub'ga yuklanmaydi)
├── config/                  # loyiha sozlamalari
│   ├── __init__.py
│   ├── settings.py          # asosiy sozlamalar
│   ├── urls.py              # asosiy URL'lar
│   ├── asgi.py              # asinxron server uchun kirish nuqtasi
│   └── wsgi.py              # oddiy server uchun kirish nuqtasi
├── api/                     # bizning app
│   ├── migrations/
│   │   ├── __init__.py
│   │   └── 0001_initial.py  # Book jadvali migratsiyasi
│   ├── __init__.py
│   ├── admin.py             # admin panel sozlamasi
│   ├── apps.py              # app konfiguratsiyasi
│   ├── models.py            # Book va Product modellari
│   ├── authentication.py    # xato urinishlari cheklangan Basic auth
│   ├── exceptions.py        # o'zbekcha xato xabarlari
│   ├── permissions.py       # rollar, ruxsat klasslari, IsOwnerOrAdmin
│   ├── serializers.py       # Book va restoran serializer'lari (qo'lda yaratilgan)
│   ├── urls.py              # router va settings/, menu/, reports/daily/
│   ├── views.py             # BookViewSet, restoran va foydalanuvchi view'lari
│   └── tests.py             # avtomatik testlar (24-bo'lim)
├── restaurant/              # restoran app'i (17-bo'lim)
│   ├── management/commands/
│   │   └── seed_restaurant.py  # namuna ma'lumot (23-bo'lim)
│   ├── migrations/
│   │   ├── __init__.py
│   │   └── 0001_initial.py  # restoran jadvallari migratsiyasi
│   ├── __init__.py
│   ├── admin.py             # admin sozlamalari
│   ├── apps.py
│   └── models.py            # 9 ta model
├── media/                   # yuklangan rasmlar (GitHub'ga yuklanmaydi, birinchi yuklashda paydo bo'ladi)
├── .gitignore               # git e'tiborsiz qoldiradigan fayllar
├── .env                     # maxfiy sozlamalar (GitHub'ga yuklanmaydi, 16-bo'lim)
├── .env.example             # .env namunasi (GitHub'ga yuklanadi)
├── db.sqlite3               # SQLite bazasi
├── manage.py                # boshqaruv buyruqlari
├── requirements.txt         # paketlar ro'yxati
└── README.md                # shu hujjat
```

**`__init__.py`** papkani Python paketiga aylantiradi, shunda `from .models import Book` kabi importlar ishlaydi. Bu fayl odatda bo'sh turadi.

### `.gitignore`

GitHub'ga yuklashdan oldin loyiha papkasida `.gitignore` fayli yaratiladi:

```
env/
__pycache__/
*.pyc
db.sqlite3
.env
media/
```

| Qator                   | Nima uchun yuklanmaydi                                                                       |
| ----------------------- | -------------------------------------------------------------------------------------------- |
| `env/`                  | Katta hajmli, `requirements.txt` orqali qayta tiklanadi                                      |
| `__pycache__/`, `*.pyc` | Python avtomatik yaratadigan kesh fayllari                                                   |
| `db.sqlite3`            | Mahalliy baza                                                                                |
| `.env`                  | Maxfiy kalitlar va parollar                                                                  |
| `media/`                | Foydalanuvchilar yuklagan rasmlar (logotip, taom rasmi). Ular kod emas, ma'lumot hisoblanadi |

---

## 13. Boshqa kompyuterda ishga tushirish

```cmd
git clone <repo-manzili>
cd Rest
py -3.13 -m venv env
env\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_restaurant
python manage.py runserver
```

---

## 14. Buyruqlar qisqa jadvali

| Buyruq                               | Vazifasi                                 |
| ------------------------------------ | ---------------------------------------- |
| `py -3.13 -m venv env`               | Python 3.13 bilan virtual muhit yaratish |
| `env\Scripts\activate`               | Muhitni faollashtirish (CMD)             |
| `deactivate`                         | Muhitdan chiqish                         |
| `pip install <paket>`                | Paket o'rnatish                          |
| `pip install -r requirements.txt`    | Ro'yxatdagi paketlarni o'rnatish         |
| `pip freeze > requirements.txt`      | Paketlar ro'yxatini saqlash              |
| `pip list`                           | O'rnatilgan paketlarni ko'rish           |
| `django-admin startproject config .` | Loyiha yaratish                          |
| `python manage.py startapp api`      | App yaratish                             |
| `python manage.py makemigrations`    | Migratsiya fayllarini yaratish           |
| `python manage.py migrate`           | Migratsiyalarni bazaga qo'llash          |
| `python manage.py createsuperuser`   | Admin foydalanuvchi yaratish             |
| `python manage.py runserver`         | Serverni ishga tushirish                 |
| `python manage.py shell`             | Django muhitida Python konsolini ochish  |
| `python manage.py showmigrations`    | Migratsiyalar holatini ko'rish           |
| `python manage.py seed_restaurant`   | Namuna ma'lumot yaratish                 |
| `python manage.py test`              | Testlarni ishga tushirish                |
| `Ctrl + C`                           | Server yoki buyruqni to'xtatish          |
| `dir`                                | Papka ichidagi fayllarni ko'rish (CMD)   |

---

## 15. Xulosa va tavsiyalar

**Qilingan ishlar:**

- Python 3.13 bilan `env` virtual muhiti yaratildi.
- Django, DRF va qo'shimcha 8 ta paket o'rnatildi: filter, JWT, CORS, Swagger, dotenv, Pillow, PostgreSQL drayveri va markdown.
- `config` loyihasi va `api` app'i yaratildi.
- `settings.py` va `urls.py` sozlandi: autentifikatsiya, ruxsatlar, filtrlash, sahifalash, CORS va Swagger.
- `Book` modeli, serializer, ViewSet, router va admin sozlamasi yozildi.
- Migratsiyalar qo'llandi va `admin` superuser yaratildi.
- 3 ta xato aniqlanib, tuzatildi.
- Loyiha klinikadan restoranga o'tkazildi (25-bo'lim).
- Foydalanuvchi API, JWT logout va parol almashtirish qo'shildi (26-bo'lim).

**Tavsiyalar:**

1. Python'ning eng yangi versiyasini emas, bir versiya oldingi barqarorini tanlang. Unda paketlarning tayyor wheel'lari deyarli har doim mavjud bo'ladi.
2. Har yangi paket o'rnatgandan keyin `pip freeze > requirements.txt` ni bajaring.
3. Model o'zgartirilganda avval `makemigrations`, keyin `migrate` ni bajaring.
4. Xato chiqqanda traceback'ni pastdan o'qing va loyiha papkangizdagi birinchi faylni toping.
5. `SECRET_KEY` va parollarni `.env` fayliga ko'chiring (`python-dotenv`), `DEBUG = False` va kuchli parolni esa faqat serverda ishlating.
6. `env/`, `db.sqlite3` va `.env` ni GitHub'ga yuklamang.

---

## 16. `.env` sozlamalari

Maxfiy va muhitga bog'liq sozlamalar kod ichida emas, loyiha papkasidagi `.env` faylida saqlanadi. Bu faylni `python-dotenv` paketi o'qiydi.

### 16.1. Fayllar

| Fayl           | Git'ga yuklanadimi             | Vazifasi                                                                |
| -------------- | ------------------------------ | ----------------------------------------------------------------------- |
| `.env`         | **Yo'q** (`.gitignore` da bor) | Haqiqiy qiymatlar, masalan sizning `SECRET_KEY` ingiz                   |
| `.env.example` | Ha                             | Namuna: qaysi o'zgaruvchilar kerakligini ko'rsatadi, haqiqiy kalit yo'q |

`.env` tarkibi:

```ini
SECRET_KEY='django-insecure-...'
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
```

| O'zgaruvchi     | Nima uchun                                                                                                                                             | Ishlab chiqishda      | Serverda                                            |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------- | --------------------------------------------------- |
| `SECRET_KEY`    | Sessiyalar, parolni tiklash havolalari, CSRF va imzolangan ma'lumotlar shu kalit bilan himoyalanadi. Kalitni bilgan odam sessiyani soxtalashtira oladi | Istalgan uzun qator   | Yangi, tasodifiy, faqat shu serverga tegishli kalit |
| `DEBUG`         | `True` bo'lsa, xato sahifasida kod, sozlamalar va so'rov ma'lumotlari ko'rinadi. Media fayllarni ham Django o'zi beradi                                | `True`                | **Albatta `False`**                                 |
| `ALLOWED_HOSTS` | Django javob beradigan domenlar. Boshqa `Host` sarlavhali so'rovlar 400 bilan rad etiladi (Host header hujumidan himoya)                               | `127.0.0.1,localhost` | `restoran.uz,www.restoran.uz`                       |

### 16.2. `settings.py` dagi kod

```python
import os
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise ImproperlyConfigured('SECRET_KEY topilmadi. .env.example dan nusxa olib, .env faylini yarating.')

DEBUG = os.getenv('DEBUG', 'False').strip().lower() in ('1', 'true', 'yes', 'on')

ALLOWED_HOSTS = [h.strip() for h in os.getenv('ALLOWED_HOSTS', '').split(',') if h.strip()]
```

| Qator                                       | Izoh                                                                                                                                                                                                                                                                                                                    |
| ------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `load_dotenv(BASE_DIR / '.env')`            | `.env` dagi qatorlarni muhit o'zgaruvchilariga (`os.environ`) yuklaydi. Yo'l `BASE_DIR` bo'yicha beriladi, shuning uchun `manage.py` qaysi papkadan ishga tushirilishidan qat'i nazar fayl topiladi. Kompyuterda shu nomli o'zgaruvchi avvaldan bo'lsa, u ustun turadi                                                  |
| `os.getenv('SECRET_KEY')`                   | O'zgaruvchini o'qiydi. Topilmasa, `None` qaytaradi                                                                                                                                                                                                                                                                      |
| `ImproperlyConfigured`                      | `.env` unutilsa, Django noaniq xato bilan emas, tushunarli xabar bilan to'xtaydi                                                                                                                                                                                                                                        |
| `DEBUG = ... in ('1', 'true', 'yes', 'on')` | `.env` dagi hamma qiymat **matn**. `bool('False')` Python'da `True` bo'ladi (bo'sh bo'lmagan har qanday matn `True`), shuning uchun matn aniq qiymatlar bilan solishtiriladi. `.lower()` `True`/`true`/`TRUE` farqini yo'qotadi. O'zgaruvchi yozilmagan bo'lsa, `False` bo'ladi: xatolik bo'lsa, xavfsiz tomonga og'adi |
| `ALLOWED_HOSTS = [...]`                     | `"127.0.0.1, localhost"` → `['127.0.0.1', 'localhost']`. `strip()` probellarni olib tashlaydi, `if h.strip()` esa bo'sh elementlarni (`"a,,b"` yoki bo'sh qator) tashlab ketadi                                                                                                                                         |

`DEBUG` o'girish tekshirildi: `True`, `true`, `1`, `yes` → `True`. `False`, `false`, `0` va bo'sh qator → `False`.

**Nega `SECRET_KEY` qo'shtirnoqda:** kalitda `#`, `$`, `(`, `)` belgilari bor. Qo'shtirnoqsiz yozilganda python-dotenv probeldan keyingi `#` ni izoh, `${...}` ni esa boshqa o'zgaruvchiga havola deb tushunishi mumkin. Bitta qo'shtirnoq ichida hech narsa o'zgartirilmaydi. Tekshiruv: `.env` dan o'qilgan kalit eskisi bilan aynan bir xil chiqdi.

### 16.3. Til va vaqt zonasi

```python
LANGUAGE_CODE = 'uz'
TIME_ZONE = 'Asia/Tashkent'
```

| Sozlama                       | Ta'siri                                                                                                                                                                                                                                                                          |
| ----------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `LANGUAGE_CODE = 'uz'`        | Admin panel va DRF xabarlari o'zbekcha chiqadi (Django'da tarjimasi bor qismlari)                                                                                                                                                                                                |
| `TIME_ZONE = 'Asia/Tashkent'` | Admin panel va API vaqtni Toshkent vaqtida (`+05:00`) ko'rsatadi. `USE_TZ = True` bo'lgani uchun bazada vaqt baribir UTC'da saqlanadi, faqat ko'rsatish va kiritish Toshkent vaqtida bo'ladi. Windows'da vaqt zonalari bazasini `tzdata` paketi beradi, u allaqachon o'rnatilgan |

### 16.4. `.env.example` dan foydalanish

Loyihani boshqa kompyuterga yoki serverga ko'chirganda:

```cmd
copy .env.example .env
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

1. `copy` buyrug'i namunadan `.env` nusxasini yaratadi (Linux'da `cp .env.example .env`).
2. Ikkinchi buyruq yangi tasodifiy kalit chiqaradi. Uni `.env` dagi `SECRET_KEY='...'` ichiga qo'ying.
3. Serverda `DEBUG=False` qiling va `ALLOWED_HOSTS` ga domeningizni yozing.

> Yangi sozlama qo'shilsa (masalan, PostgreSQL paroli), uni `.env` ga haqiqiy qiymat bilan, `.env.example` ga esa namuna qiymat bilan yozing. Shunda boshqa dasturchi nimani to'ldirish kerakligini biladi.

> Hozirgi kalit `django-insecure-` bilan boshlanadi, ya'ni `startproject` yaratgan ishlab chiqish kaliti. U hech qachon commit qilinmagan, shuning uchun mahalliy ishda xavfsiz. Lekin serverda alohida yangi kalit ishlating.

---

## 17. Restoran: modellar va bog'lanishlar

Barcha modellar `restaurant/models.py` da, API kodi esa `api` app'ida (`Book` bilan bir joyda). Pul maydonlari: `DecimalField(max_digits=12, decimal_places=2)`, so'mda.

| Model                | Vazifasi                                   | Muhim maydonlar va cheklovlar                                                                                                                                                                                                                     |
| -------------------- | ------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Timestamped`        | Abstract: jadval yaratilmaydi              | `created_at`, `updated_at`                                                                                                                                                                                                                        |
| `RestaurantSettings` | Sozlamalar, **faqat bitta yozuv** (`pk=1`) | `name`, `phone`, `address`, `logo` (3 MB, JPEG/PNG/WebP), `opens_at`, `closes_at`, `reservation_duration` (120), `booking_days` (30), `service_percent` (0–30, standart 10). `CheckConstraint(id=1)`, `load()`, `clean()`: `closes_at > opens_at` |
| `Profile`            | Foydalanuvchi roli                         | `user` (OneToOne), `role`: `admin`, `waiter`, `chef`, `customer` (standart), `phone`                                                                                                                                                              |
| `Category`           | Menyu bo'limi                              | `name` (unique), `order`, `active`                                                                                                                                                                                                                |
| `MenuItem`           | Taom                                       | `price` (> 0), `image`, `preparation_minutes`, `available`, `is_vegetarian`, `spicy`. `UniqueConstraint(category, name)`                                                                                                                          |
| `Table`              | Stol                                       | `number` (unique), `seats` (1–20), `location`: `hall`, `terrace`, `vip`, `active`                                                                                                                                                                 |
| `Reservation`        | Bron                                       | `guests`, `start`, `end`, `status`, `name`, `phone`, `note`. `CheckConstraint(end > start)`, `Index(table, start, end)`                                                                                                                           |
| `Order`              | Buyurtma                                   | `order_type`, `status`, `note`, `service_percent` (buyurtma paytidagi qiymat), `subtotal`, `service_amount`, `total` (`editable=False`), `paid_at`, `recalculate()`, `change_status()`                                                            |
| `OrderItem`          | Buyurtma qatori                            | `quantity` (1–999), `unit_price` (buyurtma paytidagi narx), `line_total` (`editable=False`), `note`                                                                                                                                               |
| `OrderStatusEvent`   | Holat tarixi, faqat o'qish                 | `previous_status`, `status`, `actor`, `changed_at`                                                                                                                                                                                                |

### 17.1. Bog'lanishlar

```
User ──1:1── Profile

Category ──1:N── MenuItem ──1:N── OrderItem ──N:1── Order ──1:N── OrderStatusEvent
                                                     │
Table ──1:N── Reservation ──1:N──────────────────────┤
  └──────────1:N─────────────────────────────────────┘

User ──1:N── Reservation (customer, created_by)
User ──1:N── Order (customer, waiter)
User ──1:N── OrderStatusEvent (actor)
```

| Bog'lanish                                                                                                | `on_delete` | Natija                                                    |
| --------------------------------------------------------------------------------------------------------- | ----------- | --------------------------------------------------------- |
| `MenuItem.category`                                                                                       | `PROTECT`   | Taomi bor kategoriya o'chmaydi                            |
| `OrderItem.menu_item`                                                                                     | `PROTECT`   | Buyurtmada ishlatilgan taom o'chmaydi                     |
| `Reservation.table`, `Order.table`                                                                        | `PROTECT`   | Broni yoki buyurtmasi bor stol o'chmaydi                  |
| `Reservation.customer`                                                                                    | `PROTECT`   | Broni bor foydalanuvchi o'chmaydi                         |
| `OrderItem.order`, `OrderStatusEvent.order`                                                               | `CASCADE`   | Buyurtma o'chsa, qatorlari va tarixi ham o'chadi          |
| `Order.customer`, `Order.waiter`, `Order.reservation`, `Reservation.created_by`, `OrderStatusEvent.actor` | `SET_NULL`  | Foydalanuvchi yoki bron o'chsa ham buyurtma tarixi qoladi |

### 17.2. Narx nega "muzlatiladi"

`OrderItem.unit_price` va `Order.service_percent` buyurtma yaratilganda nusxalanadi. Keyin menyu narxi yoki sozlamadagi foiz o'zgarsa, eski buyurtma, shu jumladan `recalculate()` natijasi ham, o'zgarmaydi.

```
subtotal       = line_total'lar yig'indisi
service_amount = subtotal × service_percent / 100   (0.01 gacha, ROUND_HALF_UP)
total          = subtotal + service_amount
```

> Xizmat haqi barcha buyurtma turlariga (`takeaway` va `delivery` ham) qo'llanadi, chunki topshiriqda istisno ko'rsatilmagan.

### 17.3. Admin panel

| Model                           | Xususiyati                                                                                                                                                                        |
| ------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `RestaurantSettings`            | Faqat bitta yozuv: ikkinchisini qo'shib ham, o'chirib ham bo'lmaydi                                                                                                               |
| `Category`                      | Ichida `MenuItem` inline                                                                                                                                                          |
| `MenuItem`                      | Ro'yxatning o'zida `price` va `available` tahrirlanadi (`list_editable`)                                                                                                          |
| `Reservation`                   | `end` avtomatik hisoblanadi; ish vaqti, sig'im va vaqt to'qnashuvi `clean()` da tekshiriladi                                                                                      |
| `Order`                         | Ichida `OrderItem` inline. Qator faqat `new` holatda qo'shiladi yoki o'chiriladi, mavjud qator tahrirlanmaydi. Saqlaganda summalar qayta hisoblanadi. `status` faqat o'qish uchun |
| `OrderItem`, `OrderStatusEvent` | Faqat o'qish                                                                                                                                                                      |

> Admin panelda tarixi bor buyurtmani o'chirib bo'lmaydi, chunki `OrderStatusEvent` da o'chirish huquqi yopiq va Django bog'langan yozuvlarni tekshiradi. Bu ataylab qoldirilgan: moliyaviy tarix tasodifan yo'qolmaydi.

---

## 18. Rollar jadvali

Rol `Profile.role` dan olinadi. `is_superuser = True` har doim **admin**. Profili yo'q foydalanuvchi **customer** hisoblanadi. `is_staff` rolga ta'sir qilmaydi. Cheklovlar ikki qavatli: `api/permissions.py` amalni, `get_queryset` esa qaysi yozuvlar ko'rinishini belgilaydi. Shuning uchun boshqa birovning yozuvi **404** qaytaradi.

| Resurs                                    | Anonim  | customer                                           | chef                                         | waiter                          | admin                           |
| ----------------------------------------- | ------- | -------------------------------------------------- | -------------------------------------------- | ------------------------------- | ------------------------------- |
| Menyu, kategoriya, taom, stol, sozlamalar | O'qish  | O'qish                                             | O'qish                                       | O'qish                          | **Hammasi**                     |
| Bron                                      | —       | O'zinikini ko'radi, yaratadi, bekor qiladi         | —                                            | **Hammasi**                     | **Hammasi**                     |
| Buyurtma                                  | —       | O'zinikini ko'radi, yaratadi                       | `new`, `cooking`, `ready` dagilarini ko'radi | **Hammasi**                     | **Hammasi**                     |
| `set-status`                              | —       | —                                                  | Faqat `cooking`, `ready` ga                  | Barcha ruxsat etilgan o'tishlar | Barcha ruxsat etilgan o'tishlar |
| Oshxona ro'yxati                          | —       | —                                                  | Ha                                           | Ha                              | Ha                              |
| Holat tarixi (o'qish)                     | —       | O'z buyurtmalari                                   | Ko'radigan buyurtmalari                      | Hammasi                         | Hammasi                         |
| Profillar, kunlik hisobot                 | —       | —                                                  | —                                            | —                               | **Hammasi**                     |
| Kitoblar (`Book`)                         | O'qish  | **Hammasi**                                        | **Hammasi**                                  | **Hammasi**                     | **Hammasi**                     |
| Mahsulotlar (`products/`)                 | Ro'yxat | Ro'yxat, tafsilot, qo'shish; o'zinikini tahrirlaydi va profilidan o'chiradi | Mijoz kabi                                   | Mijoz kabi                      | Hammasini tahrirlaydi, boshqanikini o'chirmaydi (27.6-bo'lim)       |
| O'z foydalanuvchi hisobi (`users/me/`)    | —       | **Hammasi**                                        | **Hammasi**                                  | **Hammasi**                     | **Hammasi**                     |
| Boshqa foydalanuvchilar (`users/`)        | —       | —                                                  | —                                            | —                               | **Hammasi** (26.5-bo'lim)       |

Avtomatik to'ldiriladigan maydonlar:

| Rol      | Bron                                                                                             | Buyurtma                              |
| -------- | ------------------------------------------------------------------------------------------------ | ------------------------------------- |
| customer | `customer` va `created_by` = o'zi, `status` = `pending`; yuborgan qiymati e'tiborsiz qoldiriladi | `customer` = o'zi, `waiter` = bo'sh   |
| waiter   | `created_by` = o'zi, `customer` tanlanadi (yuborilmasa o'zi)                                     | `waiter` = o'zi, `customer` tanlanadi |
| admin    | `created_by` = o'zi, `customer` tanlanadi (yuborilmasa o'zi)                                     | `waiter` va `customer` tanlanadi      |

> Topshiriqda oshpazning bronga va mijozning `set-status` ga huquqi ko'rsatilmagan, shuning uchun ikkalasi yopiq. Mijoz buyurtmani bekor qila olmaydi, buni ofitsiant qiladi.

---

## 19. Endpointlar

Barcha manzillar `/api/` bilan boshlanadi. Ro'yxatlar sahifalanadi (`?page=`), uchta maxsus ro'yxat (`menu`, `tables/available`, `orders/kitchen`) bundan mustasno. To'liq sxema: `/api/docs/`.

| Metod                         | URL                                                       | Ruxsat                                          | Vazifasi                                                                        |
| ----------------------------- | --------------------------------------------------------- | ----------------------------------------------- | ------------------------------------------------------------------------------- |
| POST                          | `token/`, `token/refresh/`, `token/verify/`               | Hamma                                           | JWT olish, yangilash va tekshirish (26-bo'lim)                                  |
| POST                          | `auth/register/`, `auth/logout/`, `auth/change-password/` | 26.2-bo'limga qarang                            | Ro'yxatdan o'tish, chiqish, parol                                               |
| GET, PUT, PATCH, DELETE       | `users/me/`, `users/{id}/`                                | 26.2-bo'limga qarang                            | Foydalanuvchi hisobi                                                            |
| GET                           | `users/`                                                  | admin                                           | Foydalanuvchilar ro'yxati                                                       |
| GET                           | `menu/`                                                   | Hamma                                           | Faol kategoriyalar ichida mavjud taomlar                                        |
| GET                           | `settings/`                                               | Hamma                                           | Sozlamalar                                                                      |
| PUT, PATCH                    | `settings/`                                               | admin                                           | Sozlamalarni o'zgartirish                                                       |
| GET                           | `categories/`, `categories/{id}/`                         | Hamma                                           | Kategoriyalar                                                                   |
| POST, PUT, PATCH, DELETE      | `categories/`, `categories/{id}/`                         | admin                                           | Boshqarish                                                                      |
| GET                           | `menu-items/`, `menu-items/{id}/`                         | Hamma                                           | Taomlar (`?category=`, `?available=`, `?is_vegetarian=`, `?spicy=`, `?search=`) |
| POST, PUT, PATCH, DELETE      | `menu-items/`, `menu-items/{id}/`                         | admin                                           | Boshqarish                                                                      |
| GET                           | `tables/`, `tables/{id}/`                                 | Hamma                                           | Stollar (`?location=`, `?active=`, `?seats=`)                                   |
| POST, PUT, PATCH, DELETE      | `tables/`, `tables/{id}/`                                 | admin                                           | Boshqarish                                                                      |
| GET                           | `tables/available/?start=...&guests=...`                  | Hamma                                           | Shu vaqtda bo'sh va sig'adigan stollar                                          |
| GET                           | `reservations/`, `reservations/{id}/`                     | customer (o'ziniki), waiter, admin              | Bronlar (`?table=`, `?status=`, `?customer=`)                                   |
| POST                          | `reservations/`                                           | customer, waiter, admin                         | Bron yaratish                                                                   |
| PUT, PATCH, DELETE            | `reservations/{id}/`                                      | waiter, admin                                   | Boshqarish                                                                      |
| POST                          | `reservations/{id}/cancel/`                               | customer (o'ziniki), waiter, admin              | Bekor qilish (`pending` yoki `confirmed` holatidan)                             |
| GET                           | `orders/`, `orders/{id}/`                                 | customer (o'ziniki), chef (faol), waiter, admin | Buyurtmalar (`?status=`, `?order_type=`, `?table=`, `?customer=`, `?waiter=`)   |
| POST                          | `orders/`                                                 | customer, waiter, admin                         | Taomlar bilan birga yaratish                                                    |
| PUT, PATCH, DELETE            | `orders/{id}/`                                            | waiter, admin                                   | Boshqarish (`items` va `status` dan tashqari)                                   |
| POST                          | `orders/{id}/set-status/`                                 | chef (cheklangan), waiter, admin                | Holatni o'zgartirish                                                            |
| GET                           | `orders/kitchen/`                                         | chef, waiter, admin                             | `new` va `cooking`, eng eskisi birinchi                                         |
| GET                           | `order-events/`, `order-events/{id}/`                     | Login qilganlar (rol bo'yicha filtr)            | Holat tarixi, faqat o'qish (`?order=`)                                          |
| GET, POST, PUT, PATCH, DELETE | `profiles/`, `profiles/{id}/`                             | admin                                           | Profillar                                                                       |
| GET                           | `reports/daily/?date=YYYY-MM-DD`                          | admin                                           | Kunlik hisobot (sana yuborilmasa, bugun)                                        |
| GET                           | `books/`, `books/{id}/`                                   | Hamma                                           | Kitoblar                                                                        |
| POST, PUT, PATCH, DELETE      | `books/`, `books/{id}/`                                   | Login qilganlar                                 | Boshqarish                                                                      |
| GET                           | `products/`                                               | Hamma                                           | Mahsulotlar ro'yxati (27-bo'lim)                                                |
| GET, POST                     | `products/{id}/`, `products/`                             | Login qilganlar                                 | Tafsilot va qo'shish                                                            |
| PUT, PATCH            | `products/{id}/`                                          | Egasi yoki admin                                | Boshqarish                                                                      |
| GET | `users/me/products/`, `users/me/products/{id}/` | Login qilganlar, faqat o'ziniki | Mening mahsulotlarim |
| DELETE | `users/me/products/{id}/` | Faqat egasi | Mahsulotni va rasmini o'chirish (27.6-bo'lim) |

Javob kodlari: **400** noto'g'ri ma'lumot, **401** login qilinmagan, **403** rolga ruxsat yo'q, **404** yozuv yo'q yoki sizga ko'rinmaydi.

> `?start=` da vaqt zonasi yozilsa, `+` belgisi URL'da `%2B` bo'lishi kerak: `2026-11-06T18:00:00%2B05:00`. Zonasiz yozilsa (`2026-11-06T18:00:00`), Toshkent vaqti deb olinadi.

**Kunlik hisobot qanday hisoblanadi:** `orders_count` shu kuni yaratilgan barcha buyurtmalar (bekor qilinganlar ham). `paid_orders_count`, `paid_total` va `top_items` esa shu kuni to'langan (`paid_at`) buyurtmalardan olinadi.

---

## 20. Validatsiyalar

### 20.1. Bron

| Qoida                                                                                             | Xato qaysi maydonda |
| ------------------------------------------------------------------------------------------------- | ------------------- |
| `guests` stol sig'imidan oshmasin                                                                 | `guests`            |
| Stol faol bo'lsin                                                                                 | `table`             |
| O'tgan vaqtga bron qilib bo'lmaydi                                                                | `start`             |
| `booking_days` kundan uzoq bo'lmasin                                                              | `start`             |
| Butun bron ish vaqtiga sig'sin: `start >= opens_at` va `end <= closes_at`, bitta kun ichida       | `start`             |
| `end` har doim serverda: `start + reservation_duration`; yuborilgan qiymat e'tiborsiz qoldiriladi | —                   |
| Shu stolda vaqt to'qnashuvi bo'lmasin; `cancelled`, `no_show`, `completed` hisobga olinmaydi      | `start`             |

- **Ish vaqti misoli:** 10:00–23:00 va 120 daqiqada eng kech bron 21:00 da boshlanadi.
- **Yonma-yon bronlar ruxsat etiladi:** 12:00–14:00 va 14:00–16:00 to'qnashmaydi.
- **Tahrirlashda faqat o'zgargan qism tekshiriladi.** Aks holda o'tib ketgan bronni `completed` qilib bo'lmay qolardi. To'qnashuv esa bron faol holatda bo'lsa har doim tekshiriladi, shuning uchun bekor qilingan bronni band vaqtga qaytarib bo'lmaydi.
- **Poyga holati:** tekshiruv va saqlash `transaction.atomic()` ichida, `Table` qatori `select_for_update()` bilan qulflanadi.

> **SQLite'da cheklov:** SQLite `select_for_update()` ni e'tiborsiz qoldiradi, shuning uchun bu qulf PostgreSQL'da haqiqatan ishlaydi. Serverda albatta PostgreSQL ishlating.

### 20.2. Buyurtma

| Qoida                                                                                                                    | Natija                             |
| ------------------------------------------------------------------------------------------------------------------------ | ---------------------------------- |
| `items` majburiy va bo'sh bo'lmasin                                                                                      | 400                                |
| `available=False` yoki faol bo'lmagan kategoriyadagi taom qo'shilmaydi                                                   | 400                                |
| `quantity` 1 dan 999 gacha                                                                                               | 400                                |
| `unit_price`, `line_total`, `subtotal`, `service_amount`, `total`, `service_percent`, `status`, `paid_at` faqat serverda | Yuborilgani e'tiborsiz qoldiriladi |
| `dine_in` uchun `table` majburiy, stol faol bo'lsin                                                                      | 400                                |
| Mijoz faqat o'z bronini bog'lay oladi; bron stoli buyurtma stoli bilan bir xil bo'lsin                                   | 400                                |
| Yaratilgandan keyin `items` o'zgarmaydi                                                                                  | 400                                |
| `paid` yoki `cancelled` buyurtma tahrirlanmaydi                                                                          | 400                                |

### 20.3. O'chirish

`PROTECT` bilan bog'langan yozuvni o'chirishda `ProtectedError` chiqadi. `ProtectedDestroyMixin` uni 500 o'rniga 400 ga aylantiradi:

```json
{ "detail": "Bu yozuvni o‘chirib bo‘lmaydi: unga bog‘langan boshqa yozuvlar bor." }
```

---

## 21. Buyurtma holatlari

```
         ┌─────┐     ┌─────────┐     ┌───────┐     ┌────────┐     ┌──────┐
 yangi → │ new │ ──→ │ cooking │ ──→ │ ready │ ──→ │ served │ ──→ │ paid │
         └──┬──┘     └────┬────┘     └───┬───┘     └───┬────┘     └──────┘
            │             │              │             │
            └─────────────┴──────┬───────┴─────────────┘
                                 ↓
                           ┌───────────┐
                           │ cancelled │
                           └───────────┘
```

| Qoida                   | Tafsilot                                                                                |
| ----------------------- | --------------------------------------------------------------------------------------- |
| Tartib                  | Bosqichni sakrab yoki orqaga o'tib bo'lmaydi: 400                                       |
| Yakuniy holatlar        | `paid` va `cancelled` dan hech qayerga o'tilmaydi                                       |
| Holat qayerda o'zgaradi | Faqat `POST /api/orders/{id}/set-status/`. `PATCH` dagi `status` e'tiborsiz qoldiriladi |
| Tarix                   | Yaratilish va har bir o'tish `OrderStatusEvent` ga yoziladi                             |
| To'lov                  | `paid` bo'lganda `paid_at` qo'yiladi                                                    |
| Oshpaz                  | Faqat `new → cooking` va `cooking → ready`. Boshqa holatga urinish: 403                 |

---

## 22. Misol so'rov va javoblar

Quyidagilar seed ma'lumotlari ustida haqiqiy so'rovlardan olingan javoblar. `customer1`, `waiter1` va `chef1` JWT bilan kirgan. Tranzaksiya bekor qilingani uchun bu bron va buyurtma bazada qolmagan, shuning uchun `id` lar sizda boshqacha bo'lishi mumkin.

### 22.1. Menyu: `GET /api/menu/`

Javobning birinchi kategoriyasi, birinchi taomi (qolganlari qisqartirildi):

```json
[
	{
		"id": 1,
		"name": "Milliy taomlar",
		"order": 1,
		"items": [
			{
				"id": 2,
				"category_name": "Milliy taomlar",
				"created_at": "2026-11-04T08:53:40.708079+05:00",
				"updated_at": "2026-11-04T08:53:40.708147+05:00",
				"name": "Lag‘mon",
				"description": "Qo‘lda cho‘zilgan xamir, go‘sht va sabzavot",
				"price": "38000.00",
				"image": null,
				"preparation_minutes": 25,
				"available": true,
				"is_vegetarian": false,
				"spicy": true,
				"category": 1
			}
		]
	}
]
```

### 22.2. Sozlamalar: `GET /api/settings/`

```json
{
	"created_at": "2026-11-04T08:53:40.704517+05:00",
	"updated_at": "2026-11-04T08:53:40.704762+05:00",
	"name": "Choyxona Registon",
	"phone": "+998712000000",
	"address": "Toshkent, Amir Temur ko‘chasi, 1",
	"logo": null,
	"opens_at": "10:00:00",
	"closes_at": "23:00:00",
	"reservation_duration": 120,
	"booking_days": 30,
	"service_percent": "10.00"
}
```

### 22.3. Bo'sh stollar: `GET /api/tables/available/?start=2026-11-06T18:00:00&guests=4`

Avval eng kichik mos stol chiqadi. Birinchi yozuv:

```json
[
	{
		"id": 3,
		"location_name": "Zal",
		"created_at": "2026-11-04T08:53:40.716163+05:00",
		"updated_at": "2026-11-04T08:53:40.716203+05:00",
		"number": 3,
		"seats": 4,
		"location": "hall",
		"active": true
	}
]
```

### 22.4. Bron: `POST /api/reservations/` (customer1)

So'rov:

```json
{
	"table": 3,
	"guests": 4,
	"start": "2026-11-06T18:00:00+05:00",
	"name": "Ali Valiyev",
	"phone": "+998901234567",
	"note": "Deraza yonida"
}
```

Javob `201`. `end`, `customer`, `created_by` va `status` serverda qo'yilgan:

```json
{
	"id": 1,
	"table_number": 3,
	"status_name": "Kutilmoqda",
	"created_at": "2026-11-04T08:53:46.160827+05:00",
	"updated_at": "2026-11-04T08:53:46.160959+05:00",
	"guests": 4,
	"start": "2026-11-06T18:00:00+05:00",
	"end": "2026-11-06T20:00:00+05:00",
	"status": "pending",
	"name": "Ali Valiyev",
	"phone": "+998901234567",
	"note": "Deraza yonida",
	"customer": 4,
	"table": 3,
	"created_by": 4
}
```

Xatolar `400`:

```json
{ "start": ["Bu stol shu vaqtda band."] }
```

```json
{ "guests": ["Bu stolga ko‘pi bilan 4 kishi sig‘adi."] }
```

### 22.5. Buyurtma: `POST /api/orders/` (waiter1)

So'rov:

```json
{
	"table": 3,
	"order_type": "dine_in",
	"items": [
		{ "menu_item": 1, "quantity": 2, "note": "Kam yog‘li" },
		{ "menu_item": 8, "quantity": 1 }
	]
}
```

Javob `201`:

```json
{
	"id": 1,
	"items": [
		{
			"id": 1,
			"menu_item": 1,
			"menu_item_name": "Osh",
			"quantity": 2,
			"unit_price": "45000.00",
			"line_total": "90000.00",
			"note": "Kam yog‘li"
		},
		{
			"id": 2,
			"menu_item": 8,
			"menu_item_name": "Ko‘k choy",
			"quantity": 1,
			"unit_price": "8000.00",
			"line_total": "8000.00",
			"note": ""
		}
	],
	"table_number": 3,
	"status_name": "Yangi",
	"order_type_name": "Restoranda",
	"created_at": "2026-11-04T08:53:46.172062+05:00",
	"updated_at": "2026-11-04T08:53:46.173641+05:00",
	"order_type": "dine_in",
	"status": "new",
	"note": "",
	"service_percent": "10.00",
	"subtotal": "98000.00",
	"service_amount": "9800.00",
	"total": "107800.00",
	"paid_at": null,
	"table": 3,
	"customer": null,
	"waiter": 2,
	"reservation": null
}
```

### 22.6. Holat: `POST /api/orders/1/set-status/`

So'rov: `{ "status": "paid" }`. Buyurtma `new` holatida bo'lsa, javob `400`:

```json
{ "status": ["«Yangi» holatidan «To‘langan» holatiga o‘tib bo‘lmaydi."] }
```

Oshpaz `cancelled` yuborsa, javob `403`:

```json
{ "detail": "Oshpaz holatni faqat «cooking» yoki «ready» ga o‘zgartira oladi." }
```

To'g'ri o'tishda to'liq buyurtma qaytadi. `paid` bo'lganda `paid_at` to'ladi: `"paid_at": "2026-11-04T08:53:46.200127+05:00"`.

### 22.7. Tarix: `GET /api/order-events/?order=1`

Yangisi birinchi. Uch yozuv (`count: 5`, qolganlari qisqartirildi):

```json
{
	"count": 5,
	"next": null,
	"previous": null,
	"results": [
		{
			"id": 5,
			"status_name": "To‘langan",
			"actor_username": "waiter1",
			"previous_status": "served",
			"status": "paid",
			"changed_at": "2026-11-04T08:53:46.200332+05:00",
			"order": 1,
			"actor": 2
		},
		{
			"id": 2,
			"status_name": "Tayyorlanmoqda",
			"actor_username": "chef1",
			"previous_status": "new",
			"status": "cooking",
			"changed_at": "2026-11-04T08:53:46.185233+05:00",
			"order": 1,
			"actor": 3
		},
		{
			"id": 1,
			"status_name": "Yangi",
			"actor_username": "waiter1",
			"previous_status": "",
			"status": "new",
			"changed_at": "2026-11-04T08:53:46.173860+05:00",
			"order": 1,
			"actor": 2
		}
	]
}
```

### 22.8. Hisobot: `GET /api/reports/daily/?date=2026-11-04` (admin)

```json
{
	"date": "2026-11-04",
	"orders_count": 1,
	"paid_orders_count": 1,
	"paid_total": "107800.00",
	"top_items": [
		{ "menu_item": 1, "name": "Osh", "quantity": 2, "revenue": "90000.00" },
		{ "menu_item": 8, "name": "Ko‘k choy", "quantity": 1, "revenue": "8000.00" }
	]
}
```

---

## 23. Namuna ma'lumot (seed)

```cmd
python manage.py seed_restaurant
```

Buyruq `restaurant/management/commands/seed_restaurant.py` da. U `get_or_create` ishlatadi, shuning uchun qayta ishga tushirilsa takrorlamaydi va qo'lda o'zgartirilgan narx yoki parolni ham qayta yozmaydi.

| Nima          | Soni                                                            |
| ------------- | --------------------------------------------------------------- |
| Sozlamalar    | 1 ("Choyxona Registon", 10:00–23:00)                            |
| Kategoriyalar | 4: Milliy taomlar, Salatlar, Ichimliklar, Shirinliklar          |
| Taomlar       | 14: osh, lag'mon, manti, shashlik, achchiq-chuchuk va boshqalar |
| Stollar       | 8: 5 ta zal, 2 ta teras, 1 ta VIP                               |

Test foydalanuvchilar:

| Login       | Parol           | Rol       |
| ----------- | --------------- | --------- |
| `waiter1`   | `Restoran2026!` | Ofitsiant |
| `chef1`     | `Restoran2026!` | Oshpaz    |
| `customer1` | `Restoran2026!` | Mijoz     |

> Bu parollar hammaga ochiq, chunki README git'da turadi. Seed'ni faqat ishlab chiqishda ishlating, serverda ishga tushirmang.

Admin rolini sinash uchun `createsuperuser` bilan yaratilgan `admin` hisobidan foydalaning.

---

## 24. Testlarni ishga tushirish

```cmd
python manage.py test
python manage.py test api.tests.ChefTests
python manage.py test api.tests.ReservationTests.test_overlap_rejected
```

Testlar vaqtinchalik bazada ishlaydi, `db.sqlite3` ga tegmaydi. Ular `api/tests.py` da.

| Klass                    | Nimani tekshiradi                                                                                             |
| ------------------------ | ------------------------------------------------------------------------------------------------------------- |
| `CatalogPermissionTests` | Menyu, stol va sozlamalarga ruxsatlar; `/api/menu/` filtri; `/api/schema/`                                    |
| `SettingsSingletonTests` | Yagona yozuv, baza cheklovi, ish vaqti, foiz, logotip formati va hajmi                                        |
| `ReservationTests`       | Rollar, to'qnashuv, sig'im, ish vaqti, o'tgan va uzoq sana, `tables/available`                                |
| `OrderCreateTests`       | Summalar, yaxlitlash, narx muzlashi, mavjud bo'lmagan taom, `dine_in` da stol                                 |
| `OrderPermissionTests`   | Har bir rol uchun buyurtmaga ruxsatlar                                                                        |
| `OrderStatusTests`       | To'g'ri va noto'g'ri o'tishlar, tarix, `paid_at`                                                              |
| `ChefTests`              | Oshpaz cheklovlari va `orders/kitchen`                                                                        |
| `OrderEventTests`        | Tarix faqat o'qish uchun, rol bo'yicha filtr                                                                  |
| `ProtectedDeleteTests`   | `ProtectedError` → 400                                                                                        |
| `DailyReportTests`       | Hisobot ruxsati va qiymatlari                                                                                 |
| `BookTests`              | `Book` CRUD                                                                                                   |
| `AdminTests`             | Admin sahifalari, yagona sozlama, bron va buyurtma qo'shish                                                   |
| `SeedTests`              | Seed takrorlamasligi                                                                                          |
| `RegisterTests`          | Ro'yxatdan o'tish, token, Profile, takror username va email, kuchsiz parol                                    |
| `JWTTests`               | Token olish, verify, refresh, rotatsiya, Basic auth                                                           |
| `UserMeTests`            | `users/me/`: GET, PUT, PATCH, soft delete, huquqni ko'tarib bo'lmasligi, parol yuborilsa 400                  |
| `UserDetailTests`        | Egasi, boshqa foydalanuvchi, admin, superuser himoyasi                                                        |
| `UserListTests`          | Faqat admin, qidiruv va filtr                                                                                 |
| `ChangePasswordTests`    | Eski parol, kuchsiz parol, tokenlar bekor bo'lishi                                                            |
| `LogoutTests`            | 205, noto'g'ri token 400, begona token, keyin refresh ishlamasligi                                            |
| `ThrottleTests`          | 429: login, register, change-password, anon, user, Basic orqali va `X-Forwarded-For` bilan aylanib o'tish     |
| `UzbekMessageTests`      | `simplejwt` va DRF xabarlari o'zbekcha, `code` o'zgarmagan                                                    |
| `ProductAPITests`        | Ro'yxat, tafsilot, ruxsatlar, egasi va admin, narx, nom va rasm validatsiyasi, qidiruv, saralash, admin panel |
| `MyProductTests` | Mening mahsulotlarim, begona mahsulot 404, egasi 204, rasm fayli o'chishi, ProtectedError 400 |
| `ProductAdminDeleteTests` | Admin panelda o'chirish sahifasi 403, `delete_selected` yo'q |

---

## 25. Tarix: klinikadan restoranga o'tish

Loyiha dastlab **Medora Clinic** (shifokorlar, bemorlar, qabullar) API'si edi. 2026-11-04 da u restoranga o'tkazildi:

```cmd
python manage.py migrate clinic zero
```

Bu buyruq klinika jadvallarini o'chirdi (ularda yozuv yo'q edi). Uni `INSTALLED_APPS` dan olib tashlashdan **oldin** bajarish shart edi: keyin Django `clinic` migratsiyalarini topa olmaydi va jadvallar bazada qolib ketadi. Shundan so'ng `clinic` app'i o'chirildi va uning o'rniga `restaurant` yozildi. Klinika kodini git tarixidan ko'rish mumkin (`git show 9f70d0d`).

Avvalgi bosqichdan bitta muhim saboq: git repozitoriyasi bir vaqtlar xato bilan `C:\Users\user` da ochilgan edi, u bo'sh bo'lgani uchun o'chirilib, `Rest` ichida qayta ochildi. `git add .` dan oldin `git status` ni tekshirishni unutmang: aks holda SSH kalitlari va shaxsiy fayllar repozitoriyaga tushib qolishi mumkin.

---

## 26. Foydalanuvchi va JWT

Bu bo'lim foydalanuvchi API'si, JWT oqimi va ruxsatlarni tushuntiradi. Kod: `api/views.py`, `api/serializers.py`, `api/permissions.py`.

### 26.1. JWT nima

**JWT (JSON Web Token)** server `SECRET_KEY` bilan imzolagan matn. Ichida foydalanuvchi `id` si va amal qilish muddati bor. Server har so'rovda parolni tekshirmaydi, faqat imzoni tekshiradi. So'rovda u sarlavhada yuboriladi:

```
Authorization: Bearer eyJhbGciOi...
```

|                    | Access token                       | Refresh token                                         |
| ------------------ | ---------------------------------- | ----------------------------------------------------- |
| Vazifasi           | API'ga har bir so'rovda yuboriladi | Yangi access token olish uchun                        |
| Muddati            | 30 daqiqa                          | 7 kun                                                 |
| Qayerga yuboriladi | Barcha API so'rovlariga            | Faqat `/api/token/refresh/` va `/api/auth/logout/` ga |
| Bekor qilinadimi   | Yo'q, muddati tugaguncha ishlaydi  | Ha, blacklist orqali                                  |

**Nega ikkita token:** access token ko'p yuboriladi, shuning uchun o'g'irlanish xavfi yuqoriroq, lekin u tez eskiradi. Foydalanuvchi esa har 30 daqiqada parol kiritmaydi, buni refresh token qiladi.

**Rotate va blacklist nima uchun:**

| Sozlama                    | Nima qiladi                                                               | Nima beradi                                                        |
| -------------------------- | ------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| `ROTATE_REFRESH_TOKENS`    | Har refresh'da yangi refresh token beriladi                               | Token umrbod bitta bo'lib qolmaydi                                 |
| `BLACKLIST_AFTER_ROTATION` | Ishlatilgan refresh token bekor qilinadi                                  | O'g'irlangan eski token qayta ishlamaydi                           |
| `token_blacklist` app'i    | Tokenlarni `OutstandingToken` va `BlacklistedToken` jadvallarida saqlaydi | Logout va parol almashtirishda tokenni bekor qilish mumkin bo'ladi |
| `UPDATE_LAST_LOGIN`        | Token olganda `last_login` yangilanadi                                    | Oxirgi kirish vaqti ko'rinadi                                      |

> **Muhim cheklov:** blacklist faqat refresh tokenlarga ishlaydi. Logout, parol almashtirish yoki `DELETE` dan keyin ham chiqarilgan **access token** o'z muddati tugaguncha, ya'ni ko'pi bilan 30 daqiqa ishlashi mumkin. Istisno: nofaol foydalanuvchining access tokeni darhol rad etiladi (`Foydalanuvchi faol emas.`), chunki `is_active` har so'rovda tekshiriladi.

Eskirgan yozuvlarni jadvaldan tozalash (masalan, kuniga bir marta):

```cmd
python manage.py flushexpiredtokens
```

Autentifikatsiya usullari ketma-ket sinaladi: `JWTAuthentication`, `SessionAuthentication`, `ThrottledBasicAuthentication`. Basic'da login va parol har so'rovda yuboriladi, shuning uchun serverda uni faqat HTTPS bilan ishlating.

### 26.2. Endpointlar

| Metod      | URL                          | Kim ishlatadi                                            | Muvaffaqiyat | Xatolar                               |
| ---------- | ---------------------------- | -------------------------------------------------------- | ------------ | ------------------------------------- |
| POST       | `/api/auth/register/`        | Hamma, 5/daqiqa                                          | 201          | 400, 429                              |
| POST       | `/api/token/`                | Hamma, 5/daqiqa                                          | 200          | 400, 401, 429                         |
| POST       | `/api/token/refresh/`        | Refresh token egasi                                      | 200          | 400, 401                              |
| POST       | `/api/token/verify/`         | Hamma                                                    | 200          | 400 (bekor qilingan), 401 (noto'g'ri) |
| POST       | `/api/auth/logout/`          | Login qilganlar, faqat o'z tokeni                        | 205          | 400, 401                              |
| POST       | `/api/auth/change-password/` | Login qilganlar, 5/daqiqa                                | 200          | 400, 401, 429                         |
| GET        | `/api/users/me/`             | Login qilganlar                                          | 200          | 401                                   |
| PUT, PATCH | `/api/users/me/`             | Login qilganlar                                          | 200          | 400, 401                              |
| DELETE     | `/api/users/me/`             | Login qilganlar (superuser'dan tashqari)                 | 204          | 400, 401                              |
| GET        | `/api/users/`                | Admin. `?search=`, `?is_active=`, `?ordering=`, `?page=` | 200          | 401, 403                              |
| GET        | `/api/users/{id}/`           | Egasi yoki admin                                         | 200          | 401, 403, 404                         |
| PUT, PATCH | `/api/users/{id}/`           | Egasi yoki admin                                         | 200          | 400, 401, 403, 404                    |
| DELETE     | `/api/users/{id}/`           | Egasi yoki admin                                         | 204          | 400, 401, 403, 404                    |

**Javobdagi maydonlar:**

| Maydon                                           | Yozish mumkinmi | Izoh                                                                                                |
| ------------------------------------------------ | --------------- | --------------------------------------------------------------------------------------------------- |
| `username`, `first_name`, `last_name`            | Ha              |                                                                                                     |
| `email`                                          | Ha              | Bo'sh bo'lishi mumkin. Bo'sh bo'lmasa, boshqa foydalanuvchida bo'lmasin (katta-kichik harf farqsiz) |
| `password`                                       | Yo'q            | Yuborilsa **400**: parol faqat `/api/auth/change-password/` orqali, eski parol bilan o'zgaradi      |
| `role`, `is_active`, `date_joined`, `last_login` | Yo'q            | Yuborilgan qiymat e'tiborsiz qoldiriladi                                                            |
| `id`                                             | Yo'q            |                                                                                                     |

`is_staff` va `is_superuser` serializer'da umuman yo'q, shuning uchun ularni API orqali o'zgartirib bo'lmaydi. Rolni admin `/api/profiles/` orqali, nofaol hisobni qayta faollashtirishni esa `/admin/` panelida qiladi.

Registratsiyada `email`, `first_name`, `last_name` ixtiyoriy.

> **Nega parol jimgina e'tiborsiz qoldirilmaydi:** aks holda javob `200` bo'lardi va mijoz parol almashdi deb o'ylab qolardi. Admin ham boshqa foydalanuvchi parolini API orqali o'rnata olmaydi: buni `/admin/` paneli yoki `python manage.py changepassword <login>` bilan qiladi.

```json
{ "password": ["Parolni change-password orqali o‘zgartiring."] }
```

### 26.3. PUT va PATCH farqi

Boshlanishida: `first_name = "Ali"`, `last_name = "Valiyev"`.

|                          | `PATCH`                                                  | `PUT`                                                                                      |
| ------------------------ | -------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| Ma'nosi                  | Qisman tahrirlash                                        | To'liq tahrirlash                                                                          |
| Majburiy maydonlar       | Yo'q                                                     | `username` majburiy                                                                        |
| So'rov                   | `{"first_name":"Alijon"}`                                | `{"username":"ali","email":"ali@example.com","first_name":"Alijon","last_name":"Karimov"}` |
| Natija                   | Faqat `first_name` o'zgaradi, `last_name` hali `Valiyev` | Yuborilgan to'rtala maydon yoziladi                                                        |
| `username` siz yuborilsa | Ishlaydi                                                 | 400                                                                                        |

Haqiqiy `PUT` javobi, `username` yuborilmaganda (`400`):

```json
{ "username": ["Ushbu maydon to'ldirilishi shart."] }
```

> DRF'da `PUT` majburiy bo'lmagan, lekin yuborilmagan maydonni tozalamaydi: u eski qiymatida qoladi. Maydonni tozalash uchun uni aniq yuboring, masalan `"email":""`.

### 26.4. Nima uchun DELETE soft delete

`DELETE` foydalanuvchini bazadan o'chirmaydi, faqat `is_active=False` qiladi (`SoftDeleteUserMixin`).

| Sabab       | Tushuntirish                                                                                                                          |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| Bronlar     | `Reservation.customer` `PROTECT`: broni bor foydalanuvchini o'chirib bo'lmaydi                                                        |
| Buyurtmalar | `Order.customer` va `Order.waiter` `SET_NULL`: haqiqiy o'chirishda kim buyurtma berganini va kim xizmat qilganini yo'qotgan bo'lardik |
| Hisobotlar  | To'lov va holat tarixi to'liq qoladi                                                                                                  |
| Qaytarish   | Xato bilan o'chirilgan hisobni `/admin/` da qayta faollashtirish mumkin                                                               |

`DELETE` dan keyin: login ishlamaydi, refresh tokenlar bekor qilinadi, access token ham rad etiladi. `username` va `email` band bo'lib qoladi. Superuser'ni o'chirib bo'lmaydi (400).

### 26.5. `IsOwnerOrAdmin` qanday ishlaydi

DRF ruxsatni ikki bosqichda tekshiradi:

| Metod                                       | Qachon ishlaydi                  | Nimani biladi                | Misol                                |
| ------------------------------------------- | -------------------------------- | ---------------------------- | ------------------------------------ |
| `has_permission(request, view)`             | Har so'rovda, view boshlanishida | Faqat so'rovni, yozuvni emas | `IsAuthenticated`: login qilinganmi? |
| `has_object_permission(request, view, obj)` | `get_object()` chaqirilganda     | Aniq yozuvni ham             | `IsOwnerOrAdmin`: bu yozuv senikimi? |

`GET /api/users/5/` ni `bob` yuborsa:

```
1. IsAuthenticated.has_permission        → login qilinmagan bo'lsa: 401
2. get_object() bazadan 5-foydalanuvchini oladi → yo'q bo'lsa: 404
3. IsOwnerOrAdmin.has_object_permission  → obj == request.user yoki rol admin? Yo'q bo'lsa: 403
4. IsSelfOrAdminForWrite.has_object_permission → superuser himoyasi
```

Ikki muhim oqibat:

- `IsOwnerOrAdmin` ning `has_permission` metodi yo'q, u standart `True` qaytaradi. Shuning uchun `IsAuthenticated` ham kerak: anonim foydalanuvchi 401 oladi.
- `has_object_permission` ro'yxatda ishlamaydi, chunki `ListAPIView` `get_object()` ni chaqirmaydi. Shu sababli `/api/users/` alohida `IsAdminRole` bilan yopilgan.

**`IsSelfOrAdminForWrite` nega kerak:** `IsOwnerOrAdmin` ning o'zi `admin` roliga hamma narsani ruxsat etadi. Unda `admin` rolidagi oddiy foydalanuvchi superuserning `username` va `email` ini o'zgartirishi mumkin edi. Bu klass superuser hisobini yozish uchun faqat superuserga ochadi. O'qish va o'zining hisobi bilan ishlashga ta'sir qilmaydi.

| Kim → kimga                | Oddiy foydalanuvchi | `admin` roli             | Superuser                            |
| -------------------------- | ------------------- | ------------------------ | ------------------------------------ |
| O'zi                       | Hammasi             | Hammasi                  | Hammasi, `DELETE` dan tashqari (400) |
| Boshqa oddiy foydalanuvchi | 403                 | Hammasi                  | Hammasi                              |
| Boshqa superuser           | 403                 | Faqat o'qish, yozish 403 | O'qish va tahrirlash, `DELETE` 400   |

### 26.6. CMD uchun curl misollari

Buyruqlar **CMD** uchun: JSON ichidagi qo'shtirnoq `\"` bilan yoziladi. PowerShell'da qo'shtirnoqlar boshqacha ishlaydi. Server ishlab turishi kerak (`python manage.py runserver`).

Quyidagi javoblar shu buyruqlarni CMD orqali bajarib olingan. Tokenlar qisqartirilgan. Bazaning vaqtinchalik nusxasi ishlatilgani uchun sizda `id` va vaqtlar boshqacha bo'ladi.

**Ro'yxatdan o'tish** (`201`):

```cmd
curl -X POST http://127.0.0.1:8000/api/auth/register/ -H "Content-Type: application/json" -d "{\"username\":\"ali\",\"email\":\"ali@example.com\",\"password\":\"Kuchli-Parol-2026\",\"password2\":\"Kuchli-Parol-2026\",\"first_name\":\"Ali\",\"last_name\":\"Valiyev\"}"
```

```json
{
	"user": {
		"id": 5,
		"username": "ali",
		"email": "ali@example.com",
		"first_name": "Ali",
		"last_name": "Valiyev",
		"role": "customer",
		"is_active": true,
		"date_joined": "2026-11-04T09:19:18.928037+05:00",
		"last_login": null
	},
	"access": "eyJhbGciOiJIUzI1NiIs...",
	"refresh": "eyJhbGciOiJIUzI1NiIs..."
}
```

Email band bo'lsa (`400`):

```json
{ "email": ["Bu email boshqa foydalanuvchiga tegishli."] }
```

**Token olish** (`200`):

```cmd
curl -X POST http://127.0.0.1:8000/api/token/ -H "Content-Type: application/json" -d "{\"username\":\"ali\",\"password\":\"Kuchli-Parol-2026\"}"
```

```json
{ "refresh": "eyJhbGciOiJIUzI1NiIs...", "access": "eyJhbGciOiJIUzI1NiIs..." }
```

Keyingi buyruqlar qulay bo'lishi uchun tokenlarni o'zgaruvchiga oling (o'zingiznikini to'liq qo'ying):

```cmd
set ACCESS=eyJhbGciOi...
set REFRESH=eyJhbGciOi...
```

**O'z hisobim: GET** (`200`):

```cmd
curl http://127.0.0.1:8000/api/users/me/ -H "Authorization: Bearer %ACCESS%"
```

```json
{
	"id": 5,
	"username": "ali",
	"email": "ali@example.com",
	"first_name": "Ali",
	"last_name": "Valiyev",
	"role": "customer",
	"is_active": true,
	"date_joined": "2026-11-04T09:19:18.928037+05:00",
	"last_login": "2026-11-04T09:19:20.035196+05:00"
}
```

Tokensiz (`401`):

```json
{ "detail": "Login ma’lumotlari yuborilmagan." }
```

Basic auth bilan ham ishlaydi (`200`, javob xuddi shunday):

```cmd
curl -u ali:Kuchli-Parol-2026 http://127.0.0.1:8000/api/users/me/
```

**PATCH** (`200`):

```cmd
curl -X PATCH http://127.0.0.1:8000/api/users/me/ -H "Authorization: Bearer %ACCESS%" -H "Content-Type: application/json" -d "{\"first_name\":\"Alijon\"}"
```

```json
{
	"id": 5,
	"username": "ali",
	"email": "ali@example.com",
	"first_name": "Alijon",
	"last_name": "Valiyev",
	"role": "customer",
	"is_active": true,
	"date_joined": "2026-11-04T09:19:18.928037+05:00",
	"last_login": "2026-11-04T09:19:20.035196+05:00"
}
```

**PUT** (`200`):

```cmd
curl -X PUT http://127.0.0.1:8000/api/users/me/ -H "Authorization: Bearer %ACCESS%" -H "Content-Type: application/json" -d "{\"username\":\"ali\",\"email\":\"ali@example.com\",\"first_name\":\"Alijon\",\"last_name\":\"Karimov\"}"
```

```json
{
	"id": 5,
	"username": "ali",
	"email": "ali@example.com",
	"first_name": "Alijon",
	"last_name": "Karimov",
	"role": "customer",
	"is_active": true,
	"date_joined": "2026-11-04T09:19:18.928037+05:00",
	"last_login": "2026-11-04T09:19:20.035196+05:00"
}
```

**Boshqa foydalanuvchiga urinish** (`403`):

```cmd
curl http://127.0.0.1:8000/api/users/1/ -H "Authorization: Bearer %ACCESS%"
```

```json
{ "detail": "Bu amal faqat hisob egasi yoki administrator uchun ruxsat etilgan." }
```

**Tokenni tekshirish** (to'g'ri bo'lsa `200`, javob `{}`):

```cmd
curl -X POST http://127.0.0.1:8000/api/token/verify/ -H "Content-Type: application/json" -d "{\"token\":\"%ACCESS%\"}"
```

Noto'g'ri token (`401`):

```json
{ "detail": "Token noto‘g‘ri.", "code": "token_not_valid" }
```

**Refresh** (`200`, ikkala token ham yangi, `set` bilan yangilang):

```cmd
curl -X POST http://127.0.0.1:8000/api/token/refresh/ -H "Content-Type: application/json" -d "{\"refresh\":\"%REFRESH%\"}"
```

```json
{ "access": "eyJhbGciOiJIUzI1NiIs...", "refresh": "eyJhbGciOiJIUzI1NiIs..." }
```

Eski refresh token qayta yuborilsa (`401`):

```json
{ "detail": "Token bekor qilingan.", "code": "token_not_valid" }
```

**Parolni almashtirish** (`200`):

```cmd
curl -X POST http://127.0.0.1:8000/api/auth/change-password/ -H "Authorization: Bearer %ACCESS%" -H "Content-Type: application/json" -d "{\"old_password\":\"Kuchli-Parol-2026\",\"new_password\":\"Yangi-Maxfiy-2027\",\"new_password2\":\"Yangi-Maxfiy-2027\"}"
```

```json
{ "detail": "Parol almashtirildi. Qaytadan login qiling." }
```

Eski parol noto'g'ri bo'lsa (`400`):

```json
{ "old_password": ["Eski parol noto‘g‘ri."] }
```

Muvaffaqiyatdan keyin barcha refresh tokenlar bekor bo'ladi (`401`, `Token bekor qilingan.`). Eski parol bilan login ham ishlamaydi (`401`):

```json
{ "detail": "Login yoki parol noto‘g‘ri, yoki hisob faol emas." }
```

Yangi parol bilan qaytadan token oling va `set` bilan yangilang.

**Chiqish** (`205`, javob tanasi bo'sh):

```cmd
curl -X POST http://127.0.0.1:8000/api/auth/logout/ -H "Authorization: Bearer %ACCESS%" -H "Content-Type: application/json" -d "{\"refresh\":\"%REFRESH%\"}"
```

Noto'g'ri token (`400`):

```json
{ "refresh": ["Token noto‘g‘ri yoki eskirgan."] }
```

Logout'dan keyin shu refresh token bilan yangi access olib bo'lmaydi (`401`, `Token bekor qilingan.`). `verify` esa bekor qilingan token uchun `401` emas, `400` qaytaradi (`simplejwt` shunday ishlaydi):

```json
{ "non_field_errors": ["Token bekor qilingan."] }
```

**Hisobni o'chirish** (`204`, javob tanasi bo'sh):

```cmd
curl -X DELETE http://127.0.0.1:8000/api/users/me/ -H "Authorization: Bearer %ACCESS%"
```

Shundan keyin eski access token rad etiladi (`401`):

```json
{ "detail": "Foydalanuvchi faol emas.", "code": "user_inactive" }
```

Token olish ham ishlamaydi (`401`):

```json
{ "detail": "Login yoki parol noto‘g‘ri, yoki hisob faol emas." }
```

### 26.7. So'rovlarni cheklash (throttling)

Cheklovdan oshilganda **429** qaytadi va `Retry-After` sarlavhasi necha soniya kutish kerakligini aytadi.

| Qayerda                                          | Doira (`scope`)   | Chegara   | Nimaga qarab sanaladi |
| ------------------------------------------------ | ----------------- | --------- | --------------------- |
| Anonim foydalanuvchining qolgan so'rovlari       | `anon`            | 100/soat  | IP                    |
| Login qilgan foydalanuvchining qolgan so'rovlari | `user`            | 1000/soat | Foydalanuvchi         |
| `POST /api/token/` va xato Basic parol           | `login`           | 5/daqiqa  | IP                    |
| `POST /api/auth/register/`                       | `register`        | 5/daqiqa  | IP                    |
| `POST /api/auth/change-password/`                | `change_password` | 5/daqiqa  | Foydalanuvchi         |

Bir daqiqa ichidagi 6-urinishda (`429`):

```cmd
curl -X POST http://127.0.0.1:8000/api/token/ -H "Content-Type: application/json" -d "{\"username\":\"customer1\",\"password\":\"notogri\"}"
```

```json
{ "detail": "So‘rovlar soni chegaradan oshdi. 52 soniyadan keyin urinib ko‘ring." }
```

**Oddiy sozlash yetmaydigan ikki joy, ikkalasi ham test bilan tekshirilgan:**

| Muammo                                                  | Sabab                                                                                                  | Yechim                                                                                                                     |
| ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------- |
| `X-Forwarded-For` ni soxtalashtirib cheklovdan qutulish | `NUM_PROXIES` berilmasa, DRF IP manzilni shu sarlavhadan oladi                                         | `NUM_PROXIES: 0`: faqat haqiqiy `REMOTE_ADDR` ishlatiladi                                                                  |
| Basic orqali parolni cheksiz tanlash                    | DRF autentifikatsiyani throttling'dan **oldin** bajaradi: xato parol 401 bilan to'xtaydi va sanalmaydi | `ThrottledBasicAuthentication` xato urinishlarni `login` hisobiga yozadi. To'g'ri parol bilan ishlaydigan mijoz sanalmaydi |

**Serverga chiqishda:**

- **Nginx ortida** `NUM_PROXIES` ni proksilar soniga teng qiling (odatda `1`). Aks holda hamma mijoz bitta IP'dan kelgandek ko'rinadi va birgalikda cheklanadi.
- **Bir nechta worker** bo'lsa (gunicorn), umumiy kesh kerak (Redis). Standart `LocMemCache` har jarayonda alohida sanaydi, ya'ni haqiqiy chegara workerlar soniga ko'payadi. Server qayta ishga tushganda hisob ham nolga tushadi.
- **Bitta tarmoq:** restoran Wi-Fi'dagi barcha anonim mehmonlar bitta IP bilan chiqsa, `100/soat` ni birgalikda ishlatadi. Menyu ko'p ko'riladigan bo'lsa, `anon` ni oshiring.

**Testlarda:** `api/tests.py` dagi `setUpModule` barcha tezliklarni juda katta qiladi, shuning uchun yuzlab so'rov bir-biriga xalaqit bermaydi. `ThrottleTests` esa haqiqiy tezliklarni qaytaradi va har testdan oldin keshni tozalaydi.

### 26.8. O'zbekcha xato xabarlari

`simplejwt` da o'zbekcha tarjima yo'q, DRF'da esa autentifikatsiya xabarlari tarjima qilinmagan. `api/exceptions.py` dagi `uzbek_exception_handler` DRF'ning standart handleridan keyin javobni ko'rib chiqadi va ma'lum matnlarni almashtiradi:

| Inglizcha                                            | O'zbekcha                                                          |
| ---------------------------------------------------- | ------------------------------------------------------------------ |
| `Token is blacklisted`                               | Token bekor qilingan.                                              |
| `Token is invalid`                                   | Token noto'g'ri.                                                   |
| `Token is expired`                                   | Token muddati o'tgan.                                              |
| `Token is invalid or expired`                        | Token noto'g'ri yoki muddati o'tgan.                               |
| `No active account found with the given credentials` | Login yoki parol noto'g'ri, yoki hisob faol emas.                  |
| `Authentication credentials were not provided.`      | Login ma'lumotlari yuborilmagan.                                   |
| `User is inactive`                                   | Foydalanuvchi faol emas.                                           |
| `Request was throttled...`                           | So'rovlar soni chegaradan oshdi. N soniyadan keyin urinib ko'ring. |

To'liq ro'yxat: `TRANSLATIONS` lug'ati.

- **`code` o'zgarmaydi** (`token_not_valid`, `user_inactive`). Frontend xabar matniga emas, shu kodga qarab ishlashi kerak.
- Javob tuzilishi saqlanadi, ichki `messages` ro'yxati ham tarjima qilinadi.
- `simplejwt` yangilanganda matnlari o'zgarsa, tarjima qilinmagan xabar inglizcha chiqadi, lekin xato bermaydi.

---

## 27. Mahsulotlar API

Mahsulotlarni ro'yxatdan o'tmaganlar ham ko'ra oladi, tafsilot va qo'shish uchun login kerak, tahrirlashni egasi yoki admin qiladi. O'chirishni esa **faqat egasi, o'z profili orqali** qiladi (27.6-bo'lim). Kod: `api/models.py`, `api/serializers.py`, `api/permissions.py`, `api/views.py`.

### 27.1. Model maydonlari

| Maydon                     | Turi                   | Cheklov                                    | Izoh                                                              |
| -------------------------- | ---------------------- | ------------------------------------------ | ----------------------------------------------------------------- |
| `id`                       | Avtomatik              | Faqat o'qish                               |                                                                   |
| `name`                     | `CharField(200)`       | Majburiy, bo'sh bo'lmasin                  | Nomi                                                              |
| `description`              | `TextField`            | Ixtiyoriy                                  | Tavsif                                                            |
| `price`                    | `DecimalField(12, 2)`  | Majburiy, `>= 0`                           | Narxi, so'mda. `0` ruxsat etiladi                                 |
| `quantity`                 | `PositiveIntegerField` | `>= 0`, standart `0`                       | Soni                                                              |
| `image`                    | `ImageField`           | Ixtiyoriy, 3 MB gacha, JPEG, PNG yoki WebP | `media/products/` ga saqlanadi. Fayl mazmuni tekshiriladi         |
| `created_by`               | FK `User`, `PROTECT`   | Faqat o'qish                               | Serverda `request.user` dan qo'yiladi. Javobda `username` chiqadi |
| `created_at`, `updated_at` | `DateTimeField`        | Faqat o'qish                               | Avtomatik                                                         |

Standart tartib: eng yangisi birinchi. `PROTECT` sababli mahsuloti bor foydalanuvchini bazadan o'chirib bo'lmaydi; API dagi soft delete (26.4-bo'lim) esa unga ta'sir qilmaydi, mahsulot va uning egasi qoladi.

### 27.2. Ruxsatlar

| Amal              | Metod  | URL                   | Kim               | Javob | Xatolar            |
| ----------------- | ------ | --------------------- | ----------------- | ----- | ------------------ |
| Ro'yxat           | GET    | `/api/products/`      | Hamma, anonim ham | 200   | 429                |
| Tafsilot          | GET    | `/api/products/{id}/` | Login qilganlar   | 200   | 401, 404           |
| Qo'shish          | POST   | `/api/products/`      | Login qilganlar   | 201   | 400, 401           |
| To'liq tahrirlash | PUT    | `/api/products/{id}/` | Egasi yoki admin  | 200   | 400, 401, 403, 404 |
| Qisman tahrirlash | PATCH  | `/api/products/{id}/` | Egasi yoki admin  | 200   | 400, 401, 403, 404 |
| O'chirish | DELETE | `/api/products/{id}/` | Hech kim: profil orqali (27.6-bo'lim) | 405 | 401 |

Admin deganda `admin` roli yoki superuser tushuniladi. `waiter` va `chef` bu yerda oddiy foydalanuvchi kabi: o'z mahsulotini boshqaradi, boshqanikini yo'q. Admin boshqaning mahsulotini o'chira olmaydi. Admin tahrirlaganda ham `created_by` o'zgarmaydi.

Ro'yxat parametrlari:

| Parametr     | Misol              | Vazifasi                                                                        |
| ------------ | ------------------ | ------------------------------------------------------------------------------- |
| `search`     | `?search=choy`     | `name` va `description` bo'yicha qidirish                                       |
| `ordering`   | `?ordering=-price` | `price`, `created_at`, `name` bo'yicha saralash                                 |
| `created_by` | `?created_by=4`    | Yaratgan foydalanuvchi **id** si bo'yicha filtr (javobda `username` chiqsa ham) |
| `page`       | `?page=2`          | Sahifa, har birida 10 ta                                                        |

### 27.3. Nima uchun ikki xil serializer

|             | `ProductListSerializer`        | `ProductDetailSerializer`                        |
| ----------- | ------------------------------ | ------------------------------------------------ |
| Qachon      | `list`                         | `retrieve`, `create`, `update`, `partial_update` |
| Maydonlar   | `id`, `name`, `price`, `image` | Hammasi                                          |
| Kim ko'radi | Hamma, anonim ham              | Login qilganlar                                  |

Ikki sabab bor:

1. **Maxfiylik.** Ro'yxat ochiq, tafsilot esa yopiq. Bitta serializer bo'lsa, anonim foydalanuvchi `quantity`, `description` va egasini ro'yxatning o'zidan bilib olardi va `401` qoidasi ma'nosiz bo'lib qolardi.
2. **Tezlik.** Katalog sahifasiga faqat nom, narx va rasm kerak. Javob kichikroq bo'ladi.

Tanlovni `get_serializer_class` qiladi:

```python
def get_serializer_class(self):
    return ProductListSerializer if self.action == 'list' else ProductDetailSerializer
```

### 27.4. `get_permissions` qanday ishlaydi

`ModelViewSet` bitta klassda bir nechta amalni bajaradi. `permission_classes` hammasiga bir xil ruxsat beradi, bizga esa har amalga boshqasi kerak. DRF so'rov boshida `self.action` ni URL va metoddan aniqlaydi va `get_permissions()` ni chaqiradi:

```python
def get_permissions(self):
    if self.action == 'list':
        return [permissions.AllowAny()]
    if self.action in ('update', 'partial_update'):
        return [permissions.IsAuthenticated(), IsProductOwnerOrAdmin()]
    return [permissions.IsAuthenticated()]
```

| So'rov                    | `self.action`      | Ruxsatlar                                   |
| ------------------------- | ------------------ | ------------------------------------------- |
| `GET /api/products/`      | `list`             | `AllowAny`                                  |
| `GET /api/products/5/`    | `retrieve`         | `IsAuthenticated`                           |
| `POST /api/products/`     | `create`           | `IsAuthenticated`                           |
| `PUT /api/products/5/`    | `update`           | `IsAuthenticated` + `IsProductOwnerOrAdmin` |
| `PATCH /api/products/5/`  | `partial_update`   | `IsAuthenticated` + `IsProductOwnerOrAdmin` |
| `DELETE /api/products/5/` | `None` (ulanmagan) | `IsAuthenticated`, keyin 405 |
| `OPTIONS` va boshqalar    | `metadata` va h.k. | `IsAuthenticated`                           |

- **Oxirgi qator ataylab eng qattiq emas, lekin yopiq:** keyin yangi action qo'shilib, ro'yxatga kiritish unutilsa, u tasodifan hammaga ochiq bo'lib qolmaydi.
- **`has_permission` va `has_object_permission`:** `IsAuthenticated` so'rov boshida ishlaydi (anonim: `401`). `IsProductOwnerOrAdmin` esa `get_object()` chaqirilganda aniq mahsulot bilan ishlaydi (begona: `403`). Batafsil: 26.5-bo'lim.

### 27.5. CMD uchun curl misollari

Quyidagi javoblar shu buyruqlarni CMD orqali bajarib olingan. Tokenlar qisqartirilgan. `id` va vaqtlar sizda boshqacha bo'ladi.

**Ro'yxat, login shart emas** (`200`):

```cmd
curl "http://127.0.0.1:8000/api/products/?search=choy&ordering=-price"
```

```json
{
	"count": 1,
	"next": null,
	"previous": null,
	"results": [{ "id": 2, "name": "Qora choy", "price": "15000.00", "image": null }]
}
```

**Tafsilot, loginsiz** (`401`):

```cmd
curl http://127.0.0.1:8000/api/products/2/
```

```json
{ "detail": "Login ma’lumotlari yuborilmagan." }
```

**Token olish** (`200`):

```cmd
curl -X POST http://127.0.0.1:8000/api/token/ -H "Content-Type: application/json" -d "{\"username\":\"customer1\",\"password\":\"Restoran2026!\"}"
```

```json
{ "refresh": "eyJhbGciOiJIUzI1NiIs...", "access": "eyJhbGciOiJIUzI1NiIs..." }
```

```cmd
set ACCESS=eyJhbGciOi...
```

**Qo'shish** (`201`). `created_by` da boshqa `id` yuborilgan, lekin u e'tiborsiz qoldirilib, egasi `customer1` bo'lgan:

```cmd
curl -X POST http://127.0.0.1:8000/api/products/ -H "Authorization: Bearer %ACCESS%" -H "Content-Type: application/json" -d "{\"name\":\"Ko'k choy\",\"description\":\"100 gramm\",\"price\":\"12000.50\",\"quantity\":10,\"created_by\":1}"
```

```json
{
	"id": 2,
	"name": "Ko'k choy",
	"description": "100 gramm",
	"price": "12000.50",
	"quantity": 10,
	"image": null,
	"created_by": "customer1",
	"created_at": "2026-11-04T09:54:13.406985+05:00",
	"updated_at": "2026-11-04T09:54:13.407003+05:00"
}
```

Manfiy narx (`400`):

```json
{ "price": ["Qiymat 0 dan kichik bo‘lmasin."] }
```

**Rasm bilan qo'shish** (`201`). Bu yerda `-F` ishlatiladi, `Content-Type` ni curl o'zi qo'yadi:

```cmd
curl -X POST http://127.0.0.1:8000/api/products/ -H "Authorization: Bearer %ACCESS%" -F "name=Rasmli" -F "price=1000" -F "image=@rasm.png"
```

```json
{
	"id": 3,
	"name": "Rasmli",
	"description": "",
	"price": "1000.00",
	"quantity": 0,
	"image": "http://127.0.0.1:8000/media/products/rasm.png",
	"created_by": "customer1",
	"created_at": "2026-11-04T09:54:13.798214+05:00",
	"updated_at": "2026-11-04T09:54:13.798227+05:00"
}
```

GIF yoki rasm bo'lmagan fayl (`400`):

```json
{ "image": ["Faqat haqiqiy JPEG, PNG yoki WebP rasmini yuklang."] }
```

**Tafsilot, login bilan** (`200`):

```cmd
curl http://127.0.0.1:8000/api/products/2/ -H "Authorization: Bearer %ACCESS%"
```

```json
{
	"id": 2,
	"name": "Ko'k choy",
	"description": "100 gramm",
	"price": "12000.50",
	"quantity": 10,
	"image": null,
	"created_by": "customer1",
	"created_at": "2026-11-04T09:54:13.406985+05:00",
	"updated_at": "2026-11-04T09:54:13.407003+05:00"
}
```

**PUT** (`200`). `name` va `price` majburiy:

```cmd
curl -X PUT http://127.0.0.1:8000/api/products/2/ -H "Authorization: Bearer %ACCESS%" -H "Content-Type: application/json" -d "{\"name\":\"Qora choy\",\"description\":\"200 gramm\",\"price\":\"15000\",\"quantity\":5}"
```

```json
{
	"id": 2,
	"name": "Qora choy",
	"description": "200 gramm",
	"price": "15000.00",
	"quantity": 5,
	"image": null,
	"created_by": "customer1",
	"created_at": "2026-11-04T09:54:13.406985+05:00",
	"updated_at": "2026-11-04T09:54:13.536807+05:00"
}
```

Majburiy maydonlarsiz (`400`):

```json
{ "name": ["Ushbu maydon to'ldirilishi shart."], "price": ["Ushbu maydon to'ldirilishi shart."] }
```

**PATCH** (`200`). Faqat yuborilgan maydon o'zgaradi:

```cmd
curl -X PATCH http://127.0.0.1:8000/api/products/2/ -H "Authorization: Bearer %ACCESS%" -H "Content-Type: application/json" -d "{\"quantity\":3}"
```

```json
{
	"id": 2,
	"name": "Qora choy",
	"description": "200 gramm",
	"price": "15000.00",
	"quantity": 3,
	"image": null,
	"created_by": "customer1",
	"created_at": "2026-11-04T09:54:13.406985+05:00",
	"updated_at": "2026-11-04T09:54:13.618749+05:00"
}
```

Boshqa foydalanuvchi (`waiter1`) urinsa, `PUT` va `PATCH` uchun (`403`):

```json
{ "detail": "Bu mahsulotni faqat uni yaratgan foydalanuvchi yoki administrator o‘zgartira oladi." }
```

### 27.6. O'chirish qoidasi va "Mening mahsulotlarim"

**Qoida:** mahsulotni faqat uni qo'shgan foydalanuvchi va faqat o'z profili orqali o'chira oladi. Admin roli va superuser boshqaning mahsulotini tahrirlay oladi (`PUT`, `PATCH`), lekin o'chira olmaydi.

| Qayerdan | Egasi | Boshqa foydalanuvchi | `admin` roli | Superuser | Anonim |
| --- | --- | --- | --- | --- | --- |
| `DELETE /api/users/me/products/{id}/` | **204** | 404 | 404 | 404 | 401 |
| `DELETE /api/products/{id}/` | 405 | 405 | 405 | 405 | 401 |
| `/admin/` paneli | Panelga kirish huquqi bo'lsa ham 403 | Panelga kirish huquqi bo'lsa ham 403 | Panelga kirish huquqi bo'lsa ham 403 | 403 | Login sahifasi |

Admin yoki superuserning o'zi qo'shgan mahsulot bo'lsa, ular ham uni o'z profilidan o'chiradi (204): bu yerda hal qiluvchi narsa rol emas, egalik.

**Endpointlar** (`MyProductViewSet`, hammasi `IsAuthenticated`):

| Metod | URL | Vazifasi | Javob | Xatolar |
| --- | --- | --- | --- | --- |
| GET | `/api/users/me/products/` | O'z mahsulotlari, to'liq maydonlar. `?search=`, `?ordering=`, `?page=` | 200 | 401 |
| GET | `/api/users/me/products/{id}/` | O'z mahsuloti | 200 | 401, 404 |
| DELETE | `/api/users/me/products/{id}/` | O'z mahsulotini va uning rasm faylini o'chiradi | 204 | 400, 401, 404 |

**Nima uchun 403 emas, 404:**

- `get_queryset` so'rovni boshidanoq `filter(created_by=request.user)` bilan cheklaydi. Boshqaning mahsuloti bu to'plamda umuman yo'q, shuning uchun "ruxsat yo'q" emas, "topilmadi" deyish to'g'ri.
- 403 mahsulot **borligini** oshkor qilardi: `id` larni birma-bir sinab, nima borligini va nechta ekanini bilish mumkin bo'lardi. 404 da begona va mavjud bo'lmagan mahsulot javobi bir xil.
- Tekshiruvni unutib qo'yish qiyin: alohida ruxsat klassi kerak emas, begona yozuv view'ga umuman yetib kelmaydi.

**Nima uchun umumiy manzilda 405, anonimga esa 401:** `ProductViewSet` da `DestroyModelMixin` yo'q, shuning uchun `DELETE` ulanmagan. DRF esa avval autentifikatsiyani, keyin metodni tekshiradi: anonim birinchi tekshiruvda to'xtaydi (401), login qilgan foydalanuvchi ikkinchisida (405).

**Rasm fayli:** `api/models.py` dagi `post_delete` signali faylni `transaction.on_commit` ichida o'chiradi. Baza o'zgarishi bekor qilinsa, fayl joyida qoladi. Fayl o'chmasa (masalan, band bo'lsa), xato logga yoziladi va foydalanuvchi 500 olmaydi. Rasmi almashtirilganda eski fayl hali ham diskda qoladi: signal faqat mahsulot o'chganda ishlaydi.

**Admin panel:** `ProductAdmin.has_delete_permission` har doim `False`. O'chirish sahifasi 403 qaytaradi, Django esa `delete_selected` amalini shu huquqqa qarab ro'yxatdan o'zi olib tashlaydi. Bu superuserga ham taalluqli.

> **Oqibat:** egasi hisobini o'chirsa (26.4-bo'lim) yoki unga kira olmasa, uning mahsulotlarini API va admin panel orqali hech kim o'chira olmaydi. Ular ochiq ro'yxatda qolaveradi. Admin faqat matnini tahrirlay oladi yoki `python manage.py shell` dan foydalanadi.

#### CMD uchun curl misollari

Javoblar shu buyruqlarni CMD orqali bajarib olingan (bazaning nusxasida).

**Mening mahsulotlarim** (`200`):

```cmd
curl "http://127.0.0.1:8000/api/users/me/products/?search=choy&ordering=-price" -H "Authorization: Bearer %ACCESS%"
```

```json
{"count":1,"next":null,"previous":null,"results":[{"id":3,"name":"Rasmli choy","description":"100 gramm","price":"12000.00","quantity":5,"image":"http://127.0.0.1:8000/media/products/rasm.png","created_by":"customer1","created_at":"2026-11-04T10:31:20.460355+05:00","updated_at":"2026-11-04T10:31:20.460367+05:00"}]}
```

Loginsiz (`401`):

```json
{"detail":"Login ma’lumotlari yuborilmagan."}
```

**Bitta mahsulotim** (`200`):

```cmd
curl http://127.0.0.1:8000/api/users/me/products/3/ -H "Authorization: Bearer %ACCESS%"
```

```json
{"id":3,"name":"Rasmli choy","description":"100 gramm","price":"12000.00","quantity":5,"image":"http://127.0.0.1:8000/media/products/rasm.png","created_by":"customer1","created_at":"2026-11-04T10:31:20.460355+05:00","updated_at":"2026-11-04T10:31:20.460367+05:00"}
```

**O'chirish** (`204`, javob tanasi bo'sh; rasm fayli ham o'chadi):

```cmd
curl -X DELETE http://127.0.0.1:8000/api/users/me/products/3/ -H "Authorization: Bearer %ACCESS%"
```

Boshqaning mahsuloti, mavjud bo'lmagan yoki allaqachon o'chirilgan mahsulot: javob bir xil (`404`):

```json
{"detail":"Yozuv topilmadi."}
```

**Umumiy manzil orqali o'chirishga urinish** (`405`, hamma uchun, egasi uchun ham):

```cmd
curl -X DELETE http://127.0.0.1:8000/api/products/3/ -H "Authorization: Bearer %ACCESS%"
```

```json
{"detail":"«DELETE» metodi ruxsat etilmagan."}
```
