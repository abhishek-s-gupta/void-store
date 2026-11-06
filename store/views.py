from decimal import Decimal
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import Category, Look, LookItem, Product, ProductVariant


@ensure_csrf_cookie
def home_view(request):
    """
    Homepage featuring the Runway Hero Carousel, curated highlights,
    and direct integration with the cart system.
    """
    looks = list(Look.objects.prefetch_related("items__product__variants").all())
    # Serialized JSON structure for client-side calculations and feet detection
    looks_json = []
    for l in looks:
        items_data = []
        for it in l.items.all():
            items_data.append({
                "slug": it.product.slug,
                "name": it.product.name,
                "price": str(it.product.price),
                "image": it.product.image,
                "sizes": it.product.size_list(),
                "pin_x": it.pin_x,
                "pin_y": it.pin_y,
                "tag": it.tag,
                "order": it.order,
            })
        looks_json.append({
            "id": l.id,
            "position": l.position,
            "name": l.name,
            "subtitle": l.subtitle,
            "img": l.image,
            "hd": l.image_hd,
            "full_price": str(l.full_price()),
            "bundle_price": str(l.bundle_price()),
            "items": items_data,
        })

    featured_products = Product.objects.filter(is_featured=True).prefetch_related("variants")[:8]
    categories = Category.objects.all()

    context = {
        "looks": looks,
        "looks_json": looks_json,
        "featured_products": featured_products,
        "categories": categories,
    }
    return render(request, "store/home.html", context)


def shop_view(request):
    """
    Product listing page with full search, category filtering,
    and sorting by price / recency.
    """
    products = Product.objects.prefetch_related("variants", "category").all()
    categories = Category.objects.all()

    # Category Filter
    active_category = request.GET.get("category", "").strip()
    if active_category:
        products = products.filter(category__slug=active_category)

    # Search query
    query = request.GET.get("q", "").strip()
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(vendor__icontains=query)
        )

    # Sorting
    sort_by = request.GET.get("sort", "featured").strip()
    if sort_by == "price_asc":
        products = products.order_by("price")
    elif sort_by == "price_desc":
        products = products.order_by("-price")
    elif sort_by == "newest":
        products = products.order_by("-created_at")
    elif sort_by == "name":
        products = products.order_by("name")
    else:
        products = products.order_by("-is_featured", "name")

    context = {
        "products": products,
        "categories": categories,
        "active_category": active_category,
        "query": query,
        "sort_by": sort_by,
        "total_count": products.count(),
    }
    return render(request, "store/shop.html", context)


def product_detail_view(request, slug):
    """
    Product details page with size selector, live inventory check,
    product narrative, and 'Complete the Look' curated pieces.
    """
    product = get_object_or_404(Product.objects.prefetch_related("variants", "category"), slug=slug)
    variants = list(product.variants.all())

    # Find Looks that contain this product for "Complete the Look"
    look_items = LookItem.objects.filter(product=product).select_related("look")
    related_looks = [li.look for li in look_items]

    # Find complementary pieces appearing in the same looks
    complementary_products = []
    if related_looks:
        comp_items = LookItem.objects.filter(look__in=related_looks).exclude(product=product).select_related("product")
        seen_ids = set()
        for ci in comp_items:
            if ci.product.id not in seen_ids:
                seen_ids.add(ci.product.id)
                complementary_products.append(ci.product)
    
    # Fallback to category products if no look match
    if not complementary_products and product.category:
        complementary_products = list(
            Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
        )

    context = {
        "product": product,
        "variants": variants,
        "related_looks": related_looks,
        "complementary_products": complementary_products[:4],
    }
    return render(request, "store/product_detail.html", context)
