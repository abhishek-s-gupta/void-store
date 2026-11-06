from decimal import Decimal
from django.db import models
from django.urls import reverse


class Category(models.Model):
    """Product category (Footwear, Apparel, Outerwear, Essentials, etc.)"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f"{reverse('shop')}?category={self.slug}"


class Product(models.Model):
    """Master product model representing streetwear pieces."""
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150, unique=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")
    vendor = models.CharField(max_length=80, default="VOID STORE")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    image = models.CharField(max_length=255, help_text="Path under static, e.g. assets/source-tshirt.webp")
    description = models.TextField(blank=True)
    details = models.TextField(blank=True, help_text="Semicolon or newline separated features")
    is_featured = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("product_detail", kwargs={"slug": self.slug})

    def size_list(self):
        """Returns ordered list of available variant sizes."""
        return list(self.variants.order_by("id").values_list("size", flat=True))

    def size_label(self):
        """Matches spec convention: 'Shoe size' for footwear, 'Size' for apparel."""
        sizes = self.size_list()
        if sizes and sizes[0].isdigit() and int(sizes[0]) >= 35:
            return "Shoe size"
        if self.category and "shoe" in self.category.name.lower() or "footwear" in self.category.name.lower():
            return "Shoe size"
        return "Size"

    def in_stock(self):
        """Returns True if any variant has stock > 0."""
        return self.variants.filter(stock__gt=0).exists()

    def total_stock(self):
        return sum(self.variants.values_list("stock", flat=True))


class ProductVariant(models.Model):
    """Size variant with specific inventory tracking."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    size = models.CharField(max_length=20)
    stock = models.PositiveIntegerField(default=10)
    sku = models.CharField(max_length=50, blank=True)

    class Meta:
        unique_together = ("product", "size")
        ordering = ["id"]

    def __str__(self):
        return f"{self.product.name} — Size {self.size} (Stock: {self.stock})"

    def is_available(self):
        return self.stock > 0


class Look(models.Model):
    """Curated full-body runway looks (1 to 6)."""
    name = models.CharField(max_length=100)
    subtitle = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    image = models.CharField(max_length=255, help_text="640px model cut-out path under static")
    image_hd = models.CharField(max_length=255, help_text="1080px original look cut-out path under static")
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["position"]

    def __str__(self):
        return f"0{self.position + 1} — {self.name}"

    def items_list(self):
        """Returns list of LookItem instances with preloaded product & variants."""
        return list(self.items.select_related("product").prefetch_related("product__variants"))

    def full_price(self):
        """Full retail sum of all pieces in this look."""
        return sum((item.product.price for item in self.items.select_related("product")), Decimal("0.00"))

    def bundle_price(self):
        """10% bundle discount applied to full look."""
        return (self.full_price() * Decimal("0.90")).quantize(Decimal("0.01"))

    def bundle_discount(self):
        return (self.full_price() - self.bundle_price()).quantize(Decimal("0.01"))


class LookItem(models.Model):
    """Positioned product piece within a Look, including hotspot pins."""
    look = models.ForeignKey(Look, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name="look_items", on_delete=models.CASCADE)
    order = models.PositiveSmallIntegerField(default=0)
    pin_x = models.FloatField(default=50.0, help_text="Hotspot anatomical X percentage (0-100)")
    pin_y = models.FloatField(default=50.0, help_text="Hotspot anatomical Y percentage (0-100)")
    tag = models.CharField(max_length=40, blank=True, help_text="Badge text, e.g. 'New'")

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.look.name} > #{self.order + 1}: {self.product.name}"
