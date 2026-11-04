import io
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils import timezone
from PIL import Image
from rest_framework import status
from rest_framework.test import APITestCase

from restaurant.models import (
    Category, MenuItem, Order, OrderStatusEvent, Profile, Reservation, RestaurantSettings, Table,
)
from .models import Book

User = get_user_model()


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
