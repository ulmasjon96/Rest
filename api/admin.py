from django.contrib import admin

from .models import Book, Product


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'author', 'price', 'created_at']
    search_fields = ['title', 'author']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'quantity', 'is_active', 'created_by', 'created_at']
    list_editable = ['is_active']
    search_fields = ['name', 'description', 'created_by__username']
    list_filter = ['is_active', 'created_at', 'created_by']
    readonly_fields = ['created_by', 'created_at', 'updated_at']

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        # Mahsulotni faqat egasi /api/users/me/products/{id}/ orqali o'chiradi.
        # Django delete_selected amalini ham shu huquqqa qarab o'zi olib tashlaydi.
        return False
