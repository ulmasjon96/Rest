from collections.abc import Mapping

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

from restaurant.models import (
    Category, MenuItem, Order, OrderItem, OrderStatusEvent, Profile, Reservation,
    RestaurantSettings, Table,
)
from .models import Book, Product
from .permissions import get_role


User = get_user_model()


def blacklist_user_tokens(user):
    """Foydalanuvchining barcha refresh tokenlarini bekor qiladi."""
    for token in OutstandingToken.objects.filter(user=user):
        BlacklistedToken.objects.get_or_create(token=token)


def check_password_strength(password, user, field='password'):
    """Django parol validatorlarini ishga tushiradi va xatoni 400 javobga aylantiradi."""
    try:
        validate_password(password, user=user)
    except DjangoValidationError as error:
        raise serializers.ValidationError({field: error.messages})


def check_email_is_free(email, exclude_pk=None):
    """Bo'sh bo'lmagan email boshqa foydalanuvchida bo'lmasin (katta-kichik harf farqsiz)."""
    if not email:
        return email
    others = User.objects.filter(email__iexact=email)
    if exclude_pk:
        others = others.exclude(pk=exclude_pk)
    if others.exists():
        raise serializers.ValidationError('Bu email boshqa foydalanuvchiga tegishli.')
    return email


def make_read_only(fields, *names):
    for name in names:
        fields[name].read_only = True
        fields[name].required = False


class RoleAwareMixin:
    @property
    def role(self):
        request = self.context.get('request')
        return get_role(request.user) if request else None


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'


class ProductListSerializer(serializers.ModelSerializer):
    """Ochiq ro'yxat uchun qisqa ko'rinish."""
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'image']


class ProductDetailSerializer(serializers.ModelSerializer):
    # id o'rniga username: yaratgan foydalanuvchi serverda request.user dan qo'yiladi.
    created_by = serializers.SlugRelatedField(slug_field='username', read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'quantity', 'image', 'created_by', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    """role, is_staff, is_superuser, is_active bu yerda o'zgarmaydi: yuborilgan qiymat e'tiborsiz qoldiriladi.

    Parol esa jimgina e'tiborsiz qoldirilmaydi: mijoz parol almashdi deb o'ylab qolmasligi uchun 400 qaytadi.
    """
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'is_active', 'date_joined', 'last_login',
        ]
        read_only_fields = ['is_active', 'date_joined', 'last_login']

    def get_role(self, obj) -> str:
        return get_role(obj)

    def to_internal_value(self, data):
        if isinstance(data, Mapping) and 'password' in data:
            raise serializers.ValidationError({'password': ['Parolni change-password orqali o‘zgartiring.']})
        return super().to_internal_value(data)

    def validate_email(self, value):
        return check_email_is_free(value, exclude_pk=getattr(self.instance, 'pk', None))


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, trim_whitespace=False, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, trim_whitespace=False, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'first_name', 'last_name']

    def validate_email(self, value):
        return check_email_is_free(value)

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password2': ['Parollar mos kelmadi.']})
        probe = User(**{name: value for name, value in attrs.items() if name not in ('password', 'password2')})
        check_password_strength(attrs['password'], probe)
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        with transaction.atomic():
            user = User.objects.create_user(**validated_data)
            Profile.objects.create(user=user, role=Profile.CUSTOMER)
        return user


class AuthResponseSerializer(serializers.Serializer):
    """Ro'yxatdan o'tish javobi (Swagger uchun)."""
    user = UserSerializer()
    access = serializers.CharField()
    refresh = serializers.CharField()


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, trim_whitespace=False, style={'input_type': 'password'})
    new_password = serializers.CharField(write_only=True, trim_whitespace=False, style={'input_type': 'password'})
    new_password2 = serializers.CharField(write_only=True, trim_whitespace=False, style={'input_type': 'password'})

    def validate_old_password(self, value):
        if not self.context['request'].user.check_password(value):
            raise serializers.ValidationError('Eski parol noto‘g‘ri.')
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({'new_password2': ['Yangi parollar mos kelmadi.']})
        check_password_strength(attrs['new_password'], self.context['request'].user, field='new_password')
        return attrs

    def save(self, **kwargs):
        user = self.context['request'].user
        with transaction.atomic():
            user.set_password(self.validated_data['new_password'])
            user.save(update_fields=['password'])
            blacklist_user_tokens(user)
        return user


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(write_only=True)


class DetailSerializer(serializers.Serializer):
    """Oddiy xabarli javob (Swagger uchun)."""
    detail = serializers.CharField()


class RestaurantSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = RestaurantSettings
        exclude = ['id']

    def validate(self, attrs):
        opens_at = attrs.get('opens_at', self.instance.opens_at)
        closes_at = attrs.get('closes_at', self.instance.closes_at)
        if closes_at <= opens_at:
            raise serializers.ValidationError({'closes_at': 'Yopilish vaqti ochilish vaqtidan keyin bo‘lsin.'})
        return attrs


class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    role_name = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = Profile
        fields = '__all__'


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class MenuItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = MenuItem
        fields = '__all__'


class MenuCategorySerializer(serializers.ModelSerializer):
    """GET /api/menu/ uchun: kategoriya ichida faqat mavjud taomlar."""
    items = MenuItemSerializer(many=True, read_only=True, source='available_items')

    class Meta:
        model = Category
        fields = ['id', 'name', 'order', 'items']


class TableSerializer(serializers.ModelSerializer):
    location_name = serializers.CharField(source='get_location_display', read_only=True)

    class Meta:
        model = Table
        fields = '__all__'


class TableAvailabilityQuerySerializer(serializers.Serializer):
    start = serializers.DateTimeField()
    guests = serializers.IntegerField(min_value=1)


class DailyReportQuerySerializer(serializers.Serializer):
    date = serializers.DateField(required=False)


class ReservationSerializer(RoleAwareMixin, serializers.ModelSerializer):
    table_number = serializers.IntegerField(source='table.number', read_only=True)
    status_name = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Reservation
        fields = '__all__'
        read_only_fields = ['end', 'created_by']

    def get_fields(self):
        fields = super().get_fields()
        # Waiter/admin mijozni tanlashi mumkin (yuborilmasa o'zi yoziladi), mijoz esa yo'q.
        fields['customer'].required = False
        if self.role == Profile.CUSTOMER:
            make_read_only(fields, 'customer', 'status')
        return fields

    def _merged(self, attrs, name):
        return attrs[name] if name in attrs else getattr(self.instance, name, None)

    def validate(self, attrs):
        table = self._merged(attrs, 'table')
        guests = self._merged(attrs, 'guests')
        start = self._merged(attrs, 'start')
        instance = self.instance

        # Faqat o'zgargan narsa tekshiriladi: aks holda o'tib ketgan bronning
        # holatini yoki izohini ham o'zgartirib bo'lmay qolardi.
        table_changed = instance is None or table != instance.table
        if table_changed and not table.active:
            raise serializers.ValidationError({'table': 'Bu stol hozir faol emas.'})
        if (table_changed or guests != instance.guests) and guests > table.seats:
            raise serializers.ValidationError({'guests': f'Bu stolga ko‘pi bilan {table.seats} kishi sig‘adi.'})
        if instance is None or start != instance.start:
            restaurant = RestaurantSettings.load()
            error = restaurant.booking_error(start)
            if error:
                raise serializers.ValidationError({'start': error})
            attrs['end'] = restaurant.reservation_end(start)
        return attrs

    def save(self, **kwargs):
        # Stol qatori qulflanadi: bir vaqtdagi ikki so'rov bitta stolni band qila olmasin.
        # Tekshiruv va saqlash bitta tranzaksiyada bo'lgani uchun validate() da emas, shu yerda.
        data = self.validated_data
        with transaction.atomic():
            table = Table.objects.select_for_update().get(pk=self._merged(data, 'table').pk)
            status = self._merged(data, 'status') or Reservation.PENDING
            if status not in Reservation.FREE_STATUSES:
                busy = Reservation.conflicts(
                    table, self._merged(data, 'start'), self._merged(data, 'end'),
                    exclude_pk=getattr(self.instance, 'pk', None),
                )
                if busy.exists():
                    raise serializers.ValidationError({'start': ['Bu stol shu vaqtda band.']})
            return super().save(**kwargs)


class OrderItemSerializer(serializers.ModelSerializer):
    menu_item_name = serializers.CharField(source='menu_item.name', read_only=True)
    # Narxlar faqat serverda: mijoz yuborgan qiymat e'tiborsiz qoldiriladi.
    unit_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    line_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'menu_item', 'menu_item_name', 'quantity', 'unit_price', 'line_total', 'note']

    def validate_menu_item(self, value):
        if not value.available or not value.category.active:
            raise serializers.ValidationError(f'«{value.name}» hozir mavjud emas.')
        return value


class OrderSerializer(RoleAwareMixin, serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, allow_empty=False)
    table_number = serializers.IntegerField(source='table.number', read_only=True, default=None)
    status_name = serializers.CharField(source='get_status_display', read_only=True)
    order_type_name = serializers.CharField(source='get_order_type_display', read_only=True)

    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['status', 'service_percent', 'subtotal', 'service_amount', 'total', 'paid_at']

    def get_fields(self):
        fields = super().get_fields()
        if self.instance is not None:
            fields['items'].required = False
        if self.role == Profile.CUSTOMER:
            make_read_only(fields, 'customer', 'waiter')
        elif self.role == Profile.WAITER:
            make_read_only(fields, 'waiter')
        return fields

    def _merged(self, attrs, name, default=None):
        return attrs[name] if name in attrs else getattr(self.instance, name, default)

    def validate(self, attrs):
        instance = self.instance
        if instance is not None:
            if 'items' in attrs:
                raise serializers.ValidationError({'items': 'Yaratilgan buyurtmaning taomlarini o‘zgartirib bo‘lmaydi.'})
            if instance.status in (Order.PAID, Order.CANCELLED):
                raise serializers.ValidationError('Yakunlangan buyurtmani o‘zgartirib bo‘lmaydi.')

        table = self._merged(attrs, 'table')
        order_type = self._merged(attrs, 'order_type', Order.DINE_IN)
        if order_type == Order.DINE_IN and table is None:
            raise serializers.ValidationError({'table': 'Restoran ichidagi buyurtma uchun stol majburiy.'})
        if 'table' in attrs and table is not None and not table.active:
            raise serializers.ValidationError({'table': 'Bu stol hozir faol emas.'})

        reservation = attrs.get('reservation')
        if reservation is not None:
            request = self.context['request']
            if self.role == Profile.CUSTOMER and reservation.customer_id != request.user.pk:
                raise serializers.ValidationError({'reservation': 'Bu bron sizga tegishli emas.'})
            if table is not None and reservation.table_id != table.pk:
                raise serializers.ValidationError({'reservation': 'Bron boshqa stolga qilingan.'})
        return attrs

    def create(self, validated_data):
        items = validated_data.pop('items')
        with transaction.atomic():
            order = Order.objects.create(**validated_data)
            for item in items:
                OrderItem.objects.create(order=order, **item)
            order.recalculate()
            OrderStatusEvent.objects.create(order=order, status=order.status, actor=self.context['request'].user)
        return order


class OrderStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.STATUSES)


class OrderStatusEventSerializer(serializers.ModelSerializer):
    status_name = serializers.CharField(source='get_status_display', read_only=True)
    actor_username = serializers.CharField(source='actor.username', read_only=True, default=None)

    class Meta:
        model = OrderStatusEvent
        fields = '__all__'


class TopItemSerializer(serializers.Serializer):
    menu_item = serializers.IntegerField()
    name = serializers.CharField()
    quantity = serializers.IntegerField()
    revenue = serializers.DecimalField(max_digits=14, decimal_places=2)


class DailyReportSerializer(serializers.Serializer):
    date = serializers.DateField()
    orders_count = serializers.IntegerField()
    paid_orders_count = serializers.IntegerField()
    paid_total = serializers.DecimalField(max_digits=14, decimal_places=2)
    top_items = TopItemSerializer(many=True)
