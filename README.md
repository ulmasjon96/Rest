# Rest — Django REST Framework loyihasi

Bu hujjatda loyihani noldan ishga tushirishgacha qilingan barcha ishlar bor: har bir buyruq, har bir kod qatori, o'rnatilgan paketlar, chiqqan xatolar va ularning qanday tuzatilgani tushuntirib yozilgan.

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
16. [Clinic app](#16-clinic-app)
17. [2026-11-02: bajarilgan ishlar va git muammosi](#17-2026-11-02-bajarilgan-ishlar-va-git-muammosi)
18. [Clinic API](#18-clinic-api)
19. [.env sozlamalari](#19-env-sozlamalari)

---

## 1. Umumiy ma'lumot

| Narsa              | Qiymati                                           |
| ------------------ | ------------------------------------------------- |
| Loyiha papkasi     | `C:\Users\user\Desktop\Rest`                      |
| Operatsion tizim   | Windows, CMD terminali                            |
| Python versiyasi   | **3.13** (dastlab 3.15 edi, 10.1-bo'limga qarang) |
| Virtual muhit      | `env`                                             |
| Django loyihasi    | `config`                                          |
| Django app         | `api`                                             |
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

> Yangilanish (2026-11-02): `SECRET_KEY`, `DEBUG` va `ALLOWED_HOSTS` endi `.env` faylidan o'qiladi, `LANGUAGE_CODE = 'uz'`, `TIME_ZONE = 'Asia/Tashkent'`. 19-bo'limga qarang.

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
    'django_filters',                # filtrlash
    'corsheaders',                   # CORS
    'drf_spectacular',               # Swagger
    'api',                           # bizning app
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
}
```

| Kalit                            | Vazifasi                                                                                                                                                                                                                                           |
| -------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `DEFAULT_AUTHENTICATION_CLASSES` | So'rov kimdan kelganini aniqlash usullari. **JWTAuthentication** `Authorization: Bearer <token>` sarlavhasini tekshiradi (React va mobil uchun). **SessionAuthentication** brauzerdagi login sessiyasini tekshiradi (DRF sahifasi va admin uchun). |
| `DEFAULT_PERMISSION_CLASSES`     | Kimga nimaga ruxsat berilishi. **IsAuthenticatedOrReadOnly** bo'yicha o'qish (GET) hammaga ochiq, yozish (POST, PUT, DELETE) esa faqat login qilganlarga.                                                                                          |
| `DEFAULT_FILTER_BACKENDS`        | **DjangoFilterBackend** maydon bo'yicha filtrlaydi (`?author=Ali`). **SearchFilter** matn bo'yicha qidiradi (`?search=python`). **OrderingFilter** saralaydi (`?ordering=-price`, minus kamayish tartibini bildiradi).                             |
| `DEFAULT_PAGINATION_CLASS`       | Natijalarni sahifalarga bo'ladi (`?page=2`).                                                                                                                                                                                                       |
| `PAGE_SIZE`                      | Bir sahifadagi yozuvlar soni: 10 ta.                                                                                                                                                                                                               |
| `DEFAULT_SCHEMA_CLASS`           | Swagger uchun API sxemasini drf-spectacular yaratishini bildiradi.                                                                                                                                                                                 |

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
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('api-auth/', include('rest_framework.urls')),
    path('api/token/', TokenObtainPairView.as_view()),
    path('api/token/refresh/', TokenRefreshView.as_view()),
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
| `TokenObtainPairView`                               | `/api/token/` ga username va parol yuborilsa, `access` va `refresh` tokenlar qaytariladi.                                               |
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
│   ├── models.py            # Book modeli
│   ├── serializers.py       # Book va clinic serializer'lari (qo'lda yaratilgan)
│   ├── urls.py              # router: books + 11 ta clinic resursi + clinic-settings
│   ├── views.py             # BookViewSet, IsStaffOrReadOnly, clinic view'lari
│   └── tests.py             # testlar uchun
├── clinic/                  # Medora Clinic app'i (16-bo'lim)
│   ├── migrations/
│   │   ├── __init__.py
│   │   └── 0001_initial.py  # klinika jadvallari migratsiyasi
│   ├── __init__.py
│   ├── admin.py             # klinika admin sozlamalari
│   ├── apps.py
│   ├── models.py            # 15 ta model (14 ta jadval + 1 proxy)
│   ├── tests.py
│   └── views.py
├── media/                   # yuklangan rasmlar (GitHub'ga yuklanmaydi, birinchi yuklashda paydo bo'ladi)
├── .gitignore               # git e'tiborsiz qoldiradigan fayllar
├── .env                     # maxfiy sozlamalar (GitHub'ga yuklanmaydi, 19-bo'lim)
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

| Qator                   | Nima uchun yuklanmaydi                                  |
| ----------------------- | ------------------------------------------------------- |
| `env/`                  | Katta hajmli, `requirements.txt` orqali qayta tiklanadi |
| `__pycache__/`, `*.pyc` | Python avtomatik yaratadigan kesh fayllari              |
| `db.sqlite3`            | Mahalliy baza                                           |
| `.env`                  | Maxfiy kalitlar va parollar                             |
| `media/`                | Foydalanuvchilar yuklagan rasmlar (logotip, shifokor fotosurati). Ular kod emas, ma'lumot hisoblanadi |

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

**Tavsiyalar:**

1. Python'ning eng yangi versiyasini emas, bir versiya oldingi barqarorini tanlang. Unda paketlarning tayyor wheel'lari deyarli har doim mavjud bo'ladi.
2. Har yangi paket o'rnatgandan keyin `pip freeze > requirements.txt` ni bajaring.
3. Model o'zgartirilganda avval `makemigrations`, keyin `migrate` ni bajaring.
4. Xato chiqqanda traceback'ni pastdan o'qing va loyiha papkangizdagi birinchi faylni toping.
5. `SECRET_KEY` va parollarni `.env` fayliga ko'chiring (`python-dotenv`), `DEBUG = False` va kuchli parolni esa faqat serverda ishlating.
6. `env/`, `db.sqlite3` va `.env` ni GitHub'ga yuklamang.

---

## 16. Clinic app

`clinic` app'i **Medora Clinic** ning ma'lumotlar tuzilmasini saqlaydi: klinika sozlamalari, bo'limlar, xonalar, shifokorlar va ularning ish jadvali, bemorlar, qabullar, qabul tarixi va audit jurnali. Hozircha faqat **modellar va admin panel** tayyor. API (serializer, view, url) keyin yoziladi.

```cmd
python manage.py startapp clinic
```

`config/settings.py` dagi o'zgarishlar:

```python
INSTALLED_APPS = [
    ...
    'api',
    'clinic',                     # Medora Clinic modellari
]

MEDIA_URL = '/media/'             # yuklangan fayllar shu manzil orqali ochiladi
MEDIA_ROOT = BASE_DIR / 'media'   # yuklangan fayllar shu papkada saqlanadi
```

`config/urls.py` oxiriga:

```python
from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

| Sozlama / qator | Vazifasi |
| --- | --- |
| `MEDIA_URL` | Brauzerdagi manzil prefiksi, masalan `http://127.0.0.1:8000/media/doctors/ali.jpg`. |
| `MEDIA_ROOT` | Diskdagi papka: `Rest\media\`. `ImageField(upload_to='doctors/')` faylni `media\doctors\` ga saqlaydi. |
| `static(...)` | Ishlab chiqishda `/media/...` so'rovlariga faylni Django o'zi beradi. `DEBUG = False` bo'lganda bu ishlamaydi, serverda bu ishni nginx bajaradi. |

> `static` va `media` farqi: **static** — dasturchi yozgan CSS, JS va rasmlar (kod bilan birga keladi). **media** — foydalanuvchi yuklagan fayllar (dastur ishlayotganda paydo bo'ladi).

> **Hali yo'q narsalar (ataylab):** `Appointment.source_visit` maydoni va `clinical_models.py` (`VisitCard` va boshqalar) keyingi bosqichda qo'shiladi.

### 16.1. Modellar ro'yxati

| Model | Jadval | Vazifasi |
| --- | --- | --- |
| `Timestamped` | — (abstract) | Boshqa modellarga `created_at` va `updated_at` maydonlarini beradi |
| `ClinicSettings` | `clinic_clinicsettings` | Klinikaning umumiy sozlamalari, **faqat bitta yozuv** |
| `Profile` | `clinic_profile` | Foydalanuvchi hisobining roli: administrator, registrator, shifokor yoki bemor |
| `Department` | `clinic_department` | Bo'lim (masalan, Terapiya, Kardiologiya) |
| `Room` | `clinic_room` | Bo'limga tegishli xona va qavat |
| `Specialty` | `clinic_specialty` | Mutaxassislik (masalan, Kardiolog) |
| `Doctor` | `clinic_doctor` | Shifokor |
| `WorkHour` | `clinic_workhour` | Shifokorning haftalik ish vaqti va tanaffusi |
| `DayOff` | `clinic_dayoff` | Shifokorning ta'til yoki ishlamaydigan kuni |
| `Patient` | `clinic_patient` | Bemor |
| `Appointment` | `clinic_appointment` | Qabul: shifokor, bemor, vaqt va holat |
| `AppointmentStatusEvent` | `clinic_appointmentstatusevent` | Qabul holati o'zgarishlari tarixi |
| `DirectionEvent` | `clinic_directionevent` | Bemorni yo'naltirish bosqichlari tarixi |
| `Audit` | `clinic_audit` | Kim, qachon, qanday amal bajarganining jurnali |
| `AppointmentHistory` | — (proxy, `clinic_audit` jadvali) | Audit jurnalining faqat qabullarga oid qismi |
| `LoginAttempt` | `clinic_loginattempt` | Noto'g'ri login urinishlarini sanash |

### 16.2. Yordamchi kodlar

#### `validate_photo(value)` — rasm validatori

U `ClinicSettings.logo` va `Doctor.photo` maydonlariga `validators=[validate_photo]` orqali ulangan va quyidagilarni tekshiradi:

| Tekshiruv | Kod | Xato matni |
| --- | --- | --- |
| Hajm 3 MB dan oshmasin | `value.size > 3 * 1024 * 1024` | `Rasm 3 MB dan kichik bo'lishi kerak.` |
| Fayl haqiqatan rasm bo'lsin | `Image.open(value)` (Pillow) | `Faqat haqiqiy JPEG, PNG yoki WebP rasmini yuklang.` |
| Format faqat JPEG, PNG yoki WebP bo'lsin | `im.format not in (...)` → `ValueError` | xuddi shu |
| Fayl buzilmagan bo'lsin | `im.verify()` | xuddi shu |

- **Nega kengaytma emas, mazmun tekshiriladi:** `virus.exe` ni `rasm.jpg` deb qayta nomlash oson. Pillow faylning ichini o'qiydi, shuning uchun soxta rasm o'tmaydi.
- `value.seek(0)`: Pillow faylni o'qib, "kursor"ni oxiriga surib qo'yadi. Kursor boshiga qaytarilmasa, Django keyin bo'sh fayl saqlab qo'yishi mumkin.
- `try/except Exception`: har qanday xatoni (buzilgan fayl, noto'g'ri format) bitta tushunarli `ValidationError` ga aylantiradi.
- `from PIL import Image` funksiya ichida import qilingan, ya'ni Pillow faqat rasm tekshirilayotganda yuklanadi.

#### `Timestamped` — abstract model

```python
created_at = models.DateTimeField(default=timezone.now, editable=False)
updated_at = models.DateTimeField(auto_now=True)
class Meta:
    abstract = True
```

- `abstract = True`: bu model uchun **jadval yaratilmaydi**. Undan meros olgan har bir model (`class Doctor(Timestamped)`) bu ikki maydonni o'z jadvaliga oladi. Shu tufayli bir xil kodni 9 marta yozish shart emas.
- `default=timezone.now`: `auto_now_add=True` dan farqi shuki, kerak bo'lsa kodda vaqtni qo'lda berish mumkin (masalan, eski ma'lumotlarni import qilganda). `editable=False` esa maydonni formalarda ko'rsatmaydi.
- `auto_now=True`: har `save()` da joriy vaqt yoziladi.

`Timestamped` dan meros oladigan modellar: `ClinicSettings`, `Profile`, `Department`, `Room`, `Specialty`, `Doctor`, `WorkHour`, `DayOff`, `Patient`. `Appointment` va tarix modellarida bu maydonlar alohida yozilgan.

#### `default_duration()` — dinamik standart qiymat

```python
def default_duration():
    return ClinicSettings.load().default_duration
```

Bu funksiya `Doctor.duration` ning standart qiymatini beradi. `default=30` deb qotirib yozish o'rniga **funksiya** berilgan (qavssiz: `default=default_duration`), shuning uchun har yangi shifokor yaratilganda qiymat klinika sozlamalaridan o'qiladi. Sozlamalar hali kiritilmagan bo'lsa, `load()` saqlanmagan standart obyektni qaytaradi va natija `30` bo'ladi.

> Diqqat: migratsiya fayli bu funksiyaga `clinic.models.default_duration` deb murojaat qiladi. Funksiya nomini o'zgartirsangiz yoki uni o'chirsangiz, migratsiyalar buziladi.

### 16.3. Modellar batafsil

#### `ClinicSettings` — klinika sozlamalari

| Maydon | Turi | Standart | Cheklov | Ma'nosi |
| --- | --- | --- | --- | --- |
| `name` | CharField(150) | `Medora Clinic` | | Klinika nomi |
| `logo` | ImageField | bo'sh | `validate_photo` | Logotip, `media/clinic/` ga saqlanadi |
| `phone`, `address` | CharField | bo'sh | | Aloqa ma'lumotlari |
| `opens_at`, `closes_at` | TimeField | 08:00, 18:00 | `clean()` | Klinikaning umumiy ish vaqti |
| `default_duration` | PositiveSmallInteger | 30 | 5–240 | Standart qabul davomiyligi (daqiqa) |
| `booking_days` | PositiveSmallInteger | 90 | 1–365 | Necha kun oldindan band qilish mumkinligi |
| `cancellation_hours` | PositiveSmallInteger | 0 | 0–168 | Bemor qabulni necha soat oldin bekor qila olishi (0 = cheklov yo'q) |
| `offer_minutes` | PositiveSmallInteger | 15 | 1–1440 | Kutish taklifining amal qilish muddati |
| `document_max_mb` | PositiveSmallInteger | 10 | 1–50 | Tibbiy fayllar uchun hajm limiti |

`MinValueValidator` va `MaxValueValidator` qiymat chegaradan chiqsa, formada xato ko'rsatadi.

`clean()`: `opens_at >= closes_at` bo'lsa, `Klinika ish tugashi boshlanishidan keyin bo'lsin.` xatosi chiqadi.

#### `Profile` — hisob roli

| Maydon | Turi | Ma'nosi |
| --- | --- | --- |
| `user` | OneToOne → User, **CASCADE** | Har foydalanuvchida ko'pi bilan bitta profil bo'ladi |
| `role` | CharField, choices | `admin`, `reception`, `doctor`, `patient` (standart: `patient`) |

`clean()`: foydalanuvchi `Doctor` ga bog'langan bo'lsa, roli `doctor` bo'lishi shart. `Patient` ga bog'langan bo'lsa, roli `patient` bo'lishi shart. Bu ziddiyatli holatning (masalan, shifokor hisobida "bemor" roli) oldini oladi.

#### `Department` — bo'lim

`name` maydoni `unique=True`: bir xil nomli ikkita bo'lim bo'lmaydi.

#### `Room` — xona

| Maydon | Turi | Ma'nosi |
| --- | --- | --- |
| `department` | FK → Department, **PROTECT** | Xona qaysi bo'limga tegishli |
| `floor` | CharField(20) | Qavat. Matn bo'lgani uchun `1`, `-1`, `Mansard` kabi qiymatlar ham bo'lishi mumkin |
| `number` | CharField(20) | Xona raqami (`105`, `105A`) |

`unique_room_location` constraint'i bir bo'limda bir qavatda bir xil raqamli xona takrorlanishiga yo'l qo'ymaydi. `__str__` natijasi: `Terapiya · 1-qavat · 105-xona`.

#### `Specialty` — mutaxassislik

`name` maydoni `unique=True`.

#### `Doctor` — shifokor

| Maydon | Turi | Ma'nosi |
| --- | --- | --- |
| `user` | OneToOne → User, **PROTECT**, ixtiyoriy | Shifokorning tizimga kirish hisobi |
| `name` | CharField(150) | Ism-familiya |
| `specialty` | FK → Specialty, **PROTECT** | Mutaxassisligi (majburiy) |
| `phone` | CharField(25) | Telefon (majburiy) |
| `bio` | TextField, ixtiyoriy | Qisqacha ma'lumot |
| `experience` | PositiveSmallInteger, 5 | Tajriba (yil) |
| `room` | CharField(15) | Xona — **oddiy matn**, majburiy |
| `location` | FK → Room, **PROTECT**, ixtiyoriy | Xona — `Room` jadvaliga bog'lanish |
| `duration` | PositiveSmallInteger | Qabul davomiyligi. Standart qiymati `default_duration()` dan olinadi |
| `active` | Boolean, True | Faol bo'lmagan shifokorga yozilib bo'lmasligi uchun |
| `photo` | ImageField, ixtiyoriy | `media/doctors/` ga saqlanadi, `validate_photo` bilan tekshiriladi |

- `valid_duration` constraint'i `5 <= duration <= 240` shartini **baza darajasida** ta'minlaydi.
- `ordering = ['name']`: ro'yxatlar ism bo'yicha tartiblanadi.
- `initials` (property): ismning birinchi ikki so'zining bosh harflarini qaytaradi, masalan `Ali Valiyev` → `AV`. Rasm bo'lmaganda avatar uchun ishlatiladi.
- `room` va `location` ikkalasi ham bor: `room` tez yoziladigan matn, `location` esa bo'lim va qavat bilan to'liq bog'lanish.

#### `WorkHour` — haftalik ish jadvali

| Maydon | Turi | Ma'nosi |
| --- | --- | --- |
| `doctor` | FK → Doctor, **CASCADE**, `related_name='hours'` | Shifokorning ish kunlari `doctor.hours.all()` orqali olinadi |
| `weekday` | 0–6 (choices) | 0 = Dushanba … 6 = Yakshanba (Python'dagi `date.weekday()` bilan bir xil) |
| `start`, `end` | TimeField | Ish boshlanishi va tugashi |
| `break_start`, `break_end` | TimeField, ixtiyoriy | Tanaffus |

- `one_workday` constraint'i: bitta shifokorda bitta hafta kuni uchun faqat bitta qator bo'ladi.
- `valid_workday` constraint'i: `end > start` (baza darajasida).
- `clean()`:
  1. `start >= end` bo'lsa: `Tugash vaqti boshlanishdan keyin bo'lsin.`
  2. Tanaffusning faqat bitta vaqti kiritilgan bo'lsa: `Tanaffusning ikkala vaqtini kiriting.`
  3. Tanaffus ish vaqtidan tashqarida bo'lsa: `Tanaffus ish vaqti ichida bo'lsin.` Shart: `start <= break_start < break_end <= end`.

#### `DayOff` — ta'til va istisno sanalar

Maydonlari: `doctor` (FK, **CASCADE**, `related_name='days_off'`), `date`, `reason`. `one_dayoff` constraint'i bitta shifokorga bitta sanani faqat bir marta kiritishga ruxsat beradi.

#### `Patient` — bemor

| Maydon | Turi | Ma'nosi |
| --- | --- | --- |
| `user` | OneToOne → User, **PROTECT**, ixtiyoriy | Bemorning shaxsiy kabinet hisobi. Bo'lmasligi ham mumkin: registrator bemorni qo'lda kiritadi |
| `name` | CharField(150) | Ism-familiya |
| `birth_date` | DateField | Tug'ilgan sana (majburiy) |
| `phone` | CharField(25) | Telefon (majburiy) |
| `address` | CharField(250), ixtiyoriy | Manzil |
| `archived` | Boolean, False | Bemor **o'chirilmaydi, arxivlanadi**, shu tufayli qabullar tarixi saqlanib qoladi |

#### `Appointment` — qabul

| Maydon | Turi | Ma'nosi |
| --- | --- | --- |
| `doctor` | FK → Doctor, **PROTECT** | Shifokor |
| `patient` | FK → Patient, **PROTECT** | Bemor |
| `start`, `end` | DateTimeField | Qabul vaqti |
| `status` | choices | `scheduled` → `arrived` → `called` → `in_progress` → `completed`, yoki `cancelled` / `missed` |
| `arrived_at`, `called_at`, `started_at`, `completed_at`, `status_changed_at` | DateTimeField, `editable=False` | Har bir bosqichning aniq vaqti (kod to'ldiradi) |
| `queue_number`, `queue_priority` | Integer, `editable=False` | Navbat raqami va ustuvorligi |
| `reason` | CharField(500) | Bemorning murojaat sababi |
| `note` | TextField | Shifokor izohi |
| `token` | UUIDField, unique | Tasodifiy, taxmin qilib bo'lmaydigan kalit, masalan bemorga SMS'da yuboriladigan havola uchun. `id=5` ni taxmin qilish oson, UUID'ni esa emas |
| `created_by` | FK → User, **PROTECT** | Qabulni yaratgan xodim (majburiy) |
| `created_at`, `updated_at` | DateTimeField | `auto_now_add` / `auto_now` |

- `positive_appointment` constraint'i: `end > start`.
- `indexes`: `(doctor, start, end)` va `(patient, start, end)`. Ular "shu shifokorning shu kungi qabullari" kabi so'rovlarni tezlashtiradi.
- `editable=False` maydonlar admin formasida tahrirlanmaydi. Ularni keyin yoziladigan API yoki servis kodi to'ldiradi.
- **Modelda `clean()` yo'q.** Vaqt to'qnashuvi, `end > start` va shifokor faolligi API'dagi `AppointmentSerializer.validate()` da tekshiriladi (18.4-bo'lim). Admin panelda esa bu tekshiruvlar yo'q. Ish vaqti (`WorkHour`) va `DayOff` hali hech qayerda tekshirilmaydi.

#### `AppointmentStatusEvent` — holat o'zgarishlari tarixi

Maydonlari: `appointment` (FK, **PROTECT**, `related_name='status_events'`), `actor` (FK → User, PROTECT), `previous_status`, `status` (ikkalasi `Appointment.STATUSES` dan) va `changed_at`. Masalan: `scheduled → arrived`, admin, 09:12. `ordering = ['changed_at', 'pk']` — vaqt bir xil bo'lsa, yozuvlar yaratilish tartibida chiqadi.

> Bu modelda `verbose_name` yo'q, shuning uchun admin panelda uning nomi inglizcha (`Appointment status events`) chiqadi.

#### `DirectionEvent` — yo'naltirish tarixi

Bemorning klinika ichidagi yo'lini qayd etadi: `reception` (kelgani tasdiqlandi) → `directed` (xona ko'rsatildi) → `called` → `in_progress` → `completed`. Navbat tartibi o'zgarsa, `reordered` bosqichi yoziladi.

`destination` — **o'sha paytdagi** yo'nalish matni (masalan, `Terapiya · 1-qavat · 105-xona`). U FK emas, oddiy matn, shuning uchun keyin xona o'zgarsa ham tarixda bemor qayerga yuborilgani o'zgarmay qoladi.

#### `Audit` — audit jurnali

Maydonlari: `actor` (FK → User, PROTECT, `null=True` — tizimning o'zi bajargan amallar uchun), `appointment` (FK, PROTECT, ixtiyoriy, `related_name='history'`), `action`, `detail` va `created_at`. `ordering = ['-created_at']` — eng yangi yozuv birinchi chiqadi.

#### `AppointmentHistory` — proxy model

```python
class AppointmentHistory(Audit):
    class Meta:
        proxy = True
```

**Proxy** model uchun yangi jadval yaratilmaydi, `Audit` jadvalining o'zi ishlatiladi. Python tomonda esa boshqa nom, boshqa admin sahifa yoki boshqa metodlar berish mumkin. Bu yerda admin panelda "Qabul o'zgarish tarixi" alohida bo'lim bo'lib chiqadi va unda faqat qabulga bog'langan audit yozuvlari ko'rsatiladi.

#### `LoginAttempt` — login urinishlari

Maydonlari: `key` (unique, masalan `ip:username`), `count` (urinishlar soni) va `since` (birinchi urinish vaqti). Model parolni ko'p marta taxmin qilishga (brute force) qarshi kerak: `count` chegaradan oshsa, login vaqtincha bloklanadi. Bu mantiq keyin yoziladi.

### 16.4. Bog'lanishlar va `on_delete`

```
User ─1:1 CASCADE─ Profile
User ─1:1 PROTECT─ Doctor ─FK PROTECT─ Specialty
                     │ └──FK PROTECT─ Room ─FK PROTECT─ Department
                     ├──< WorkHour (CASCADE)
                     └──< DayOff   (CASCADE)
User ─1:1 PROTECT─ Patient
Doctor, Patient, User(created_by) ─FK PROTECT─< Appointment
Appointment ─FK PROTECT─< AppointmentStatusEvent, DirectionEvent, Audit
```

**ForeignKey** — "ko'pdan birga" bog'lanish: bitta bo'limda ko'p xona bo'ladi, har bir xona esa bitta bo'limga tegishli. **OneToOneField** — "birga bir" bog'lanish: bitta foydalanuvchi hisobi faqat bitta shifokorga (yoki bitta bemorga, bitta profilga) bog'lanadi.

| `on_delete` | Asosiy yozuv o'chirilganda | Qayerda | Nima uchun |
| --- | --- | --- | --- |
| **CASCADE** | Bog'langan yozuvlar **ham o'chadi** | `Profile.user`, `WorkHour.doctor`, `DayOff.doctor` | Bu yozuvlar o'z-o'zidan ma'noga ega emas: shifokorsiz ish jadvali kerak emas |
| **PROTECT** | O'chirish **taqiqlanadi** (`ProtectedError`). Avval bog'langan yozuvlarni olib tashlash kerak | Qolgan barcha FK va OneToOne'lar | Tibbiy va moliyaviy tarix tasodifan yo'qolmasligi uchun |

Amaldagi natijalari:
- Qabullari bor shifokor yoki bemorni o'chirib bo'lmaydi. Uning o'rniga shifokorga `active = False`, bemorga `archived = True` qo'yiladi.
- Tarixi (status, yo'naltirish yoki audit yozuvlari) bor qabulni o'chirib bo'lmaydi. Uning o'rniga `status = cancelled` qo'yiladi.
- Ichida xona bor bo'limni yoki shifokori bor mutaxassislikni o'chirib bo'lmaydi.
- Shifokor yoki bemorga bog'langan, yoki qabul yaratgan User'ni o'chirib bo'lmaydi. Uning o'rniga `is_active = False` qo'yiladi.
- Boshqa hech narsaga bog'lanmagan User o'chirilsa, uning `Profile` i ham birga o'chadi.

### 16.5. Constraint'lar (baza darajasidagi cheklovlar)

| Nomi | Model | Shart |
| --- | --- | --- |
| `single_clinic_settings` | ClinicSettings | `id = 1` |
| `unique_room_location` | Room | `(department, floor, number)` takrorlanmaydi |
| `valid_duration` | Doctor | `5 <= duration <= 240` |
| `one_workday` | WorkHour | `(doctor, weekday)` takrorlanmaydi |
| `valid_workday` | WorkHour | `end > start` |
| `one_dayoff` | DayOff | `(doctor, date)` takrorlanmaydi |
| `positive_appointment` | Appointment | `end > start` |

Bulardan tashqari `unique=True` maydonlar: `Department.name`, `Specialty.name`, `Appointment.token`, `LoginAttempt.key`.

**Constraint va `clean()` farqi:**

| | Constraint | `clean()` va validator'lar |
| --- | --- | --- |
| Qayerda ishlaydi | Ma'lumotlar bazasining o'zida | Python'da, `full_clean()` chaqirilganda |
| Qachon ishlaydi | **Har doim**, hatto `shell` yoki xom SQL'da ham | Admin panel va ModelForm'da avtomatik. Oddiy `obj.save()` da **ishlamaydi** |
| Xato turi | `IntegrityError` (dastur yiqiladi) | `ValidationError` (formada tushunarli xabar chiqadi) |

Shu sababli muhim qoidalar ikki joyda yozilgan, masalan `WorkHour` da `valid_workday` constraint'i ham, `clean()` ham bor. Constraint kafolat beradi, `clean()` esa foydalanuvchiga tushunarli xabar ko'rsatadi.

> DRF'ning `ModelSerializer` i ham modelning `clean()` metodini **chaqirmaydi**. Shu sababli API'da `ModelCleanMixin` yozilgan (18.5-bo'lim).

### 16.6. `clean()` validatsiyalari — jamlanma

| Model | Tekshiruv | Xabar |
| --- | --- | --- |
| ClinicSettings | `opens_at < closes_at` | Klinika ish tugashi boshlanishidan keyin bo'lsin. |
| Profile | Shifokorga bog'langan hisobning roli `doctor` | Hisob shifokorga bog'langan. Avval bog'lanishni tekshiring. |
| Profile | Bemorga bog'langan hisobning roli `patient` | Hisob bemorga bog'langan. Avval bog'lanishni tekshiring. |
| WorkHour | `start < end` | Tugash vaqti boshlanishdan keyin bo'lsin. |
| WorkHour | Tanaffusning ikkala vaqti kiritilgan yoki ikkalasi ham bo'sh | Tanaffusning ikkala vaqtini kiriting. |
| WorkHour | Tanaffus ish vaqti ichida | Tanaffus ish vaqti ichida bo'lsin. |
| logo, photo | `validate_photo` | 16.2-bo'limga qarang |

### 16.7. `ClinicSettings` — singleton usuli

**Singleton** — jadvalda faqat bitta yozuv bo'lishi. Bu 4 ta qatlamda ta'minlangan:

| Qatlam | Kod | Natija |
| --- | --- | --- |
| 1. `save()` | `self.pk = 1` | Har qanday saqlash 1-yozuvga tushadi. Ikkinchi marta saqlansa, yangi qator yaratilmaydi, mavjud yozuv **yangilanadi** |
| 2. `load()` | `filter(pk=1).first() or cls(pk=1)` | Sozlamalarni o'qishning yagona to'g'ri usuli. Yozuv bo'lmasa, standart qiymatli (bazaga saqlanmagan) obyekt qaytadi, shuning uchun kod hech qachon `None` olmaydi |
| 3. Constraint | `CheckConstraint(Q(id=1))` | `save()` chetlab o'tilsa ham (masalan, `bulk_create` yoki SQL orqali), baza `id != 1` ni qabul qilmaydi |
| 4. Admin | `has_add_permission`, `has_delete_permission` | Yozuv bo'lsa "Qo'shish" tugmasi yo'qoladi, o'chirish esa butunlay yopiq |

Ishlatish:

```python
from clinic.models import ClinicSettings

s = ClinicSettings.load()      # o'qish
s.default_duration = 20
s.save()                       # yangilash
```

> `ClinicSettings(name='X').save()` ham ishlaydi, lekin u 1-yozuvdagi **barcha** maydonlarni yangi obyektning standart qiymatlari bilan almashtirib yuboradi. `ClinicSettings.objects.create(...)` esa yozuv mavjud bo'lsa `IntegrityError` beradi. Shuning uchun har doim `load()` → o'zgartirish → `save()` tartibidan foydalaning.

2026-11-02 dagi tekshiruv natijasi: ikki marta saqlangandan keyin ham yozuvlar soni `1` bo'lib qoldi, qo'shish va o'chirish sahifalari `403` qaytardi. Sinov tranzaksiya ichida o'tkazilib, oxirida bekor qilindi, shuning uchun bazaga hech narsa yozilmadi.

### 16.8. `clinic/admin.py` — sozlamalar izohi

**Umumiy sozlamalar:**

| Sozlama | Vazifasi |
| --- | --- |
| `@admin.register(Model)` | Modelni admin panelga qo'shadi |
| `list_display` | Ro'yxat sahifasidagi ustunlar |
| `list_filter` | O'ng tomondagi filtr paneli (masalan, holat yoki shifokor bo'yicha) |
| `search_fields` | Qidiruv maydoni. `doctor__name` dagi qo'sh pastki chiziq bog'langan modelning maydonini bildiradi |
| `list_select_related` | Ro'yxatdagi FK'larni bitta SQL so'rovda oladi. Usiz har bir qator uchun alohida so'rov ketadi (N+1 muammosi) |
| `autocomplete_fields` | FK/OneToOne uchun oddiy ochiluvchi ro'yxat o'rniga qidiruvli maydon. Buning uchun bog'langan model admin'ida `search_fields` bo'lishi shart |
| `readonly_fields` | Maydon ko'rsatiladi, lekin tahrirlanmaydi. `editable=False` maydonlarni formada ko'rsatishning yagona usuli shu |
| `date_hierarchy` | Ro'yxat ustida yil → oy → kun bo'yicha navigatsiya |
| `list_editable` | Ro'yxatning o'zida tahrirlash (Doctor'da `active` belgisi) |
| `inlines` | Bog'langan yozuvlarni asosiy sahifaning ichida tahrirlash |

**Model bo'yicha:**

| Admin | Xususiyati |
| --- | --- |
| `ClinicSettingsAdmin` | `has_add_permission` faqat yozuv bo'lmaganda `True` qaytaradi. `has_delete_permission` doim `False`. `created_at` va `updated_at` faqat o'qish uchun |
| `ProfileAdmin` | `role` bo'yicha filtr. User'ning username, ismi va emaili bo'yicha qidiruv |
| `DepartmentAdmin`, `SpecialtyAdmin` | Nomi bo'yicha qidiruv (Room va Doctor'dagi autocomplete uchun ham kerak) |
| `RoomAdmin` | Bo'lim va qavat bo'yicha filtr |
| `DoctorAdmin` | `inlines = [WorkHourInline, DayOffInline]`: ish jadvali va ta'tillar shifokor sahifasida jadval ko'rinishida (`TabularInline`) chiqadi. `extra = 0` ortiqcha bo'sh qatorlarni yashiradi, yangi qator "Add another" tugmasi bilan qo'shiladi. Faollik, mutaxassislik va bo'lim bo'yicha filtr |
| `WorkHourAdmin`, `DayOffAdmin` | Barcha shifokorlarning jadvalini bir joyda ko'rish uchun alohida ro'yxatlar. DayOff'da `date_hierarchy = 'date'` |
| `PatientAdmin` | `archived` bo'yicha filtr. Ism va telefon bo'yicha qidiruv |
| `AppointmentAdmin` | `date_hierarchy = 'start'`. Holat, shifokor va mutaxassislik bo'yicha filtr. Bemor ismi va telefoni, shifokor, murojaat sababi bo'yicha qidiruv. Vaqt, navbat va token maydonlari `readonly_fields` da. `save_model()`: `created_by` bo'sh bo'lsa, admin panelga kirgan foydalanuvchi avtomatik yoziladi |
| `HistoryAdminMixin` | `has_change_permission` va `has_delete_permission` `False` qaytaradi. Tarixni qo'lda o'zgartirib bo'lmaydi, faqat ko'rish mumkin. API hali yo'qligi uchun qo'shishga hozircha ruxsat bor |
| `AppointmentStatusEventAdmin`, `DirectionEventAdmin`, `AuditAdmin` | `HistoryAdminMixin` dan foydalanadi, vaqt bo'yicha `date_hierarchy` bor |
| `AppointmentHistoryAdmin` | `AuditAdmin` dan meros oladi. `get_queryset()` faqat `appointment` maydoni bo'sh bo'lmagan yozuvlarni qaytaradi |
| `LoginAttemptAdmin` | Kalit bo'yicha qidiruv, eng yangi yozuv birinchi |

Tekshiruv natijasi: 15 ta modelning ro'yxat va qo'shish sahifalari `200` qaytardi.

### 16.9. Ma'lumot kiritish tartibi

Admin panelda (`/admin/`) ma'lumotni quyidagi tartibda kiriting. Har bir qadam oldingisiga bog'liq (majburiy FK'lar sababli):

| № | Bo'lim | Nima uchun shu tartibda |
| --- | --- | --- |
| 1 | **Klinika sozlamalari** | Shifokorning standart qabul vaqti (`default_duration`) shu yerdan olinadi |
| 2 | **Bo'limlar** | Xona bo'limsiz yaratilmaydi |
| 3 | **Xonalar va qavatlar** | Shifokorning `location` maydoni uchun kerak |
| 4 | **Mutaxassisliklar** | Shifokor mutaxassisliksiz yaratilmaydi |
| 5 | **Shifokorlar** | Shu sahifaning pastki qismida haftalik ish jadvali va ta'tillarni ham qo'shing |
| 6 | **Bemorlar** | Qabul uchun kerak |
| 7 | **Qabullar** | Shifokor va bemor tanlanadi, `created_by` avtomatik yoziladi |

Ixtiyoriy: shifokor yoki bemor tizimga kirishi kerak bo'lsa, avval **Users** bo'limida hisob yarating, uni `Doctor.user` yoki `Patient.user` ga bog'lang va **Hisob profillari** bo'limida mos rolni bering.

---

## 17. 2026-11-02: bajarilgan ishlar va git muammosi

### 17.1. Bajarilgan ishlar

```cmd
python manage.py startapp clinic
python manage.py check
python manage.py makemigrations clinic
python manage.py migrate
python manage.py check
pip freeze > requirements.txt
```

| № | Ish | Natija |
| --- | --- | --- |
| 1 | `clinic` app yaratildi va `INSTALLED_APPS` ga qo'shildi | |
| 2 | `MEDIA_URL`, `MEDIA_ROOT` va `urls.py` ga `static(...)` qo'shildi | |
| 3 | `.gitignore` yaratildi (`media/` bilan) | Avval bu fayl umuman yo'q edi |
| 4 | `clinic/models.py` yozildi | `check` natijasi `no issues`: kod tuzatishsiz o'tdi |
| 5 | `clinic/admin.py` yozildi | 15 ta admin sahifa ishlaydi |
| 6 | `makemigrations clinic` | `clinic\migrations\0001_initial.py`: 15 ta model, 2 ta index, 7 ta constraint |
| 7 | `migrate` | `Applying clinic.0001_initial... OK` |
| 8 | `requirements.txt` yangilandi | O'zgarish yo'q: yangi paket o'rnatilmagan, Pillow avvaldan bor edi |
| 9 | Git repozitoriyasi to'g'ri joyga ko'chirildi | 17.2-bo'limga qarang |
| 10 | Clinic API: serializer, view, URL (18-bo'lim) | Fayllarda oldindan yozilgan qoralama kod bor edi. U ko'rib chiqilib, 5 ta kamchiligi tuzatildi (18.7) |
| 11 | API test client bilan tekshirildi | 32 / 32 o'tdi, test ma'lumotlari rollback qilindi |
| 12 | `SPECTACULAR_SETTINGS` qo'shildi | Swagger'dagi enum ogohlantirishi yo'qoldi |
| 13 | `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` → `.env` (19-bo'lim) | `.env.example` yaratildi, `.env` git'ga kirmaydi |
| 14 | `LANGUAGE_CODE = 'uz'`, `TIME_ZONE = 'Asia/Tashkent'` | `check`: `no issues` |
| 15 | Birinchi git commit | Push qilinmadi (remote yo'q) |

> `makemigrations` chiqishida `single_clinic_settings` va `one_dayoff` alohida qator bo'lib ko'rinmaydi. Sababi shuki, ular `CreateModel` operatsiyasining ichiga (`options={'constraints': [...]}`) yozilgan. Migratsiya faylida ikkalasi ham bor.

### 17.2. Git muammosi va yechimi

**Muammo:** git repozitoriyasi loyiha papkasida emas, butun foydalanuvchi papkasida (`C:\Users\user`) ochilgan edi. Shu sababli `git status` loyihadan tashqari `.ssh/`, `NTUSER.DAT`, `AppData/`, `Downloads/` kabi papkalarni ham ko'rsatardi.

**Nega xavfli:** `git add .` va `git push` qilinsa, SSH kalitlari, brauzer ma'lumotlari va shaxsiy fayllar GitHub'ga ketib qolishi mumkin edi. Bundan tashqari, foydalanuvchi papkasidagi istalgan boshqa loyiha ham shu bitta repozitoriyaning qismi bo'lib qolardi.

**Sababi:** qachondir `git init` buyrug'i `C:\Users\user` papkasida (CMD ochilgandagi standart papka) ishga tushirilgan.

**Tekshiruv:**

```cmd
git -C C:\Users\user log --oneline -5
```

```
fatal: your current branch 'master' does not have any commits yet
```

`git -C <papka>` buyruqni o'sha papkaga `cd` qilmasdan bajaradi. Qo'shimcha tekshiruvda commitlar soni `0` chiqdi, branch, stash va remote yo'q edi, staged fayllar ham `0` ta edi. Ya'ni repozitoriya bo'sh edi va uni o'chirganda hech narsa yo'qolmasdi.

**Yechim (ruxsat olingandan keyin):**

```cmd
rmdir /s /q C:\Users\user\.git
cd C:\Users\user\Desktop\Rest
git init
git add .
git status
```

| Buyruq | Vazifasi |
| --- | --- |
| `rmdir /s /q C:\Users\user\.git` | Faqat yashirin `.git` papkasini o'chiradi. Foydalanuvchi fayllari o'zgarmaydi, chunki `.git` faqat git'ning xizmat ma'lumotlarini saqlaydi |
| `git init` | `Rest` ichida yangi, toza repozitoriya ochadi |
| `git add .` | Fayllarni commit'ga tayyorlaydi, `.gitignore` dagi fayllar bundan mustasno |
| `git status` | Nima tayyorlanganini ko'rsatadi |

**Natija:** 27 ta fayl tayyorlandi. `env/`, `db.sqlite3`, `.env`, `__pycache__/` va `media/` ro'yxatga kirmadi. Commit hali qilinmagan.

> **Hal qilindi:** `SECRET_KEY` dastlab `settings.py` da edi va staged holatda turardi. Commit qilishdan oldin u `.env` ga ko'chirildi, shuning uchun git tarixiga kirmadi (19-bo'lim).

### 17.3. Keyingi qadamlar

- `Appointment.source_visit` maydoni va `clinical_models.py` (`VisitCard` va boshqalar) ni qo'shish.
- Qabul validatsiyasiga ish vaqti (`WorkHour`), `DayOff`, bemordagi vaqt to'qnashuvi va arxivlangan bemor tekshiruvlarini qo'shish.
- `Profile.role` asosida ruxsatlar: bemor faqat o'z ma'lumotini ko'rsin.
- `ProtectedError` uchun 500 o'rniga tushunarli javob qaytarish.
- `api/tests.py` ga avtomatik testlar yozish (hozirgi tekshiruv qo'lda ishga tushiriladigan skript).
- GitHub'da repozitoriya ochib, `git remote add origin ...` va `git push`.
- `AppointmentStatusEvent` va `LoginAttempt` ga `verbose_name` qo'shish, shunda admin panelda ularning nomi o'zbekcha chiqadi.

---

## 18. Clinic API

Modellar `clinic/models.py` da turadi. API kodi esa `api` app'ida, `Book` bilan bir joyda joylashgan:

| Fayl | Ichida nima bor |
| --- | --- |
| `api/serializers.py` | `BookSerializer`, `ModelCleanMixin` va har bir clinic modeli uchun serializer |
| `api/views.py` | `IsStaffOrReadOnly`, `BookViewSet`, `ClinicSettingsView` va clinic ViewSet'lari |
| `api/urls.py` | `DefaultRouter` (12 ta resurs) va `clinic-settings/` yo'li |

`api/models.py` o'zgarmagan, unda faqat `Book` bor.

### 18.1. Endpointlar va ruxsatlar

Barcha manzillar `/api/` bilan boshlanadi. Router har bir resurs uchun 2 ta manzil yaratadi: `/api/doctors/` (ro'yxat) va `/api/doctors/{id}/` (bitta yozuv).

| URL | Metodlar | Kim o'qiydi | Kim yozadi | Ruxsat klassi |
| --- | --- | --- | --- | --- |
| `books/` | GET, POST, PUT, PATCH, DELETE | Hamma | Login qilganlar | `IsAuthenticatedOrReadOnly` (global sozlama) |
| `clinic-settings/` | GET, PUT, PATCH | Hamma | Xodim (`is_staff`) | `IsStaffOrReadOnly` |
| `departments/` | GET, POST, PUT, PATCH, DELETE | Hamma | Xodim | `IsStaffOrReadOnly` |
| `rooms/` | GET, POST, PUT, PATCH, DELETE | Hamma | Xodim | `IsStaffOrReadOnly` |
| `specialties/` | GET, POST, PUT, PATCH, DELETE | Hamma | Xodim | `IsStaffOrReadOnly` |
| `doctors/` | GET, POST, PUT, PATCH, DELETE | Hamma | Xodim | `IsStaffOrReadOnly` |
| `work-hours/` | GET, POST, PUT, PATCH, DELETE | Hamma | Xodim | `IsStaffOrReadOnly` |
| `days-off/` | GET, POST, PUT, PATCH, DELETE | Hamma | Xodim | `IsStaffOrReadOnly` |
| `patients/` | GET, POST, PUT, PATCH, DELETE | Login qilganlar | Login qilganlar | `IsAuthenticated` |
| `appointments/` | GET, POST, PUT, PATCH, DELETE | Login qilganlar | Login qilganlar | `IsAuthenticated` |
| `status-events/` | faqat GET | Login qilganlar | — (405) | `IsAuthenticated` + `ReadOnlyModelViewSet` |
| `directions/` | faqat GET | Login qilganlar | — (405) | `IsAuthenticated` + `ReadOnlyModelViewSet` |
| `audit/` | faqat GET | Xodim (`is_staff`) | — (405) | `IsAdminUser` |

- **Nega shifokorlar ochiq, bemorlar yopiq:** shifokorlar ro'yxati, bo'limlar va ish jadvali saytda hammaga ko'rsatiladigan ma'lumot. Bemorlar va qabullar esa **shaxsiy tibbiy ma'lumot**, ularni anonim foydalanuvchi o'qiy olmaydi (401).
- `clinic-settings/` router'da emas, oddiy `path()` orqali ulangan. Sababi: u bitta obyekt, ro'yxati va `{id}` si yo'q. `ClinicSettings` uchun `POST` va `DELETE` yo'q (`RetrieveUpdateAPIView`).
- `IsAdminUser` nomiga qaramay, superuser'ni emas, `is_staff = True` ni tekshiradi.
- `DELETE` qilinganda `PROTECT` bog'lanish bo'lsa (masalan, qabullari bor shifokor), Django `ProtectedError` beradi. Hozircha bu 500 bo'lib qaytadi (18.6-bo'limga qarang). Shifokorni `active=false`, bemorni `archived=true` qilish kerak.

> 401 va 403 farqi: **401 Unauthorized** — "siz kimsiz?", ya'ni login qilinmagan. **403 Forbidden** — "siz kimligingizni bilaman, lekin ruxsat yo'q", masalan oddiy foydalanuvchi bo'lim qo'shmoqchi bo'lsa.

### 18.2. Filtrlash, qidiruv va saralash

| URL | `?field=` (aniq filtr) | `?search=` | `?ordering=` |
| --- | --- | --- | --- |
| `departments/` | — | `name` | `name`, `created_at` |
| `rooms/` | `department`, `floor` | `number`, `floor`, bo'lim nomi | `department__name`, `floor`, `number` |
| `specialties/` | — | `name` | `name`, `created_at` |
| `doctors/` | `specialty`, `active`, `location` | `name`, `phone`, mutaxassislik nomi | `name`, `experience`, `duration` |
| `work-hours/` | `doctor`, `weekday` | — | `doctor__name`, `weekday`, `start` |
| `days-off/` | `doctor`, `date` | shifokor ismi, `reason` | `date` |
| `patients/` | `archived` | `name`, `phone` | `name`, `birth_date`, `created_at` |
| `appointments/` | `doctor`, `patient`, `status` | bemor ismi/telefoni, shifokor ismi, `reason` | `start`, `end`, `status`, `queue_number`, `created_at` |
| `status-events/` | `appointment`, `status`, `actor` | — | `changed_at` |
| `directions/` | `appointment`, `stage`, `actor` | `destination`, `reason` | `created_at` |
| `audit/` | `action`, `actor`, `appointment` | `action`, `detail` | `created_at` |

Misollar: `/api/doctors/?active=true&specialty=2`, `/api/appointments/?doctor=1&status=scheduled&ordering=start`, `/api/patients/?search=+99890`.

**Tezlik uchun:** `select_related` (FK, bitta JOIN so'rov) va `prefetch_related` (teskari bog'lanish, alohida bitta so'rov) ishlatilgan. Masalan, `doctors/` ro'yxati har shifokor uchun alohida so'rov yubormaydi: mutaxassislik, xona va bo'lim JOIN orqali, `hours` va `days_off` esa 2 ta qo'shimcha so'rov bilan keladi.

### 18.3. Serializer'lardagi qo'shimcha maydonlar

Bu maydonlar faqat o'qish uchun (`read_only`). Frontend ID o'rniga tayyor nomni ko'rsatishi uchun qo'shilgan:

| Serializer | Maydon | Manbasi |
| --- | --- | --- |
| Room | `department_name` | `department.name` |
| WorkHour | `weekday_name` | `get_weekday_display()` → `Dushanba` |
| Doctor | `specialty_name` | `specialty.name` |
| Doctor | `initials` | modeldagi `initials` property → `AV` |
| Doctor | `hours`, `days_off` | ichma-ich (nested) `WorkHourSerializer` va `DayOffSerializer` ro'yxatlari |
| Appointment | `doctor_name`, `patient_name` | `doctor.name`, `patient.name` |
| Appointment | `status_name` | `get_status_display()` → `Belgilangan` |
| Profile | `role_name` | `get_role_display()` |
| AppointmentStatusEvent | `status_name` | `get_status_display()` |
| DirectionEvent | `stage_name` | `get_stage_display()` |

`source='...'` — maydon qiymati qayerdan olinishini bildiradi. Nuqta bog'langan obyektga o'tishni bildiradi (`department.name`). Metod nomi berilsa, DRF uni o'zi chaqiradi.

`ProfileSerializer` va `LoginAttemptSerializer` ham yozilgan, lekin ular uchun endpoint ochilmagan (`LoginAttempt` ichki xavfsizlik modeli). `AppointmentHistory` proxy modeli `Audit` jadvalidan foydalangani uchun `AuditSerializer` bilan ishlaydi.

### 18.4. Validatsiyalar

| Joy | Tekshiruv | Javob (400) |
| --- | --- | --- |
| `AppointmentSerializer` | `end > start` | `{"end": ["Tugash vaqti boshlanishdan keyin bo‘lsin."]}` |
| `AppointmentSerializer` | Shifokor faol bo'lsin (yangi qabulda yoki shifokor almashtirilganda) | `{"doctor": ["Bu shifokor hozir faol emas."]}` |
| `AppointmentSerializer` | Shu shifokorda vaqt to'qnashuvi yo'q | `{"non_field_errors": ["Shifokorda bu vaqtda boshqa qabul bor."]}` |
| `DoctorSerializer` | `5 <= duration <= 240` | `{"duration": ["Qabul davomiyligi 5 dan 240 daqiqagacha bo‘lsin."]}` |
| `ClinicSettingsSerializer` | `ModelCleanMixin` → `opens_at < closes_at` | `{"non_field_errors": ["Klinika ish tugashi boshlanishidan keyin bo‘lsin."]}` |
| `WorkHourSerializer` | `ModelCleanMixin` → 16.6-bo'limdagi 3 ta qoida | `{"non_field_errors": ["Tanaffus ish vaqti ichida bo‘lsin."]}` |
| `ProfileSerializer` | `ModelCleanMixin` → rol va bog'lanish mosligi | |
| Model validator'lari | `MinValueValidator`, `MaxValueValidator`, `validate_photo` | DRF ularni modeldan o'zi oladi |
| `unique` va `UniqueConstraint` | `Department.name`, `one_workday`, `one_dayoff`, `unique_room_location` | DRF ularni ham modeldan o'zi oladi |

**Vaqt to'qnashuvi qanday tekshiriladi:** ikki oraliq `[A_start, A_end)` va `[B_start, B_end)` faqat `A_start < B_end` **va** `A_end > B_start` bo'lganda kesishadi:

```python
Appointment.objects.filter(doctor=doctor, start__lt=end, end__gt=start)
    .exclude(status__in=['cancelled', 'missed'])   # bekor qilingan/kelmagan qabul vaqtni band qilmaydi
    .exclude(pk=self.instance.pk)                  # faqat update paytida: o'zi bilan solishtirilmaydi
```

- 09:00–09:30 va 09:30–10:00 qabullari to'qnashmaydi, chunki chegaraviy vaqt qat'iy taqqoslanadi (`<`, `>`).
- Qabul `cancelled` yoki `missed` holatiga o'tkazilayotgan bo'lsa, to'qnashuv tekshirilmaydi: bekor qilishni hech narsa to'smasligi kerak.
- Bekor qilingan qabulni qayta faollashtirish (masalan, `completed` ga o'tkazish) to'qnashuvni yana tekshiradi. Bu vaqtga boshqa qabul yozilgan bo'lsa, 400 qaytadi.
- **Nega faollik har update'da tekshirilmaydi:** shifokor ishdan ketib `active=false` qilinsa ham, uning bugungi qabullarini yakunlash yoki bekor qilish mumkin bo'lishi kerak.

`created_by` maydoni `read_only`, uni klient yubora olmaydi. U `AppointmentViewSet.perform_create()` da qo'yiladi:

```python
def perform_create(self, serializer):
    serializer.save(created_by=self.request.user)
```

### 18.5. `ModelCleanMixin` va `IsStaffOrReadOnly` qanday ishlaydi

#### `ModelCleanMixin`

**Muammo:** modeldagi `clean()` faqat Django formalarida (admin) avtomatik chaqiriladi. DRF serializer'i uni **chaqirmaydi**, shuning uchun mixin'siz API orqali tanaffusi ish vaqtidan tashqarida bo'lgan jadvalni saqlash mumkin bo'lardi.

```python
class ModelCleanMixin:
    def validate(self, attrs):
        attrs = super().validate(attrs)
        instance = copy.copy(self.instance) if self.instance else self.Meta.model()
        for key, value in attrs.items():
            setattr(instance, key, value)
        try:
            instance.clean()
        except DjangoValidationError as e:
            if hasattr(e, 'error_dict'):
                raise serializers.ValidationError(e.message_dict)
            raise serializers.ValidationError({'non_field_errors': e.messages})
        return attrs
```

| Qadam | Izoh |
| --- | --- |
| `super().validate(attrs)` | Avval DRF'ning oddiy tekshiruvlari ishlaydi |
| `copy.copy(self.instance)` | Update (PUT/PATCH) paytida mavjud obyektning **nusxasi** olinadi. Nusxa bo'lmasa, validatsiya xato bersa ham asl obyekt xotirada o'zgarib qolardi |
| `self.Meta.model()` | Create (POST) paytida bo'sh yangi obyekt yaratiladi |
| `setattr(...)` | Kelgan qiymatlar obyektga yoziladi. PATCH da kelmagan maydonlar eski qiymatida qoladi |
| `instance.clean()` | Modelning o'z validatsiyasi chaqiriladi, kod takrorlanmaydi |
| `DjangoValidationError` → `serializers.ValidationError` | Django xatosini DRF tushunadigan xatoga aylantiradi, natijada klient 500 emas, **400** va xabar oladi |
| `message_dict` / `non_field_errors` | Xato maydonga bog'langan bo'lsa, `{"maydon": [...]}`, aks holda `{"non_field_errors": [...]}` qaytadi |

Ishlatilgan joylari: `ClinicSettingsSerializer`, `WorkHourSerializer`, `ProfileSerializer`. Mixin `ModelSerializer` dan **oldin** yoziladi (`class X(ModelCleanMixin, serializers.ModelSerializer)`), shunda `validate()` avval mixin'da ishlaydi, `super()` esa DRF'nikini chaqiradi.

#### `IsStaffOrReadOnly`

```python
class IsStaffOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)
```

- `SAFE_METHODS` = `GET`, `HEAD`, `OPTIONS`. Bu metodlar ma'lumotni o'zgartirmaydi, shuning uchun hammaga ruxsat beriladi.
- `POST`, `PUT`, `PATCH`, `DELETE` faqat `is_staff = True` bo'lgan foydalanuvchiga ruxsat etiladi. Admin panelda bu **Staff status** belgisi.
- Anonim foydalanuvchi uchun `request.user` — `AnonymousUser`, uning `is_staff` qiymati `False`.
- DRF'dagi tayyor `IsAdminUser` o'qishni ham yopadi, `IsAuthenticatedOrReadOnly` esa yozishni har qanday login qilgan foydalanuvchiga ochadi. Bizga ularning o'rtasidagi variant kerak edi.

### 18.6. Misol so'rov va javoblar

**Qabul yaratish** — `POST /api/appointments/`, sarlavhada `Authorization: Bearer <access_token>`:

```json
{
	"doctor": 1,
	"patient": 1,
	"start": "2026-11-10T09:00:00+05:00",
	"end": "2026-11-10T09:30:00+05:00",
	"reason": "Bosh og'rig'i"
}
```

Javob `201 Created`:

```json
{
	"id": 1,
	"doctor_name": "Ali Valiyev",
	"patient_name": "Vali Aliyev",
	"status_name": "Belgilangan",
	"start": "2026-11-10T09:00:00+05:00",
	"end": "2026-11-10T09:30:00+05:00",
	"status": "scheduled",
	"arrived_at": null,
	"started_at": null,
	"completed_at": null,
	"status_changed_at": null,
	"queue_number": null,
	"queue_priority": 0,
	"called_at": null,
	"reason": "Bosh og'rig'i",
	"note": "",
	"token": "31b399dc-403f-49c2-ab6e-a0b7d3476213",
	"created_at": "2026-11-02T09:05:40.982644+05:00",
	"updated_at": "2026-11-02T09:05:40.982650+05:00",
	"doctor": 1,
	"patient": 1,
	"created_by": 1
}
```

Vaqtlar `+05:00` (Toshkent) bilan qaytadi, chunki `TIME_ZONE = 'Asia/Tashkent'`. Bazada esa ular UTC'da saqlanadi (`USE_TZ = True`).

**Xuddi shu shifokorga 09:15–09:45** — `400 Bad Request`:

```json
{ "non_field_errors": ["Shifokorda bu vaqtda boshqa qabul bor."] }
```

**Shifokor** — `GET /api/doctors/1/` (login shart emas):

```json
{
	"id": 1,
	"specialty_name": "Terapevt",
	"initials": "AV",
	"hours": [
		{
			"id": 1,
			"weekday_name": "Dushanba",
			"weekday": 0,
			"start": "09:00:00",
			"end": "17:00:00",
			"break_start": "13:00:00",
			"break_end": "14:00:00",
			"doctor": 1,
			"created_at": "2026-11-02T09:05:40.977984+05:00",
			"updated_at": "2026-11-02T09:05:40.978085+05:00"
		}
	],
	"days_off": [],
	"name": "Ali Valiyev",
	"phone": "+998901112233",
	"bio": "",
	"experience": 5,
	"room": "105",
	"duration": 30,
	"active": true,
	"photo": null,
	"user": null,
	"specialty": 1,
	"location": null,
	"created_at": "2026-11-02T09:05:40.974074+05:00",
	"updated_at": "2026-11-02T09:05:40.974951+05:00"
}
```

**Klinika sozlamalari** — `GET /api/clinic-settings/`. Yozuv hali saqlanmagan bo'lsa ham `ClinicSettings.load()` standart qiymatlarni qaytaradi (`updated_at: null` shundan dalolat beradi):

```json
{
	"created_at": "2026-11-02T09:05:40.992727+05:00",
	"updated_at": null,
	"document_max_mb": 10,
	"offer_minutes": 15,
	"name": "Medora Clinic",
	"logo": null,
	"phone": "",
	"address": "",
	"opens_at": "08:00:00",
	"closes_at": "18:00:00",
	"default_duration": 30,
	"booking_days": 90,
	"cancellation_hours": 0
}
```

`PATCH /api/clinic-settings/` (`{"default_duration": 20}`) faqat xodimga ruxsat etiladi va har doim `id=1` yozuvni yangilaydi yoki yaratadi.

**Login qilmasdan bemorlar** — `GET /api/patients/` → `401`:

```json
{ "detail": "Authentication credentials were not provided." }
```

> DRF'ning maydon xabarlari `LANGUAGE_CODE = 'uz'` tufayli o'zbekcha chiqadi (`Ushbu maydon to'ldirilishi shart.`). Ammo autentifikatsiya kabi ba'zi xabarlar inglizcha qoladi, chunki DRF'ning o'zbekcha tarjimasi to'liq emas.

### 18.7. Tekshiruv natijalari (2026-11-02)

Sinov `manage.py shell` ichida DRF `APIClient` bilan o'tkazildi. Barcha ma'lumotlar `transaction.atomic()` ichida yaratilib, oxirida `set_rollback(True)` bilan bekor qilindi, shuning uchun baza o'zgarmadi. Natija: **32 / 32 o'tdi**.

| Tekshiruv | Kutilgan | Natija |
| --- | --- | --- |
| Anonim `GET /api/doctors/` | 200 | 200 |
| Anonim `POST /api/doctors/` | 401/403 | 401 |
| Anonim `GET /api/patients/` | 401/403 | 401 |
| Admin `GET /api/patients/` | 200 | 200 |
| Qabul 09:00–09:30 | 201 | 201, `created_by` = admin |
| To'qnashgan qabul 09:15–09:45 | 400 | 400 |
| Qo'shni qabul 09:30–10:00 | 201 | 201 |
| Qabulni o'zini PATCH qilish | 200 | 200 |
| `end <= start` | 400 | 400 |
| Bekor qilingan vaqtga yangi qabul | 201 | 201 |
| Faol bo'lmagan shifokorga qabul | 400 | 400 |
| Faol bo'lmagan shifokorning eski qabulini yakunlash | 200 | 200 |
| `duration = 300` | 400 | 400 |
| WorkHour: tanaffus ish vaqtidan tashqarida | 400 | 400 |
| ClinicSettings: `opens_at` > `closes_at` | 400 | 400 |
| ClinicSettings PATCH, so'ng yozuvlar soni | 200, 1 | 200, 1 |
| Anonim `GET /api/clinic-settings/` | 200 | 200 |
| Oddiy user `POST /api/departments/` | 403 | 403 |
| Oddiy user / admin `GET /api/audit/` | 403 / 200 | 403 / 200 |
| `POST /api/status-events/` | 405 | 405 |
| `GET /api/docs/`, `GET /api/schema/` | 200 | 200 |

**Sinov paytida topilib, tuzatilgan muammolar:**

| Muammo | Sababi | Yechim |
| --- | --- | --- |
| `duration=300` yuborilsa, 500 xato bo'lishi mumkin edi | DRF modeldagi `CheckConstraint` ni bilmaydi, xato bazaning o'zida chiqadi | `DoctorSerializer.validate_duration()` qo'shildi |
| Faolsizlantirilgan shifokorning qabulini yakunlab bo'lmasdi | Faollik har update'da tekshirilardi | Faollik faqat yangi qabulda yoki shifokor almashtirilganda tekshiriladi |
| `Warning: encountered multiple names for the same choice set (PreviousStatusEnum)` | `status` va `previous_status` bir xil choices'dan foydalanadi, drf-spectacular esa ularga ikki xil enum nomi beryapti | `settings.py` ga `SPECTACULAR_SETTINGS['ENUM_NAME_OVERRIDES']` qo'shildi |
| `UnorderedObjectListWarning: ... Book QuerySet` | Tartiblanmagan querysetni sahifalash bir xil yozuvni ikki sahifada ko'rsatishi mumkin | `Book.objects.order_by('id')` |
| `ModelCleanMixin` asl obyektni o'zgartirardi | `setattr` to'g'ridan-to'g'ri `self.instance` ga yozilardi | `copy.copy()` nusxasi ustida tekshiriladi |

**Hali tekshirilmaydigan narsalar** (keyingi bosqich):
- Qabul shifokorning ish vaqtiga (`WorkHour`) va ta'tilga (`DayOff`) to'g'ri kelishi.
- Bemorning o'zida ham vaqt to'qnashuvi bo'lmasligi.
- Arxivlangan bemorga qabul yozish.
- Bir vaqtda kelgan ikki so'rovdagi poyga holati (race condition): ikkalasi ham tekshiruvdan o'tib ketishi mumkin. Buni PostgreSQL'da `select_for_update()` yoki `ExclusionConstraint` bilan hal qilish mumkin.
- Rollar bo'yicha cheklov: hozir login qilgan **har qanday** foydalanuvchi (masalan, bemor roli bilan ham) barcha bemorlarni ko'ra oladi. `Profile.role` asosida ruxsat yozish kerak.
- `PROTECT` sababli o'chirish rad etilsa, 500 o'rniga tushunarli 400/409 javob qaytarish.

---

## 19. `.env` sozlamalari

Maxfiy va muhitga bog'liq sozlamalar kod ichida emas, loyiha papkasidagi `.env` faylida saqlanadi. Bu faylni `python-dotenv` paketi o'qiydi.

### 19.1. Fayllar

| Fayl | Git'ga yuklanadimi | Vazifasi |
| --- | --- | --- |
| `.env` | **Yo'q** (`.gitignore` da bor) | Haqiqiy qiymatlar, masalan sizning `SECRET_KEY` ingiz |
| `.env.example` | Ha | Namuna: qaysi o'zgaruvchilar kerakligini ko'rsatadi, haqiqiy kalit yo'q |

`.env` tarkibi:

```ini
SECRET_KEY='django-insecure-...'
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
```

| O'zgaruvchi | Nima uchun | Ishlab chiqishda | Serverda |
| --- | --- | --- | --- |
| `SECRET_KEY` | Sessiyalar, parolni tiklash havolalari, CSRF va imzolangan ma'lumotlar shu kalit bilan himoyalanadi. Kalitni bilgan odam sessiyani soxtalashtira oladi | Istalgan uzun qator | Yangi, tasodifiy, faqat shu serverga tegishli kalit |
| `DEBUG` | `True` bo'lsa, xato sahifasida kod, sozlamalar va so'rov ma'lumotlari ko'rinadi. Media fayllarni ham Django o'zi beradi | `True` | **Albatta `False`** |
| `ALLOWED_HOSTS` | Django javob beradigan domenlar. Boshqa `Host` sarlavhali so'rovlar 400 bilan rad etiladi (Host header hujumidan himoya) | `127.0.0.1,localhost` | `medora.uz,www.medora.uz` |

### 19.2. `settings.py` dagi kod

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

| Qator | Izoh |
| --- | --- |
| `load_dotenv(BASE_DIR / '.env')` | `.env` dagi qatorlarni muhit o'zgaruvchilariga (`os.environ`) yuklaydi. Yo'l `BASE_DIR` bo'yicha beriladi, shuning uchun `manage.py` qaysi papkadan ishga tushirilishidan qat'i nazar fayl topiladi. Kompyuterda shu nomli o'zgaruvchi avvaldan bo'lsa, u ustun turadi |
| `os.getenv('SECRET_KEY')` | O'zgaruvchini o'qiydi. Topilmasa, `None` qaytaradi |
| `ImproperlyConfigured` | `.env` unutilsa, Django noaniq xato bilan emas, tushunarli xabar bilan to'xtaydi |
| `DEBUG = ... in ('1', 'true', 'yes', 'on')` | `.env` dagi hamma qiymat **matn**. `bool('False')` Python'da `True` bo'ladi (bo'sh bo'lmagan har qanday matn `True`), shuning uchun matn aniq qiymatlar bilan solishtiriladi. `.lower()` `True`/`true`/`TRUE` farqini yo'qotadi. O'zgaruvchi yozilmagan bo'lsa, `False` bo'ladi: xatolik bo'lsa, xavfsiz tomonga og'adi |
| `ALLOWED_HOSTS = [...]` | `"127.0.0.1, localhost"` → `['127.0.0.1', 'localhost']`. `strip()` probellarni olib tashlaydi, `if h.strip()` esa bo'sh elementlarni (`"a,,b"` yoki bo'sh qator) tashlab ketadi |

`DEBUG` o'girish tekshirildi: `True`, `true`, `1`, `yes` → `True`. `False`, `false`, `0` va bo'sh qator → `False`.

**Nega `SECRET_KEY` qo'shtirnoqda:** kalitda `#`, `$`, `(`, `)` belgilari bor. Qo'shtirnoqsiz yozilganda python-dotenv probeldan keyingi `#` ni izoh, `${...}` ni esa boshqa o'zgaruvchiga havola deb tushunishi mumkin. Bitta qo'shtirnoq ichida hech narsa o'zgartirilmaydi. Tekshiruv: `.env` dan o'qilgan kalit eskisi bilan aynan bir xil chiqdi.

### 19.3. Til va vaqt zonasi

```python
LANGUAGE_CODE = 'uz'
TIME_ZONE = 'Asia/Tashkent'
```

| Sozlama | Ta'siri |
| --- | --- |
| `LANGUAGE_CODE = 'uz'` | Admin panel va DRF xabarlari o'zbekcha chiqadi (Django'da tarjimasi bor qismlari) |
| `TIME_ZONE = 'Asia/Tashkent'` | Admin panel va API vaqtni Toshkent vaqtida (`+05:00`) ko'rsatadi. `USE_TZ = True` bo'lgani uchun bazada vaqt baribir UTC'da saqlanadi, faqat ko'rsatish va kiritish Toshkent vaqtida bo'ladi. Windows'da vaqt zonalari bazasini `tzdata` paketi beradi, u allaqachon o'rnatilgan |

### 19.4. `.env.example` dan foydalanish

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
