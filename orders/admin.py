from django.contrib import admin
from .models import Cart, CartItem, Order, OrderItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "session_key", "total_items", "total", "updated_at")
    list_filter = ("created_at", "updated_at")
    search_fields = ("user__username", "session_key")
    inlines = [CartItemInline]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "size", "quantity", "price", "discounted_price", "is_bundle_item")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "user", "full_name", "total", "status", "payment_method", "created_at")
    list_filter = ("status", "payment_method", "created_at")
    search_fields = ("order_number", "full_name", "email", "phone")
    readonly_fields = ("order_number", "created_at", "updated_at")
    inlines = [OrderItemInline]
