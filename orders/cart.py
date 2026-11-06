from decimal import Decimal
from django.db import transaction
from store.models import Look, Product, ProductVariant
from .models import Cart, CartItem


def get_or_create_cart(request):
    """
    Retrieves or initializes the appropriate Cart instance.
    Handles authenticated users and anonymous session tracking.
    """
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return cart

    if not request.session.session_key:
        request.session.create()
    cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
    return cart


def merge_carts_on_login(sender, user, request, **kwargs):
    """
    Signal handler: merges anonymous session cart items into the user's persistent cart upon login.
    """
    session_key = request.session.session_key
    if not session_key:
        return

    try:
        session_cart = Cart.objects.get(session_key=session_key)
    except Cart.DoesNotExist:
        return

    with transaction.atomic():
        user_cart, _ = Cart.objects.get_or_create(user=user)

        for session_item in session_cart.items.select_related("variant"):
            existing = user_cart.items.filter(variant=session_item.variant).first()
            if existing:
                existing.quantity = min(20, existing.quantity + session_item.quantity)
                if session_item.is_bundle_item:
                    existing.is_bundle_item = True
                    existing.bundle_look = session_item.bundle_look
                existing.save()
            else:
                session_item.cart = user_cart
                session_item.save()

        session_cart.delete()


def add_item_to_cart(cart, product_slug, size_str, quantity=1, is_bundle_item=False, bundle_look=None):
    """
    Adds a specific product size to the cart.
    Validates stock availability.
    """
    product = Product.objects.get(slug=product_slug)
    variant = ProductVariant.objects.filter(product=product, size=size_str).first()
    if not variant:
        raise ValueError(f"Size '{size_str}' is unavailable for {product.name}.")

    if variant.stock < 1:
        raise ValueError(f"Sorry, {product.name} in size {size_str} is out of stock.")

    item = cart.items.filter(variant=variant).first()
    if item:
        new_qty = min(20, item.quantity + quantity)
        if new_qty > variant.stock:
            raise ValueError(f"Only {variant.stock} units available for {product.name} ({size_str}).")
        item.quantity = new_qty
        if is_bundle_item:
            item.is_bundle_item = True
            item.bundle_look = bundle_look
        item.save()
    else:
        qty = min(20, max(1, quantity))
        if qty > variant.stock:
            raise ValueError(f"Only {variant.stock} units available for {product.name} ({size_str}).")
        item = CartItem.objects.create(
            cart=cart,
            variant=variant,
            quantity=qty,
            is_bundle_item=is_bundle_item,
            bundle_look=bundle_look,
        )
    return item


def add_full_look_bundle(cart, look_id, size_selections):
    """
    Adds all products in a Look with 10% bundle discount applied to each.
    size_selections is a dict: { 'size_<product_slug>': '<size_value>' }
    """
    look = Look.objects.prefetch_related("items__product__variants").get(pk=look_id)
    added_items = []

    with transaction.atomic():
        for look_item in look.items.all():
            prod = look_item.product
            key = f"size_{prod.slug}"
            selected_size = size_selections.get(key)
            if not selected_size:
                # Fallback to first available size
                sizes = prod.size_list()
                selected_size = sizes[0] if sizes else "M"

            item = add_item_to_cart(
                cart=cart,
                product_slug=prod.slug,
                size_str=selected_size,
                quantity=1,
                is_bundle_item=True,
                bundle_look=look
            )
            added_items.append(item)

    return look, added_items
