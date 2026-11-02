from rest_framework import generics, permissions, viewsets

from clinic.models import (
    ClinicSettings, Department, Room, Specialty, Doctor, WorkHour, DayOff,
    Patient, Appointment, AppointmentStatusEvent, DirectionEvent, Audit,
)
from .models import Book
from .serializers import (
    BookSerializer, ClinicSettingsSerializer, DepartmentSerializer, RoomSerializer,
    SpecialtySerializer, DoctorSerializer, WorkHourSerializer, DayOffSerializer,
    PatientSerializer, AppointmentSerializer, AppointmentStatusEventSerializer,
    DirectionEventSerializer, AuditSerializer,
)


class IsStaffOrReadOnly(permissions.BasePermission):
    """O'qish hammaga, yozish faqat xodimlarga (is_staff)."""
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.order_by('id')   # sahifalash barqaror bo'lishi uchun tartib shart
    serializer_class = BookSerializer
    filterset_fields = ['author']
    search_fields = ['title', 'author']
    ordering_fields = ['price', 'created_at']


# ---------- Ochiq ma'lumotlar (o'qish hammaga) ----------

class ClinicSettingsView(generics.RetrieveUpdateAPIView):
    serializer_class = ClinicSettingsSerializer
    permission_classes = [IsStaffOrReadOnly]

    def get_object(self):
        return ClinicSettings.load()


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsStaffOrReadOnly]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']


class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.select_related('department')
    serializer_class = RoomSerializer
    permission_classes = [IsStaffOrReadOnly]
    filterset_fields = ['department', 'floor']
    search_fields = ['number', 'floor', 'department__name']
    ordering_fields = ['department__name', 'floor', 'number']


class SpecialtyViewSet(viewsets.ModelViewSet):
    queryset = Specialty.objects.all()
    serializer_class = SpecialtySerializer
    permission_classes = [IsStaffOrReadOnly]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']


class DoctorViewSet(viewsets.ModelViewSet):
    queryset = Doctor.objects.select_related('specialty', 'location__department').prefetch_related('hours', 'days_off')
    serializer_class = DoctorSerializer
    permission_classes = [IsStaffOrReadOnly]
    filterset_fields = ['specialty', 'active', 'location']
    search_fields = ['name', 'phone', 'specialty__name']
    ordering_fields = ['name', 'experience', 'duration']


class WorkHourViewSet(viewsets.ModelViewSet):
    queryset = WorkHour.objects.select_related('doctor')
    serializer_class = WorkHourSerializer
    permission_classes = [IsStaffOrReadOnly]
    filterset_fields = ['doctor', 'weekday']
    ordering_fields = ['doctor__name', 'weekday', 'start']


class DayOffViewSet(viewsets.ModelViewSet):
    queryset = DayOff.objects.select_related('doctor')
    serializer_class = DayOffSerializer
    permission_classes = [IsStaffOrReadOnly]
    filterset_fields = ['doctor', 'date']
    search_fields = ['doctor__name', 'reason']
    ordering_fields = ['date']


# ---------- Shaxsiy tibbiy ma'lumotlar (faqat login qilganlar) ----------

class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['archived']
    search_fields = ['name', 'phone']
    ordering_fields = ['name', 'birth_date', 'created_at']


class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.select_related('doctor', 'patient', 'created_by')
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['doctor', 'patient', 'status']
    search_fields = ['patient__name', 'patient__phone', 'doctor__name', 'reason']
    ordering_fields = ['start', 'end', 'status', 'queue_number', 'created_at']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class AppointmentStatusEventViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AppointmentStatusEvent.objects.select_related('appointment', 'actor')
    serializer_class = AppointmentStatusEventSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['appointment', 'status', 'actor']
    ordering_fields = ['changed_at']


class DirectionEventViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DirectionEvent.objects.select_related('appointment', 'actor')
    serializer_class = DirectionEventSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['appointment', 'stage', 'actor']
    search_fields = ['destination', 'reason']
    ordering_fields = ['created_at']


class AuditViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Audit.objects.select_related('actor', 'appointment')
    serializer_class = AuditSerializer
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = ['action', 'actor', 'appointment']
    search_fields = ['action', 'detail']
    ordering_fields = ['created_at']
