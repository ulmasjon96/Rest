from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    BookViewSet, ClinicSettingsView, DepartmentViewSet, RoomViewSet, SpecialtyViewSet,
    DoctorViewSet, WorkHourViewSet, DayOffViewSet, PatientViewSet, AppointmentViewSet,
    AppointmentStatusEventViewSet, DirectionEventViewSet, AuditViewSet,
)

router = DefaultRouter()
router.register('books', BookViewSet)
router.register('departments', DepartmentViewSet)
router.register('rooms', RoomViewSet)
router.register('specialties', SpecialtyViewSet)
router.register('doctors', DoctorViewSet)
router.register('work-hours', WorkHourViewSet)
router.register('days-off', DayOffViewSet)
router.register('patients', PatientViewSet)
router.register('appointments', AppointmentViewSet)
router.register('status-events', AppointmentStatusEventViewSet)
router.register('directions', DirectionEventViewSet)
router.register('audit', AuditViewSet)

urlpatterns = [
    path('clinic-settings/', ClinicSettingsView.as_view()),
] + router.urls