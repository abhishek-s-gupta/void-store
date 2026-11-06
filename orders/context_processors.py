from decimal import Decimal
from .cart import get_or_create_cart


def cart_summary(request):
    """
    Supplies real-time cart metrics across all templates for header badges,
    the slide-out cart drawer, and interactive styling components.
    """
    try:
        cart = get_or_create_cart(request)
        items = list(cart.items.select_related("variant__product", "bundle_look").order_by("-created_at"))
        count = sum(it.quantity for it in items)
        subtotal = sum((it.line_total() for it in items), Decimal("0.00"))
        discount = sum((it.line_total() - it.discounted_line_total() for it in items), Decimal("0.00"))
        total = (subtotal - discount).quantize(Decimal("0.01"))
        return {
            "cart": cart,
            "cart_items": items,
            "cart_count": count,
            "cart_subtotal": subtotal,
            "cart_discount": discount,
            "cart_total": total,
        }
    except Exception:
        return {
            "cart": None,
            "cart_items": [],
            "cart_count": 0,
            "cart_subtotal": Decimal("0.00"),
            "cart_discount": Decimal("0.00"),
            "cart_total": Decimal("0.00"),
        }
