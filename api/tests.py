import base64
import io
import os
from datetime import datetime, time, timedelta
from decimal import Decimal

import tempfile
from unittest import mock

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.throttling import SimpleRateThrottle
from rest_framework_simplejwt.tokens import AccessToken

from restaurant.models import (
    Category, MenuItem, Order, OrderStatusEvent, Profile, Reservation, RestaurantSettings, Table,
)
from .exceptions import translate, translate_data
from .models import Book, Product
from .serializers import UserSerializer

User = get_user_model()

REAL_THROTTLE_RATES = dict(settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'])
_relaxed_rates = mock.patch.object(
    SimpleRateThrottle, 'THROTTLE_RATES', {scope: '1000000/hour' for scope in REAL_THROTTLE_RATES},
)


def setUpModule():
    # Throttling boshqa testlarga xalaqit bermasin: yuzlab so'rov bitta IP'dan keladi.
    # Cheklovning o'zini ThrottleTests haqiqiy tezliklar bilan tekshiradi.
    _relaxed_rates.start()


def tearDownModule():
    _relaxed_rates.stop()


def at(hour, days=2, minute=0):
    """Kelajakdagi aniq vaqt (Toshkent vaqti bilan), testlar soatga bog'liq bo'lmasligi uchun."""
    day = timezone.localdate() + timedelta(days=days)
    return timezone.make_aware(datetime.combine(day, time(hour, minute)))


class BaseAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.restaurant = RestaurantSettings.objects.create(
            name='Test', opens_at=time(10), closes_at=time(23),
            reservation_duration=120, booking_days=30, service_percent=Decimal('10'),
        )
        cls.superuser = User.objects.create_superuser('root', password='x')
        cls.admin = cls.make_user('admin1', Profile.ADMIN)
        cls.waiter = cls.make_user('waiter1', Profile.WAITER)
        cls.chef = cls.make_user('chef1', Profile.CHEF)
        cls.customer = cls.make_user('customer1', Profile.CUSTOMER)
        cls.other_customer = cls.make_user('customer2', Profile.CUSTOMER)
        cls.no_profile = User.objects.create_user('noprofile', password='x')

        cls.category = Category.objects.create(name='Milliy', order=1)
        cls.osh = MenuItem.objects.create(category=cls.category, name='Osh', price=Decimal('30000'))
        cls.salad = MenuItem.objects.create(category=cls.category, name='Salat', price=Decimal('15000'))
        cls.unavailable = MenuItem.objects.create(category=cls.category, name='Yo‘q', price=Decimal('1000'), available=False)
        cls.table = Table.objects.create(number=1, seats=4)
        cls.big_table = Table.objects.create(number=2, seats=10)
        cls.inactive_table = Table.objects.create(number=3, seats=4, active=False)

    @staticmethod
    def make_user(username, role):
        user = User.objects.create_user(username, password='x')
        Profile.objects.create(user=user, role=role)
        return user

    def login(self, user):
        self.client.force_authenticate(user=user)

    def results(self, response):
        data = response.data
        return data['results'] if isinstance(data, dict) and 'results' in data else data


class CatalogPermissionTests(BaseAPITest):
    READ_URLS = ['/api/categories/', '/api/menu-items/', '/api/tables/', '/api/settings/', '/api/menu/']

    def test_anonymous_can_read(self):
        for url in self.READ_URLS:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, status.HTTP_200_OK)

    def test_anonymous_cannot_write(self):
        response = self.client.post('/api/categories/', {'name': 'Yangi'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_admin_roles_cannot_write(self):
        for user in (self.waiter, self.chef, self.customer, self.no_profile):
            self.login(user)
            with self.subTest(user=user.username):
                self.assertEqual(self.client.post('/api/categories/', {'name': 'Yangi'}).status_code, status.HTTP_403_FORBIDDEN)
                self.assertEqual(self.client.post('/api/tables/', {'number': 50, 'seats': 2}).status_code, status.HTTP_403_FORBIDDEN)
                self.assertEqual(self.client.patch('/api/settings/', {'name': 'X'}).status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_role_and_superuser_can_write(self):
        for index, user in enumerate((self.admin, self.superuser)):
            self.login(user)
            with self.subTest(user=user.username):
                response = self.client.post('/api/categories/', {'name': f'Yangi{index}'})
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_menu_item_price_must_be_positive(self):
        self.login(self.admin)
        response = self.client.post('/api/menu-items/', {'category': self.category.pk, 'name': 'Bepul', 'price': '0'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_menu_item_duplicate_in_category_rejected(self):
        self.login(self.admin)
        response = self.client.post('/api/menu-items/', {'category': self.category.pk, 'name': 'Osh', 'price': '1000'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_table_seats_range(self):
        self.login(self.admin)
        response = self.client.post('/api/tables/', {'number': 60, 'seats': 21})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_profiles_admin_only(self):
        self.assertEqual(self.client.get('/api/profiles/').status_code, status.HTTP_401_UNAUTHORIZED)
        for user in (self.waiter, self.chef, self.customer):
            self.login(user)
            self.assertEqual(self.client.get('/api/profiles/').status_code, status.HTTP_403_FORBIDDEN)
        self.login(self.admin)
        self.assertEqual(self.client.get('/api/profiles/').status_code, status.HTTP_200_OK)

    def test_menu_shows_only_active_categories_and_available_items(self):
        hidden = Category.objects.create(name='Yashirin', active=False)
        MenuItem.objects.create(category=hidden, name='Ko‘rinmas', price=Decimal('1000'))
        response = self.client.get('/api/menu/')
        self.assertEqual([c['name'] for c in response.data], ['Milliy'])
        self.assertEqual({i['name'] for i in response.data[0]['items']}, {'Osh', 'Salat'})

    def test_schema_generates(self):
        self.assertEqual(self.client.get('/api/schema/').status_code, status.HTTP_200_OK)


class SettingsSingletonTests(BaseAPITest):
    def test_load_returns_same_row(self):
        self.assertEqual(RestaurantSettings.load().pk, 1)
        self.assertEqual(RestaurantSettings.objects.count(), 1)

    def test_second_save_overwrites_first(self):
        RestaurantSettings(name='Ikkinchi').save()
        self.assertEqual(RestaurantSettings.objects.count(), 1)
        self.assertEqual(RestaurantSettings.objects.get().name, 'Ikkinchi')

    def test_database_rejects_second_row(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            RestaurantSettings.objects.bulk_create([RestaurantSettings(pk=2)])

    def test_closes_after_opens(self):
        self.login(self.admin)
        response = self.client.patch('/api/settings/', {'closes_at': '09:00:00'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_service_percent_range(self):
        self.login(self.admin)
        response = self.client.patch('/api/settings/', {'service_percent': '31'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_settings_cannot_be_deleted_or_created_via_api(self):
        self.login(self.admin)
        self.assertEqual(self.client.delete('/api/settings/').status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(self.client.post('/api/settings/', {}).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_logo_format_rejected(self):
        buffer = io.BytesIO()
        Image.new('RGB', (2, 2)).save(buffer, format='GIF')
        self.login(self.admin)
        response = self.client.patch(
            '/api/settings/', {'logo': SimpleUploadedFile('a.gif', buffer.getvalue(), 'image/gif')}, format='multipart',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('logo', response.data)

    def test_logo_too_big_rejected(self):
        buffer = io.BytesIO()
        Image.new('RGB', (2, 2)).save(buffer, format='PNG')
        big = buffer.getvalue() + b'\0' * (3 * 1024 * 1024)
        self.login(self.admin)
        response = self.client.patch(
            '/api/settings/', {'logo': SimpleUploadedFile('a.png', big, 'image/png')}, format='multipart',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ReservationTests(BaseAPITest):
    def payload(self, **overrides):
        data = {
            'table': self.table.pk, 'guests': 2, 'start': at(12).isoformat(),
            'name': 'Ali', 'phone': '+998901234567',
        }
        data.update(overrides)
        return data

    def make_reservation(self, customer=None, table=None, start=None, res_status=Reservation.PENDING):
        start = start or at(12)
        return Reservation.objects.create(
            customer=customer or self.customer, table=table or self.table, guests=2, start=start,
            end=start + timedelta(minutes=120), status=res_status, name='Ali', phone='+998901234567',
        )

    def test_anonymous_rejected(self):
        self.assertEqual(self.client.get('/api/reservations/').status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.post('/api/reservations/', self.payload()).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_customer_create_sets_owner_and_end(self):
        self.login(self.customer)
        response = self.client.post('/api/reservations/', self.payload(
            customer=self.other_customer.pk, status='confirmed', end=at(22).isoformat(),
        ))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        reservation = Reservation.objects.get(pk=response.data['id'])
        self.assertEqual(reservation.customer, self.customer)
        self.assertEqual(reservation.created_by, self.customer)
        self.assertEqual(reservation.status, Reservation.PENDING)
        self.assertEqual(reservation.end, at(14))

    def test_user_without_profile_acts_as_customer(self):
        self.login(self.no_profile)
        self.assertEqual(self.client.post('/api/reservations/', self.payload()).status_code, status.HTTP_201_CREATED)

    def test_customer_sees_only_own(self):
        own = self.make_reservation()
        foreign = self.make_reservation(customer=self.other_customer, table=self.big_table)
        self.login(self.customer)
        ids = [r['id'] for r in self.results(self.client.get('/api/reservations/'))]
        self.assertEqual(ids, [own.pk])
        self.assertEqual(self.client.get(f'/api/reservations/{foreign.pk}/').status_code, status.HTTP_404_NOT_FOUND)

    def test_customer_cancels_own(self):
        reservation = self.make_reservation()
        self.login(self.customer)
        response = self.client.post(f'/api/reservations/{reservation.pk}/cancel/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], Reservation.CANCELLED)
        self.assertEqual(self.client.post(f'/api/reservations/{reservation.pk}/cancel/').status_code, status.HTTP_400_BAD_REQUEST)

    def test_customer_cannot_cancel_foreign(self):
        reservation = self.make_reservation(customer=self.other_customer)
        self.login(self.customer)
        self.assertEqual(self.client.post(f'/api/reservations/{reservation.pk}/cancel/').status_code, status.HTTP_404_NOT_FOUND)

    def test_customer_cannot_edit_or_delete(self):
        reservation = self.make_reservation()
        self.login(self.customer)
        url = f'/api/reservations/{reservation.pk}/'
        self.assertEqual(self.client.patch(url, {'status': 'confirmed'}).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.delete(url).status_code, status.HTTP_403_FORBIDDEN)

    def test_waiter_manages_all(self):
        reservation = self.make_reservation(customer=self.other_customer)
        self.login(self.waiter)
        self.assertEqual(len(self.results(self.client.get('/api/reservations/'))), 1)
        response = self.client.patch(f'/api/reservations/{reservation.pk}/', {'status': 'confirmed'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.post('/api/reservations/', self.payload(table=self.big_table.pk, customer=self.customer.pk))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        created = Reservation.objects.get(pk=response.data['id'])
        self.assertEqual(created.customer, self.customer)
        self.assertEqual(created.created_by, self.waiter)
        self.assertEqual(self.client.delete(f'/api/reservations/{reservation.pk}/').status_code, status.HTTP_204_NO_CONTENT)

    def test_waiter_without_customer_defaults_to_self(self):
        self.login(self.waiter)
        response = self.client.post('/api/reservations/', self.payload())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(Reservation.objects.get(pk=response.data['id']).customer, self.waiter)

    def test_chef_has_no_access(self):
        self.login(self.chef)
        self.assertEqual(self.client.get('/api/reservations/').status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.post('/api/reservations/', self.payload()).status_code, status.HTTP_403_FORBIDDEN)

    def test_overlap_rejected(self):
        self.make_reservation(start=at(12))
        self.login(self.customer)
        for start in (at(12), at(11), at(13, minute=59)):
            with self.subTest(start=start):
                response = self.client.post('/api/reservations/', self.payload(start=start.isoformat()))
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertEqual(response.data['start'], ['Bu stol shu vaqtda band.'])

    def test_error_format_is_always_a_list(self):
        reservation = self.make_reservation(res_status=Reservation.COMPLETED)
        self.login(self.waiter)
        response = self.client.post(f'/api/reservations/{reservation.pk}/cancel/')
        self.assertIsInstance(response.data['status'], list)
        response = self.client.get('/api/tables/available/', {'start': at(3).isoformat(), 'guests': 2})
        self.assertIsInstance(response.data['start'], list)

    def test_adjacent_and_other_table_allowed(self):
        self.make_reservation(start=at(12))
        self.login(self.customer)
        self.assertEqual(self.client.post('/api/reservations/', self.payload(start=at(14).isoformat())).status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.client.post('/api/reservations/', self.payload(start=at(10).isoformat())).status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.client.post('/api/reservations/', self.payload(table=self.big_table.pk)).status_code, status.HTTP_201_CREATED)

    def test_free_statuses_do_not_block(self):
        for res_status in Reservation.FREE_STATUSES:
            self.make_reservation(res_status=res_status)
        self.login(self.customer)
        self.assertEqual(self.client.post('/api/reservations/', self.payload()).status_code, status.HTTP_201_CREATED)

    def test_reschedule_into_conflict_rejected(self):
        self.make_reservation(start=at(12))
        later = self.make_reservation(start=at(16))
        self.login(self.waiter)
        response = self.client.patch(f'/api/reservations/{later.pk}/', {'start': at(13).isoformat()})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reschedule_updates_end(self):
        reservation = self.make_reservation(start=at(12))
        self.login(self.waiter)
        response = self.client.patch(f'/api/reservations/{reservation.pk}/', {'start': at(15).isoformat()})
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        reservation.refresh_from_db()
        self.assertEqual(reservation.end, at(17))

    def test_reactivating_into_conflict_rejected(self):
        cancelled = self.make_reservation(res_status=Reservation.CANCELLED)
        self.make_reservation()
        self.login(self.waiter)
        response = self.client.patch(f'/api/reservations/{cancelled.pk}/', {'status': 'confirmed'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_past_reservation_status_can_change(self):
        past = at(12, days=-3)
        reservation = self.make_reservation(start=past)
        self.login(self.waiter)
        response = self.client.patch(f'/api/reservations/{reservation.pk}/', {'status': 'completed', 'note': 'keldi'})
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

    def test_capacity(self):
        self.login(self.customer)
        response = self.client.post('/api/reservations/', self.payload(guests=5))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('guests', response.data)
        self.assertEqual(self.client.post('/api/reservations/', self.payload(guests=4)).status_code, status.HTTP_201_CREATED)

    def test_inactive_table(self):
        self.login(self.customer)
        response = self.client.post('/api/reservations/', self.payload(table=self.inactive_table.pk))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('table', response.data)

    def test_working_hours(self):
        self.login(self.customer)
        cases = {
            'ochilishdan oldin': at(9, minute=59),
            'tugashi yopilishdan keyin': at(21, minute=1),
            'yarim tundan keyin': at(23, minute=30),
        }
        for label, start in cases.items():
            with self.subTest(label):
                response = self.client.post('/api/reservations/', self.payload(start=start.isoformat()))
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn('start', response.data)

    def test_working_hours_boundaries_allowed(self):
        self.login(self.customer)
        self.assertEqual(self.client.post('/api/reservations/', self.payload(start=at(10).isoformat())).status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.client.post('/api/reservations/', self.payload(start=at(21).isoformat())).status_code, status.HTTP_201_CREATED)

    def test_past_rejected(self):
        self.login(self.customer)
        response = self.client.post('/api/reservations/', self.payload(start=at(12, days=-1).isoformat()))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_too_far_rejected(self):
        self.login(self.customer)
        response = self.client.post('/api/reservations/', self.payload(start=at(12, days=31).isoformat()))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.client.post('/api/reservations/', self.payload(start=at(12, days=29).isoformat())).status_code, status.HTTP_201_CREATED)

    def test_database_rejects_end_before_start(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Reservation.objects.create(
                customer=self.customer, table=self.table, guests=1, start=at(12), end=at(11), name='A', phone='+998901234567',
            )

    def test_available_tables(self):
        self.make_reservation(start=at(12))
        url = '/api/tables/available/'
        numbers = lambda r: [t['number'] for t in r.data]

        response = self.client.get(url, {'start': at(13).isoformat(), 'guests': 2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(numbers(response), [2])   # 1-stol band, 3-stol faol emas

        response = self.client.get(url, {'start': at(15).isoformat(), 'guests': 2})
        self.assertEqual(numbers(response), [1, 2])

        response = self.client.get(url, {'start': at(15).isoformat(), 'guests': 5})
        self.assertEqual(numbers(response), [2])   # 1-stolga 5 kishi sig'maydi

        # Vaqt zonasisiz yuborilsa, Toshkent vaqti deb olinadi: 13:00 da 1-stol band.
        naive = timezone.localtime(at(13)).strftime('%Y-%m-%dT%H:%M:%S')
        self.assertEqual(numbers(self.client.get(url, {'start': naive, 'guests': 2})), [2])

    def test_available_tables_bad_query(self):
        url = '/api/tables/available/'
        self.assertEqual(self.client.get(url, {'guests': 2}).status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.client.get(url, {'start': 'ertaga', 'guests': 2}).status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.client.get(url, {'start': at(13).isoformat(), 'guests': 0}).status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.client.get(url, {'start': at(3).isoformat(), 'guests': 2}).status_code, status.HTTP_400_BAD_REQUEST)


class OrderTestBase(BaseAPITest):
    def payload(self, **overrides):
        data = {
            'table': self.table.pk, 'order_type': 'dine_in',
            'items': [
                {'menu_item': self.osh.pk, 'quantity': 2},
                {'menu_item': self.salad.pk, 'quantity': 1, 'note': 'Piyozsiz'},
            ],
        }
        data.update(overrides)
        return data

    def create_order(self, user=None, **overrides):
        self.login(user or self.waiter)
        response = self.client.post('/api/orders/', self.payload(**overrides), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        return Order.objects.get(pk=response.data['id'])

    def set_status(self, order, value):
        return self.client.post(f'/api/orders/{order.pk}/set-status/', {'status': value}, format='json')

    def advance(self, order, *statuses):
        self.login(self.waiter)
        for value in statuses:
            self.assertEqual(self.set_status(order, value).status_code, status.HTTP_200_OK)


class OrderCreateTests(OrderTestBase):
    def test_totals_with_service_percent(self):
        order = self.create_order()
        self.assertEqual(order.subtotal, Decimal('75000.00'))
        self.assertEqual(order.service_percent, Decimal('10.00'))
        self.assertEqual(order.service_amount, Decimal('7500.00'))
        self.assertEqual(order.total, Decimal('82500.00'))
        self.assertEqual(order.status, Order.NEW)
        self.assertEqual(order.items.count(), 2)

    def test_service_amount_is_rounded(self):
        RestaurantSettings.objects.update(service_percent=Decimal('12.50'))
        item = MenuItem.objects.create(category=self.category, name='Qimmat', price=Decimal('333.33'))
        order = self.create_order(items=[{'menu_item': item.pk, 'quantity': 1}])
        self.assertEqual(order.service_amount, Decimal('41.67'))
        self.assertEqual(order.total, Decimal('375.00'))

    def test_client_cannot_set_prices_or_totals(self):
        order = self.create_order(
            items=[{'menu_item': self.osh.pk, 'quantity': 1, 'unit_price': '1.00', 'line_total': '1.00'}],
            subtotal='1.00', service_amount='0', total='1.00', service_percent='0', status='paid',
        )
        item = order.items.get()
        self.assertEqual(item.unit_price, Decimal('30000.00'))
        self.assertEqual(item.line_total, Decimal('30000.00'))
        self.assertEqual(order.total, Decimal('33000.00'))
        self.assertEqual(order.status, Order.NEW)

    def test_old_order_survives_price_and_percent_change(self):
        order = self.create_order()
        MenuItem.objects.filter(pk=self.osh.pk).update(price=Decimal('99000'))
        RestaurantSettings.objects.update(service_percent=Decimal('25'))

        order = Order.objects.get(pk=order.pk)
        order.recalculate()
        order.refresh_from_db()
        self.assertEqual(order.items.get(menu_item=self.osh).unit_price, Decimal('30000.00'))
        self.assertEqual(order.service_percent, Decimal('10.00'))
        self.assertEqual(order.total, Decimal('82500.00'))

        newer = self.create_order(items=[{'menu_item': self.osh.pk, 'quantity': 1}])
        self.assertEqual(newer.items.get().unit_price, Decimal('99000.00'))
        self.assertEqual(newer.service_percent, Decimal('25.00'))

    def test_unavailable_item_rejected(self):
        self.login(self.waiter)
        response = self.client.post('/api/orders/', self.payload(items=[{'menu_item': self.unavailable.pk, 'quantity': 1}]), format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Order.objects.count(), 0)

    def test_item_in_inactive_category_rejected(self):
        hidden = Category.objects.create(name='Yashirin', active=False)
        item = MenuItem.objects.create(category=hidden, name='Ko‘rinmas', price=Decimal('1000'))
        self.login(self.waiter)
        response = self.client.post('/api/orders/', self.payload(items=[{'menu_item': item.pk, 'quantity': 1}]), format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_items_rejected(self):
        self.login(self.waiter)
        cases = {
            'bo‘sh': [],
            'nol dona': [{'menu_item': self.osh.pk, 'quantity': 0}],
            'juda ko‘p': [{'menu_item': self.osh.pk, 'quantity': 1000}],
            'mavjud emas': [{'menu_item': 99999, 'quantity': 1}],
        }
        for label, items in cases.items():
            with self.subTest(label):
                response = self.client.post('/api/orders/', self.payload(items=items), format='json')
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = self.payload()
        del data['items']
        self.assertEqual(self.client.post('/api/orders/', data, format='json').status_code, status.HTTP_400_BAD_REQUEST)

    def test_dine_in_requires_table(self):
        self.login(self.waiter)
        data = self.payload()
        del data['table']
        response = self.client.post('/api/orders/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('table', response.data)

    def test_takeaway_without_table(self):
        data = self.payload(order_type='takeaway')
        del data['table']
        self.login(self.waiter)
        self.assertEqual(self.client.post('/api/orders/', data, format='json').status_code, status.HTTP_201_CREATED)

    def test_inactive_table_rejected(self):
        self.login(self.waiter)
        response = self.client.post('/api/orders/', self.payload(table=self.inactive_table.pk), format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_waiter_is_auto_assigned(self):
        order = self.create_order(waiter=self.other_customer.pk, customer=self.customer.pk)
        self.assertEqual(order.waiter, self.waiter)
        self.assertEqual(order.customer, self.customer)

    def test_customer_order_owner_is_forced(self):
        order = self.create_order(user=self.customer, customer=self.other_customer.pk, waiter=self.waiter.pk)
        self.assertEqual(order.customer, self.customer)
        self.assertIsNone(order.waiter)

    def test_creation_writes_event(self):
        order = self.create_order()
        event = order.events.get()
        self.assertEqual((event.previous_status, event.status, event.actor), ('', Order.NEW, self.waiter))

    def test_customer_cannot_use_foreign_reservation(self):
        reservation = Reservation.objects.create(
            customer=self.other_customer, table=self.table, guests=2, start=at(12), end=at(14), name='A', phone='+998901234567',
        )
        self.login(self.customer)
        response = self.client.post('/api/orders/', self.payload(reservation=reservation.pk), format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('reservation', response.data)

    def test_reservation_table_must_match(self):
        reservation = Reservation.objects.create(
            customer=self.customer, table=self.big_table, guests=2, start=at(12), end=at(14), name='A', phone='+998901234567',
        )
        self.login(self.waiter)
        response = self.client.post('/api/orders/', self.payload(reservation=reservation.pk), format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class OrderPermissionTests(OrderTestBase):
    def test_anonymous_rejected(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get('/api/orders/').status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.post('/api/orders/', self.payload(), format='json').status_code, status.HTTP_401_UNAUTHORIZED)

    def test_customer_sees_only_own(self):
        own = self.create_order(user=self.customer)
        foreign = self.create_order(user=self.other_customer)
        self.login(self.customer)
        self.assertEqual([o['id'] for o in self.results(self.client.get('/api/orders/'))], [own.pk])
        self.assertEqual(self.client.get(f'/api/orders/{foreign.pk}/').status_code, status.HTTP_404_NOT_FOUND)

    def test_customer_cannot_change(self):
        order = self.create_order(user=self.customer)
        self.login(self.customer)
        url = f'/api/orders/{order.pk}/'
        self.assertEqual(self.client.patch(url, {'note': 'x'}, format='json').status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.delete(url).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.set_status(order, 'cancelled').status_code, status.HTTP_403_FORBIDDEN)

    def test_waiter_and_admin_see_all(self):
        self.create_order(user=self.customer)
        self.create_order(user=self.other_customer)
        for user in (self.waiter, self.admin, self.superuser):
            self.login(user)
            self.assertEqual(len(self.results(self.client.get('/api/orders/'))), 2)

    def test_waiter_can_edit_but_not_status_or_totals_via_patch(self):
        order = self.create_order()
        response = self.client.patch(f'/api/orders/{order.pk}/', {'note': 'Tez', 'status': 'paid', 'total': '1'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        order.refresh_from_db()
        self.assertEqual(order.note, 'Tez')
        self.assertEqual(order.status, Order.NEW)
        self.assertEqual(order.total, Decimal('82500.00'))

    def test_put_without_items_works(self):
        order = self.create_order()
        response = self.client.put(
            f'/api/orders/{order.pk}/', {'table': self.big_table.pk, 'order_type': 'dine_in', 'note': 'Boshqa stol'}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        order.refresh_from_db()
        self.assertEqual(order.table, self.big_table)
        self.assertEqual(order.items.count(), 2)

    def test_items_cannot_change_after_create(self):
        order = self.create_order()
        response = self.client.patch(f'/api/orders/{order.pk}/', {'items': [{'menu_item': self.osh.pk, 'quantity': 9}]}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_finished_order_cannot_be_edited(self):
        order = self.create_order()
        self.advance(order, 'cancelled')
        response = self.client.patch(f'/api/orders/{order.pk}/', {'note': 'x'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_cannot_remove_table_from_dine_in(self):
        order = self.create_order()
        response = self.client.patch(f'/api/orders/{order.pk}/', {'table': None}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class OrderStatusTests(OrderTestBase):
    def test_full_path(self):
        order = self.create_order()
        self.advance(order, 'cooking', 'ready', 'served')
        self.assertIsNone(Order.objects.get(pk=order.pk).paid_at)
        response = self.set_status(order, 'paid')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'paid')
        self.assertIsNotNone(response.data['paid_at'])
        order.refresh_from_db()
        self.assertIsNotNone(order.paid_at)
        path = list(order.events.order_by('id').values_list('previous_status', 'status', 'actor__username'))
        self.assertEqual(path, [
            ('', 'new', 'waiter1'), ('new', 'cooking', 'waiter1'), ('cooking', 'ready', 'waiter1'),
            ('ready', 'served', 'waiter1'), ('served', 'paid', 'waiter1'),
        ])

    def test_invalid_transitions(self):
        order = self.create_order()
        for value in ('ready', 'served', 'paid', 'new'):
            with self.subTest(value):
                self.assertEqual(self.set_status(order, value).status_code, status.HTTP_400_BAD_REQUEST)
        self.advance(order, 'cooking')
        self.assertEqual(self.set_status(order, 'new').status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.set_status(order, 'cooking').status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(order.events.count(), 2)

    def test_unknown_status(self):
        order = self.create_order()
        self.assertEqual(self.set_status(order, 'kuydi').status_code, status.HTTP_400_BAD_REQUEST)

    def test_cancel_from_every_stage_except_paid(self):
        stages = [[], ['cooking'], ['cooking', 'ready'], ['cooking', 'ready', 'served']]
        for path in stages:
            with self.subTest(path=path):
                order = self.create_order()
                self.advance(order, *path)
                self.assertEqual(self.set_status(order, 'cancelled').status_code, status.HTTP_200_OK)
                self.assertEqual(self.set_status(order, 'cooking').status_code, status.HTTP_400_BAD_REQUEST)
                self.assertEqual(self.set_status(order, 'cancelled').status_code, status.HTTP_400_BAD_REQUEST)

    def test_paid_cannot_be_cancelled(self):
        order = self.create_order()
        self.advance(order, 'cooking', 'ready', 'served', 'paid')
        self.assertEqual(self.set_status(order, 'cancelled').status_code, status.HTTP_400_BAD_REQUEST)


class ChefTests(OrderTestBase):
    def test_chef_moves_to_cooking_and_ready(self):
        order = self.create_order()
        self.login(self.chef)
        self.assertEqual(self.set_status(order, 'cooking').status_code, status.HTTP_200_OK)
        self.assertEqual(self.set_status(order, 'ready').status_code, status.HTTP_200_OK)
        self.assertEqual(order.events.order_by('-id').first().actor, self.chef)

    def test_chef_cannot_serve_pay_or_cancel(self):
        order = self.create_order()
        self.advance(order, 'cooking', 'ready')
        self.login(self.chef)
        for value in ('served', 'paid', 'cancelled'):
            with self.subTest(value):
                self.assertEqual(self.set_status(order, value).status_code, status.HTTP_403_FORBIDDEN)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.READY)

    def test_chef_invalid_transition_is_400(self):
        order = self.create_order()
        self.login(self.chef)
        self.assertEqual(self.set_status(order, 'ready').status_code, status.HTTP_400_BAD_REQUEST)

    def test_chef_cannot_edit_create_or_delete(self):
        order = self.create_order()
        self.login(self.chef)
        url = f'/api/orders/{order.pk}/'
        self.assertEqual(self.client.patch(url, {'note': 'x'}, format='json').status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.put(url, self.payload(), format='json').status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.delete(url).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.post('/api/orders/', self.payload(), format='json').status_code, status.HTTP_403_FORBIDDEN)

    def test_chef_sees_only_kitchen_statuses(self):
        new = self.create_order()
        cooking = self.create_order()
        self.advance(cooking, 'cooking')
        ready = self.create_order()
        self.advance(ready, 'cooking', 'ready')
        served = self.create_order()
        self.advance(served, 'cooking', 'ready', 'served')
        cancelled = self.create_order()
        self.advance(cancelled, 'cancelled')

        self.login(self.chef)
        ids = {o['id'] for o in self.results(self.client.get('/api/orders/'))}
        self.assertEqual(ids, {new.pk, cooking.pk, ready.pk})
        self.assertEqual(self.client.get(f'/api/orders/{served.pk}/').status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.set_status(served, 'cooking').status_code, status.HTTP_404_NOT_FOUND)

    def test_kitchen_endpoint(self):
        first = self.create_order()
        second = self.create_order()
        self.advance(first, 'cooking')
        ready = self.create_order()
        self.advance(ready, 'cooking', 'ready')

        self.login(self.chef)
        response = self.client.get('/api/orders/kitchen/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([o['id'] for o in response.data], [first.pk, second.pk])

        self.login(self.customer)
        self.assertEqual(self.client.get('/api/orders/kitchen/').status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get('/api/orders/kitchen/').status_code, status.HTTP_401_UNAUTHORIZED)


class OrderEventTests(OrderTestBase):
    def test_read_only(self):
        order = self.create_order()
        event = order.events.get()
        self.login(self.admin)
        self.assertEqual(self.client.get('/api/order-events/').status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.post('/api/order-events/', {'order': order.pk, 'status': 'paid'}).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(self.client.delete(f'/api/order-events/{event.pk}/').status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_filtered_by_role(self):
        own = self.create_order(user=self.customer)
        self.create_order(user=self.other_customer)
        self.login(self.customer)
        response = self.client.get('/api/order-events/')
        self.assertEqual([e['order'] for e in self.results(response)], [own.pk])

        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get('/api/order-events/').status_code, status.HTTP_401_UNAUTHORIZED)


class ProtectedDeleteTests(OrderTestBase):
    def assert_protected(self, url):
        self.login(self.admin)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('o‘chirib bo‘lmaydi', response.data['detail'])

    def test_category_with_items(self):
        self.assert_protected(f'/api/categories/{self.category.pk}/')
        self.assertTrue(Category.objects.filter(pk=self.category.pk).exists())

    def test_menu_item_in_order(self):
        self.create_order()
        self.assert_protected(f'/api/menu-items/{self.osh.pk}/')

    def test_table_with_reservation(self):
        Reservation.objects.create(
            customer=self.customer, table=self.table, guests=2, start=at(12), end=at(14), name='A', phone='+998901234567',
        )
        self.assert_protected(f'/api/tables/{self.table.pk}/')

    def test_table_with_order(self):
        self.create_order()
        self.assert_protected(f'/api/tables/{self.table.pk}/')

    def test_free_records_can_be_deleted(self):
        self.login(self.admin)
        self.assertEqual(self.client.delete(f'/api/menu-items/{self.unavailable.pk}/').status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.client.delete(f'/api/tables/{self.inactive_table.pk}/').status_code, status.HTTP_204_NO_CONTENT)


class DailyReportTests(OrderTestBase):
    def test_admin_only(self):
        self.assertEqual(self.client.get('/api/reports/daily/').status_code, status.HTTP_401_UNAUTHORIZED)
        for user in (self.waiter, self.chef, self.customer):
            self.login(user)
            self.assertEqual(self.client.get('/api/reports/daily/').status_code, status.HTTP_403_FORBIDDEN)

    def test_values(self):
        paid = self.create_order()   # 2 osh + 1 salat = 82500
        self.advance(paid, 'cooking', 'ready', 'served', 'paid')
        extra = self.create_order(items=[{'menu_item': self.salad.pk, 'quantity': 4}])   # 60000 + 10%
        self.advance(extra, 'cooking', 'ready', 'served', 'paid')
        self.create_order()   # to'lanmagan: summaga kirmaydi

        self.login(self.admin)
        response = self.client.get('/api/reports/daily/', {'date': timezone.localdate().isoformat()})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['orders_count'], 3)
        self.assertEqual(response.data['paid_orders_count'], 2)
        self.assertEqual(response.data['paid_total'], '148500.00')
        self.assertEqual(
            [(i['name'], i['quantity']) for i in response.data['top_items']],
            [('Salat', 5), ('Osh', 2)],
        )

    def test_top_items_limited_to_five(self):
        items = [MenuItem.objects.create(category=self.category, name=f'T{n}', price=Decimal('1000')) for n in range(7)]
        order = self.create_order(items=[{'menu_item': i.pk, 'quantity': 1} for i in items])
        self.advance(order, 'cooking', 'ready', 'served', 'paid')
        self.login(self.admin)
        self.assertEqual(len(self.client.get('/api/reports/daily/').data['top_items']), 5)

    def test_other_day_is_empty(self):
        order = self.create_order()
        self.advance(order, 'cooking', 'ready', 'served', 'paid')
        self.login(self.admin)
        day = timezone.localdate() - timedelta(days=1)
        response = self.client.get('/api/reports/daily/', {'date': day.isoformat()})
        self.assertEqual(response.data['orders_count'], 0)
        self.assertEqual(response.data['paid_total'], '0.00')
        self.assertEqual(response.data['top_items'], [])

    def test_bad_date(self):
        self.login(self.admin)
        self.assertEqual(self.client.get('/api/reports/daily/', {'date': 'kecha'}).status_code, status.HTTP_400_BAD_REQUEST)


class BookTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('reader', password='x')

    def test_anonymous_reads_but_cannot_write(self):
        self.assertEqual(self.client.get('/api/books/').status_code, status.HTTP_200_OK)
        response = self.client.post('/api/books/', {'title': 'A', 'author': 'B', 'price': '1000'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_crud(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/books/', {'title': 'Kitob', 'author': 'Ali', 'price': '25000.00'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        url = f"/api/books/{response.data['id']}/"

        self.assertEqual(self.client.get(url).data['title'], 'Kitob')
        self.assertEqual(self.client.patch(url, {'price': '30000.00'}).data['price'], '30000.00')
        self.assertEqual(self.client.put(url, {'title': 'Yangi', 'author': 'Vali', 'price': '1.00'}).data['author'], 'Vali')
        self.assertEqual(self.client.delete(url).status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Book.objects.count(), 0)


class AdminTests(BaseAPITest):
    def setUp(self):
        self.client.force_login(self.superuser)

    def test_pages_open(self):
        for model in ('restaurantsettings', 'profile', 'category', 'menuitem', 'table', 'reservation', 'order', 'orderitem', 'orderstatusevent'):
            with self.subTest(model):
                response = self.client.get(reverse(f'admin:restaurant_{model}_changelist'))
                self.assertEqual(response.status_code, status.HTTP_200_OK)
        for model in ('profile', 'category', 'menuitem', 'table', 'reservation', 'order'):
            with self.subTest(add=model):
                response = self.client.get(reverse(f'admin:restaurant_{model}_add'))
                self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_settings_singleton_in_admin(self):
        self.assertEqual(self.client.get(reverse('admin:restaurant_restaurantsettings_add')).status_code, status.HTTP_403_FORBIDDEN)
        url = reverse('admin:restaurant_restaurantsettings_delete', args=[1])
        self.assertEqual(self.client.get(url).status_code, status.HTTP_403_FORBIDDEN)

    def test_events_are_read_only_in_admin(self):
        self.assertEqual(self.client.get(reverse('admin:restaurant_orderstatusevent_add')).status_code, status.HTTP_403_FORBIDDEN)

    def test_reservation_add_computes_end_and_checks_conflict(self):
        data = {
            'customer': self.customer.pk, 'table': self.table.pk, 'guests': 2, 'status': 'pending',
            'start_0': at(12).astimezone(timezone.get_current_timezone()).strftime('%Y-%m-%d'), 'start_1': '12:00:00',
            'name': 'Ali', 'phone': '+998901234567', 'note': '',
        }
        url = reverse('admin:restaurant_reservation_add')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND, getattr(response, 'context', None) and response.context['errors'])
        reservation = Reservation.objects.get()
        self.assertEqual(reservation.end, at(14))
        self.assertEqual(reservation.created_by, self.superuser)

        self.assertEqual(self.client.post(url, data).status_code, status.HTTP_200_OK)   # forma xato bilan qaytadi
        self.assertEqual(Reservation.objects.count(), 1)

    def test_order_with_history_cannot_be_deleted_in_admin(self):
        order = Order.objects.create(table=self.table)
        OrderStatusEvent.objects.create(order=order, status=order.status, actor=self.superuser)
        response = self.client.post(reverse('admin:restaurant_order_delete', args=[order.pk]), {'post': 'yes'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Order.objects.filter(pk=order.pk).exists())

    def test_order_add_recalculates_and_writes_event(self):
        response = self.client.post(reverse('admin:restaurant_order_add'), {
            'table': self.table.pk, 'order_type': 'dine_in', 'note': '',
            'items-TOTAL_FORMS': 1, 'items-INITIAL_FORMS': 0, 'items-MIN_NUM_FORMS': 0, 'items-MAX_NUM_FORMS': 1000,
            'items-0-menu_item': self.osh.pk, 'items-0-quantity': 2, 'items-0-note': '',
        })
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        order = Order.objects.get()
        self.assertEqual(order.total, Decimal('66000.00'))
        self.assertEqual(OrderStatusEvent.objects.filter(order=order).count(), 1)


STRONG_PASSWORD = 'Kuchli-Parol-2026'
NEW_PASSWORD = 'Yangi-Maxfiy-2027'


class UserAPITestBase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = User.objects.create_user('alice', email='alice@example.com', password=STRONG_PASSWORD, first_name='Alisa')
        cls.bob = User.objects.create_user('bob', email='bob@example.com', password=STRONG_PASSWORD)
        cls.admin = User.objects.create_user('boss', email='boss@example.com', password=STRONG_PASSWORD)
        Profile.objects.create(user=cls.admin, role=Profile.ADMIN)
        cls.root = User.objects.create_superuser('root', email='root@example.com', password=STRONG_PASSWORD)

    def obtain(self, username='alice', password=STRONG_PASSWORD):
        self.client.credentials()
        return self.client.post('/api/token/', {'username': username, 'password': password}, format='json')

    def bearer(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def login_as(self, username='alice', password=STRONG_PASSWORD):
        """Haqiqiy JWT bilan kiradi va tokenlarni qaytaradi."""
        response = self.obtain(username, password)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.bearer(response.data['access'])
        return response.data

    def refresh(self, token):
        self.client.credentials()
        return self.client.post('/api/token/refresh/', {'refresh': token}, format='json')


class RegisterTests(UserAPITestBase):
    def payload(self, **overrides):
        data = {
            'username': 'yangi', 'email': 'yangi@example.com', 'password': STRONG_PASSWORD,
            'password2': STRONG_PASSWORD, 'first_name': 'Ali', 'last_name': 'Valiyev',
        }
        data.update(overrides)
        return data

    def post(self, **overrides):
        return self.client.post('/api/auth/register/', self.payload(**overrides), format='json')

    def test_success_returns_user_and_working_tokens(self):
        response = self.post()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data['user']['username'], 'yangi')
        self.assertEqual(response.data['user']['role'], Profile.CUSTOMER)
        self.assertNotIn('password', response.data['user'])

        user = User.objects.get(username='yangi')
        self.assertEqual(user.profile.role, Profile.CUSTOMER)
        self.assertTrue(user.check_password(STRONG_PASSWORD))
        self.assertFalse(user.is_staff or user.is_superuser)

        self.bearer(response.data['access'])
        self.assertEqual(self.client.get('/api/users/me/').data['username'], 'yangi')
        self.assertEqual(self.refresh(response.data['refresh']).status_code, status.HTTP_200_OK)

    def test_cannot_register_as_privileged(self):
        response = self.post(is_staff=True, is_superuser=True, role='admin')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username='yangi')
        self.assertFalse(user.is_staff or user.is_superuser)
        self.assertEqual(user.profile.role, Profile.CUSTOMER)

    def test_password_mismatch(self):
        response = self.post(password2='Boshqa-Parol-2026')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password2', response.data)

    def test_duplicate_username(self):
        response = self.post(username='alice')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)

    def test_duplicate_email_ignores_case(self):
        response = self.post(email='ALICE@example.com')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['email'], ['Bu email boshqa foydalanuvchiga tegishli.'])

    def test_blank_email_can_repeat(self):
        User.objects.create_user('bosh', email='', password=STRONG_PASSWORD)
        self.assertEqual(self.post(email='').status_code, status.HTTP_201_CREATED)

    def test_weak_passwords(self):
        for password in ('12345678', 'password', 'qisqa', 'yangi12'):
            with self.subTest(password):
                response = self.post(password=password, password2=password)
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn('password', response.data)
        self.assertFalse(User.objects.filter(username='yangi').exists())

    def test_password_similar_to_username(self):
        response = self.post(username='sardorbek', password='sardorbek1', password2='sardorbek1')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_stale_token_does_not_block_registration(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer buzilgan')
        self.assertEqual(self.post().status_code, status.HTTP_201_CREATED)


class JWTTests(UserAPITestBase):
    def test_obtain_and_use_token(self):
        tokens = self.login_as()
        self.assertIn('refresh', tokens)
        response = self.client.get('/api/users/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'alice')
        self.assertIsNotNone(response.data['last_login'])   # UPDATE_LAST_LOGIN

    def test_wrong_password(self):
        self.assertEqual(self.obtain(password='notogri').status_code, status.HTTP_401_UNAUTHORIZED)

    def test_no_token(self):
        self.assertEqual(self.client.get('/api/users/me/').status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_token(self):
        self.bearer('buzilgan.token.qiymat')
        self.assertEqual(self.client.get('/api/users/me/').status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token_is_not_accepted_as_access(self):
        tokens = self.login_as()
        self.bearer(tokens['refresh'])
        self.assertEqual(self.client.get('/api/users/me/').status_code, status.HTTP_401_UNAUTHORIZED)

    def test_verify(self):
        tokens = self.login_as()
        self.client.credentials()
        self.assertEqual(self.client.post('/api/token/verify/', {'token': tokens['access']}, format='json').status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.post('/api/token/verify/', {'token': 'buzilgan'}, format='json').status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_rotates_and_old_token_dies(self):
        tokens = self.login_as()
        response = self.refresh(tokens['refresh'])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(response.data['refresh'], tokens['refresh'])

        self.bearer(response.data['access'])
        self.assertEqual(self.client.get('/api/users/me/').status_code, status.HTTP_200_OK)

        self.assertEqual(self.refresh(tokens['refresh']).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.refresh(response.data['refresh']).status_code, status.HTTP_200_OK)

    def test_basic_auth(self):
        credentials = base64.b64encode(f'alice:{STRONG_PASSWORD}'.encode()).decode()
        self.client.credentials(HTTP_AUTHORIZATION=f'Basic {credentials}')
        response = self.client.get('/api/users/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'alice')

    def test_basic_auth_wrong_password(self):
        credentials = base64.b64encode(b'alice:notogri').decode()
        self.client.credentials(HTTP_AUTHORIZATION=f'Basic {credentials}')
        self.assertEqual(self.client.get('/api/users/me/').status_code, status.HTTP_401_UNAUTHORIZED)


class UserMeTests(UserAPITestBase):
    def setUp(self):
        self.tokens = self.login_as()

    def test_get(self):
        response = self.client.get('/api/users/me/')
        self.assertEqual(response.data['email'], 'alice@example.com')
        self.assertEqual(response.data['role'], Profile.CUSTOMER)
        self.assertTrue(response.data['is_active'])
        self.assertNotIn('password', response.data)
        self.assertEqual(set(response.data), {
            'id', 'username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'date_joined', 'last_login',
        })

    def test_put_requires_username_and_replaces_fields(self):
        response = self.client.put('/api/users/me/', {'first_name': 'Faqat'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)

        response = self.client.put('/api/users/me/', {
            'username': 'alice2', 'email': 'alice2@example.com', 'first_name': 'A', 'last_name': 'B',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.alice.refresh_from_db()
        self.assertEqual(
            (self.alice.username, self.alice.email, self.alice.first_name, self.alice.last_name),
            ('alice2', 'alice2@example.com', 'A', 'B'),
        )

        # Majburiy bo'lmagan maydon PUT da yuborilmasa, eski qiymati saqlanadi.
        response = self.client.put('/api/users/me/', {'username': 'alice3'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'alice2@example.com')

    def test_patch_changes_only_sent_field(self):
        response = self.client.patch('/api/users/me/', {'last_name': 'Yangi'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.alice.refresh_from_db()
        self.assertEqual(self.alice.last_name, 'Yangi')
        self.assertEqual(self.alice.first_name, 'Alisa')
        self.assertEqual(self.alice.email, 'alice@example.com')

    def test_email_must_be_free_but_own_is_ok(self):
        response = self.client.patch('/api/users/me/', {'email': 'BOB@example.com'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['email'], ['Bu email boshqa foydalanuvchiga tegishli.'])
        self.assertEqual(self.client.patch('/api/users/me/', {'email': 'ALICE@example.com'}, format='json').status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.patch('/api/users/me/', {'email': ''}, format='json').status_code, status.HTTP_200_OK)

    def test_cannot_escalate(self):
        response = self.client.patch('/api/users/me/', {
            'is_staff': True, 'is_superuser': True, 'role': 'admin', 'is_active': False,
            'last_login': None, 'date_joined': '2000-01-01T00:00:00Z',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['role'], Profile.CUSTOMER)
        joined = self.alice.date_joined
        self.alice.refresh_from_db()
        self.assertFalse(self.alice.is_staff or self.alice.is_superuser)
        self.assertTrue(self.alice.is_active)
        self.assertEqual(self.alice.date_joined, joined)
        self.assertFalse(Profile.objects.filter(user=self.alice).exists())

        self.assertEqual(self.client.get('/api/users/').status_code, status.HTTP_403_FORBIDDEN)

    def test_password_rejected_in_patch_and_put(self):
        requests = (
            lambda: self.client.patch('/api/users/me/', {'password': NEW_PASSWORD, 'first_name': 'Boshqa'}, format='json'),
            lambda: self.client.put('/api/users/me/', {'username': 'alice', 'password': NEW_PASSWORD, 'first_name': 'Boshqa'}, format='json'),
            lambda: self.client.patch('/api/users/me/', {'password': NEW_PASSWORD}, format='multipart'),
            lambda: self.client.patch('/api/users/me/', {'password': ''}, format='json'),
        )
        for request in requests:
            response = request()
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data['password'], ['Parolni change-password orqali o‘zgartiring.'])

        # Hech narsa o'zgarmagan: parol ham, yonidagi maydon ham, tokenlar ham.
        self.alice.refresh_from_db()
        self.assertTrue(self.alice.check_password(STRONG_PASSWORD))
        self.assertEqual(self.alice.first_name, 'Alisa')
        self.assertEqual(self.refresh(self.tokens['refresh']).status_code, status.HTTP_200_OK)

    def test_password_field_not_in_serializer(self):
        self.assertNotIn('password', self.client.get('/api/users/me/').data)
        self.assertNotIn('password', UserSerializer().fields)

    def test_delete_is_soft_and_blocks_all_access(self):
        response = self.client.delete('/api/users/me/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.alice.refresh_from_db()
        self.assertFalse(self.alice.is_active)

        self.assertEqual(self.client.get('/api/users/me/').status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.refresh(self.tokens['refresh']).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.obtain().status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_keeps_reservation_history(self):
        table = Table.objects.create(number=1, seats=2)
        reservation = Reservation.objects.create(
            customer=self.alice, table=table, guests=1, start=at(12), end=at(14), name='A', phone='+998901234567',
        )
        self.assertEqual(self.client.delete('/api/users/me/').status_code, status.HTTP_204_NO_CONTENT)
        reservation.refresh_from_db()
        self.assertEqual(reservation.customer, self.alice)

    def test_superuser_cannot_delete_self(self):
        self.login_as('root')
        response = self.client.delete('/api/users/me/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.root.refresh_from_db()
        self.assertTrue(self.root.is_active)


class UserDetailTests(UserAPITestBase):
    def url(self, user):
        return f'/api/users/{user.pk}/'

    def test_anonymous(self):
        self.assertEqual(self.client.get(self.url(self.alice)).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_owner(self):
        self.login_as()
        self.assertEqual(self.client.get(self.url(self.alice)).status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.patch(self.url(self.alice), {'last_name': 'Z'}, format='json').status_code, status.HTTP_200_OK)

    def test_other_user_forbidden_with_uzbek_message(self):
        self.login_as()
        url = self.url(self.bob)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], 'Bu amal faqat hisob egasi yoki administrator uchun ruxsat etilgan.')
        self.assertEqual(self.client.patch(url, {'last_name': 'X'}, format='json').status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.put(url, {'username': 'x'}, format='json').status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.delete(url).status_code, status.HTTP_403_FORBIDDEN)
        self.bob.refresh_from_db()
        self.assertTrue(self.bob.is_active)
        self.assertEqual(self.bob.last_name, '')

    def test_missing_user_is_404(self):
        self.login_as('boss')
        self.assertEqual(self.client.get('/api/users/999999/').status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_reads_edits_and_deletes_others(self):
        for username in ('boss', 'root'):
            with self.subTest(username):
                target = User.objects.create_user(f'target_{username}', password=STRONG_PASSWORD)
                self.login_as(username)
                url = self.url(target)
                self.assertEqual(self.client.get(url).status_code, status.HTTP_200_OK)
                self.assertEqual(self.client.patch(url, {'first_name': 'Tahrir'}, format='json').status_code, status.HTTP_200_OK)
                self.assertEqual(self.client.delete(url).status_code, status.HTTP_204_NO_CONTENT)
                target.refresh_from_db()
                self.assertEqual(target.first_name, 'Tahrir')
                self.assertFalse(target.is_active)

    def test_admin_cannot_escalate_others_via_serializer(self):
        self.login_as('boss')
        self.client.patch(self.url(self.bob), {'is_superuser': True, 'is_staff': True}, format='json')
        self.bob.refresh_from_db()
        self.assertFalse(self.bob.is_superuser or self.bob.is_staff)

    def test_admin_cannot_set_others_password(self):
        self.login_as('boss')
        response = self.client.patch(self.url(self.bob), {'password': NEW_PASSWORD}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.bob.refresh_from_db()
        self.assertTrue(self.bob.check_password(STRONG_PASSWORD))

    def test_delete_revokes_target_tokens(self):
        tokens = self.login_as('bob')
        self.login_as('boss')
        self.assertEqual(self.client.delete(self.url(self.bob)).status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.refresh(tokens['refresh']).status_code, status.HTTP_401_UNAUTHORIZED)
        self.bearer(tokens['access'])
        self.assertEqual(self.client.get('/api/users/me/').status_code, status.HTTP_401_UNAUTHORIZED)

    def test_superuser_cannot_be_deleted(self):
        self.login_as('root')
        other = User.objects.create_superuser('root2', password=STRONG_PASSWORD)
        response = self.client.delete(self.url(other))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        other.refresh_from_db()
        self.assertTrue(other.is_active)

    def test_admin_role_cannot_take_over_superuser(self):
        self.login_as('boss')
        url = self.url(self.root)
        self.assertEqual(self.client.get(url).status_code, status.HTTP_200_OK)
        for request in (
            lambda: self.client.patch(url, {'password': NEW_PASSWORD}, format='json'),
            lambda: self.client.patch(url, {'email': 'men@example.com'}, format='json'),
            lambda: self.client.put(url, {'username': 'root', 'password': NEW_PASSWORD}, format='json'),
            lambda: self.client.delete(url),
        ):
            self.assertEqual(request().status_code, status.HTTP_403_FORBIDDEN)
        self.root.refresh_from_db()
        self.assertTrue(self.root.check_password(STRONG_PASSWORD))
        self.assertEqual(self.root.email, 'root@example.com')


class UserListTests(UserAPITestBase):
    def usernames(self, **params):
        return {u['username'] for u in self.client.get('/api/users/', params).data['results']}

    def test_admin_only(self):
        self.assertEqual(self.client.get('/api/users/').status_code, status.HTTP_401_UNAUTHORIZED)
        self.login_as()
        self.assertEqual(self.client.get('/api/users/').status_code, status.HTTP_403_FORBIDDEN)
        for username in ('boss', 'root'):
            self.login_as(username)
            self.assertEqual(self.client.get('/api/users/').status_code, status.HTTP_200_OK)

    def test_post_not_allowed(self):
        self.login_as('boss')
        self.assertEqual(self.client.post('/api/users/', {'username': 'x'}, format='json').status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_search_and_filter(self):
        User.objects.filter(pk=self.bob.pk).update(is_active=False)
        self.login_as('boss')
        self.assertEqual(self.usernames(search='alice'), {'alice'})
        self.assertEqual(self.usernames(search='bob@example'), {'bob'})
        self.assertEqual(self.usernames(search='Alisa'), {'alice'})
        self.assertEqual(self.usernames(is_active='false'), {'bob'})
        self.assertNotIn('bob', self.usernames(is_active='true'))


class ChangePasswordTests(UserAPITestBase):
    URL = '/api/auth/change-password/'

    def payload(self, **overrides):
        data = {'old_password': STRONG_PASSWORD, 'new_password': NEW_PASSWORD, 'new_password2': NEW_PASSWORD}
        data.update(overrides)
        return data

    def test_anonymous(self):
        self.assertEqual(self.client.post(self.URL, self.payload(), format='json').status_code, status.HTTP_401_UNAUTHORIZED)

    def test_wrong_old_password(self):
        self.login_as()
        response = self.client.post(self.URL, self.payload(old_password='notogri'), format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['old_password'], ['Eski parol noto‘g‘ri.'])

    def test_mismatch_and_weak(self):
        self.login_as()
        response = self.client.post(self.URL, self.payload(new_password2='Boshqa-Parol-2026'), format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('new_password2', response.data)
        response = self.client.post(self.URL, self.payload(new_password='12345678', new_password2='12345678'), format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('new_password', response.data)
        self.alice.refresh_from_db()
        self.assertTrue(self.alice.check_password(STRONG_PASSWORD))

    def test_success_changes_login_and_revokes_all_refresh_tokens(self):
        first = self.obtain().data
        rotated = self.refresh(first['refresh']).data   # rotatsiyadan chiqqan token ham bekor bo'lishi kerak
        second = self.login_as()

        response = self.client.post(self.URL, self.payload(), format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

        self.assertEqual(self.obtain(password=STRONG_PASSWORD).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.obtain(password=NEW_PASSWORD).status_code, status.HTTP_200_OK)
        for token in (rotated['refresh'], second['refresh']):
            self.assertEqual(self.refresh(token).status_code, status.HTTP_401_UNAUTHORIZED)


class LogoutTests(UserAPITestBase):
    URL = '/api/auth/logout/'

    def test_success_then_refresh_fails(self):
        tokens = self.login_as()
        response = self.client.post(self.URL, {'refresh': tokens['refresh']}, format='json')
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)
        self.assertEqual(self.refresh(tokens['refresh']).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_tokens(self):
        tokens = self.login_as()
        for value in ('buzilgan', tokens['access']):
            with self.subTest(value=value[:10]):
                self.assertEqual(self.client.post(self.URL, {'refresh': value}, format='json').status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.client.post(self.URL, {}, format='json').status_code, status.HTTP_400_BAD_REQUEST)

    def test_twice(self):
        tokens = self.login_as()
        self.assertEqual(self.client.post(self.URL, {'refresh': tokens['refresh']}, format='json').status_code, status.HTTP_205_RESET_CONTENT)
        self.assertEqual(self.client.post(self.URL, {'refresh': tokens['refresh']}, format='json').status_code, status.HTTP_400_BAD_REQUEST)

    def test_foreign_token_rejected(self):
        foreign = self.login_as('bob')
        self.login_as()
        response = self.client.post(self.URL, {'refresh': foreign['refresh']}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.refresh(foreign['refresh']).status_code, status.HTTP_200_OK)

    def test_anonymous(self):
        tokens = self.obtain().data
        self.client.credentials()
        self.assertEqual(self.client.post(self.URL, {'refresh': tokens['refresh']}, format='json').status_code, status.HTTP_401_UNAUTHORIZED)


class ThrottleTests(UserAPITestBase):
    """Haqiqiy tezliklar bilan: setUpModule dagi yumshatish shu klassda bekor qilinadi."""
    TOKEN_URL = '/api/token/'
    REGISTER_URL = '/api/auth/register/'

    def setUp(self):
        self.use_rates(REAL_THROTTLE_RATES)
        cache.clear()
        self.addCleanup(cache.clear)

    def use_rates(self, rates):
        patcher = mock.patch.object(SimpleRateThrottle, 'THROTTLE_RATES', rates)
        patcher.start()
        self.addCleanup(patcher.stop)

    def attempt_login(self, password='notogri', **extra):
        return self.client.post(self.TOKEN_URL, {'username': 'alice', 'password': password}, format='json', **extra)

    def basic(self, password):
        credentials = base64.b64encode(f'alice:{password}'.encode()).decode()
        self.client.credentials(HTTP_AUTHORIZATION=f'Basic {credentials}')
        return self.client.get('/api/users/me/')

    def assert_throttled(self, response):
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn('Retry-After', response.headers)
        self.assertRegex(response.data['detail'], r'^So‘rovlar soni chegaradan oshdi\. \d+ soniyadan keyin urinib ko‘ring\.$')

    def test_configured_rates(self):
        self.assertEqual(REAL_THROTTLE_RATES['anon'], '100/hour')
        self.assertEqual(REAL_THROTTLE_RATES['user'], '1000/hour')
        self.assertEqual(REAL_THROTTLE_RATES['login'], '5/minute')
        self.assertEqual(REAL_THROTTLE_RATES['register'], '5/minute')

    def test_login_limit_blocks_even_correct_password(self):
        for _ in range(5):
            self.assertEqual(self.attempt_login().status_code, status.HTTP_401_UNAUTHORIZED)
        self.assert_throttled(self.attempt_login(STRONG_PASSWORD))

    def test_login_limit_is_per_ip(self):
        for _ in range(5):
            self.attempt_login()
        self.assert_throttled(self.attempt_login())
        self.assertEqual(self.attempt_login(STRONG_PASSWORD, REMOTE_ADDR='10.0.0.2').status_code, status.HTTP_200_OK)

    def test_spoofed_forwarded_header_does_not_bypass(self):
        for number in range(5):
            self.attempt_login(HTTP_X_FORWARDED_FOR=f'1.2.3.{number}')
        self.assert_throttled(self.attempt_login(HTTP_X_FORWARDED_FOR='9.9.9.9'))

    def test_register_limit(self):
        for number in range(5):
            response = self.client.post(self.REGISTER_URL, {
                'username': f'yangi{number}', 'password': STRONG_PASSWORD, 'password2': STRONG_PASSWORD,
            }, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.post(self.REGISTER_URL, {
            'username': 'yangi9', 'password': STRONG_PASSWORD, 'password2': STRONG_PASSWORD,
        }, format='json')
        self.assert_throttled(response)
        self.assertFalse(User.objects.filter(username='yangi9').exists())

    def test_login_and_register_have_separate_limits(self):
        for _ in range(5):
            self.attempt_login()
        self.assert_throttled(self.attempt_login())
        response = self.client.post(self.REGISTER_URL, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_limit_blocks_guessing(self):
        self.client.force_authenticate(user=self.alice)
        url = '/api/auth/change-password/'
        def data(old):
            return {'old_password': old, 'new_password': NEW_PASSWORD, 'new_password2': NEW_PASSWORD}
        for _ in range(5):
            self.assertEqual(self.client.post(url, data('notogri'), format='json').status_code, status.HTTP_400_BAD_REQUEST)
        self.assert_throttled(self.client.post(url, data(STRONG_PASSWORD), format='json'))
        self.alice.refresh_from_db()
        self.assertTrue(self.alice.check_password(STRONG_PASSWORD))

    def test_anon_rate(self):
        self.use_rates({**REAL_THROTTLE_RATES, 'anon': '3/minute'})
        for _ in range(3):
            self.assertEqual(self.client.get('/api/menu/').status_code, status.HTTP_200_OK)
        self.assert_throttled(self.client.get('/api/menu/'))

    def test_user_rate_is_per_user(self):
        self.use_rates({**REAL_THROTTLE_RATES, 'user': '3/minute'})
        self.client.force_authenticate(user=self.alice)
        for _ in range(3):
            self.assertEqual(self.client.get('/api/menu/').status_code, status.HTTP_200_OK)
        self.assert_throttled(self.client.get('/api/menu/'))
        self.client.force_authenticate(user=self.bob)
        self.assertEqual(self.client.get('/api/menu/').status_code, status.HTTP_200_OK)

    def test_basic_auth_guessing_is_limited(self):
        for _ in range(5):
            self.assertEqual(self.basic('notogri').status_code, status.HTTP_401_UNAUTHORIZED)
        # To'g'ri parol ham rad etiladi: aks holda tanlash davom etaverardi.
        self.assert_throttled(self.basic(STRONG_PASSWORD))

    def test_basic_auth_shares_limit_with_token_endpoint(self):
        for _ in range(5):
            self.attempt_login()
        self.assert_throttled(self.basic('notogri'))

    def test_correct_basic_auth_is_not_counted(self):
        for _ in range(8):
            self.assertEqual(self.basic(STRONG_PASSWORD).status_code, status.HTTP_200_OK)


class UzbekMessageTests(UserAPITestBase):
    def test_blacklisted_refresh(self):
        tokens = self.obtain().data
        self.refresh(tokens['refresh'])
        response = self.refresh(tokens['refresh'])
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['detail'], 'Token bekor qilingan.')
        self.assertEqual(response.data['code'], 'token_not_valid')   # dastur uchun kod o'zgarmaydi

    def test_invalid_token_on_verify(self):
        response = self.client.post('/api/token/verify/', {'token': 'buzilgan'}, format='json')
        self.assertEqual(response.data['detail'], 'Token noto‘g‘ri.')

    def test_blacklisted_token_on_verify(self):
        tokens = self.obtain().data
        self.refresh(tokens['refresh'])
        response = self.client.post('/api/token/verify/', {'token': tokens['refresh']}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['non_field_errors'], ['Token bekor qilingan.'])

    def test_expired_token(self):
        token = AccessToken.for_user(self.alice)
        token.set_exp(lifetime=-timedelta(minutes=1))
        response = self.client.post('/api/token/verify/', {'token': str(token)}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['detail'], 'Token muddati o‘tgan.')

    def test_bad_bearer_translates_nested_messages(self):
        self.bearer('buzilgan.token.qiymat')
        response = self.client.get('/api/users/me/')
        self.assertEqual(response.data['detail'], 'Token hech qaysi token turiga mos kelmaydi.')
        self.assertEqual(response.data['code'], 'token_not_valid')
        self.assertEqual(response.data['messages'][0]['message'], 'Token noto‘g‘ri.')
        self.assertEqual(response.data['messages'][0]['token_type'], 'access')

    def test_wrong_login(self):
        response = self.obtain(password='notogri')
        self.assertEqual(response.data['detail'], 'Login yoki parol noto‘g‘ri, yoki hisob faol emas.')

    def test_no_credentials(self):
        self.assertEqual(self.client.get('/api/users/me/').data['detail'], 'Login ma’lumotlari yuborilmagan.')

    def test_inactive_user(self):
        tokens = self.obtain().data
        User.objects.filter(pk=self.alice.pk).update(is_active=False)
        self.bearer(tokens['access'])
        response = self.client.get('/api/users/me/')
        self.assertEqual(response.data['detail'], 'Foydalanuvchi faol emas.')

    def test_wrong_basic_password(self):
        credentials = base64.b64encode(b'alice:notogri').decode()
        self.client.credentials(HTTP_AUTHORIZATION=f'Basic {credentials}')
        self.assertEqual(self.client.get('/api/users/me/').data['detail'], 'Login yoki parol noto‘g‘ri.')

    def test_translate_helpers(self):
        self.assertEqual(translate("Token has no 'jti' claim"), 'Tokenda «jti» maydoni yo‘q.')
        self.assertEqual(translate("Token 'exp' claim has expired"), 'Tokenning «exp» maydoni muddati o‘tgan.')
        self.assertEqual(translate('Boshqa matn'), 'Boshqa matn')
        self.assertEqual(
            translate_data({'code': 'Token is invalid', 'a': ['Token is expired'], 'n': 1}),
            {'code': 'Token is invalid', 'a': ['Token muddati o‘tgan.'], 'n': 1},
        )

    def test_project_messages_untouched(self):
        self.login_as()
        response = self.client.get(f'/api/users/{self.bob.pk}/')
        self.assertEqual(response.data['detail'], 'Bu amal faqat hisob egasi yoki administrator uchun ruxsat etilgan.')


class ProductAPITests(APITestCase):
    URL = '/api/products/'

    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user('owner', password='x')
        cls.other = User.objects.create_user('other', password='x')
        cls.admin = User.objects.create_user('boss', password='x')
        Profile.objects.create(user=cls.admin, role=Profile.ADMIN)
        cls.waiter = User.objects.create_user('ofitsiant', password='x')
        Profile.objects.create(user=cls.waiter, role=Profile.WAITER)
        cls.root = User.objects.create_superuser('root', password='x')
        cls.product = Product.objects.create(
            name='Non', description='Tandir noni', price=Decimal('5000'), quantity=20, created_by=cls.owner,
        )
        cls.detail_url = f'{cls.URL}{cls.product.pk}/'

    def valid_payload(self, **overrides):
        data = {'name': 'Choy', 'description': 'Ko‘k choy', 'price': '12000.50', 'quantity': 3}
        data.update(overrides)
        return data

    def image_file(self, fmt='PNG', name='a.png', padding=0):
        buffer = io.BytesIO()
        Image.new('RGB', (2, 2)).save(buffer, format=fmt)
        return SimpleUploadedFile(name, buffer.getvalue() + b'\0' * padding, f'image/{fmt.lower()}')

    # --- Anonim ---

    def test_anonymous_list_is_short(self):
        response = self.client.get(self.URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item = response.data['results'][0]
        self.assertEqual(set(item), {'id', 'name', 'price', 'image'})
        self.assertEqual(item['name'], 'Non')
        self.assertEqual(item['price'], '5000.00')

    def test_hidden_products_are_not_in_public_list_or_detail(self):
        hidden = Product.objects.create(name='Yashirin', price=Decimal('1'), is_active=False, created_by=self.owner)
        self.assertNotIn('Yashirin', self.names())
        for user, expected in ((None, status.HTTP_401_UNAUTHORIZED), (self.owner, status.HTTP_404_NOT_FOUND), (self.admin, status.HTTP_404_NOT_FOUND), (self.root, status.HTTP_404_NOT_FOUND)):
            with self.subTest(user=getattr(user, 'username', 'anonymous')):
                self.client.force_authenticate(user=user)
                self.assertEqual(self.client.get(f'{self.URL}{hidden.pk}/').status_code, expected)

    def test_anonymous_cannot_read_detail_or_write(self):
        self.assertEqual(self.client.get(self.detail_url).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.post(self.URL, self.valid_payload(), format='json').status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.patch(self.detail_url, {'name': 'X'}, format='json').status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.put(self.detail_url, self.valid_payload(), format='json').status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.delete(self.detail_url).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.options(self.detail_url).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Product.objects.count(), 1)

    # --- Login qilgan ---

    def test_authenticated_detail_has_all_fields(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data), {
            'id', 'name', 'description', 'price', 'quantity', 'image', 'is_active', 'created_by', 'created_at', 'updated_at',
        })
        self.assertTrue(response.data['is_active'])
        self.assertEqual(response.data['created_by'], 'owner')
        self.assertEqual(response.data['quantity'], 20)
        self.assertEqual(response.data['description'], 'Tandir noni')

    def test_list_stays_short_when_logged_in(self):
        self.client.force_authenticate(user=self.owner)
        self.assertEqual(set(self.client.get(self.URL).data['results'][0]), {'id', 'name', 'price', 'image'})

    def test_create_forces_created_by_and_read_only_fields(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.post(self.URL, self.valid_payload(
            created_by=self.owner.pk, id=999, created_at='2000-01-01T00:00:00Z',
        ), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data['created_by'], 'other')
        self.assertNotEqual(response.data['id'], 999)
        product = Product.objects.get(pk=response.data['id'])
        self.assertEqual(product.created_by, self.other)
        self.assertEqual(product.price, Decimal('12000.50'))
        self.assertGreater(product.created_at.year, 2000)

    def test_any_role_can_create(self):
        self.client.force_authenticate(user=self.waiter)
        self.assertEqual(self.client.post(self.URL, self.valid_payload(), format='json').status_code, status.HTTP_201_CREATED)

    # --- Boshqaning mahsuloti ---

    def test_other_user_cannot_change(self):
        self.client.force_authenticate(user=self.other)
        for response in (
            self.client.put(self.detail_url, self.valid_payload(), format='json'),
            self.client.patch(self.detail_url, {'name': 'Buzildi'}, format='json'),
        ):
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
            self.assertEqual(response.data['detail'], 'Bu mahsulotni faqat uni yaratgan foydalanuvchi yoki administrator o‘zgartira oladi.')
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, 'Non')

    def test_non_admin_staff_role_cannot_change_others(self):
        self.client.force_authenticate(user=self.waiter)
        self.assertEqual(self.client.patch(self.detail_url, {'name': 'X'}, format='json').status_code, status.HTTP_403_FORBIDDEN)

    def test_missing_product_is_404(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(f'{self.URL}999999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['detail'], 'Yozuv topilmadi.')

    # --- Egasi ---

    def test_owner_put(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.put(self.detail_url, self.valid_payload(name='Yangi non'), format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, 'Yangi non')
        self.assertEqual(self.product.quantity, 3)

    def test_put_requires_name_and_price(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.put(self.detail_url, {'description': 'faqat tavsif'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)
        self.assertIn('price', response.data)

    def test_owner_patch_changes_only_sent_field(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(self.detail_url, {'quantity': 7}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity, 7)
        self.assertEqual(self.product.name, 'Non')

    def test_regular_user_cannot_change_is_active(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(self.detail_url, {'is_active': False}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertTrue(self.product.is_active)

    def test_ownership_cannot_be_transferred(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(self.detail_url, {'created_by': self.other.pk}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.created_by, self.owner)

    def test_delete_on_public_url_is_405_for_everyone(self):
        for user in (self.owner, self.other, self.admin, self.root):
            with self.subTest(user=user.username):
                self.client.force_authenticate(user=user)
                response = self.client.delete(self.detail_url)
                self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
                self.assertNotIn('DELETE', response.headers['Allow'])
                self.assertEqual(response.data['detail'], '«DELETE» metodi ruxsat etilmagan.')
        self.assertTrue(Product.objects.filter(pk=self.product.pk).exists())

    # --- Admin ---

    def test_admin_role_and_superuser_can_change_others(self):
        for user in (self.admin, self.root):
            with self.subTest(user=user.username):
                product = Product.objects.create(name='Tahrir', price=Decimal('1'), created_by=self.owner)
                url = f'{self.URL}{product.pk}/'
                self.client.force_authenticate(user=user)
                response = self.client.patch(url, {'name': 'Admin tahriri'}, format='json')
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.data['created_by'], 'owner')   # egasi o'zgarmaydi
                product.refresh_from_db()
                self.assertEqual(product.name, 'Admin tahriri')

    def test_admin_role_and_superuser_can_hide_and_unhide(self):
        for user in (self.admin, self.root):
            with self.subTest(user=user.username):
                product = Product.objects.create(name='Yashiriladigan', price=Decimal('1'), created_by=self.owner)
                self.client.force_authenticate(user=user)
                response = self.client.post(f'{self.URL}{product.pk}/hide/')
                self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
                product.refresh_from_db()
                self.assertFalse(product.is_active)
                self.assertEqual(self.client.get(f'{self.URL}{product.pk}/').status_code, status.HTTP_404_NOT_FOUND)

                response = self.client.post(f'{self.URL}{product.pk}/unhide/')
                self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
                product.refresh_from_db()
                self.assertTrue(product.is_active)

    def test_only_admin_and_superuser_can_hide_or_unhide(self):
        for user, expected in ((self.owner, status.HTTP_403_FORBIDDEN), (self.other, status.HTTP_403_FORBIDDEN), (None, status.HTTP_401_UNAUTHORIZED)):
            with self.subTest(user=getattr(user, 'username', 'anonymous')):
                self.client.force_authenticate(user=user)
                self.assertEqual(self.client.post(f'{self.detail_url}hide/').status_code, expected)
                self.assertEqual(self.client.post(f'{self.detail_url}unhide/').status_code, expected)
        self.assertTrue(self.product.is_active)

    def test_admin_can_set_is_active_directly(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(self.detail_url, {'is_active': False}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertFalse(self.product.is_active)

    # --- Validatsiya ---

    def assert_invalid(self, field, **overrides):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(self.URL, self.valid_payload(**overrides), format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(field, response.data)

    def test_negative_price(self):
        self.assert_invalid('price', price='-1')
        response = self.client.post(self.URL, self.valid_payload(price='-1'), format='json')
        self.assertEqual(response.data['price'], ['Qiymat 0 dan kichik bo‘lmasin.'])

    def test_zero_price_allowed(self):
        self.client.force_authenticate(user=self.owner)
        self.assertEqual(self.client.post(self.URL, self.valid_payload(price='0'), format='json').status_code, status.HTTP_201_CREATED)

    def test_blank_name(self):
        self.assert_invalid('name', name='')
        self.assert_invalid('name', name='   ')

    def test_negative_quantity(self):
        self.assert_invalid('quantity', quantity=-1)

    def test_price_too_large(self):
        self.assert_invalid('price', price='12345678901.00')

    def post_image(self, image):
        self.client.force_authenticate(user=self.owner)
        return self.client.post(self.URL, {**self.valid_payload(), 'image': image}, format='multipart')

    def test_wrong_image_format(self):
        response = self.post_image(self.image_file('GIF', 'a.gif'))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('image', response.data)

    def test_fake_image_renamed_to_png(self):
        response = self.post_image(SimpleUploadedFile('virus.png', b'bu rasm emas', 'image/png'))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('image', response.data)

    def test_image_too_big(self):
        response = self.post_image(self.image_file(padding=3 * 1024 * 1024))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('image', response.data)

    def test_valid_image_upload(self):
        with tempfile.TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media):
            response = self.post_image(self.image_file())
            self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
            self.assertIn('/media/products/', response.data['image'])
            listed = self.client.get(self.URL).data['results'][0]
            self.assertEqual(listed['image'], response.data['image'])

    # --- Qidiruv, saralash, filtr ---

    def names(self, **params):
        return [p['name'] for p in self.client.get(self.URL, params).data['results']]

    def make_catalog(self):
        Product.objects.create(name='Asal', description='Tog‘ asali', price=Decimal('90000'), created_by=self.other)
        Product.objects.create(name='Zira', description='Ziravor', price=Decimal('100'), created_by=self.other)

    def test_search(self):
        self.make_catalog()
        self.assertEqual(self.names(search='asal'), ['Asal'])
        self.assertEqual(self.names(search='Tandir'), ['Non'])
        self.assertEqual(self.names(search='yo‘q narsa'), [])

    def test_ordering(self):
        self.make_catalog()
        self.assertEqual(self.names(ordering='price'), ['Zira', 'Non', 'Asal'])
        self.assertEqual(self.names(ordering='-price'), ['Asal', 'Non', 'Zira'])
        self.assertEqual(self.names(ordering='name'), ['Asal', 'Non', 'Zira'])

    def test_default_order_is_newest_first(self):
        self.make_catalog()
        self.assertEqual(self.names(), ['Zira', 'Asal', 'Non'])

    def test_filter_by_creator(self):
        self.make_catalog()
        self.assertEqual(self.names(created_by=self.owner.pk), ['Non'])

    # --- Admin panel ---

    def test_admin_add_sets_created_by(self):
        self.client.force_login(self.root)
        response = self.client.post(reverse('admin:api_product_add'), {
            'name': 'Paneldan', 'description': '', 'price': '100', 'quantity': 1,
        })
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(Product.objects.get(name='Paneldan').created_by, self.root)
        self.assertEqual(self.client.get(reverse('admin:api_product_changelist')).status_code, status.HTTP_200_OK)

    def test_admin_edit_keeps_created_by(self):
        self.client.force_login(self.root)
        response = self.client.post(reverse('admin:api_product_change', args=[self.product.pk]), {
            'name': 'Tahrirlandi', 'description': '', 'price': '100', 'quantity': 1,
        })
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, 'Tahrirlandi')
        self.assertEqual(self.product.created_by, self.owner)

    def test_creator_with_products_is_protected(self):
        with self.assertRaises(ProtectedError):
            self.owner.delete()


class MyProductTests(APITestCase):
    URL = '/api/users/me/products/'

    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user('owner', password='x')
        cls.other = User.objects.create_user('other', password='x')
        cls.admin = User.objects.create_user('boss', password='x')
        Profile.objects.create(user=cls.admin, role=Profile.ADMIN)
        cls.root = User.objects.create_superuser('root', password='x')
        cls.mine = Product.objects.create(name='Asal', description='Tog‘ asali', price=Decimal('90000'), created_by=cls.owner)
        cls.mine2 = Product.objects.create(name='Zira', price=Decimal('100'), created_by=cls.owner)
        cls.foreign = Product.objects.create(name='Begona', price=Decimal('5'), created_by=cls.other)

    def url(self, product):
        return f'{self.URL}{product.pk}/'

    def names(self, **params):
        return [p['name'] for p in self.client.get(self.URL, params).data['results']]

    def image_upload(self, name='a.png'):
        buffer = io.BytesIO()
        Image.new('RGB', (2, 2)).save(buffer, format='PNG')
        return SimpleUploadedFile(name, buffer.getvalue(), 'image/png')

    def test_anonymous_rejected(self):
        self.assertEqual(self.client.get(self.URL).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.get(self.url(self.mine)).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.delete(self.url(self.mine)).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(Product.objects.filter(pk=self.mine.pk).exists())

    def test_list_shows_only_own_with_full_fields(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(self.URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual({p['name'] for p in response.data['results']}, {'Asal', 'Zira'})
        self.assertIn('quantity', response.data['results'][0])
        self.assertEqual(response.data['results'][0]['created_by'], 'owner')

    def test_owner_list_includes_hidden_products_and_is_active(self):
        self.mine2.is_active = False
        self.mine2.save(update_fields=['is_active'])
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(self.URL)
        self.assertEqual(response.data['count'], 2)
        by_name = {item['name']: item for item in response.data['results']}
        self.assertTrue(by_name['Asal']['is_active'])
        self.assertFalse(by_name['Zira']['is_active'])

    def test_admin_list_is_also_only_own(self):
        for user in (self.admin, self.root):
            self.client.force_authenticate(user=user)
            self.assertEqual(self.names(), [])

    def test_search_ordering_pagination(self):
        self.client.force_authenticate(user=self.owner)
        self.assertEqual(self.names(search='asal'), ['Asal'])
        self.assertEqual(self.names(search='Begona'), [])
        self.assertEqual(self.names(ordering='price'), ['Zira', 'Asal'])
        self.assertEqual(self.names(ordering='-price'), ['Asal', 'Zira'])
        for number in range(10):
            Product.objects.create(name=f'P{number}', price=Decimal('1'), created_by=self.owner)
        first = self.client.get(self.URL).data
        self.assertEqual(first['count'], 12)
        self.assertEqual(len(first['results']), 10)
        self.assertEqual(len(self.client.get(self.URL, {'page': 2}).data['results']), 2)

    def test_retrieve_own(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(self.url(self.mine))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['description'], 'Tog‘ asali')

    def test_foreign_product_is_404_for_everyone(self):
        for user in (self.owner, self.admin, self.root):
            with self.subTest(user=user.username):
                self.client.force_authenticate(user=user)
                url = self.url(self.foreign)
                self.assertEqual(self.client.get(url).status_code, status.HTTP_404_NOT_FOUND)
                self.assertEqual(self.client.delete(url).status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Product.objects.filter(pk=self.foreign.pk).exists())

    def test_foreign_and_missing_products_look_the_same(self):
        self.client.force_authenticate(user=self.owner)
        foreign = self.client.delete(self.url(self.foreign))
        missing = self.client.delete(f'{self.URL}999999/')
        self.assertEqual(foreign.status_code, missing.status_code)
        self.assertEqual(foreign.data, missing.data)

    def test_owner_deletes_own(self):
        self.client.force_authenticate(user=self.owner)
        self.assertEqual(self.client.delete(self.url(self.mine)).status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Product.objects.filter(pk=self.mine.pk).exists())
        self.assertTrue(Product.objects.filter(pk=self.mine2.pk).exists())
        self.assertEqual(self.client.delete(self.url(self.mine)).status_code, status.HTTP_404_NOT_FOUND)

    def test_superuser_deletes_only_own_product(self):
        product = Product.objects.create(name='Rootniki', price=Decimal('1'), created_by=self.root)
        self.client.force_authenticate(user=self.root)
        self.assertEqual(self.client.delete(self.url(product)).status_code, status.HTTP_204_NO_CONTENT)

    def test_admin_role_deletes_only_own_product(self):
        product = Product.objects.create(name='Adminniki', price=Decimal('1'), created_by=self.admin)
        self.client.force_authenticate(user=self.admin)
        self.assertEqual(self.client.delete(self.url(product)).status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.client.delete(self.url(self.foreign)).status_code, status.HTTP_404_NOT_FOUND)

    def test_no_write_methods(self):
        self.client.force_authenticate(user=self.owner)
        self.assertEqual(self.client.post(self.URL, {'name': 'X', 'price': '1'}, format='json').status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(self.client.patch(self.url(self.mine), {'name': 'X'}, format='json').status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_protected_error_is_400(self):
        self.client.force_authenticate(user=self.owner)
        with mock.patch.object(Product, 'delete', side_effect=ProtectedError('x', set())):
            response = self.client.delete(self.url(self.mine))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('o‘chirib bo‘lmaydi', response.data['detail'])

    def test_delete_removes_image_file(self):
        with tempfile.TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media):
            self.client.force_authenticate(user=self.owner)
            response = self.client.post('/api/products/', {'name': 'Rasmli', 'price': '1', 'image': self.image_upload()}, format='multipart')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
            product = Product.objects.get(pk=response.data['id'])
            path = product.image.path
            self.assertTrue(path.startswith(media))
            self.assertTrue(os.path.exists(path))

            with self.captureOnCommitCallbacks(execute=True):
                self.assertEqual(self.client.delete(self.url(product)).status_code, status.HTTP_204_NO_CONTENT)
            self.assertFalse(os.path.exists(path))

    def test_replacing_image_deletes_old_file(self):
        with tempfile.TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media):
            self.client.force_authenticate(user=self.owner)
            created = self.client.post('/api/products/', {'name': 'Rasmli', 'price': '1', 'image': self.image_upload('old.png')}, format='multipart')
            product = Product.objects.get(pk=created.data['id'])
            old_path = product.image.path
            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.patch(f'/api/products/{product.pk}/', {'image': self.image_upload('new.png')}, format='multipart')
            self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
            self.assertFalse(os.path.exists(old_path))
            product.refresh_from_db()
            new_path = product.image.path
            self.assertTrue(os.path.exists(new_path))
            self.assertNotEqual(old_path, new_path)

    def test_put_replacing_image_deletes_old_file(self):
        with tempfile.TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media):
            self.client.force_authenticate(user=self.owner)
            created = self.client.post('/api/products/', {'name': 'Rasmli', 'price': '1', 'image': self.image_upload('old.png')}, format='multipart')
            product = Product.objects.get(pk=created.data['id'])
            old_path = product.image.path
            payload = {'name': 'Rasmli', 'description': '', 'price': '1', 'quantity': 0, 'image': self.image_upload('put-new.png')}
            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.put(f'/api/products/{product.pk}/', payload, format='multipart')
            self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
            self.assertFalse(os.path.exists(old_path))
            product.refresh_from_db()
            self.assertTrue(os.path.exists(product.image.path))

    def test_patch_null_image_removes_file(self):
        with tempfile.TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media):
            self.client.force_authenticate(user=self.owner)
            created = self.client.post('/api/products/', {'name': 'Rasmli', 'price': '1', 'image': self.image_upload()}, format='multipart')
            product = Product.objects.get(pk=created.data['id'])
            old_path = product.image.path
            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.patch(f'/api/products/{product.pk}/', {'image': None}, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
            self.assertIsNone(response.data['image'])
            self.assertFalse(os.path.exists(old_path))
            product.refresh_from_db()
            self.assertFalse(product.image)

    def test_failed_attempts_keep_image_file(self):
        with tempfile.TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media):
            self.client.force_authenticate(user=self.owner)
            response = self.client.post('/api/products/', {'name': 'Rasmli', 'price': '1', 'image': self.image_upload()}, format='multipart')
            product = Product.objects.get(pk=response.data['id'])
            path = product.image.path

            self.client.force_authenticate(user=self.root)
            with self.captureOnCommitCallbacks(execute=True):
                self.assertEqual(self.client.delete(self.url(product)).status_code, status.HTTP_404_NOT_FOUND)
                self.assertEqual(self.client.delete(f'/api/products/{product.pk}/').status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
            self.assertTrue(os.path.exists(path))

    def test_rolled_back_delete_keeps_image_file(self):
        with tempfile.TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media):
            self.client.force_authenticate(user=self.owner)
            response = self.client.post('/api/products/', {'name': 'Rasmli', 'price': '1', 'image': self.image_upload()}, format='multipart')
            product = Product.objects.get(pk=response.data['id'])
            path = product.image.path

            with self.captureOnCommitCallbacks(execute=True):
                with self.assertRaises(ValueError), transaction.atomic():
                    product.delete()
                    raise ValueError
            self.assertTrue(os.path.exists(path))
            self.assertTrue(Product.objects.filter(name='Rasmli').exists())

    def test_product_without_image_deletes_cleanly(self):
        self.client.force_authenticate(user=self.owner)
        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            self.assertEqual(self.client.delete(self.url(self.mine)).status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(callbacks, [])

    def test_schema_has_expected_methods(self):
        schema = self.client.get('/api/schema/', {'format': 'json'}).data['paths']
        self.assertNotIn('delete', schema['/api/products/{id}/'])
        self.assertEqual(set(schema['/api/users/me/products/{id}/']), {'get', 'delete'})
        self.assertEqual(schema['/api/users/me/products/{id}/']['delete']['tags'], ['users'])


class ProductAdminDeleteTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.root = User.objects.create_superuser('root', password='x')
        cls.product = Product.objects.create(name='Non', price=Decimal('1'), created_by=cls.root)

    def setUp(self):
        self.client.force_login(self.root)

    def test_delete_page_is_403_even_for_own_product(self):
        url = reverse('admin:api_product_delete', args=[self.product.pk])
        self.assertEqual(self.client.get(url).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.post(url, {'post': 'yes'}).status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Product.objects.filter(pk=self.product.pk).exists())

    def test_delete_selected_action_is_gone(self):
        url = reverse('admin:api_product_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotContains(response, 'delete_selected')

        # Formani qo'lda yuborish ham ishlamaydi.
        self.client.post(url, {'action': 'delete_selected', '_selected_action': [self.product.pk], 'post': 'yes'})
        self.assertTrue(Product.objects.filter(pk=self.product.pk).exists())

    def test_change_page_has_no_delete_link(self):
        response = self.client.get(reverse('admin:api_product_change', args=[self.product.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotContains(response, 'deletelink')


class SeedTests(APITestCase):
    def test_seed_is_idempotent(self):
        out = io.StringIO()
        call_command('seed_restaurant', stdout=out)
        counts = (Category.objects.count(), MenuItem.objects.count(), Table.objects.count(), User.objects.count(), Profile.objects.count())
        self.assertEqual(counts[0], 4)
        self.assertEqual(counts[2], 8)
        self.assertEqual(counts[3], 3)
        for category in Category.objects.all():
            self.assertIn(category.items.count(), (3, 4))

        call_command('seed_restaurant', stdout=out)
        self.assertEqual(
            counts,
            (Category.objects.count(), MenuItem.objects.count(), Table.objects.count(), User.objects.count(), Profile.objects.count()),
        )
        self.assertTrue(User.objects.get(username='chef1').check_password('Restoran2026!'))
        self.assertEqual(User.objects.get(username='chef1').profile.role, Profile.CHEF)
