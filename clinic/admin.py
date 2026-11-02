from django.contrib import admin

from .models import (
    Appointment, AppointmentHistory, AppointmentStatusEvent, Audit, ClinicSettings,
    DayOff, Department, DirectionEvent, Doctor, LoginAttempt, Patient, Profile,
    Room, Specialty, WorkHour,
)


# ---------- Sozlamalar (singleton) ----------

@admin.register(ClinicSettings)
class ClinicSettingsAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'opens_at', 'closes_at', 'default_duration', 'booking_days', 'updated_at']
    readonly_fields = ['created_at', 'updated_at']

    def has_add_permission(self, request):
        # Yozuv bo'lmasa, qo'shish mumkin; bitta yozuv bo'lgach "Qo'shish" tugmasi yo'qoladi.
        return not ClinicSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Sozlamalarni o'chirish taqiqlangan.
        return False


# ---------- Hisoblar ----------

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'created_at']
    list_filter = ['role']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'user__email']
    autocomplete_fields = ['user']


# ---------- Tuzilma ----------

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['number', 'floor', 'department']
    list_filter = ['department', 'floor']
    search_fields = ['number', 'floor', 'department__name']
    list_select_related = ['department']


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']


# ---------- Shifokorlar va jadval ----------

class WorkHourInline(admin.TabularInline):
    model = WorkHour
    extra = 0
    fields = ['weekday', 'start', 'end', 'break_start', 'break_end']


class DayOffInline(admin.TabularInline):
    model = DayOff
    extra = 0
    fields = ['date', 'reason']


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ['name', 'specialty', 'phone', 'room', 'location', 'duration', 'experience', 'active']
    list_filter = ['active', 'specialty', 'location__department']
    search_fields = ['name', 'phone', 'room', 'user__username']
    list_editable = ['active']
    list_select_related = ['specialty', 'location__department']
    autocomplete_fields = ['user', 'specialty', 'location']
    inlines = [WorkHourInline, DayOffInline]


@admin.register(WorkHour)
class WorkHourAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'weekday', 'start', 'end', 'break_start', 'break_end']
    list_filter = ['weekday', 'doctor']
    search_fields = ['doctor__name']
    list_select_related = ['doctor']


@admin.register(DayOff)
class DayOffAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'date', 'reason']
    list_filter = ['doctor']
    search_fields = ['doctor__name', 'reason']
    date_hierarchy = 'date'
    list_select_related = ['doctor']


# ---------- Bemorlar ----------

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'birth_date', 'archived', 'created_at']
    list_filter = ['archived']
    search_fields = ['name', 'phone', 'user__username']
    autocomplete_fields = ['user']


# ---------- Qabullar ----------

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'start', 'end', 'status', 'queue_number', 'created_by']
    list_filter = ['status', 'doctor', 'doctor__specialty']
    search_fields = ['patient__name', 'patient__phone', 'doctor__name', 'reason']
    date_hierarchy = 'start'
    list_select_related = ['patient', 'doctor', 'created_by']
    autocomplete_fields = ['doctor', 'patient']
    readonly_fields = [
        'created_by', 'token', 'queue_number', 'queue_priority', 'arrived_at', 'called_at',
        'started_at', 'completed_at', 'status_changed_at', 'created_at', 'updated_at',
    ]

    def save_model(self, request, obj, form, change):
        # Qabulni yaratgan xodim avtomatik — admin panelga kirgan foydalanuvchi.
        if not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# ---------- Tarix va audit (tahrirlab/o'chirib bo'lmaydi) ----------

class HistoryAdminMixin:
    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AppointmentStatusEvent)
class AppointmentStatusEventAdmin(HistoryAdminMixin, admin.ModelAdmin):
    list_display = ['appointment', 'previous_status', 'status', 'actor', 'changed_at']
    list_filter = ['status', 'previous_status']
    search_fields = ['appointment__patient__name', 'actor__username']
    date_hierarchy = 'changed_at'
    list_select_related = ['appointment__patient', 'actor']


@admin.register(DirectionEvent)
class DirectionEventAdmin(HistoryAdminMixin, admin.ModelAdmin):
    list_display = ['appointment', 'stage', 'destination', 'next_step', 'actor', 'created_at']
    list_filter = ['stage']
    search_fields = ['appointment__patient__name', 'destination', 'reason', 'actor__username']
    date_hierarchy = 'created_at'
    list_select_related = ['appointment__patient', 'actor']


@admin.register(Audit)
class AuditAdmin(HistoryAdminMixin, admin.ModelAdmin):
    list_display = ['action', 'actor', 'appointment', 'detail', 'created_at']
    list_filter = ['action']
    search_fields = ['action', 'detail', 'actor__username']
    date_hierarchy = 'created_at'
    list_select_related = ['actor', 'appointment__patient']


@admin.register(AppointmentHistory)
class AppointmentHistoryAdmin(AuditAdmin):
    # Proxy model: faqat qabulga bog'langan audit yozuvlari.
    def get_queryset(self, request):
        return super().get_queryset(request).filter(appointment__isnull=False)


# ---------- Xavfsizlik ----------

@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ['key', 'count', 'since']
    search_fields = ['key']
    ordering = ['-since']
