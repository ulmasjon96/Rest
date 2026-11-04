from django.contrib import admin

from .models import Book, Product


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'author', 'price', 'created_at']
    search_fields = ['title', 'author']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'quantity', 'created_by', 'created_at']
    search_fields = ['name', 'description', 'created_by__username']
    list_filter = ['created_at', 'created_by']
    readonly_fields = ['created_by', 'created_at', 'updated_at']

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
