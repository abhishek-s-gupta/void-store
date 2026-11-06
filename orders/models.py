from decimal import Decimal
import uuid
from django.conf import settings
from django.db import models
from store.models import Look, Product, ProductVariant


class Cart(models.Model):
    """Shopping cart attached to authenticated user or anonymous session key."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="carts"
    )
    session_key = models.CharField(max_length=40, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        owner = self.user.username if self.user else f"Guest ({self.session_key})"
        return f"Cart #{self.pk} - {owner}"

    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    def subtotal(self):
        """Raw sum of regular variant prices."""
        return sum((item.variant.product.price * item.quantity for item in self.items.select_related("variant__product")), Decimal("0.00"))

    def total_discount(self):
        """Savings achieved from look bundles (10% off)."""
        savings = Decimal("0.00")
        for item in self.items.select_related("variant__product"):
            if item.is_bundle_item:
                regular = item.variant.product.price * item.quantity
                discounted = item.discounted_line_total()
                savings += (regular - discounted)
        return savings.quantize(Decimal("0.01"))

    def total(self):
        """Final payable amount."""
        return sum((item.discounted_line_total() for item in self.items.select_related("variant__product")), Decimal("0.00")).quantize(Decimal("0.01"))


class CartItem(models.Model):
    """Line item in Cart linking to a specific ProductVariant."""
    cart = models.ForeignKey(Cart, related_name="items", on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, related_name="cart_items", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    is_bundle_item = models.BooleanField(default=False, help_text="True if added via Complete Look bundle (10% off)")
    bundle_look = models.ForeignKey(Look, on_delete=models.SET_NULL, null=True, blank=True, related_name="bundle_cart_items")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.variant.product.name} ({self.variant.size}) x {self.quantity}"

    def unit_price(self):
        return self.variant.product.price

    def line_total(self):
        return self.unit_price() * self.quantity

    def effective_unit_price(self):
        """Applies 10% discount if part of a full look bundle."""
        if self.is_bundle_item:
            return (self.unit_price() * Decimal("0.90")).quantize(Decimal("0.01"))
        return self.unit_price()

    def discounted_line_total(self):
        return (self.effective_unit_price() * self.quantity).quantize(Decimal("0.01"))


class Order(models.Model):
    """Customer order recorded upon checkout."""
    STATUS_CHOICES = (
        ("placed", "Order Placed"),
        ("confirmed", "Confirmed"),
        ("processing", "Processing"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders")
    order_number = models.CharField(max_length=32, unique=True, editable=False)
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    address = models.TextField()
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    payment_method = models.CharField(max_length=60, default="Cash on Delivery (Mock)")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    shipping = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="confirmed")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.order_number} ({self.user.username})"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"VOID-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def total_items(self):
        return sum(item.quantity for item in self.items.all())


class OrderItem(models.Model):
    """Archival record of each line item inside an Order."""
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="order_items")
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    size = models.CharField(max_length=20)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Original unit price")
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Paid unit price")
    is_bundle_item = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.product.name} ({self.size}) x {self.quantity}"

    def line_total(self):
        return (self.discounted_price * self.quantity).quantize(Decimal("0.01"))
