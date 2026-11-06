from django.apps import AppConfig


class OrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'orders'

    def ready(self):
        from django.contrib.auth.signals import user_logged_in
        from .cart import merge_carts_on_login
        user_logged_in.connect(merge_carts_on_login)
