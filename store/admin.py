from django.contrib import admin
from .models import Category, Look, LookItem, Product, ProductVariant


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ("size", "stock", "sku")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "vendor", "in_stock", "total_stock", "is_featured")
    list_filter = ("category", "is_featured")
    search_fields = ("name", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductVariantInline]


class LookItemInline(admin.TabularInline):
    model = LookItem
    extra = 3
    fields = ("order", "product", "pin_x", "pin_y", "tag")


@admin.register(Look)
class LookAdmin(admin.ModelAdmin):
    list_display = ("position", "name", "full_price", "bundle_price")
    inlines = [LookItemInline]
    ordering = ("position",)


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("product", "size", "stock", "sku")
    list_filter = ("size",)
    search_fields = ("product__name", "sku")
