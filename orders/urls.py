from django.urls import path
from . import views

urlpatterns = [
    path("cart/", views.cart_detail_view, name="cart"),
    path("cart/add/", views.cart_add_view, name="cart_add"),
    path("cart/add-look/", views.cart_add_look_view, name="cart_add_look"),
    path("cart/update/", views.cart_update_view, name="cart_update"),
    path("cart/remove/", views.cart_remove_view, name="cart_remove"),
    path("cart/drawer-data/", views.cart_drawer_data_view, name="cart_drawer_data"),
    path("checkout/", views.checkout_view, name="checkout"),
    path("orders/<str:order_number>/confirmation/", views.order_confirmation_view, name="order_confirmation"),
    path("my-orders/", views.my_orders_view, name="my_orders"),
]
