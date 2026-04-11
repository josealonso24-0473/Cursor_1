from django.contrib import admin
from .models import Category, Supplier, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("name", "contact_email", "phone", "is_active", "created_at")
    search_fields = ("name", "contact_email")
    list_filter = ("is_active", "created_at")
    ordering = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "sku",
        "name",
        "category",
        "supplier",
        "unit_price",
        "stock_quantity",
        "minimum_stock",
        "is_active",
        "updated_at",
    )
    list_filter = ("is_active", "category")
    search_fields = ("name", "sku")
    list_editable = ("is_active",)
    raw_id_fields = ("category", "supplier")
    ordering = ("name",)
