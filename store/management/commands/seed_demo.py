from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from store.models import Category, Look, LookItem, Product, ProductVariant

User = get_user_model()

# Category Definitions
CATEGORIES_DATA = [
    ("Footwear", "footwear", "Architectural footwear engineered for streetwear aesthetics and daily versatility."),
    ("T-Shirts", "t-shirts", "Heavyweight premium cotton jersey tees with structured drapes and custom ribs."),
    ("Hoodies & Sweaters", "hoodies-sweaters", "Brushed fleece hoodies and textured knitwear made for layering."),
    ("Outerwear", "outerwear", "Technical jackets, overshirts, and modular utility layering pieces."),
]

# 8 Products Definitions
PRODUCTS_DATA = [
    {
        "slug": "tatum-5-orbit-copy",
        "name": "Retro High Leather Sneaker",
        "category": "footwear",
        "vendor": "VOID ARCHIVE",
        "price": "149.00",
        "original_price": "175.00",
        "image": "assets/source-tatum-5-orbit-copy.webp",
        "sizes": ["40", "41", "42", "43", "44", "45", "46"],
        "description": "A heritage basketball silhouette engineered for luxury streetwear. Crafted with premium full-grain leather, responsive air cushioning, and tonal carbon-fiber shank plate for structured support.",
        "details": "Full-grain textured leather upper; Responsive encapsulated air sole; Durable herringbone rubber tread; Structural carbon composite shank plate."
    },
    {
        "slug": "tshirt",
        "name": "Boxy Heavyweight Graphic Tee",
        "category": "t-shirts",
        "vendor": "VOID ARCHIVE",
        "price": "199.00",
        "original_price": None,
        "image": "assets/source-tshirt.webp",
        "sizes": ["S", "L", "M", "XL"],
        "description": "Heavyweight 280 GSM combed cotton jersey with a relaxed, dropped-shoulder boxy drape. Features contrast bound rib collar detailing and archival graphic screenprint across the chest.",
        "details": "280 GSM heavyweight 100% cotton; Ribbed 1.25\" collar with twin-needle stitching; Pre-shrunk vintage wash; Relaxed boxy silhouette."
    },
    {
        "slug": "sweatshirt",
        "name": "Minimalist Crewneck Sweatshirt",
        "category": "hoodies-sweaters",
        "vendor": "VOID ARCHIVE",
        "price": "199.00",
        "original_price": None,
        "image": "assets/source-sweatshirt.webp",
        "sizes": ["S", "L", "M", "XL"],
        "description": "Clean, elevated crewneck crafted from 450 GSM French terry cotton. Minimalist silhouette featuring refined raglan sleeves, ribbed cuffs, and subtle tonal branding.",
        "details": "450 GSM diagonal loop French terry; Raglan construction for ease of movement; Tonal subtle embroidery at wrist; Heavy ribbed waistband."
    },
    {
        "slug": "tatum-5-orbit",
        "name": "Architectural Low-Top Sneaker",
        "category": "footwear",
        "vendor": "VOID ARCHIVE",
        "price": "149.00",
        "original_price": "165.00",
        "image": "assets/source-tatum-5-orbit.webp",
        "sizes": ["40", "41", "42", "43", "44", "45", "46"],
        "description": "A low-profile court silhouette defined by sculpted paneling, perforated vamp, and sculpted dual-density midsole for all-day comfort.",
        "details": "Supple nappa leather and suede overlays; Perforated toe box for airflow; OrthoLite antimicrobial insole; High-abrasion rubber cupsole."
    },
    {
        "slug": "hoodie-black",
        "name": "Noir Oversized Heavyweight Hoodie",
        "category": "hoodies-sweaters",
        "vendor": "VOID ARCHIVE",
        "price": "199.00",
        "original_price": "220.00",
        "image": "assets/source-hoodie-black.webp",
        "sizes": ["S", "L", "M", "XL"],
        "description": "Constructed from 500 GSM loopback cotton fleece. Designed with an exaggerated double-layered hood without drawstrings, deep kangaroo pocket, and wide body cut.",
        "details": "500 GSM custom milled heavyweight fleece; Double-layered hood without eyelets; Hidden interior security pocket; Deep kangaroo handwarmer pocket."
    },
    {
        "slug": "sweatshirt-plus",
        "name": "Forest Green Embroidered Sweatshirt",
        "category": "hoodies-sweaters",
        "vendor": "VOID ARCHIVE",
        "price": "199.00",
        "original_price": None,
        "image": "assets/source-sweatshirt-plus.webp",
        "sizes": ["S", "L", "M", "XL"],
        "description": "Rich forest-green pullover hoodie in heavyweight combed cotton with vintage varsity arched chainstitch embroidery on the chest.",
        "details": "Rich deep-dyed organic cotton; Archival chainstitched varsity lettering; Reinforced elbow panels; Custom woven size and label tags."
    },
    {
        "slug": "hoodie",
        "name": "Muted Grey Graphic Fleece Hoodie",
        "category": "hoodies-sweaters",
        "vendor": "VOID ARCHIVE",
        "price": "199.00",
        "original_price": None,
        "image": "assets/source-hoodie.webp",
        "sizes": ["S", "L", "M", "XL"],
        "description": "Heather-grey fleece hoodie showcasing brutalist typographic screenprint. Garment-dyed and enzyme washed for a broken-in vintage patina.",
        "details": "Garment-washed 420 GSM fleece; Anti-pilling enzyme wash treatment; Water-based soft hand screenprint; Preshrunk fit."
    },
    {
        "slug": "air-jordan-12-retro-copy",
        "name": "Monochrome Court Leather Sneaker",
        "category": "footwear",
        "vendor": "VOID ARCHIVE",
        "price": "149.00",
        "original_price": "170.00",
        "image": "assets/source-air-jordan-12-retro-copy.webp",
        "sizes": ["40", "41", "42", "43", "44", "45", "46"],
        "description": "Monochromatic black tumbled leather upper perched atop a contrasting stark white cupsole. Minimal branding and sleek profile for high-low styling.",
        "details": "Tumbled calfskin upper; Waxed cotton tonal laces; Lightweight Phylon midsole cushioning; Pivot-point traction outsole."
    },
]

# 6 Runway Looks Definitions
LOOKS_DATA = [
    {
        "position": 0,
        "name": "The City Edit",
        "subtitle": "A charcoal knit and easy denim.",
        "description": "Layered textures engineered for urban mobility. Relaxed drape meets technical court footwear.",
        "model_no": 1,
        "orig_no": 1,
        "items": [
            ("tatum-5-orbit-copy", 47.0, 27.0, ""),
            ("tshirt", 48.0, 58.0, ""),
            ("sweatshirt", 45.0, 96.0, ""),
        ]
    },
    {
        "position": 1,
        "name": "Gallery Opening",
        "subtitle": "A clean white tee and relaxed denim.",
        "description": "Clean lines and understated luxury for evening cultural transitions.",
        "model_no": 5,
        "orig_no": 5,
        "items": [
            ("tatum-5-orbit", 50.0, 28.0, ""),
            ("hoodie-black", 48.0, 58.0, "New"),
            ("tshirt", 45.0, 88.0, ""),
        ]
    },
    {
        "position": 2,
        "name": "Gallery Opening",
        "subtitle": "Olive knitwear. A grounded palette.",
        "description": "Earthy tones grounded by classic low-top footwear and relaxed wide-leg tailoring.",
        "model_no": 4,
        "orig_no": 4,
        "items": [
            ("sweatshirt-plus", 50.0, 28.0, ""),
            ("tatum-5-orbit", 48.0, 58.0, "New"),
            ("tshirt", 45.0, 88.0, ""),
        ]
    },
    {
        "position": 3,
        "name": "Studio Day",
        "subtitle": "Black, white and laid-back denim.",
        "description": "Monochrome streetwear staples built for long creative sessions and casual studio meetings.",
        "model_no": 6,
        "orig_no": 6,
        "items": [
            ("hoodie-black", 50.0, 28.0, ""),
            ("tatum-5-orbit-copy", 48.0, 58.0, ""),
            ("tshirt", 45.0, 88.0, ""),
        ]
    },
    {
        "position": 4,
        "name": "Studio Day",
        "subtitle": "Burgundy layers. A tailored perspective.",
        "description": "Warm tone exploration with heavyweight cotton knitwear and versatile court sneakers.",
        "model_no": 3,
        "orig_no": 3,
        "items": [
            ("sweatshirt", 50.0, 28.0, ""),
            ("tatum-5-orbit", 48.0, 58.0, ""),
            ("tshirt", 45.0, 88.0, ""),
        ]
    },
    {
        "position": 5,
        "name": "Studio Day",
        "subtitle": "A grey crew and your favourite denim.",
        "description": "Effortless casual styling featuring tonal grey fleece and monochrome leather sneakers.",
        "model_no": 2,
        "orig_no": 2,
        "items": [
            ("hoodie", 50.0, 28.0, ""),
            ("air-jordan-12-retro-copy", 48.0, 58.0, ""),
            ("tshirt", 45.0, 88.0, ""),
        ]
    },
]


class Command(BaseCommand):
    help = "Seeds database with VOID STORE categories, 8 products with variants, 6 runway looks, and demo user"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE("--- SEEDING VOID STORE DATABASE ---"))

        # 1. Categories
        cat_map = {}
        for name, slug, desc in CATEGORIES_DATA:
            cat, _ = Category.objects.update_or_create(
                slug=slug,
                defaults={"name": name, "description": desc}
            )
            cat_map[slug] = cat
        self.stdout.write(self.style.SUCCESS(f"[OK] Seeded {len(cat_map)} categories."))

        # 2. Products and ProductVariants
        prod_map = {}
        for item in PRODUCTS_DATA:
            category = cat_map.get(item["category"])
            orig_p = Decimal(item["original_price"]) if item["original_price"] else None
            product, _ = Product.objects.update_or_create(
                slug=item["slug"],
                defaults={
                    "name": item["name"],
                    "category": category,
                    "vendor": item["vendor"],
                    "price": Decimal(item["price"]),
                    "original_price": orig_p,
                    "image": item["image"],
                    "description": item["description"],
                    "details": item["details"],
                    "is_featured": True,
                }
            )
            prod_map[item["slug"]] = product

            # Seed variants
            for idx, sz in enumerate(item["sizes"]):
                stock = 15 if idx > 0 else 8  # healthy realistic stock
                ProductVariant.objects.update_or_create(
                    product=product,
                    size=sz,
                    defaults={
                        "stock": stock,
                        "sku": f"VOID-{item['slug'][:6].upper()}-{sz}"
                    }
                )

        self.stdout.write(self.style.SUCCESS(f"[OK] Seeded {len(prod_map)} products with size variants."))

        # 3. Runway Looks and LookItems
        LookItem.objects.all().delete()
        Look.objects.all().delete()

        for look_data in LOOKS_DATA:
            m = look_data["model_no"]
            o = look_data["orig_no"]
            look = Look.objects.create(
                position=look_data["position"],
                name=look_data["name"],
                subtitle=look_data["subtitle"],
                description=look_data["description"],
                image=f"assets/model-{m}-640.webp",
                image_hd=f"assets/original-look-{o}.webp",
            )
            for order, (prod_slug, px, py, tag) in enumerate(look_data["items"]):
                prod = prod_map[prod_slug]
                LookItem.objects.create(
                    look=look,
                    product=prod,
                    order=order,
                    pin_x=px,
                    pin_y=py,
                    tag=tag
                )

        self.stdout.write(self.style.SUCCESS(f"[OK] Seeded {len(LOOKS_DATA)} runway looks with interactive pins."))

        # 4. Superuser & Demo User
        if not User.objects.filter(username="admin").exists():
            admin = User.objects.create_superuser("admin", "admin@voidstore.com", "admin12345")
            admin.first_name = "Admin"
            admin.last_name = "User"
            admin.save()
            self.stdout.write(self.style.SUCCESS("[OK] Created superuser 'admin' with password 'admin12345'."))
        else:
            self.stdout.write(self.style.NOTICE("[SKIP] Superuser 'admin' already exists."))

        if not User.objects.filter(username="demouser").exists():
            demo = User.objects.create_user("demouser", "demo@voidstore.com", "demo12345")
            demo.first_name = "Alexander"
            demo.last_name = "Wright"
            demo.save()
            self.stdout.write(self.style.SUCCESS("[OK] Created demo user 'demouser' with password 'demo12345'."))
        else:
            self.stdout.write(self.style.NOTICE("[SKIP] Demo user 'demouser' already exists."))

        self.stdout.write(self.style.SUCCESS("--- SEEDING COMPLETED SUCCESSFULLY ---"))
