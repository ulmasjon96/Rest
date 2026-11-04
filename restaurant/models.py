from datetime import time, timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models, transaction
from django.db.models import F, Q, Sum
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

validate_phone = RegexValidator(r'^\+?[0-9\s\-()]{7,20}$', _('Telefon raqami noto‘g‘ri.'))


def validate_image(value):
    """Hajm 3 MB gacha va fayl mazmuni haqiqiy JPEG, PNG yoki WebP bo'lsin."""
    from PIL import Image
    if value.size > 3 * 1024 * 1024:
        raise ValidationError(_('Rasm 3 MB dan kichik bo‘lishi kerak.'))
    try:
        image = Image.open(value)
        if image.format not in ('JPEG', 'PNG', 'WEBP'):
            raise ValueError
        image.verify()
        value.seek(0)
    except Exception:
        raise ValidationError(_('Faqat haqiqiy JPEG, PNG yoki WebP rasmini yuklang.'))


class Timestamped(models.Model):
    created_at = models.DateTimeField(_('Yaratilgan sana'), default=timezone.now, editable=False)
    updated_at = models.DateTimeField(_('Yangilangan sana'), auto_now=True)

    class Meta:
        abstract = True


class RestaurantSettings(Timestamped):
    name = models.CharField(_('Restoran nomi'), max_length=150, default='Restoran')
    phone = models.CharField(_('Telefon'), max_length=25, blank=True, validators=[validate_phone])
    address = models.CharField(_('Manzil'), max_length=250, blank=True)
    logo = models.ImageField(_('Logotip'), upload_to='restaurant/', blank=True, validators=[validate_image])
    opens_at = models.TimeField(_('Ochilish vaqti'), default=time(10))
    closes_at = models.TimeField(_('Yopilish vaqti'), default=time(23))
    reservation_duration = models.PositiveSmallIntegerField(
        _('Bron davomiyligi (daqiqa)'), default=120,
        validators=[MinValueValidator(15), MaxValueValidator(720)],
    )
    booking_days = models.PositiveSmallIntegerField(
        _('Oldindan bron qilish (kun)'), default=30,
        validators=[MinValueValidator(1), MaxValueValidator(365)],
    )
    service_percent = models.DecimalField(
        _('Xizmat haqi (%)'), max_digits=5, decimal_places=2, default=Decimal('10.00'),
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('30'))],
    )

    class Meta:
        verbose_name = _('Restoran sozlamalari')
        verbose_name_plural = _('Restoran sozlamalari')
        constraints = [models.CheckConstraint(condition=Q(id=1), name='single_restaurant_settings')]

    def __str__(self):
        return self.name

    def clean(self):
        if self.opens_at and self.closes_at and self.closes_at <= self.opens_at:
            raise ValidationError(_('Yopilish vaqti ochilish vaqtidan keyin bo‘lsin.'))

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        return cls.objects.get_or_create(pk=1)[0]

    def reservation_end(self, start):
        return start + timedelta(minutes=self.reservation_duration)

    def booking_error(self, start):
        """Bron vaqti qoidaga zid bo'lsa xato matnini, aks holda None qaytaradi."""
        now = timezone.now()
        if start < now:
            return _('O‘tgan vaqtga bron qilib bo‘lmaydi.')
        if start > now + timedelta(days=self.booking_days):
            return _('%(days)s kundan uzoq muddatga bron qilib bo‘lmaydi.') % {'days': self.booking_days}
        local_start = timezone.localtime(start)
        local_end = timezone.localtime(self.reservation_end(start))
        if (
            local_start.time() < self.opens_at
            or local_end.date() != local_start.date()
            or local_end.time() > self.closes_at
        ):
            return _('Bron ish vaqti ichida bo‘lsin (%(opens)s–%(closes)s).') % {
                'opens': self.opens_at.strftime('%H:%M'),
                'closes': self.closes_at.strftime('%H:%M'),
            }
        return None


def current_service_percent():
    return RestaurantSettings.load().service_percent


class Profile(Timestamped):
    ADMIN = 'admin'
    WAITER = 'waiter'
    CHEF = 'chef'
    CUSTOMER = 'customer'
    ROLES = [
        (ADMIN, _('Administrator')),
        (WAITER, _('Ofitsiant')),
        (CHEF, _('Oshpaz')),
        (CUSTOMER, _('Mijoz')),
    ]
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='profile', verbose_name=_('Foydalanuvchi'),
    )
    role = models.CharField(_('Rol'), max_length=10, choices=ROLES, default=CUSTOMER)
    phone = models.CharField(_('Telefon'), max_length=25, blank=True, validators=[validate_phone])

    class Meta:
        verbose_name = _('Profil')
        verbose_name_plural = _('Profillar')
        ordering = ['user__username']

    def __str__(self):
        return f'{self.user} — {self.get_role_display()}'


class Category(Timestamped):
    name = models.CharField(_('Nomi'), max_length=120, unique=True)
    order = models.PositiveSmallIntegerField(_('Tartib raqami'), default=0)
    active = models.BooleanField(_('Faol'), default=True)

    class Meta:
        verbose_name = _('Kategoriya')
        verbose_name_plural = _('Kategoriyalar')
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class MenuItem(Timestamped):
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name='items', verbose_name=_('Kategoriya'),
    )
    name = models.CharField(_('Nomi'), max_length=150)
    description = models.TextField(_('Tavsif'), blank=True)
    price = models.DecimalField(
        _('Narxi (so‘m)'), max_digits=12, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    image = models.ImageField(_('Rasm'), upload_to='menu/', blank=True, validators=[validate_image])
    preparation_minutes = models.PositiveSmallIntegerField(_('Tayyorlash vaqti (daqiqa)'), default=15)
    available = models.BooleanField(_('Mavjud'), default=True)
    is_vegetarian = models.BooleanField(_('Vegetarian'), default=False)
    spicy = models.BooleanField(_('Achchiq'), default=False)

    class Meta:
        verbose_name = _('Taom')
        verbose_name_plural = _('Taomlar')
        ordering = ['category__order', 'name']
        constraints = [
            models.UniqueConstraint(fields=['category', 'name'], name='unique_menu_item_in_category'),
            models.CheckConstraint(
                condition=Q(price__gt=0), name='menu_item_price_positive',
                violation_error_message=_('Narx 0 dan katta bo‘lsin.'),
            ),
        ]

    def __str__(self):
        return self.name


class Table(Timestamped):
    HALL = 'hall'
    TERRACE = 'terrace'
    VIP = 'vip'
    LOCATIONS = [
        (HALL, _('Zal')),
        (TERRACE, _('Teras')),
        (VIP, _('VIP')),
    ]
    number = models.PositiveSmallIntegerField(_('Stol raqami'), unique=True)
    seats = models.PositiveSmallIntegerField(
        _('O‘rindiqlar soni'), validators=[MinValueValidator(1), MaxValueValidator(20)],
    )
    location = models.CharField(_('Joylashuvi'), max_length=10, choices=LOCATIONS, default=HALL)
    active = models.BooleanField(_('Faol'), default=True)

    class Meta:
        verbose_name = _('Stol')
        verbose_name_plural = _('Stollar')
        ordering = ['number']
        constraints = [
            models.CheckConstraint(
                condition=Q(seats__gte=1, seats__lte=20), name='table_seats_range',
                violation_error_message=_('O‘rindiqlar soni 1 dan 20 gacha bo‘lsin.'),
            ),
        ]

    def __str__(self):
        return _('%(number)s-stol') % {'number': self.number}


class Reservation(Timestamped):
    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    SEATED = 'seated'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'
    NO_SHOW = 'no_show'
    STATUSES = [
        (PENDING, _('Kutilmoqda')),
        (CONFIRMED, _('Tasdiqlangan')),
        (SEATED, _('O‘tirgan')),
        (COMPLETED, _('Yakunlangan')),
        (CANCELLED, _('Bekor qilingan')),
        (NO_SHOW, _('Kelmadi')),
    ]
    # Bu holatdagi bronlar stolni band qilmaydi.
    FREE_STATUSES = (COMPLETED, CANCELLED, NO_SHOW)
    # Mijoz yoki xodim faqat shu holatlardan bekor qila oladi.
    CANCELLABLE_STATUSES = (PENDING, CONFIRMED)

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='reservations', verbose_name=_('Mijoz'),
    )
    table = models.ForeignKey(
        Table, on_delete=models.PROTECT, related_name='reservations', verbose_name=_('Stol'),
    )
    guests = models.PositiveSmallIntegerField(
        _('Mehmonlar soni'), validators=[MinValueValidator(1), MaxValueValidator(20)],
    )
    start = models.DateTimeField(_('Boshlanishi'))
    end = models.DateTimeField(_('Tugashi'))
    status = models.CharField(_('Holati'), max_length=10, choices=STATUSES, default=PENDING)
    name = models.CharField(_('Ism'), max_length=150)
    phone = models.CharField(_('Telefon'), max_length=25, validators=[validate_phone])
    note = models.TextField(_('Izoh'), blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_reservations', verbose_name=_('Yaratgan'),
    )

    class Meta:
        verbose_name = _('Bron')
        verbose_name_plural = _('Bronlar')
        ordering = ['-start', '-id']
        indexes = [models.Index(fields=['table', 'start', 'end'], name='reservation_table_time_idx')]
        constraints = [
            models.CheckConstraint(
                condition=Q(end__gt=F('start')), name='reservation_end_after_start',
                violation_error_message=_('Tugash vaqti boshlanishdan keyin bo‘lsin.'),
            ),
        ]

    def __str__(self):
        return f'{self.table} · {timezone.localtime(self.start):%Y-%m-%d %H:%M} · {self.name}'

    @classmethod
    def conflicts(cls, table, start, end, exclude_pk=None):
        """Shu stolda shu vaqt oralig'ini band qilgan bronlar."""
        busy = cls.objects.filter(table=table, start__lt=end, end__gt=start).exclude(status__in=cls.FREE_STATUSES)
        return busy.exclude(pk=exclude_pk) if exclude_pk else busy

    def clean(self):
        # Admin panel uchun. API'da shu qoidalarni serializer tekshiradi.
        if not self.start:
            return
        restaurant = RestaurantSettings.load()
        old_start = None if self._state.adding else Reservation.objects.filter(pk=self.pk).values_list('start', flat=True).first()
        if old_start != self.start:
            error = restaurant.booking_error(self.start)
            if error:
                raise ValidationError({'start': error})
            self.end = restaurant.reservation_end(self.start)
        if not self.table_id:
            return
        if self.guests and self.guests > self.table.seats:
            raise ValidationError({'guests': _('Mehmonlar soni stol sig‘imidan oshmasin.')})
        if self.status not in self.FREE_STATUSES and self.conflicts(self.table, self.start, self.end, self.pk).exists():
            raise ValidationError(_('Bu stol shu vaqtda band.'))


class Order(Timestamped):
    DINE_IN = 'dine_in'
    TAKEAWAY = 'takeaway'
    DELIVERY = 'delivery'
    TYPES = [
        (DINE_IN, _('Restoranda')),
        (TAKEAWAY, _('Olib ketish')),
        (DELIVERY, _('Yetkazib berish')),
    ]
    NEW = 'new'
    COOKING = 'cooking'
    READY = 'ready'
    SERVED = 'served'
    PAID = 'paid'
    CANCELLED = 'cancelled'
    STATUSES = [
        (NEW, _('Yangi')),
        (COOKING, _('Tayyorlanmoqda')),
        (READY, _('Tayyor')),
        (SERVED, _('Berildi')),
        (PAID, _('To‘langan')),
        (CANCELLED, _('Bekor qilingan')),
    ]
    TRANSITIONS = {
        NEW: (COOKING, CANCELLED),
        COOKING: (READY, CANCELLED),
        READY: (SERVED, CANCELLED),
        SERVED: (PAID, CANCELLED),
        PAID: (),
        CANCELLED: (),
    }

    table = models.ForeignKey(
        Table, on_delete=models.PROTECT, null=True, blank=True,
        related_name='orders', verbose_name=_('Stol'),
    )
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='orders', verbose_name=_('Mijoz'),
    )
    waiter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='served_orders', verbose_name=_('Ofitsiant'),
    )
    reservation = models.ForeignKey(
        Reservation, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='orders', verbose_name=_('Bron'),
    )
    order_type = models.CharField(_('Buyurtma turi'), max_length=10, choices=TYPES, default=DINE_IN)
    status = models.CharField(_('Holati'), max_length=10, choices=STATUSES, default=NEW)
    note = models.TextField(_('Izoh'), blank=True)
    # Buyurtma paytidagi foiz: sozlama keyin o'zgarsa ham eski buyurtma o'zgarmaydi.
    service_percent = models.DecimalField(
        _('Xizmat haqi (%)'), max_digits=5, decimal_places=2,
        default=current_service_percent, editable=False,
    )
    subtotal = models.DecimalField(_('Taomlar summasi'), max_digits=12, decimal_places=2, default=0, editable=False)
    service_amount = models.DecimalField(_('Xizmat haqi summasi'), max_digits=12, decimal_places=2, default=0, editable=False)
    total = models.DecimalField(_('Jami'), max_digits=12, decimal_places=2, default=0, editable=False)
    paid_at = models.DateTimeField(_('To‘langan vaqti'), null=True, blank=True, editable=False)

    class Meta:
        verbose_name = _('Buyurtma')
        verbose_name_plural = _('Buyurtmalar')
        ordering = ['-created_at', '-id']

    def __str__(self):
        return _('Buyurtma #%(id)s') % {'id': self.pk}

    def recalculate(self):
        """Summalarni OrderItem'lardan qayta hisoblab saqlaydi."""
        self.subtotal = self.items.aggregate(value=Sum('line_total'))['value'] or Decimal('0.00')
        self.service_amount = (self.subtotal * self.service_percent / 100).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP,
        )
        self.total = self.subtotal + self.service_amount
        self.save(update_fields=['subtotal', 'service_amount', 'total', 'updated_at'])

    def change_status(self, status, actor):
        """Ruxsat etilgan o'tishni bajaradi va tarixga yozadi. Noto'g'ri o'tishda ValidationError."""
        with transaction.atomic():
            current = Order.objects.select_for_update().get(pk=self.pk).status
            if status not in self.TRANSITIONS[current]:
                raise ValidationError(_('«%(old)s» holatidan «%(new)s» holatiga o‘tib bo‘lmaydi.') % {
                    'old': dict(self.STATUSES)[current],
                    'new': dict(self.STATUSES).get(status, status),
                })
            self.status = status
            update_fields = ['status', 'updated_at']
            if status == self.PAID:
                self.paid_at = timezone.now()
                update_fields.append('paid_at')
            self.save(update_fields=update_fields)
            OrderStatusEvent.objects.create(order=self, previous_status=current, status=status, actor=actor)


class OrderItem(Timestamped):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name=_('Buyurtma'))
    menu_item = models.ForeignKey(MenuItem, on_delete=models.PROTECT, related_name='order_items', verbose_name=_('Taom'))
    quantity = models.PositiveSmallIntegerField(
        _('Soni'), default=1, validators=[MinValueValidator(1), MaxValueValidator(999)],
    )
    # Buyurtma paytidagi narx: menyu narxi keyin o'zgarsa ham eski buyurtma o'zgarmaydi.
    unit_price = models.DecimalField(_('Birlik narxi'), max_digits=12, decimal_places=2, editable=False)
    line_total = models.DecimalField(_('Qator summasi'), max_digits=12, decimal_places=2, editable=False)
    note = models.CharField(_('Izoh'), max_length=250, blank=True)

    class Meta:
        verbose_name = _('Buyurtma taomi')
        verbose_name_plural = _('Buyurtma taomlari')
        ordering = ['id']
        constraints = [
            models.CheckConstraint(
                condition=Q(quantity__gte=1), name='order_item_quantity_positive',
                violation_error_message=_('Soni kamida 1 bo‘lsin.'),
            ),
        ]

    def __str__(self):
        return f'{self.menu_item} × {self.quantity}'

    def save(self, *args, **kwargs):
        if self.unit_price is None:
            self.unit_price = self.menu_item.price
        self.line_total = self.unit_price * self.quantity
        super().save(*args, **kwargs)


class OrderStatusEvent(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='events', verbose_name=_('Buyurtma'))
    # Bo'sh qiymat — buyurtma yaratilgan payt.
    previous_status = models.CharField(_('Oldingi holat'), max_length=10, choices=Order.STATUSES, blank=True)
    status = models.CharField(_('Yangi holat'), max_length=10, choices=Order.STATUSES)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='order_events', verbose_name=_('Bajaruvchi'),
    )
    changed_at = models.DateTimeField(_('O‘zgargan vaqti'), default=timezone.now, editable=False)

    class Meta:
        verbose_name = _('Buyurtma holati tarixi')
        verbose_name_plural = _('Buyurtma holatlari tarixi')
        ordering = ['-changed_at', '-id']

    def __str__(self):
        return f'{self.order}: {self.previous_status or "—"} → {self.status}'
