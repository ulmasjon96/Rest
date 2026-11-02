import copy

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from clinic.models import (
    ClinicSettings, Profile, Department, Room, Specialty, Doctor, WorkHour, DayOff,
    Patient, Appointment, AppointmentStatusEvent, DirectionEvent, Audit, LoginAttempt,
)
from .models import Book


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'


class ModelCleanMixin:
    """Modeldagi clean() validatsiyasini API'da ham ishlatadi.

    DRF ModelSerializer modelning clean() metodini o'zi chaqirmaydi,
    shuning uchun bu mixin uni validate() ichida chaqiradi va Django
    ValidationError'ini DRF ValidationError'iga (400 javob) aylantiradi.
    """
    def validate(self, attrs):
        attrs = super().validate(attrs)
        # Haqiqiy obyektni buzmaslik uchun nusxa ustida tekshiriladi.
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


class ClinicSettingsSerializer(ModelCleanMixin, serializers.ModelSerializer):
    class Meta:
        model = ClinicSettings
        exclude = ['id']


class ProfileSerializer(ModelCleanMixin, serializers.ModelSerializer):
    role_name = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = Profile
        fields = '__all__'


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'


class RoomSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)

    class Meta:
        model = Room
        fields = '__all__'


class SpecialtySerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialty
        fields = '__all__'


class WorkHourSerializer(ModelCleanMixin, serializers.ModelSerializer):
    weekday_name = serializers.CharField(source='get_weekday_display', read_only=True)

    class Meta:
        model = WorkHour
        fields = '__all__'


class DayOffSerializer(serializers.ModelSerializer):
    class Meta:
        model = DayOff
        fields = '__all__'


class DoctorSerializer(serializers.ModelSerializer):
    specialty_name = serializers.CharField(source='specialty.name', read_only=True)
    initials = serializers.CharField(read_only=True)
    hours = WorkHourSerializer(many=True, read_only=True)
    days_off = DayOffSerializer(many=True, read_only=True)

    class Meta:
        model = Doctor
        fields = '__all__'

    def validate_duration(self, value):
        # Modeldagi 'valid_duration' constraint'i bilan bir xil shart.
        # Usiz noto'g'ri qiymat bazada IntegrityError (500) beradi.
        if not 5 <= value <= 240:
            raise serializers.ValidationError('Qabul davomiyligi 5 dan 240 daqiqagacha bo‘lsin.')
        return value


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = '__all__'


class AppointmentSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='doctor.name', read_only=True)
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    status_name = serializers.CharField(source='get_status_display', read_only=True)

    INACTIVE_STATUSES = ['cancelled', 'missed']

    class Meta:
        model = Appointment
        fields = '__all__'
        read_only_fields = ['created_by']

    def validate(self, attrs):
        attrs = super().validate(attrs)
        start = attrs.get('start', getattr(self.instance, 'start', None))
        end = attrs.get('end', getattr(self.instance, 'end', None))
        doctor = attrs.get('doctor', getattr(self.instance, 'doctor', None))
        status = attrs.get('status', getattr(self.instance, 'status', 'scheduled'))

        if start and end and end <= start:
            raise serializers.ValidationError({'end': 'Tugash vaqti boshlanishdan keyin bo‘lsin.'})

        # Faollik yangi qabulda yoki shifokor almashtirilganda tekshiriladi.
        # Aks holda faolsizlantirilgan shifokorning eski qabulini yakunlab bo'lmay qolardi.
        doctor_changed = self.instance is None or ('doctor' in attrs and attrs['doctor'] != self.instance.doctor)
        if doctor and doctor_changed and not doctor.active:
            raise serializers.ValidationError({'doctor': 'Bu shifokor hozir faol emas.'})

        # Shu shifokorda vaqt to'qnashuvi bormi.
        # Bekor qilingan va kelmagan qabullar vaqtni band qilmaydi.
        if doctor and start and end and status not in self.INACTIVE_STATUSES:
            busy = Appointment.objects.filter(
                doctor=doctor, start__lt=end, end__gt=start,
            ).exclude(status__in=self.INACTIVE_STATUSES)
            if self.instance:
                busy = busy.exclude(pk=self.instance.pk)
            if busy.exists():
                raise serializers.ValidationError('Shifokorda bu vaqtda boshqa qabul bor.')
        return attrs


class AppointmentStatusEventSerializer(serializers.ModelSerializer):
    status_name = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = AppointmentStatusEvent
        fields = '__all__'


class DirectionEventSerializer(serializers.ModelSerializer):
    stage_name = serializers.CharField(source='get_stage_display', read_only=True)

    class Meta:
        model = DirectionEvent
        fields = '__all__'


class AuditSerializer(serializers.ModelSerializer):
    # AppointmentHistory proxy modeli ham shu serializer bilan ishlaydi (jadval bir xil).
    class Meta:
        model = Audit
        fields = '__all__'


class LoginAttemptSerializer(serializers.ModelSerializer):
    # Ichki xavfsizlik modeli: endpoint ochilmagan, faqat to'liqlik uchun.
    class Meta:
        model = LoginAttempt
        fields = '__all__'
