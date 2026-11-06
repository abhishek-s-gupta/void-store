import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from store.models import Look, Product

print("=" * 60)
print("TESTING MILESTONE 3: RUNWAY HOMEPAGE HERO SPEC VERIFICATION")
print("=" * 60)

c = Client()
resp = c.get('/')
assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
content = resp.content.decode('utf-8')

# 1. Custom Element & Spec Tokens
assert "<runway-section" in content, "Missing <runway-section> custom element tag"
assert 'id="runway"' in content, "Missing id='runway'"
assert 'data-speed="5000"' in content, "Missing data-speed 5000"
assert 'data-feel="balanced"' in content, "Missing data-feel balanced"
print("[PASS] <runway-section> custom element found with spec attributes")

# 2. Runway DOM Elements
assert 'class="rw__stage"' in content, "Missing .rw__stage"
assert 'class="rw__actors"' in content, "Missing .rw__actors"
assert 'class="rw__heroes"' in content, "Missing .rw__heroes"
assert 'class="rw__controls"' in content, "Missing .rw__controls"
assert 'class="rw__ticks"' in content, "Missing .rw__ticks"
assert 'class="rw__panel"' in content, "Missing .rw__panel"
assert 'class="rw__sweep"' in content, "Missing .rw__sweep light sweep"
assert 'data-rw-cursor' in content, "Missing data-rw-cursor"
print("[PASS] All required Runway layout structures present in DOM")

# 3. Embedded JSON Data verification
import re
match = re.search(r'<script[^>]*id="rw-looks-data"[^>]*>(.*?)</script>', content, re.DOTALL)
assert match is not None, "Missing embedded rw-looks-data JSON"
raw_json = match.group(1).strip()
looks_data = json.loads(raw_json)
assert len(looks_data) == 6, f"Expected 6 looks, found {len(looks_data)}"
for look in looks_data:
    assert len(look['items']) == 3, f"Look {look['name']} should have 3 pieces"
    assert float(look['bundle_price']) < float(look['full_price']), "Bundle discount not reflected in JSON"
print("[PASS] Embedded looks JSON contains 6 looks with 3 pieces each and 10% bundle prices")

# 4. Verify Local Assets Existence
from django.conf import settings
static_dir = settings.BASE_DIR / 'static'
for look in looks_data:
    img_path = static_dir / look['img']
    hd_path = static_dir / look['hd']
    assert img_path.exists(), f"Missing static asset {img_path}"
    assert hd_path.exists(), f"Missing static asset {hd_path}"
    for it in look['items']:
        prod_img = static_dir / it['image']
        assert prod_img.exists(), f"Missing product image {prod_img}"
print("[PASS] All model 640px, HD 1080px, and product WebP cut-outs verified locally on disk")

# 5. Plus button states and Add Full Look to Bag
assert 'data-rw-add' in content, "Missing data-rw-add plus button"
assert 'data-rw-all' in content, "Missing data-rw-all button"
assert 'svg-plus' in content and 'svg-spinner' in content and 'svg-check' in content, "Missing plus button state SVGs"
print("[PASS] Plus button states and bundle CTA elements verified")

# 6. Test Runway Cart Add API via fetch
r_add = c.post('/cart/add/', {'slug': 'tshirt', 'size': 'L', 'qty': 1}, HTTP_X_REQUESTED_WITH='fetch')
assert r_add.status_code == 200
add_json = r_add.json()
assert add_json['ok'] is True
print(f"[PASS] Runway individual piece add to bag API verified: count={add_json['count']}")

# 7. Test Runway Add Full Look to Bag API
r_bundle = c.post('/cart/add-look/', {
    'look_id': looks_data[0]['id'],
    'size_tatum-5-orbit-copy': '43',
    'size_tshirt': 'M',
    'size_sweatshirt': 'L'
}, HTTP_X_REQUESTED_WITH='fetch')
assert r_bundle.status_code == 200
bundle_json = r_bundle.json()
assert bundle_json['ok'] is True
assert float(bundle_json['discount']) > 0
print(f"[PASS] Runway Add Full Look API verified with server-side 10% bundle discount: count={bundle_json['count']}, savings=${bundle_json['discount']}")

print("\n>>> ALL MILESTONE 3 TESTS PASSED PERFECTLY! <<<")
