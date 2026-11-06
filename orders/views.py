from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from store.models import Look, Product, ProductVariant
from .cart import add_full_look_bundle, add_item_to_cart, get_or_create_cart
from .models import Cart, CartItem, Order, OrderItem


def _is_ajax(request):
    return (
        request.headers.get("X-Requested-With") in ["fetch", "XMLHttpRequest"] or
        request.headers.get("Accept") == "application/json" or
        "application/json" in request.headers.get("Content-Type", "")
    )


def cart_detail_view(request):
    """Full shopping cart page with quantity adjustments, line items, and breakdown."""
    cart = get_or_create_cart(request)
    items = list(cart.items.select_related("variant__product", "bundle_look").all())

    context = {
        "cart": cart,
        "items": items,
        "subtotal": cart.subtotal(),
        "discount": cart.total_discount(),
        "total": cart.total(),
    }
    return render(request, "orders/cart.html", context)


@require_POST
def cart_add_view(request):
    """
    Adds a single product variant to the cart.
    Supports both fetch() AJAX requests and standard form submissions.
    """
    slug = request.POST.get("slug", "").strip()
    size = request.POST.get("size", "").strip()
    try:
        qty = int(request.POST.get("qty", 1))
    except (ValueError, TypeError):
        qty = 1

    cart = get_or_create_cart(request)
    try:
        item = add_item_to_cart(cart, product_slug=slug, size_str=size, quantity=qty)
        msg = f"{item.variant.product.name} ({item.variant.size}) added to your bag."
        ok = True
    except Exception as e:
        msg = str(e)
        ok = False

    if _is_ajax(request):
        items_data = [
            {
                "id": it.id,
                "name": it.variant.product.name,
                "size": it.variant.size,
                "image": it.variant.product.image,
                "price": str(it.effective_unit_price()),
                "original_price": str(it.unit_price()) if it.is_bundle_item else None,
                "is_bundle": it.is_bundle_item,
                "qty": it.quantity,
                "line_total": str(it.discounted_line_total()),
            }
            for it in cart.items.select_related("variant__product").all()
        ]
        return JsonResponse({
            "ok": ok,
            "message": msg,
            "count": cart.total_items(),
            "subtotal": str(cart.subtotal()),
            "discount": str(cart.total_discount()),
            "total": str(cart.total()),
            "items": items_data,
        }, status=200 if ok else 400)

    if ok:
        messages.success(request, msg)
    else:
        messages.error(request, msg)
    return redirect("cart")


@require_POST
def cart_add_look_view(request):
    """
    Adds all products in a Runway Look bundle at 10% discount.
    """
    look_id = request.POST.get("look_id") or request.POST.get("look")
    if not look_id:
        return JsonResponse({"ok": False, "message": "Missing look reference."}, status=400)

    cart = get_or_create_cart(request)
    try:
        look, added_items = add_full_look_bundle(cart, look_id=look_id, size_selections=request.POST)
        msg = f"Full look '{look.name}' (3 pieces with 10% bundle savings) added to your bag."
        ok = True
    except Exception as e:
        msg = str(e)
        ok = False

    if _is_ajax(request):
        items_data = [
            {
                "id": it.id,
                "name": it.variant.product.name,
                "size": it.variant.size,
                "image": it.variant.product.image,
                "price": str(it.effective_unit_price()),
                "original_price": str(it.unit_price()),
                "is_bundle": it.is_bundle_item,
                "qty": it.quantity,
                "line_total": str(it.discounted_line_total()),
            }
            for it in cart.items.select_related("variant__product").all()
        ]
        return JsonResponse({
            "ok": ok,
            "message": msg,
            "count": cart.total_items(),
            "subtotal": str(cart.subtotal()),
            "discount": str(cart.total_discount()),
            "total": str(cart.total()),
            "items": items_data,
        }, status=200 if ok else 400)

    if ok:
        messages.success(request, msg)
    else:
        messages.error(request, msg)
    return redirect("cart")


@require_POST
def cart_update_view(request):
    """Updates line item quantity in the cart."""
    item_id = request.POST.get("item_id")
    try:
        qty = int(request.POST.get("quantity", 1))
    except (ValueError, TypeError):
        qty = 1

    cart = get_or_create_cart(request)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)

    if qty <= 0:
        item.delete()
        msg = "Item removed from your bag."
    else:
        if qty > item.variant.stock:
            return JsonResponse({
                "ok": False,
                "message": f"Only {item.variant.stock} units available in stock."
            }, status=400) if _is_ajax(request) else redirect("cart")
        item.quantity = min(20, qty)
        item.save()
        msg = "Bag updated."

    if _is_ajax(request):
        return JsonResponse({
            "ok": True,
            "message": msg,
            "count": cart.total_items(),
            "subtotal": str(cart.subtotal()),
            "discount": str(cart.total_discount()),
            "total": str(cart.total()),
        })

    messages.info(request, msg)
    return redirect("cart")


@require_POST
def cart_remove_view(request):
    """Deletes an item from the cart."""
    item_id = request.POST.get("item_id")
    cart = get_or_create_cart(request)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    item.delete()
    msg = "Item removed from your bag."

    if _is_ajax(request):
        return JsonResponse({
            "ok": True,
            "message": msg,
            "count": cart.total_items(),
            "subtotal": str(cart.subtotal()),
            "discount": str(cart.total_discount()),
            "total": str(cart.total()),
        })

    messages.info(request, msg)
    return redirect("cart")


def cart_drawer_data_view(request):
    """Supplies real-time JSON for the slide-out cart drawer."""
    cart = get_or_create_cart(request)
    items = list(cart.items.select_related("variant__product").order_by("-created_at"))
    items_data = [
        {
            "id": it.id,
            "name": it.variant.product.name,
            "size": it.variant.size,
            "image": it.variant.product.image,
            "price": str(it.effective_unit_price()),
            "original_price": str(it.unit_price()) if it.is_bundle_item else None,
            "is_bundle": it.is_bundle_item,
            "qty": it.quantity,
            "line_total": str(it.discounted_line_total()),
        }
        for it in items
    ]
    return JsonResponse({
        "count": cart.total_items(),
        "subtotal": str(cart.subtotal()),
        "discount": str(cart.total_discount()),
        "total": str(cart.total()),
        "items": items_data,
    })


def checkout_view(request):
    """
    Checkout page handling customer shipping address and order finalization.
    Anonymous users are given option to log in or checkout directly.
    """
    cart = get_or_create_cart(request)
    items = list(cart.items.select_related("variant__product").all())

    if not items:
        messages.warning(request, "Your bag is currently empty.")
        return redirect("cart")

    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        address = request.POST.get("address", "").strip()
        city = request.POST.get("city", "").strip()
        postal_code = request.POST.get("postal_code", "").strip()
        payment_method = request.POST.get("payment_method", "Cash on Delivery (Mock)").strip()

        # Validation
        errors = []
        if not full_name:
            errors.append("Please provide your full recipient name.")
        if not email or "@" not in email:
            errors.append("Please provide a valid contact email address.")
        if not phone:
            errors.append("Please provide a contact phone number.")
        if not address:
            errors.append("Please provide your delivery address.")
        if not city:
            errors.append("Please provide your city.")

        # Inventory check
        for it in items:
            if it.quantity > it.variant.stock:
                errors.append(f"Insufficient stock for {it.variant.product.name} ({it.variant.size}). Only {it.variant.stock} available.")

        if errors:
            for err in errors:
                messages.error(request, err)
        else:
            # Atomic creation of Order and reduction of inventory
            with transaction.atomic():
                # If guest user, assign order to demo user or create account / link to user if logged in
                order_user = request.user if request.user.is_authenticated else None
                if not order_user:
                    from django.contrib.auth.models import User
                    # Fallback to demo user for anonymous checkout recording
                    order_user = User.objects.filter(username="demouser").first()

                subtotal = cart.subtotal()
                discount = cart.total_discount()
                total = cart.total()

                order = Order.objects.create(
                    user=order_user,
                    full_name=full_name,
                    email=email,
                    phone=phone,
                    address=address,
                    city=city,
                    postal_code=postal_code,
                    payment_method=payment_method,
                    subtotal=subtotal,
                    discount=discount,
                    shipping=Decimal("0.00"),
                    total=total,
                    status="confirmed"
                )

                # Order Items & Inventory deduction
                for it in items:
                    OrderItem.objects.create(
                        order=order,
                        product=it.variant.product,
                        variant=it.variant,
                        size=it.variant.size,
                        quantity=it.quantity,
                        price=it.unit_price(),
                        discounted_price=it.effective_unit_price(),
                        is_bundle_item=it.is_bundle_item,
                    )
                    # Deduct stock
                    it.variant.stock = max(0, it.variant.stock - it.quantity)
                    it.variant.save()

                # Clear cart
                cart.items.all().delete()

            messages.success(request, f"Order #{order.order_number} confirmed! Thank you for shopping with VOID STORE.")
            return redirect("order_confirmation", order_number=order.order_number)

    context = {
        "cart": cart,
        "items": items,
        "subtotal": cart.subtotal(),
        "discount": cart.total_discount(),
        "total": cart.total(),
    }
    return render(request, "orders/checkout.html", context)


def order_confirmation_view(request, order_number):
    """Confirmation receipt page showing order details and breakdown."""
    order = get_object_or_404(Order.objects.prefetch_related("items__product"), order_number=order_number)
    return render(request, "orders/confirmation.html", {"order": order})


@login_required
def my_orders_view(request):
    """Customer account dashboard displaying past order history."""
    orders = Order.objects.filter(user=request.user).prefetch_related("items__product").order_by("-created_at")
    return render(request, "orders/my_orders.html", {"orders": orders})
