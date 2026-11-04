from datetime import time
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from restaurant.models import Category, MenuItem, Profile, RestaurantSettings, Table

TEST_PASSWORD = 'Restoran2026!'

MENU = {
    'Milliy taomlar': [
        ('Osh', 'Toshkent oshi: guruch, qo‘y go‘shti, sabzi', '45000', 30, False, False),
        ('Lag‘mon', 'Qo‘lda cho‘zilgan xamir, go‘sht va sabzavot', '38000', 25, False, True),
        ('Manti', 'Bug‘da pishirilgan, go‘sht va piyozli (5 dona)', '35000', 40, False, False),
        ('Shashlik', 'Ko‘mirda pishirilgan qo‘y go‘shti (1 six)', '22000', 20, False, False),
    ],
    'Salatlar': [
        ('Achchiq-chuchuk', 'Pomidor, piyoz va achchiq qalampir', '15000', 5, True, True),
        ('Toshkent salati', 'Turp, mol go‘shti, tuxum', '25000', 10, False, False),
        ('Sabzavotli salat', 'Bodring, pomidor, ko‘kat', '18000', 5, True, False),
    ],
    'Ichimliklar': [
        ('Ko‘k choy', 'Choynakda', '8000', 3, True, False),
        ('Qora choy', 'Choynakda', '8000', 3, True, False),
        ('Ayron', 'Sovuq, tuzli', '10000', 2, True, False),
        ('Kompot', 'Uy kompoti, 1 stakan', '12000', 2, True, False),
    ],
    'Shirinliklar': [
        ('Chak-chak', 'Asalli xamir shirinligi', '20000', 5, True, False),
        ('Holvaytar', 'Un va shakar sharbatidan', '18000', 10, True, False),
        ('Medovik', 'Asalli tort, 1 bo‘lak', '28000', 5, True, False),
    ],
}

# (raqam, o'rindiq, joylashuv)
TABLES = [
    (1, 2, Table.HALL), (2, 2, Table.HALL), (3, 4, Table.HALL), (4, 4, Table.HALL),
    (5, 6, Table.HALL), (6, 4, Table.TERRACE), (7, 6, Table.TERRACE), (8, 10, Table.VIP),
]

USERS = [
    ('waiter1', Profile.WAITER, 'Ofitsiant', '+998901110001'),
    ('chef1', Profile.CHEF, 'Oshpaz', '+998901110002'),
    ('customer1', Profile.CUSTOMER, 'Mijoz', '+998901110003'),
]


class Command(BaseCommand):
    help = 'Restoran uchun namuna ma’lumot yaratadi. Qayta ishga tushirilsa takrorlamaydi va mavjudini o‘zgartirmaydi.'

    @transaction.atomic
    def handle(self, *args, **options):
        RestaurantSettings.objects.get_or_create(pk=1, defaults={
            'name': 'Choyxona Registon',
            'phone': '+998712000000',
            'address': 'Toshkent, Amir Temur ko‘chasi, 1',
            'opens_at': time(10),
            'closes_at': time(23),
        })

        items_created = 0
        categories_created = 0
        for order, (category_name, items) in enumerate(MENU.items(), start=1):
            category, created = Category.objects.get_or_create(name=category_name, defaults={'order': order})
            categories_created += created
            for name, description, price, minutes, vegetarian, spicy in items:
                _, created = MenuItem.objects.get_or_create(category=category, name=name, defaults={
                    'description': description,
                    'price': Decimal(price),
                    'preparation_minutes': minutes,
                    'is_vegetarian': vegetarian,
                    'spicy': spicy,
                })
                items_created += created

        tables_created = 0
        for number, seats, location in TABLES:
            _, created = Table.objects.get_or_create(number=number, defaults={'seats': seats, 'location': location})
            tables_created += created

        User = get_user_model()
        users_created = 0
        for username, role, first_name, phone in USERS:
            user, created = User.objects.get_or_create(username=username, defaults={'first_name': first_name})
            if created:
                user.set_password(TEST_PASSWORD)
                user.save(update_fields=['password'])
                users_created += 1
            Profile.objects.get_or_create(user=user, defaults={'role': role, 'phone': phone})

        self.stdout.write(self.style.SUCCESS(
            f'Tayyor. Yangi: {categories_created} kategoriya, {items_created} taom, '
            f'{tables_created} stol, {users_created} foydalanuvchi.'
        ))
