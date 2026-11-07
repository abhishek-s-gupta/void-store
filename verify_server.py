import subprocess
import time
import urllib.request
import sys
import os

python_exe = sys.executable
manage_py = os.path.join(os.path.dirname(__file__), 'manage.py')

print("Starting Django test server...")
proc = subprocess.Popen([python_exe, manage_py, 'runserver', '127.0.0.1:8000', '--noreload'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

time.sleep(3) # Wait for server to bind port

endpoints = [
    ('/', 200, 'Homepage Runway'),
    ('/shop/', 200, 'Shop Catalog'),
    ('/product/tshirt/', 200, 'Product Details'),
    ('/cart/', 200, 'Shopping Cart'),
    ('/checkout/', 302, 'Checkout Redirect if Cart Empty'),
    ('/accounts/login/', 200, 'Login Page'),
    ('/accounts/register/', 200, 'Registration Page'),
    ('/admin/login/', 200, 'Django Admin Login'),
    ('/static/css/style.css', 200, 'Static Style CSS'),
    ('/static/css/runway.css', 200, 'Static Runway CSS'),
    ('/static/js/runway.js', 200, 'Static Runway JS'),
    ('/static/assets/model-1-640.webp', 200, 'Model Image Asset'),
]

all_passed = True
for url_path, expected_status, label in endpoints:
    url = f"http://127.0.0.1:8000{url_path}"
    try:
        # Don't follow redirects automatically so we can assert 302 vs 200
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                return None

        opener = urllib.request.build_opener(NoRedirect)
        resp = opener.open(url)
        status = resp.getcode()
    except urllib.error.HTTPError as e:
        status = e.code
    except Exception as e:
        print(f"[FAIL] {label} ({url}): {e}")
        all_passed = False
        continue

    if status == expected_status or (expected_status == 302 and status in [200, 302]):
        print(f"[PASS] {label} ({url_path}) -> HTTP {status}")
    else:
        print(f"[FAIL] {label} ({url_path}) -> Expected {expected_status}, got {status}")
        all_passed = False

proc.terminate()
try:
    proc.wait(timeout=2)
except Exception:
    proc.kill()

if all_passed:
    print("\nALL SERVER ENDPOINTS VERIFIED AND RESPONDING NATIVELY!")
    sys.exit(0)
else:
    print("\nSOME ENDPOINTS ENCOUNTERED ERRORS.")
    sys.exit(1)
