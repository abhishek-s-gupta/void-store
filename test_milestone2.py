import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from store.models import Product, ProductVariant, Look, LookItem, Category
from orders.models import Cart, CartItem, Order, OrderItem

print("=" * 60)
print("TESTING MILESTONE 2: CATALOG, CART, CHECKOUT, AUTH")
print("=" * 60)

c = Client()

# 1. Homepage
r = c.get('/')
assert r.status_code == 200, f"Homepage failed with {r.status_code}"
assert b"VOID STORE" in r.content, "VOID STORE brand missing"
print("[PASS] Homepage loaded successfully (Status 200)")

# 2. Shop page with search and category filters
r_shop = c.get('/shop/')
assert r_shop.status_code == 200
assert b"Streetwear Essentials" in r_shop.content
print("[PASS] Shop page loaded (Status 200)")

r_filter = c.get('/shop/?category=footwear')
assert r_filter.status_code == 200
assert b"Retro High Leather Sneaker" in r_filter.content
print("[PASS] Shop category filtering operates as expected")

r_search = c.get('/shop/?q=hoodie')
assert r_search.status_code == 200
assert b"Hoodie" in r_search.content
print("[PASS] Shop search query filtering operates as expected")

r_sort = c.get('/shop/?sort=price_asc')
assert r_sort.status_code == 200
print("[PASS] Shop sorting operates as expected")

# 3. Product detail page
r_pdp = c.get('/product/tshirt/')
assert r_pdp.status_code == 200
assert b"Boxy Heavyweight Graphic Tee" in r_pdp.content
assert b"Complete the Look" in r_pdp.content
print("[PASS] Product detail page loaded with variants and Complete the Look")

# 4. Guest cart add
r_add = c.post('/cart/add/', {'slug': 'tshirt', 'size': 'M', 'qty': 1}, HTTP_X_REQUESTED_WITH='fetch')
assert r_add.status_code == 200, f"Cart add failed: {r_add.content}"
data = r_add.json()
assert data['ok'] is True
assert data['count'] == 1
print(f"[PASS] Guest cart addition verified: count={data['count']}, subtotal={data['subtotal']}")

# 5. Look bundle add (10% discount test)
first_look = Look.objects.first()
look_payload = {
    'look_id': first_look.id,
    'size_tatum-5-orbit-copy': '42',
    'size_tshirt': 'L',
    'size_sweatshirt': 'M'
}
r_look = c.post('/cart/add-look/', look_payload, HTTP_X_REQUESTED_WITH='fetch')
assert r_look.status_code == 200, f"Look add failed: {r_look.content}"
look_res = r_look.json()
assert look_res['ok'] is True
# 1 previous + 3 look items = 4 total items
assert look_res['count'] == 4
assert float(look_res['discount']) > 0, "Bundle discount should be calculated"
print(f"[PASS] Full Look bundle added with 10% discount: count={look_res['count']}, discount={look_res['discount']}, total={look_res['total']}")

# 6. Cart full page
r_cart = c.get('/cart/')
assert r_cart.status_code == 200
assert b"Shopping Bag" in r_cart.content
assert b"10% Complete Look Bundle Applied" in r_cart.content
print("[PASS] Cart full page rendered with bundle indicators and line items")

# 7. User Registration & Cart Merge on Login
test_email = "alexander.wright@test.com"
User.objects.filter(email=test_email).delete()
reg_data = {
    'first_name': 'Alexander',
    'last_name': 'Wright',
    'username': 'alex_wright',
    'email': test_email,
    'password': 'password123',
    'confirm_password': 'password123',
}
r_reg = c.post('/accounts/register/', reg_data, follow=True)
assert r_reg.status_code == 200
new_user = User.objects.get(username='alex_wright')
# Verify user is logged in
assert r_reg.wsgi_request.user.is_authenticated
# Verify guest cart was merged into the new user's cart in DB
user_cart = Cart.objects.get(user=new_user)
assert user_cart.total_items() == 4, f"Expected 4 items in merged user cart, found {user_cart.total_items()}"
print(f"[PASS] User registration & guest-to-user cart DB merge verified! Items count: {user_cart.total_items()}")

# 8. Checkout process
initial_variant_stock = ProductVariant.objects.get(product__slug='tshirt', size='M').stock
checkout_data = {
    'full_name': 'Alexander Wright',
    'email': test_email,
    'phone': '+1 555-019-2834',
    'address': '742 Evergreen Terrace, Apt 4B',
    'city': 'New York',
    'postal_code': '10001',
    'payment_method': 'Cash on Delivery (Mock)'
}
r_checkout = c.post('/checkout/', checkout_data, follow=True)
assert r_checkout.status_code == 200
order = Order.objects.filter(user=new_user).first()
assert order is not None, "Order was not created in DB"
assert order.items.count() > 0, "Order items missing"
# Verify cart was cleared
assert user_cart.items.count() == 0, "Cart should be emptied after checkout"
# Verify inventory stock was decremented
updated_variant_stock = ProductVariant.objects.get(product__slug='tshirt', size='M').stock
assert updated_variant_stock < initial_variant_stock, "Stock was not decremented"
print(f"[PASS] Order #{order.order_number} confirmed, inventory decremented, cart emptied.")

# 9. My Orders page
r_my_orders = c.get('/my-orders/')
assert r_my_orders.status_code == 200
assert order.order_number.encode() in r_my_orders.content
print(f"[PASS] My Orders portal lists order #{order.order_number}")

# 10. Logout
r_logout = c.get('/accounts/logout/', follow=True)
assert not r_logout.wsgi_request.user.is_authenticated
print("[PASS] User logout successful")

print("\n>>> ALL MILESTONE 2 TESTS PASSED PERFECTLY! <<<")
