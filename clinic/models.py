import uuid
from datetime import time

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Q, F
from django.utils import timezone
from django.utils.translation import gettext_lazy as _tr


def validate_photo(value):
    from PIL import Image
    if value.size > 3 * 1024 * 1024:
        raise ValidationError(_tr('Rasm 3 MB dan kichik bo‘lishi kerak.'))
    try:
        im = Image.open(value)
        if im.format not in ('JPEG', 'PNG', 'WEBP'):
            raise ValueError()
        im.verify()
        value.seek(0)
    except Exception:
        raise ValidationError(_tr('Faqat haqiqiy JPEG, PNG yoki WebP rasmini yuklang.'))


class Timestamped(models.Model):
    created_at = models.DateTimeField(_tr('Yaratilgan sana'), default=timezone.now, editable=False)
    updated_at = models.DateTimeField(_tr('Yangilangan sana'), auto_now=True)

    class Meta:
        abstract = True


def default_duration():
    return ClinicSettings.load().default_duration


class ClinicSettings(Timestamped):
    document_max_mb = models.PositiveSmallIntegerField(_tr('Tibbiy fayl limiti (MB)'), default=10, validators=[MinValueValidator(1), MaxValueValidator(50)])
    offer_minutes = models.PositiveSmallIntegerField(_tr('Kutish taklifi muddati (daqiqa)'), default=15, validators=[MinValueValidator(1), MaxValueValidator(1440)])
    name = models.CharField(_tr('Klinika nomi'), max_length=150, default='Medora Clinic')
    logo = models.ImageField(_tr('Logotip'), upload_to='clinic/', blank=True, validators=[validate_photo])
    phone = models.CharField(_tr('Telefon'), max_length=25, blank=True)
    address = models.CharField(_tr('Manzil'), max_length=250, blank=True)
    opens_at = models.TimeField(_tr('Umumiy ish boshlanishi'), default=time(8))
    closes_at = models.TimeField(_tr('Umumiy ish tugashi'), default=time(18))
    default_duration = models.PositiveSmallIntegerField(_tr('Standart qabul (daqiqa)'), default=30, validators=[MinValueValidator(5), MaxValueValidator(240)])
    booking_days = models.PositiveSmallIntegerField(_tr('Oldindan band qilish (kun)'), default=90, validators=[MinValueValidator(1), MaxValueValidator(365)])
    cancellation_hours = models.PositiveSmallIntegerField(_tr('Bemor bekor qilish chegarasi (soat)'), default=0, validators=[MaxValueValidator(168)])

    class Meta:
        verbose_name = _tr('Klinika sozlamalari')
        verbose_name_plural = _tr('Klinika sozlamalari')
        constraints = [models.CheckConstraint(condition=Q(id=1), name='single_clinic_settings')]

    def clean(self):
        if self.opens_at and self.closes_at and self.opens_at >= self.closes_at:
            raise ValidationError(_tr('Klinika ish tugashi boshlanishidan keyin bo‘lsin.'))

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        return cls.objects.filter(pk=1).first() or cls(pk=1)

    def __str__(self):
        return self.name


class Profile(Timestamped):
    ROLES = [
        ('admin', _tr('Administrator')),
        ('reception', _tr('Registrator')),
        ('doctor', _tr('Shifokor')),
        ('patient', _tr('Bemor')),
    ]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_tr('Foydalanuvchi'))
    role = models.CharField(_tr('Hisob roli'), max_length=12, choices=ROLES, default='patient')

    class Meta:
        verbose_name = _tr('Hisob profili')
        verbose_name_plural = _tr('Hisob profillari')

    def clean(self):
        if self.user_id:
            if Doctor.objects.filter(user_id=self.user_id).exists() and self.role != 'doctor':
                raise ValidationError(_tr('Hisob shifokorga bog‘langan. Avval bog‘lanishni tekshiring.'))
            if Patient.objects.filter(user_id=self.user_id).exists() and self.role != 'patient':
                raise ValidationError(_tr('Hisob bemorga bog‘langan. Avval bog‘lanishni tekshiring.'))

    def __str__(self):
        return f'{self.user} — {self.get_role_display()}'


class Department(Timestamped):
    name = models.CharField(_tr('Bo‘lim nomi'), max_length=120, unique=True)

    class Meta:
        verbose_name = _tr('Bo‘lim')
        verbose_name_plural = _tr('Bo‘limlar')

    def __str__(self):
        return self.name


class Room(Timestamped):
    department = models.ForeignKey(Department, on_delete=models.PROTECT, verbose_name=_tr('Bo‘lim'))
    floor = models.CharField(_tr('Qavat'), max_length=20)
    number = models.CharField(_tr('Xona raqami'), max_length=20)

    class Meta:
        verbose_name = _tr('Xona va qavat')
        verbose_name_plural = _tr('Xonalar va qavatlar')
        constraints = [models.UniqueConstraint(fields=['department', 'floor', 'number'], name='unique_room_location')]

    def __str__(self):
        return _tr('%(department)s · %(floor)s-qavat · %(room)s-xona') % {
            'department': self.department, 'floor': self.floor, 'room': self.number,
        }


class Specialty(Timestamped):
    name = models.CharField(_tr('Nomi'), max_length=100, unique=True)

    class Meta:
        verbose_name = _tr('Mutaxassislik')
        verbose_name_plural = _tr('Mutaxassisliklar')

    def __str__(self):
        return self.name


class Doctor(Timestamped):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, verbose_name=_tr('Foydalanuvchi hisobi'))
    name = models.CharField(_tr('Ism-familiya'), max_length=150)
    specialty = models.ForeignKey(Specialty, on_delete=models.PROTECT, verbose_name=_tr('Mutaxassislik'))
    phone = models.CharField(_tr('Telefon'), max_length=25)
    bio = models.TextField(_tr('Qisqacha ma’lumot'), blank=True)
    experience = models.PositiveSmallIntegerField(_tr('Tajriba (yil)'), default=5)
    room = models.CharField(_tr('Xona'), max_length=15)
    location = models.ForeignKey(Room, verbose_name=_tr('Xona va bo‘lim'), on_delete=models.PROTECT, null=True, blank=True)
    duration = models.PositiveSmallIntegerField(_tr('Qabul davomiyligi (daqiqa)'), default=default_duration)
    active = models.BooleanField(_tr('Faol'), default=True)
    photo = models.ImageField(_tr('Fotosurat'), upload_to='doctors/', blank=True, validators=[validate_photo])

    class Meta:
        verbose_name = _tr('Shifokor')
        verbose_name_plural = _tr('Shifokorlar')
        ordering = ['name']
        constraints = [models.CheckConstraint(condition=Q(duration__gte=5) & Q(duration__lte=240), name='valid_duration')]

    def __str__(self):
        return self.name

    @property
    def initials(self):
        return ''.join(x[0] for x in self.name.split()[:2])


class WorkHour(Timestamped):
    WEEKDAYS = list(enumerate([
        _tr('Dushanba'), _tr('Seshanba'), _tr('Chorshanba'), _tr('Payshanba'),
        _tr('Juma'), _tr('Shanba'), _tr('Yakshanba'),
    ]))
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='hours', verbose_name=_tr('Shifokor'))
    weekday = models.PositiveSmallIntegerField(_tr('Hafta kuni'), choices=WEEKDAYS)
    start = models.TimeField(_tr('Boshlanish'))
    end = models.TimeField(_tr('Tugash'))
    break_start = models.TimeField(_tr('Tanaffus boshlanishi'), null=True, blank=True)
    break_end = models.TimeField(_tr('Tanaffus tugashi'), null=True, blank=True)

    class Meta:
        verbose_name = _tr('Haftalik ish jadvali va tanaffus')
        verbose_name_plural = _tr('Haftalik ish jadvali va tanaffuslar')
        constraints = [
            models.UniqueConstraint(fields=['doctor', 'weekday'], name='one_workday'),
            models.CheckConstraint(condition=Q(end__gt=F('start')), name='valid_workday'),
        ]

    def clean(self):
        if self.start and self.end and self.start >= self.end:
            raise ValidationError(_tr('Tugash vaqti boshlanishdan keyin bo‘lsin.'))
        if bool(self.break_start) != bool(self.break_end):
            raise ValidationError(_tr('Tanaffusning ikkala vaqtini kiriting.'))
        if (self.start and self.end and self.break_start and self.break_end
                and not self.start <= self.break_start < self.break_end <= self.end):
            raise ValidationError(_tr('Tanaffus ish vaqti ichida bo‘lsin.'))

    def __str__(self):
        return f'{self.doctor} — {self.get_weekday_display()}'


class DayOff(Timestamped):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='days_off', verbose_name=_tr('Shifokor'))
    date = models.DateField(_tr('Sana'))
    reason = models.CharField(_tr('Sabab'), max_length=150, blank=True)

    class Meta:
        verbose_name = _tr('Ta’til yoki istisno sana')
        verbose_name_plural = _tr('Ta’tillar va istisno sanalar')
        constraints = [models.UniqueConstraint(fields=['doctor', 'date'], name='one_dayoff')]

    def __str__(self):
        return f'{self.doctor} — {self.date}'


class Patient(Timestamped):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, verbose_name=_tr('Foydalanuvchi hisobi'))
    name = models.CharField(_tr('Ism-familiya'), max_length=150)
    birth_date = models.DateField(_tr('Tug‘ilgan sana'))
    phone = models.CharField(_tr('Telefon'), max_length=25)
    address = models.CharField(_tr('Manzil'), max_length=250, blank=True)
    archived = models.BooleanField(_tr('Arxivlangan'), default=False)

    class Meta:
        verbose_name = _tr('Bemor')
        verbose_name_plural = _tr('Bemorlar')
        ordering = ['name']

    def __str__(self):
        return f'{self.name} · {self.phone}'


class Appointment(models.Model):
    STATUSES = [
        ('scheduled', _tr('Belgilangan')),
        ('arrived', _tr('Kelgan')),
        ('called', _tr('Chaqirilgan')),
        ('in_progress', _tr('Qabulda')),
        ('completed', _tr('Yakunlangan')),
        ('cancelled', _tr('Bekor qilingan')),
        ('missed', _tr('Kelmagan')),
    ]
    doctor = models.ForeignKey(Doctor, on_delete=models.PROTECT, verbose_name=_tr('Shifokor'))
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, verbose_name=_tr('Bemor'))
    start = models.DateTimeField(_tr('Boshlanish'))
    end = models.DateTimeField(_tr('Tugash'))
    status = models.CharField(_tr('Holat'), max_length=15, choices=STATUSES, default='scheduled')
    arrived_at = models.DateTimeField(_tr('Kelgan vaqti'), null=True, blank=True, editable=False)
    started_at = models.DateTimeField(_tr('Qabul boshlangan vaqt'), null=True, blank=True, editable=False)
    completed_at = models.DateTimeField(_tr('Qabul yakunlangan vaqt'), null=True, blank=True, editable=False)
    status_changed_at = models.DateTimeField(_tr('Holat o‘zgargan vaqt'), null=True, blank=True, editable=False)
    queue_number = models.PositiveIntegerField(_tr('Navbat raqami'), null=True, blank=True, editable=False)
    queue_priority = models.IntegerField(_tr('Navbat ustuvorligi'), default=0, editable=False)
    called_at = models.DateTimeField(_tr('Chaqirilgan vaqt'), null=True, blank=True, editable=False)
    reason = models.CharField(_tr('Murojaat sababi'), max_length=500, blank=True)
    note = models.TextField(_tr('Shifokor izohi'), blank=True)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name=_tr('Yaratgan xodim'))
    created_at = models.DateTimeField(_tr('Yaratilgan sana'), auto_now_add=True)
    updated_at = models.DateTimeField(_tr('Yangilangan sana'), auto_now=True)

    class Meta:
        verbose_name = _tr('Qabul')
        verbose_name_plural = _tr('Qabullar')
        ordering = ['start']
        indexes = [
            models.Index(fields=['doctor', 'start', 'end']),
            models.Index(fields=['patient', 'start', 'end']),
        ]
        constraints = [models.CheckConstraint(condition=Q(end__gt=F('start')), name='positive_appointment')]

    def __str__(self):
        return f'{self.patient.name} — {self.start:%Y-%m-%d %H:%M}'


class AppointmentStatusEvent(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.PROTECT, related_name='status_events')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    previous_status = models.CharField(max_length=15, choices=Appointment.STATUSES)
    status = models.CharField(max_length=15, choices=Appointment.STATUSES)
    changed_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        ordering = ['changed_at', 'pk']

    def __str__(self):
        return f'{self.appointment} : {self.previous_status} → {self.status}'


class DirectionEvent(models.Model):
    STAGES = [
        ('reception', _tr('Kelgani tasdiqlandi')),
        ('directed', _tr('Xona ko‘rsatildi')),
        ('called', _tr('Chaqirildi')),
        ('in_progress', _tr('Qabul boshlandi')),
        ('completed', _tr('Xizmat yakunlandi')),
        ('reordered', _tr('Navbat tartibi o‘zgardi')),
    ]
    appointment = models.ForeignKey(Appointment, on_delete=models.PROTECT, related_name='directions')
    stage = models.CharField(_tr('Bosqich'), max_length=15, choices=STAGES)
    destination = models.CharField(_tr('Yo‘nalish (o‘sha paytdagi)'), max_length=250)
    next_step = models.CharField(_tr('Keyingi bosqich'), max_length=250, blank=True)
    reason = models.CharField(_tr('Sabab'), max_length=500, blank=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(_tr('Vaqt'), default=timezone.now, editable=False)

    class Meta:
        ordering = ['created_at', 'pk']
        verbose_name = _tr('Yo‘naltirish hodisasi')
        verbose_name_plural = _tr('Yo‘naltirish tarixi')

    def __str__(self):
        return f'{self.appointment} — {self.get_stage_display()}'


class Audit(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, verbose_name=_tr('Amal bajargan hisob'))
    appointment = models.ForeignKey(Appointment, on_delete=models.PROTECT, null=True, blank=True, related_name='history', verbose_name=_tr('Qabul'))
    action = models.CharField(_tr('Amal'), max_length=100)
    detail = models.CharField(_tr('Tafsilot'), max_length=500, blank=True)
    created_at = models.DateTimeField(_tr('Amal vaqti'), auto_now_add=True)

    class Meta:
        verbose_name = _tr('Audit yozuvi')
        verbose_name_plural = _tr('Audit jurnali')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.action} — {self.created_at:%Y-%m-%d %H:%M}'


class AppointmentHistory(Audit):
    class Meta:
        proxy = True
        verbose_name = _tr('Qabul o‘zgarish tarixi')
        verbose_name_plural = _tr('Qabul o‘zgarish tarixi')


class LoginAttempt(models.Model):
    key = models.CharField(max_length=64, unique=True)
    count = models.PositiveIntegerField(default=0)
    since = models.DateTimeField()

    def __str__(self):
        return f'{self.key} ({self.count})'
