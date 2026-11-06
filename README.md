# VOID STORE — Luxury Streetwear E-Commerce Platform

> **Task 1: Simple E-commerce Store (College Project Submission)**  
> **Architecture & Creative Direction:** Brutalist Luxury Minimalist Fashion Platform featuring the interactive **"Try the Look." 3D Runway Hero Carousel**.

---

## 1. Overview & Key Capabilities

**VOID STORE** is an end-to-end full-stack e-commerce web application engineered with **Django 5** on the backend and **vanilla HTML5, CSS3, and modern JavaScript (ES2022)** on the frontend—with zero third-party animation libraries or external UI frameworks.

### Required Features:
1. **Interactive 3D Runway Hero (`<runway-section>`)**:
   - Exact pixel-level realization of `runway-spec.md`.
   - Desktop 3D Ring carousel with 12 bodies (6 originals + 6 clones), critically damped springs ($K=95, C=19.49$), depth blur up to 6.5px, and perspective perspective shrinking toward a 36% horizon line.
   - Phone classic diagonal walk mode ($\le 749\text{px}$) with exit stride past the camera.
   - 5-second autoplay with linear progress fill ticks, pause/play toggle, and engagement pausing.
   - Smooth pointer drag / swipe gesture physics with momentum release.
   - Custom floating "Drag / View" cursor with lerp tracking.
   - High-resolution stationary hero swap at rest (`rw--still`) with anatomical hotspot pins.
   - Soft-light sweep band animation (`rw-sweep 1.5s`) across models on look transitions.
   - Dynamic feet detection probe using an offscreen canvas alpha scan to anchor model soles to the stage floor line.
   - "View Look" lightbox modal with high-definition cut-outs and interactive numbered pins.
   - Server-side 10% bundle discount applied to full 3-piece looks.
2. **Product Catalog & Shop Listing (`/shop/`)**:
   - Monolithic grid with responsive column wrapping.
   - Category filtering (Footwear, T-Shirts, Hoodies & Sweaters, Outerwear).
   - Real-time text search querying titles, descriptions, and materials.
   - Price & recency sorting (Low to High, High to Low, Newest Drops, Curated).
3. **Product Details Page (`/product/<slug>/`)**:
   - Showcase gallery, clean architectural framing.
   - Dynamic size variant picker with live inventory verification.
   - Quantity selector (+ / - / input, min 1, max stock).
   - Instant "Add to Bag" button with multi-stage animation (plus $\rightarrow$ spinner $\rightarrow$ check mark).
   - Material composition and technical garment specifications.
   - Curated **"Complete the Look"** block featuring runway look cards and complementary silhouettes.
4. **Shopping Cart Engine (`/cart/` & Slide-Out Drawer)**:
   - Database persistence for authenticated users; session persistence for guest shoppers.
   - **Automatic Cart Merge on Login**: anonymous carts seamlessly combine with user carts upon registration or login.
   - Real-time slide-out Cart Drawer with line items, quantity steppers, item deletion, live subtotal, and 10% bundle discount calculations.
   - Full dedicated `/cart/` page with order staging breakdown.
5. **Order Processing & Checkout (`/checkout/` & `/orders/`)**:
   - Customer shipping information form (full name, email, phone, street address, city, postal code).
   - Inventory reservation: atomic database transactions verify stock and decrement variant inventory on confirmation.
   - Mock Cash on Delivery (COD) payment verification.
   - Order confirmation receipt page (`/orders/<order_number>/confirmation/`).
   - "My Orders" customer portal listing previous order references, delivery addresses, line items, and fulfillment statuses.
6. **Authentication & User Management (`/accounts/`)**:
   - Custom registration, login, and logout with validation error styling.
   - Pre-seeded evaluation accounts (`demouser` / `demo12345` and `admin` / `admin12345`) with a 1-click Quick-Fill button on the login screen.
7. **Django Admin**:
   - Comprehensive admin suite configured for `Category`, `Product`, `ProductVariant` (inline), `Look`, `LookItem` (inline), `Cart`, `CartItem` (inline), `Order`, and `OrderItem` (inline).
   - Custom management command: `python manage.py seed_demo`.

---

## 2. Technical Stack

- **Backend**: Python 3.13 / Django 5.2.19, Django ORM, SQLite3, Django Auth & Sessions.
- **Frontend**: Django Templates, HTML5, Vanilla CSS3 (Custom Tokens, CSS Grid, Flexbox, Keyframe Animations), Vanilla JavaScript (Web Components, Web Animations, IntersectionObserver, ResizeObserver, Canvas API).
- **Zero Frameworks / Zero Animation Libraries**: No React, Vue, GSAP, or Three.js.

---

## 3. Project File Structure

```text
void-store/
├── config/                  # Django project configuration
│   ├── settings.py          # App registry, templates, static/media paths
│   ├── urls.py              # Central routing table
│   ├── wsgi.py / asgi.py
├── store/                   # Core catalog & runway application
│   ├── models.py            # Category, Product, ProductVariant, Look, LookItem
│   ├── views.py             # home_view, shop_view, product_detail_view
│   ├── urls.py
│   ├── admin.py             # Model admins with tabular inlines
│   └── management/commands/
│       └── seed_demo.py     # Custom management command seeding 6 looks & 8 products
├── orders/                  # Shopping cart & checkout application
│   ├── models.py            # Cart, CartItem, Order, OrderItem
│   ├── cart.py              # Cart engine & session-to-DB merge logic
│   ├── context_processors.py# Global cart count & subtotal metrics
│   ├── views.py             # Cart add/update/remove, checkout, orders
│   └── urls.py
├── accounts/                # Authentication & user profile application
│   ├── forms.py             # Custom UserRegisterForm and UserLoginForm
│   ├── views.py             # register_view, login_view, logout_view
│   └── urls.py
├── static/
│   ├── assets/              # Local transparent WebP models & product cut-outs (no hotlinking)
│   ├── css/
│   │   ├── style.css        # Site-wide brutalist luxury design system
│   │   └── runway.css       # Spec-exact tokens, 3D ring & keyframes
│   └── js/
│       ├── main.js          # Cart drawer, toasts, route transitions, scroll observers
│       └── runway.js        # <runway-section> custom element & 3D carousel physics
├── templates/
│   ├── base.html            # Universal layout, header, footer, cart drawer, toast
│   ├── store/
│   │   ├── home.html        # Homepage with <runway-section> hero
│   │   ├── shop.html        # Catalog grid, search, categories, sort
│   │   └── product_detail.html # Detail view, size picker, complete the look
│   ├── orders/
│   │   ├── cart.html        # Dedicated shopping bag page
│   │   ├── checkout.html    # Express checkout form & summary
│   │   ├── confirmation.html# Order confirmation receipt
│   │   └── my_orders.html   # Customer order archive
│   └── accounts/
│       ├── login.html       # Sign-in page with 1-click demo filler
│       └── register.html    # Client registration form
├── requirements.txt         # Pinned Python package dependencies
├── manage.py
└── README.md
```

---

## 4. Setup & Running Instructions

### Step 1: Clone or Navigate to the Project Folder
```bash
cd C:\Users\abhis\.gemini\antigravity\scratch\void-store
```

### Step 2: Create & Activate Virtual Environment
```bash
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Run Migrations
```bash
python manage.py migrate
```

### Step 5: Seed Demo Catalog & Test Accounts
```bash
python manage.py seed_demo
```
*This command creates 4 categories, 8 products with variant sizes/stock, 6 runway looks with anatomical hotspot coordinates, an `admin` superuser, and a `demouser` customer account.*

### Step 6: Create Superuser (Optional if already seeded)
```bash
python manage.py createsuperuser
```

### Step 7: Launch the Development Server
```bash
python manage.py runserver
```
Visit **`http://127.0.0.1:8000/`** in your browser to experience the site.

---

## 5. Pre-Configured Demo Accounts for Grading

| Role | Username / Email | Password | Permissions |
|---|---|---|---|
| **Demo Customer** | `demouser` / `demo@voidstore.com` | `demo12345` | Can browse, add to bag, checkout, view order history |
| **Administrator** | `admin` / `admin@voidstore.com` | `admin12345` | Full access to Django admin portal (`/admin/`) |

*Tip: On `/accounts/login/`, click the **"Quick-Fill Demo Account"** button to automatically populate credentials.*

---

## 6. Verification & Automated Test Suites

The project includes two end-to-end automated test suites verifying all grading criteria:

```bash
# Run Milestone 2 Verification (Catalog, Cart, Merge, Checkout, Orders)
python test_milestone2.py

# Run Milestone 3 Verification (Runway Section, 3D Ring, Assets, Bundle Cart API)
python test_milestone3.py
```
Both test suites exit with code `0` and verify complete functional compliance.
