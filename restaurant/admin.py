from django.contrib import admin

from .models import (
    Category, MenuItem, Order, OrderItem, OrderStatusEvent, Profile, Reservation,
    RestaurantSettings, Table,
)


@admin.register(RestaurantSettings)
class RestaurantSettingsAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'opens_at', 'closes_at', 'reservation_duration', 'booking_days', 'service_percent']
    readonly_fields = ['created_at', 'updated_at']

    def has_add_permission(self, request):
        return not RestaurantSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'phone', 'created_at']
    list_filter = ['role']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'phone']


class MenuItemInline(admin.TabularInline):
    model = MenuItem
    extra = 1
    fields = ['name', 'price', 'preparation_minutes', 'available', 'is_vegetarian', 'spicy']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'active']
    list_filter = ['active']
    search_fields = ['name']
    inlines = [MenuItemInline]


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'preparation_minutes', 'available', 'is_vegetarian', 'spicy']
    list_editable = ['price', 'available']
    list_filter = ['category', 'available', 'is_vegetarian', 'spicy']
    search_fields = ['name', 'description', 'category__name']


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ['number', 'seats', 'location', 'active']
    list_filter = ['location', 'active']
    search_fields = ['number']


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ['id', 'table', 'name', 'phone', 'guests', 'start', 'end', 'status', 'customer']
    list_filter = ['status', 'table', 'start']
    search_fields = ['name', 'phone', 'note', 'customer__username']
    date_hierarchy = 'start'
    # Tugash vaqti Reservation.clean() da hisoblanadi.
    readonly_fields = ['end', 'created_by', 'created_at', 'updated_at']

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class OrderItemInline(admin.TabularInline):
    """Mavjud qatorlar o'zgarmaydi (narx saqlanib qolishi uchun): faqat qo'shish va o'chirish."""
    model = OrderItem
    extra = 0
    fields = ['menu_item', 'quantity', 'note', 'unit_price', 'line_total']
    readonly_fields = ['unit_price', 'line_total']

    def _editable(self, obj):
        return obj is None or obj.status == Order.NEW

    def has_add_permission(self, request, obj=None):
        return self._editable(obj)

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return self._editable(obj)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'menu_item':
            kwargs['queryset'] = MenuItem.objects.filter(available=True, category__active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'order_type', 'status', 'table', 'customer', 'waiter', 'total', 'paid_at', 'created_at']
    list_filter = ['status', 'order_type', 'created_at']
    search_fields = ['id', 'customer__username', 'waiter__username', 'note']
    date_hierarchy = 'created_at'
    # Holat faqat API orqali (set-status) o'zgaradi, shunda tarix va tartib buzilmaydi.
    readonly_fields = ['status', 'service_percent', 'subtotal', 'service_amount', 'total', 'paid_at', 'created_at', 'updated_at']
    inlines = [OrderItemInline]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:
            OrderStatusEvent.objects.create(order=obj, status=obj.status, actor=request.user)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.instance.recalculate()


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'menu_item', 'quantity', 'unit_price', 'line_total']
    search_fields = ['menu_item__name', 'order__id']
    list_filter = ['menu_item__category']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(OrderStatusEvent)
class OrderStatusEventAdmin(admin.ModelAdmin):
    list_display = ['order', 'previous_status', 'status', 'actor', 'changed_at']
    list_filter = ['status', 'changed_at']
    search_fields = ['order__id', 'actor__username']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
