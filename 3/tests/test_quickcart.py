"""
QuickCart API - Black Box Test Suite
Roll Number: 2024101033
Server: http://localhost:8080

Run with:  pytest test_quickcart.py -v
"""

import requests
import pytest

BASE_URL = "http://localhost:8080/api/v1"
ROLL = "2024101033"

# ─── SHARED HELPERS ────────────────────────────────────────────────────────────

def h(user_id=None):
    """Build headers. Admin calls omit X-User-ID."""
    hdrs = {"X-Roll-Number": ROLL, "Content-Type": "application/json"}
    if user_id is not None:
        hdrs["X-User-ID"] = str(user_id)
    return hdrs

def clear_cart(user_id):
    requests.delete(f"{BASE_URL}/cart/clear", headers=h(user_id))

def add_to_cart(user_id, product_id, quantity):
    return requests.post(
        f"{BASE_URL}/cart/add",
        json={"product_id": product_id, "quantity": quantity},
        headers=h(user_id),
    )

def remove_coupon(user_id):
    requests.post(f"{BASE_URL}/coupon/remove", headers=h(user_id))

def place_order(user_id, product_id, qty, method="CARD"):
    """Helper that adds an item and checks out. Returns order_id or None."""
    add_to_cart(user_id, product_id, qty)
    res = requests.post(
        f"{BASE_URL}/checkout",
        json={"payment_method": method},
        headers=h(user_id),
    )
    if res.status_code == 200:
        data = res.json()
        order = data.get("order") or data
        return order.get("order_id")
    return None

# ══════════════════════════════════════════════════════════════════════════════
# 1. HEADER VALIDATION
# ══════════════════════════════════════════════════════════════════════════════

class TestHeaders:
    """
    TC-HDR-01..07
    Every request needs X-Roll-Number (integer).
    User-scoped endpoints also need X-User-ID (positive int, must exist).
    """

    # TC-HDR-01: Missing X-Roll-Number → 401
    def test_missing_roll_number_returns_401(self):
        res = requests.get(f"{BASE_URL}/admin/users")
        assert res.status_code == 401, "Missing X-Roll-Number must return 401"

    # TC-HDR-02: Non-integer roll number (letters) → 400
    def test_roll_number_letters_returns_400(self):
        res = requests.get(f"{BASE_URL}/admin/users",
                           headers={"X-Roll-Number": "abc"})
        assert res.status_code == 400

    # TC-HDR-03: Non-integer roll number (symbols) → 400
    def test_roll_number_symbols_returns_400(self):
        res = requests.get(f"{BASE_URL}/admin/users",
                           headers={"X-Roll-Number": "@@!!"})
        assert res.status_code == 400

    # TC-HDR-04: Valid roll number, admin endpoint (no user ID needed) → 200
    def test_valid_roll_number_admin_returns_200(self):
        res = requests.get(f"{BASE_URL}/admin/users", headers={"X-Roll-Number": ROLL})
        assert res.status_code == 200

    # TC-HDR-05: Missing X-User-ID on user-scoped endpoint → 400
    def test_missing_user_id_on_user_endpoint_returns_400(self):
        res = requests.get(f"{BASE_URL}/profile",
                           headers={"X-Roll-Number": ROLL})
        assert res.status_code == 400

    # TC-HDR-06: Non-existent user ID → 400
    def test_nonexistent_user_id_returns_400(self):
        res = requests.get(f"{BASE_URL}/profile",
                           headers={"X-Roll-Number": ROLL, "X-User-ID": "999999"})
        assert res.status_code == 400

    # TC-HDR-07: Admin endpoint does NOT require X-User-ID
    def test_admin_endpoint_without_user_id_returns_200(self):
        res = requests.get(f"{BASE_URL}/admin/coupons",
                           headers={"X-Roll-Number": ROLL})
        assert res.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
# 2. ADMIN ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

class TestAdmin:
    """
    TC-ADMIN-01..08
    Admin endpoints return full DB state including inactive/expired records.
    """

    # TC-ADMIN-01: GET /admin/users returns list with wallet and loyalty
    def test_get_all_users_returns_list(self):
        res = requests.get(f"{BASE_URL}/admin/users", headers=h())
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list) and len(data) > 0
        assert "wallet_balance" in data[0]
        assert "loyalty_points" in data[0]

    # TC-ADMIN-02: GET /admin/users/{id} returns single user
    def test_get_single_user(self):
        res = requests.get(f"{BASE_URL}/admin/users/1", headers=h())
        assert res.status_code == 200
        assert res.json()["user_id"] == 1

    # TC-ADMIN-03: GET /admin/products includes inactive products
    def test_admin_products_includes_inactive(self):
        res = requests.get(f"{BASE_URL}/admin/products", headers=h())
        assert res.status_code == 200
        data = res.json()
        inactive = [p for p in data if not p["is_active"]]
        assert len(inactive) > 0, "Admin products must include inactive items"

    # TC-ADMIN-04: GET /admin/coupons includes expired coupons
    def test_admin_coupons_includes_expired(self):
        res = requests.get(f"{BASE_URL}/admin/coupons", headers=h())
        assert res.status_code == 200
        codes = [c["coupon_code"] for c in res.json()]
        assert "EXPIRED100" in codes, "Admin coupons must include expired ones"

    # TC-ADMIN-05: GET /admin/carts returns list
    def test_get_all_carts(self):
        res = requests.get(f"{BASE_URL}/admin/carts", headers=h())
        assert res.status_code == 200

    # TC-ADMIN-06: GET /admin/orders returns list
    def test_get_all_orders(self):
        res = requests.get(f"{BASE_URL}/admin/orders", headers=h())
        assert res.status_code == 200

    # TC-ADMIN-07: GET /admin/tickets returns list
    def test_get_all_tickets(self):
        res = requests.get(f"{BASE_URL}/admin/tickets", headers=h())
        assert res.status_code == 200

    # TC-ADMIN-08: GET /admin/addresses returns list
    def test_get_all_addresses(self):
        res = requests.get(f"{BASE_URL}/admin/addresses", headers=h())
        assert res.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
# 3. PROFILE
# ══════════════════════════════════════════════════════════════════════════════

class TestProfile:
    """
    TC-PROF-01..08
    Name: 2–50 chars. Phone: exactly 10 digits.
    """
    UID = 50  # Uma Davis

    # TC-PROF-01: GET profile returns user data
    def test_get_profile(self):
        res = requests.get(f"{BASE_URL}/profile", headers=h(self.UID))
        assert res.status_code == 200
        data = res.json()
        assert "name" in data and "email" in data

    # TC-PROF-02: PUT valid name + phone succeeds
    def test_update_profile_valid(self):
        res = requests.put(f"{BASE_URL}/profile",
                           json={"name": "Uma Davis", "phone": "8687310389"},
                           headers=h(self.UID))
        assert res.status_code == 200

    # TC-PROF-03: Name length 1 (below min) → 400
    def test_name_too_short_returns_400(self):
        res = requests.put(f"{BASE_URL}/profile",
                           json={"name": "U", "phone": "8687310389"},
                           headers=h(self.UID))
        assert res.status_code == 400

    # TC-PROF-04: Name length 51 (above max) → 400
    def test_name_too_long_returns_400(self):
        res = requests.put(f"{BASE_URL}/profile",
                           json={"name": "A" * 51, "phone": "8687310389"},
                           headers=h(self.UID))
        assert res.status_code == 400

    # TC-PROF-05: Name length 2 (boundary min) → 200
    def test_name_boundary_min_2_chars(self):
        res = requests.put(f"{BASE_URL}/profile",
                           json={"name": "AB", "phone": "8687310389"},
                           headers=h(self.UID))
        assert res.status_code == 200

    # TC-PROF-06: Name length 50 (boundary max) → 200
    def test_name_boundary_max_50_chars(self):
        res = requests.put(f"{BASE_URL}/profile",
                           json={"name": "A" * 50, "phone": "8687310389"},
                           headers=h(self.UID))
        assert res.status_code == 200

    # TC-PROF-07: Phone 9 digits (below 10) → 400
    def test_phone_9_digits_returns_400(self):
        res = requests.put(f"{BASE_URL}/profile",
                           json={"name": "Uma Davis", "phone": "123456789"},
                           headers=h(self.UID))
        assert res.status_code == 400

    # TC-PROF-08: Phone 11 digits (above 10) → 400
    def test_phone_11_digits_returns_400(self):
        res = requests.put(f"{BASE_URL}/profile",
                           json={"name": "Uma Davis", "phone": "12345678901"},
                           headers=h(self.UID))
        assert res.status_code == 400


# ══════════════════════════════════════════════════════════════════════════════
# 4. ADDRESSES
# ══════════════════════════════════════════════════════════════════════════════

class TestAddresses:
    """
    TC-ADDR-01..12
    label: HOME|OFFICE|OTHER. street: 5–100. city: 2–50. pincode: exactly 6 digits.
    Only one address can be default at a time.
    Only street and is_default are updatable.
    """
    UID = 80  # Sam Smith

    def _add(self, label="HOME", street="123 Test Street Hyderabad",
             city="Hyderabad", pincode="500001", is_default=False):
        return requests.post(f"{BASE_URL}/addresses",
                             json={"label": label, "street": street,
                                   "city": city, "pincode": pincode,
                                   "is_default": is_default},
                             headers=h(self.UID))

    def _get_addr_id(self, res):
        data = res.json()
        return (data.get("address_id")
                or (data.get("address") or {}).get("address_id"))

    # TC-ADDR-01: GET addresses returns list
    def test_get_addresses(self):
        res = requests.get(f"{BASE_URL}/addresses", headers=h(self.UID))
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    # TC-ADDR-02: POST valid HOME address succeeds and returns address object with address_id
    def test_add_home_address(self):
        res = self._add("HOME")
        assert res.status_code in [200, 201]
        data = res.json()
        addr = data.get("address") or data
        assert "address_id" in addr

    # TC-ADDR-03: POST valid OFFICE address succeeds
    def test_add_office_address(self):
        res = self._add("OFFICE", street="456 Office Boulevard City")
        assert res.status_code in [200, 201]

    # TC-ADDR-04: POST valid OTHER address succeeds
    def test_add_other_address(self):
        res = self._add("OTHER", street="789 Other Lane Area District")
        assert res.status_code in [200, 201]

    # TC-ADDR-05: Invalid label → 400
    def test_invalid_label_returns_400(self):
        res = self._add("SCHOOL")
        assert res.status_code == 400

    # TC-ADDR-06: Street too short (4 chars) → 400
    def test_street_too_short_returns_400(self):
        res = self._add(street="123S")
        assert res.status_code == 400

    # TC-ADDR-07: City too short (1 char) → 400
    def test_city_too_short_returns_400(self):
        res = self._add(city="A")
        assert res.status_code == 400

    # TC-ADDR-08: Pincode 4 digits → 400
    def test_pincode_too_short_returns_400(self):
        res = self._add(pincode="5000")
        assert res.status_code == 400

    # TC-ADDR-09: Pincode 7 digits → 400
    def test_pincode_too_long_returns_400(self):
        res = self._add(pincode="5000011")
        assert res.status_code == 400

    # TC-ADDR-10: Only one default address allowed at a time
    def test_only_one_default_address(self):
        self._add("HOME", street="First Default Home Street City",
                  is_default=True)
        self._add("OFFICE", street="Second Default Office Avenue Town",
                  is_default=True)
        res = requests.get(f"{BASE_URL}/addresses", headers=h(self.UID))
        defaults = [a for a in res.json() if a.get("is_default")]
        assert len(defaults) == 1, "Only one address can be default"

    # TC-ADDR-11: Delete non-existent address → 404
    def test_delete_nonexistent_address_returns_404(self):
        res = requests.delete(f"{BASE_URL}/addresses/999999", headers=h(self.UID))
        assert res.status_code == 404

    # TC-ADDR-12: Update returns new data (not old)
    def test_update_address_reflects_new_data(self):
        post_res = self._add(street="Original Street Name Here Long")
        addr_id = self._get_addr_id(post_res)
        if addr_id:
            upd = requests.put(f"{BASE_URL}/addresses/{addr_id}",
                               json={"street": "Updated Street Name Here New", "is_default": False},
                               headers=h(self.UID))
            assert upd.status_code == 200
            result = upd.json()
            addr = result.get("address") or result
            assert "Updated" in (addr.get("street") or ""), \
                "PUT must return updated data, not stale"
            
    # TC-ADDR-13: Delete existing address succeeds
    def test_delete_existing_address(self):
        post_res = self._add(street="Address To Be Deleted")
        addr_id = self._get_addr_id(post_res)
        if addr_id:
            del_res = requests.delete(f"{BASE_URL}/addresses/{addr_id}", headers=h(self.UID))
            assert del_res.status_code in [200, 204]
            
            # Verify it's actually gone
            get_res = requests.get(f"{BASE_URL}/addresses", headers=h(self.UID))
            ids = [a.get("address_id") for a in get_res.json()]
            assert addr_id not in ids, "Address should no longer appear in the list"

    # TC-ADDR-14: Update ignores or rejects changes to restricted fields
    def test_update_restricted_fields(self):
        post_res = self._add(city="OriginalCity", label="HOME", pincode="500001")
        addr_id = self._get_addr_id(post_res)
        if addr_id:
            upd = requests.put(f"{BASE_URL}/addresses/{addr_id}",
                               json={"city": "NewCity", "label": "OFFICE", "pincode": "999999", "street": "Updated Street"},
                               headers=h(self.UID))
            
            # It might return 400, or it might return 200 but ignore the restricted fields.
            # We assert that the city/label/pincode MUST NOT have changed if it returns 200.
            if upd.status_code == 200:
                result = upd.json()
                addr = result.get("address") or result
                assert addr.get("city") == "OriginalCity", "City should not be updatable"
                assert addr.get("label") == "HOME", "Label should not be updatable"
                assert addr.get("pincode") == "500001", "Pincode should not be updatable"


# ══════════════════════════════════════════════════════════════════════════════
# 5. PRODUCTS
# ══════════════════════════════════════════════════════════════════════════════

class TestProducts:
    """
    TC-PROD-01..10
    Public list shows only active products.
    Single product lookup returns 404 for non-existent.
    Prices must match DB. Filtering/search/sort supported.
    """
    UID = 1

    # TC-PROD-01: GET /products returns list
    def test_get_products_returns_list(self):
        res = requests.get(f"{BASE_URL}/products", headers=h(self.UID))
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    # TC-PROD-02: Inactive products NOT in public list
    def test_inactive_products_excluded(self):
        res = requests.get(f"{BASE_URL}/products", headers=h(self.UID))
        ids = [p["product_id"] for p in res.json()]
        assert 90 not in ids, "Inactive product_id 90 must NOT appear in /products"

    # TC-PROD-03: Active products present in list
    def test_active_products_present(self):
        res = requests.get(f"{BASE_URL}/products", headers=h(self.UID))
        ids = [p["product_id"] for p in res.json()]
        assert 1 in ids

    # TC-PROD-04: GET /products/{id} returns correct product
    def test_get_single_product(self):
        res = requests.get(f"{BASE_URL}/products/1", headers=h(self.UID))
        assert res.status_code == 200
        assert res.json()["product_id"] == 1

    # TC-PROD-05: Non-existent product → 404
    def test_nonexistent_product_returns_404(self):
        res = requests.get(f"{BASE_URL}/products/99999", headers=h(self.UID))
        assert res.status_code == 404

    # TC-PROD-06: Price matches DB value exactly (Mango Alphonso = 250)
    def test_product_price_is_exact(self):
        res = requests.get(f"{BASE_URL}/products/5", headers=h(self.UID))
        assert res.status_code == 200
        assert res.json()["price"] == 250, "Price must match DB exactly"

    # TC-PROD-07: Filter by category returns only that category
    def test_filter_by_category(self):
        res = requests.get(f"{BASE_URL}/products?category=Fruits", headers=h(self.UID))
        assert res.status_code == 200
        for p in res.json():
            assert p["category"] == "Fruits"

    # TC-PROD-08: Search by name returns matching results
    def test_search_by_name(self):
        res = requests.get(f"{BASE_URL}/products?search=Apple", headers=h(self.UID))
        assert res.status_code == 200
        data = res.json()
        assert len(data) > 0
        for p in data:
            assert "apple" in p["name"].lower()

    # TC-PROD-09: Sort by price ascending
    def test_sort_price_ascending(self):
        res = requests.get(f"{BASE_URL}/products?sort=price_asc", headers=h(self.UID))
        assert res.status_code == 200
        prices = [p["price"] for p in res.json()]
        assert prices == sorted(prices), "Products not sorted ascending"

    # TC-PROD-10: Sort by price descending
    def test_sort_price_descending(self):
        res = requests.get(f"{BASE_URL}/products?sort=price_desc", headers=h(self.UID))
        assert res.status_code == 200
        prices = [p["price"] for p in res.json()]
        assert prices == sorted(prices, reverse=True), "Products not sorted descending"

    # TC-PROD-11: GET /products/{id} for inactive product -> 404
    def test_get_inactive_product_directly_returns_404(self):
        # Product 90 is known to be inactive from TC-PROD-02
        res = requests.get(f"{BASE_URL}/products/90", headers=h(self.UID))
        assert res.status_code == 404, "Direct lookup of inactive product should return 404"

# ══════════════════════════════════════════════════════════════════════════════
# 6. CART
# ══════════════════════════════════════════════════════════════════════════════

class TestCart:
    """
    TC-CART-01..15
    qty >= 1. Duplicate adds accumulate. Subtotal = qty * price. Total = sum of subtotals.
    """
    UID = 10  # Sita Anderson

    def setup_method(self):
        clear_cart(self.UID)

    # TC-CART-01: GET cart returns valid structure
    def test_get_cart(self):
        res = requests.get(f"{BASE_URL}/cart", headers=h(self.UID))
        assert res.status_code == 200

    # TC-CART-02: Add item with qty=1 (minimum valid) → 200
    def test_add_item_qty_1(self):
        res = add_to_cart(self.UID, 1, 1)
        assert res.status_code == 200

    # TC-CART-03: Add item with qty=0 → 400
    def test_add_item_qty_zero_returns_400(self):
        res = add_to_cart(self.UID, 1, 0)
        assert res.status_code == 400

    # TC-CART-04: Add item with qty=-1 → 400
    def test_add_item_negative_qty_returns_400(self):
        res = add_to_cart(self.UID, 1, -1)
        assert res.status_code == 400

    # TC-CART-05: Add non-existent product → 404
    def test_add_nonexistent_product_returns_404(self):
        res = add_to_cart(self.UID, 99999, 1)
        assert res.status_code == 404

    # TC-CART-06: Add out-of-stock product (stock=0) → 400
    def test_add_out_of_stock_product_returns_400(self):
        # product_id 70 has stock_quantity = 0
        res = add_to_cart(self.UID, 70, 1)
        assert res.status_code == 400

    # TC-CART-07: Add quantity exceeding stock → 400
    def test_add_qty_exceeding_stock_returns_400(self):
        # Product 13 (Pineapple) has stock=30; request 31
        res = add_to_cart(self.UID, 13, 31)
        assert res.status_code == 400

    # TC-CART-08: Add quantity at stock limit → 200
    def test_add_qty_at_stock_limit(self):
        # Product 13 (Pineapple) stock=30
        res = add_to_cart(self.UID, 13, 30)
        assert res.status_code == 200

    # TC-CART-09: Adding same product twice accumulates qty (not replaces)
    def test_duplicate_add_accumulates_quantity(self):
        add_to_cart(self.UID, 3, 2)   # Banana qty 2
        add_to_cart(self.UID, 3, 3)   # Banana qty 3 more
        cart = requests.get(f"{BASE_URL}/cart", headers=h(self.UID)).json()
        items = cart.get("items", [])
        banana = next((i for i in items if i["product_id"] == 3), None)
        assert banana is not None
        assert banana["quantity"] == 5, "Quantities must accumulate, not replace"

    # TC-CART-10: Item subtotal = qty * unit price
    def test_item_subtotal_is_correct(self):
        # Product 1 = ₹120; add qty=3 → subtotal = 360
        add_to_cart(self.UID, 1, 3)
        cart = requests.get(f"{BASE_URL}/cart", headers=h(self.UID)).json()
        items = cart.get("items", [])
        apple = next((i for i in items if i["product_id"] == 1), None)
        assert apple is not None
        expected = apple["unit_price"] * apple["quantity"]
        assert apple["subtotal"] == expected, "subtotal must equal qty * unit_price"

    # TC-CART-11: Cart total = sum of all item subtotals
    def test_cart_total_equals_sum_of_subtotals(self):
        add_to_cart(self.UID, 1, 2)   # 120*2 = 240
        add_to_cart(self.UID, 3, 3)   # 40*3  = 120
        cart = requests.get(f"{BASE_URL}/cart", headers=h(self.UID)).json()
        items = cart.get("items", [])
        expected = sum(i["subtotal"] for i in items)
        assert cart["total"] == expected, "Cart total must be exact sum of subtotals"

    # TC-CART-12: Remove item not in cart → 404
    def test_remove_item_not_in_cart_returns_404(self):
        res = requests.post(f"{BASE_URL}/cart/remove",
                            json={"product_id": 99999},
                            headers=h(self.UID))
        assert res.status_code == 404

    # TC-CART-13: Remove existing item → 200
    def test_remove_existing_item(self):
        add_to_cart(self.UID, 1, 1)
        res = requests.post(f"{BASE_URL}/cart/remove",
                            json={"product_id": 1},
                            headers=h(self.UID))
        assert res.status_code == 200

    # TC-CART-14: Update cart item to qty=0 → 400
    def test_update_cart_qty_zero_returns_400(self):
        add_to_cart(self.UID, 1, 2)
        res = requests.post(f"{BASE_URL}/cart/update",
                            json={"product_id": 1, "quantity": 0},
                            headers=h(self.UID))
        assert res.status_code == 400

    # TC-CART-15: Clear cart → 200
    def test_clear_cart(self):
        add_to_cart(self.UID, 1, 1)
        res = requests.delete(f"{BASE_URL}/cart/clear", headers=h(self.UID))
        assert res.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
# 7. COUPONS
# ══════════════════════════════════════════════════════════════════════════════

class TestCoupons:
    """
    TC-CPN-01..08
    Coupon checks: not expired, cart >= min, correct discount calc, cap respected.
    Today = 2026-03-24. Expired coupons: EXPIRED100, EXPIRED50, DEAL5, FLASH25,
    BIGDEAL500, OLDPERCENT20. Valid ones include SAVE50, PERCENT10, BONUS75, etc.
    """
    UID = 30  # Noah Thomas — wallet 88.37

    def setup_method(self):
        clear_cart(self.UID)
        remove_coupon(self.UID)

    # TC-CPN-01: Apply expired coupon → 400
    def test_expired_coupon_returns_400(self):
        add_to_cart(self.UID, 1, 10)  # 1200 > min 1000
        res = requests.post(f"{BASE_URL}/coupon/apply",
                            json={"coupon_code": "EXPIRED100"},
                            headers=h(self.UID))
        assert res.status_code == 400, "Expired coupon must be rejected"

    # TC-CPN-02: Cart total below minimum → 400
    def test_coupon_below_minimum_cart_returns_400(self):
        # BONUS75 requires min_cart_value=750; add only 200 worth
        add_to_cart(self.UID, 3, 5)  # 40*5 = 200
        res = requests.post(f"{BASE_URL}/coupon/apply",
                            json={"coupon_code": "BONUS75"},
                            headers=h(self.UID))
        assert res.status_code == 400

    # TC-CPN-03: Apply valid FIXED coupon → 200
    def test_fixed_coupon_valid(self):
        # SAVE50: FIXED ₹50, min_cart=500; cart=600
        add_to_cart(self.UID, 1, 5)  # 120*5 = 600
        res = requests.post(f"{BASE_URL}/coupon/apply",
                            json={"coupon_code": "SAVE50"},
                            headers=h(self.UID))
        assert res.status_code == 200

    # TC-CPN-04: Apply valid PERCENT coupon → 200
    def test_percent_coupon_valid(self):
        # PERCENT10: 10%, min=300, max=100; cart=360
        add_to_cart(self.UID, 1, 3)  # 360
        res = requests.post(f"{BASE_URL}/coupon/apply",
                            json={"coupon_code": "PERCENT10"},
                            headers=h(self.UID))
        assert res.status_code == 200

    # TC-CPN-05: PERCENT coupon discount capped at max_discount
    def test_percent_coupon_respects_cap(self):
        # PERCENT10: 10% of 1200 = 120, but cap = 100, so discount must be 100
        add_to_cart(self.UID, 1, 10)  # 1200
        res = requests.post(f"{BASE_URL}/coupon/apply",
                            json={"coupon_code": "PERCENT10"},
                            headers=h(self.UID))
        assert res.status_code == 200
        data = res.json()
        discount = (data.get("discount")
                    or (data.get("cart") or {}).get("discount"))
        if discount is not None:
            assert discount == 100, f"Discount capped at 100, got {discount}"

    # TC-CPN-06: FIXED coupon gives exact flat discount
    def test_fixed_coupon_exact_discount(self):
        # SAVE50: flat ₹50 off if cart >= 500
        add_to_cart(self.UID, 1, 5)  # 600
        res = requests.post(f"{BASE_URL}/coupon/apply",
                            json={"coupon_code": "SAVE50"},
                            headers=h(self.UID))
        assert res.status_code == 200
        data = res.json()
        discount = (data.get("discount")
                    or (data.get("cart") or {}).get("discount"))
        if discount is not None:
            assert discount == 50, f"FIXED discount must be exactly 50, got {discount}"

    # TC-CPN-07: Non-existent coupon code → 400
    def test_fake_coupon_returns_400(self):
        add_to_cart(self.UID, 1, 5)
        res = requests.post(f"{BASE_URL}/coupon/apply",
                            json={"coupon_code": "NOTACOUPON"},
                            headers=h(self.UID))
        assert res.status_code == 400

    # TC-CPN-08: Remove coupon → 200
    def test_remove_coupon(self):
        add_to_cart(self.UID, 1, 5)
        requests.post(f"{BASE_URL}/coupon/apply",
                      json={"coupon_code": "SAVE50"},
                      headers=h(self.UID))
        res = requests.post(f"{BASE_URL}/coupon/remove", headers=h(self.UID))
        assert res.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
# 8. CHECKOUT
# ══════════════════════════════════════════════════════════════════════════════

class TestCheckout:
    """
    TC-CHK-01..09
    Payment: COD | WALLET | CARD only.
    GST = 5% added once. COD blocked if total > 5000.
    COD/WALLET → PENDING. CARD → PAID.
    """
    # User 35: Tom Thomas — wallet 72.19 (low, good for COD tests)
    COD_UID  = 35
    # User 36: Charlie White — wallet 2028.36
    CARD_UID = 36
    # User 7: Grace Patel — wallet 5011.31 (high enough for wallet checkout)
    WAL_UID  = 7

    def setup_method(self):
        for uid in [self.COD_UID, self.CARD_UID, self.WAL_UID]:
            clear_cart(uid)

    # TC-CHK-01: Checkout with empty cart → 400
    def test_empty_cart_returns_400(self):
        res = requests.post(f"{BASE_URL}/checkout",
                            json={"payment_method": "COD"},
                            headers=h(self.COD_UID))
        assert res.status_code == 400

    # TC-CHK-02: Invalid payment method → 400
    def test_invalid_payment_method_returns_400(self):
        add_to_cart(self.COD_UID, 1, 1)
        res = requests.post(f"{BASE_URL}/checkout",
                            json={"payment_method": "CRYPTO"},
                            headers=h(self.COD_UID))
        assert res.status_code == 400

    # TC-CHK-03: COD checkout succeeds (total <= 5000)
    def test_cod_checkout_success(self):
        add_to_cart(self.COD_UID, 3, 2)  # Banana 40*2=80, total=84
        res = requests.post(f"{BASE_URL}/checkout",
                            json={"payment_method": "COD"},
                            headers=h(self.COD_UID))
        assert res.status_code == 200

    # TC-CHK-04: COD order has payment_status = PENDING
    def test_cod_payment_status_is_pending(self):
        add_to_cart(self.COD_UID, 3, 2)
        res = requests.post(f"{BASE_URL}/checkout",
                            json={"payment_method": "COD"},
                            headers=h(self.COD_UID))
        assert res.status_code == 200
        order = (res.json().get("order") or res.json())
        assert order.get("payment_status") == "PENDING"

    # TC-CHK-05: CARD order has payment_status = PAID
    def test_card_payment_status_is_paid(self):
        add_to_cart(self.CARD_UID, 1, 1)  # 120
        res = requests.post(f"{BASE_URL}/checkout",
                            json={"payment_method": "CARD"},
                            headers=h(self.CARD_UID))
        assert res.status_code == 200
        order = (res.json().get("order") or res.json())
        assert order.get("payment_status") == "PAID"

    # TC-CHK-06: COD rejected when order total > 5000
    # Product 42 (Ghee 500ml) = ₹380. 14 units → subtotal=5320, total=5586 > 5000
    def test_cod_blocked_above_5000(self):
        add_to_cart(self.COD_UID, 42, 14)
        res = requests.post(f"{BASE_URL}/checkout",
                            json={"payment_method": "COD"},
                            headers=h(self.COD_UID))
        assert res.status_code == 400, "COD must be blocked when total > 5000"

    # TC-CHK-07: GST is exactly 5% (subtotal=300 → total=315)
    def test_gst_is_5_percent(self):
        # Product 18 (Potato) price=30; 10 units → subtotal=300, total=315
        add_to_cart(self.CARD_UID, 18, 10)
        res = requests.post(f"{BASE_URL}/checkout",
                            json={"payment_method": "CARD"},
                            headers=h(self.CARD_UID))
        assert res.status_code == 200
        order = (res.json().get("order") or res.json())
        total = order.get("total_amount") or order.get("total")
        if total is not None:
            assert abs(total - 315.0) < 0.01, f"Expected 315.0 (with 5% GST), got {total}"

    # TC-CHK-08: WALLET checkout fails if balance too low
    # User 289: Yara White — wallet 0.07
    def test_wallet_checkout_insufficient_balance_returns_400(self):
        clear_cart(289)
        add_to_cart(289, 1, 1)  # 120, wallet only 0.07
        res = requests.post(f"{BASE_URL}/checkout",
                            json={"payment_method": "WALLET"},
                            headers=h(289))
        assert res.status_code == 400

    # TC-CHK-09: WALLET checkout succeeds when balance is sufficient
    def test_wallet_checkout_success(self):
        # User 7 wallet=5011.31; Coriander 100g price=15, total=15.75
        add_to_cart(self.WAL_UID, 27, 1)
        res = requests.post(f"{BASE_URL}/checkout",
                            json={"payment_method": "WALLET"},
                            headers=h(self.WAL_UID))
        assert res.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
# 9. WALLET
# ══════════════════════════════════════════════════════════════════════════════

class TestWallet:
    """
    TC-WAL-01..09
    Add: 0 < amount <= 100000. Pay: amount > 0, balance must cover it.
    Exact amount is deducted.
    """
    UID = 57  # Ivy Johnson — wallet 5066.21 (high, won't run dry)

    # TC-WAL-01: GET wallet returns balance
    def test_get_wallet(self):
        res = requests.get(f"{BASE_URL}/wallet", headers=h(self.UID))
        assert res.status_code == 200
        data = res.json()
        assert "balance" in data or "wallet_balance" in data

    # TC-WAL-02: Add valid amount → 200
    def test_add_money_valid(self):
        res = requests.post(f"{BASE_URL}/wallet/add",
                            json={"amount": 100},
                            headers=h(self.UID))
        assert res.status_code == 200

    # TC-WAL-03: Add 0 → 400
    def test_add_zero_returns_400(self):
        res = requests.post(f"{BASE_URL}/wallet/add",
                            json={"amount": 0},
                            headers=h(self.UID))
        assert res.status_code == 400

    # TC-WAL-04: Add negative → 400
    def test_add_negative_returns_400(self):
        res = requests.post(f"{BASE_URL}/wallet/add",
                            json={"amount": -50},
                            headers=h(self.UID))
        assert res.status_code == 400

    # TC-WAL-05: Add 100001 (above 100000 limit) → 400
    def test_add_above_limit_returns_400(self):
        res = requests.post(f"{BASE_URL}/wallet/add",
                            json={"amount": 100001},
                            headers=h(self.UID))
        assert res.status_code == 400

    # TC-WAL-06: Add exactly 100000 (boundary max) → 200
    def test_add_at_max_limit(self):
        res = requests.post(f"{BASE_URL}/wallet/add",
                            json={"amount": 100000},
                            headers=h(self.UID))
        assert res.status_code == 200

    # TC-WAL-07: Pay from wallet → 200
    def test_pay_from_wallet(self):
        res = requests.post(f"{BASE_URL}/wallet/pay",
                            json={"amount": 10},
                            headers=h(self.UID))
        assert res.status_code == 200

    # TC-WAL-08: Pay 0 → 400
    def test_pay_zero_returns_400(self):
        res = requests.post(f"{BASE_URL}/wallet/pay",
                            json={"amount": 0},
                            headers=h(self.UID))
        assert res.status_code == 400

    # TC-WAL-09: Pay more than balance → 400
    # User 289: Yara White — wallet 0.07
    def test_pay_exceeding_balance_returns_400(self):
        res = requests.post(f"{BASE_URL}/wallet/pay",
                            json={"amount": 100},
                            headers=h(289))
        assert res.status_code == 400

    # TC-WAL-10: Exact amount deducted (no extra)
    def test_exact_deduction(self):
        before_data = requests.get(f"{BASE_URL}/wallet", headers=h(self.UID)).json()
        before = before_data.get("balance") or before_data.get("wallet_balance")
        requests.post(f"{BASE_URL}/wallet/pay", json={"amount": 50}, headers=h(self.UID))
        after_data = requests.get(f"{BASE_URL}/wallet", headers=h(self.UID)).json()
        after = after_data.get("balance") or after_data.get("wallet_balance")
        if before is not None and after is not None:
            assert abs((before - after) - 50) < 0.01, "Must deduct exactly the requested amount"


# ══════════════════════════════════════════════════════════════════════════════
# 10. LOYALTY POINTS
# ══════════════════════════════════════════════════════════════════════════════

class TestLoyalty:
    """
    TC-LOY-01..04
    Redeem: points >= 1, user must have enough.
    """
    UID = 1  # Anita Johnson — 448 loyalty points

    # TC-LOY-01: GET loyalty points
    def test_get_loyalty(self):
        res = requests.get(f"{BASE_URL}/loyalty", headers=h(self.UID))
        assert res.status_code == 200
        data = res.json()
        assert "loyalty_points" in data or "points" in data

    # TC-LOY-02: Redeem valid amount → 200
    def test_redeem_valid(self):
        res = requests.post(f"{BASE_URL}/loyalty/redeem",
                            json={"points": 10},
                            headers=h(self.UID))
        assert res.status_code == 200

    # TC-LOY-03: Redeem 0 points → 400
    def test_redeem_zero_returns_400(self):
        res = requests.post(f"{BASE_URL}/loyalty/redeem",
                            json={"points": 0},
                            headers=h(self.UID))
        assert res.status_code == 400

    # TC-LOY-04: Redeem more than available → 400
    # User 219: Suresh Kumar — loyalty_points = 0
    def test_redeem_more_than_available_returns_400(self):
        res = requests.post(f"{BASE_URL}/loyalty/redeem",
                            json={"points": 1},
                            headers=h(219))
        assert res.status_code == 400


# ══════════════════════════════════════════════════════════════════════════════
# 11. ORDERS
# ══════════════════════════════════════════════════════════════════════════════

class TestOrders:
    """
    TC-ORD-01..08
    Cancel: DELIVERED orders cannot be cancelled.
    Cancel restores stock.
    Invoice math: subtotal + 5% GST = total.
    """
    UID = 45  # Amit Davis — wallet 5056.97 (high, can place many orders)

    def setup_method(self):
        clear_cart(self.UID)

    # TC-ORD-01: GET /orders returns list
    def test_get_all_orders(self):
        res = requests.get(f"{BASE_URL}/orders", headers=h(self.UID))
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    # TC-ORD-02: GET /orders/{id} for non-existent → 404
    def test_get_nonexistent_order_returns_404(self):
        res = requests.get(f"{BASE_URL}/orders/999999", headers=h(self.UID))
        assert res.status_code == 404

    # TC-ORD-03: GET /orders/{id} returns valid data for real order
    def test_get_specific_order(self):
        oid = place_order(self.UID, product_id=3, qty=1)
        if oid:
            res = requests.get(f"{BASE_URL}/orders/{oid}", headers=h(self.UID))
            assert res.status_code == 200
            assert res.json().get("order_id") == oid or \
                   (res.json().get("order") or {}).get("order_id") == oid

    # TC-ORD-04: Cancel valid order → 200
    def test_cancel_order(self):
        oid = place_order(self.UID, product_id=3, qty=1)
        if oid:
            res = requests.post(f"{BASE_URL}/orders/{oid}/cancel", headers=h(self.UID))
            assert res.status_code == 200

    # TC-ORD-05: Cancel non-existent order → 404
    def test_cancel_nonexistent_order_returns_404(self):
        res = requests.post(f"{BASE_URL}/orders/999999/cancel", headers=h(self.UID))
        assert res.status_code == 404

    # TC-ORD-06: Stock is restored after cancellation
    def test_stock_restored_on_cancel(self):
        # Get stock before
        before = requests.get(f"{BASE_URL}/products/9", headers=h(self.UID)).json()
        stock_before = before.get("stock_quantity")

        oid = place_order(self.UID, product_id=9, qty=2)
        if oid:
            requests.post(f"{BASE_URL}/orders/{oid}/cancel", headers=h(self.UID))
            after = requests.get(f"{BASE_URL}/products/9", headers=h(self.UID)).json()
            stock_after = after.get("stock_quantity")
            if stock_before is not None and stock_after is not None:
                assert stock_after == stock_before, "Stock must be restored on cancel"

    # TC-ORD-07: GET invoice returns subtotal, gst_amount, and total
    def test_invoice_fields_present(self):
        oid = place_order(self.UID, product_id=18, qty=5)  # Potato 30*5=150
        if oid:
            res = requests.get(f"{BASE_URL}/orders/{oid}/invoice", headers=h(self.UID))
            assert res.status_code == 200
            data = res.json()
            assert "subtotal" in data or "total" in data

    # TC-ORD-08: Invoice math — subtotal=300, GST=15, total=315
    def test_invoice_math_is_correct(self):
        # Product 18 (Potato) price=30, qty=10 → subtotal=300, total=315
        oid = place_order(self.UID, product_id=18, qty=10)
        if oid:
            res = requests.get(f"{BASE_URL}/orders/{oid}/invoice", headers=h(self.UID))
            assert res.status_code == 200
            data = res.json()
            subtotal = data.get("subtotal")
            total = data.get("total")
            if subtotal is not None and total is not None:
                assert abs(subtotal - 300.0) < 0.01, f"Subtotal should be 300, got {subtotal}"
                assert abs(total - 315.0) < 0.01, f"Total should be 315, got {total}"

    # TC-ORD-09: Cancel DELIVERED order -> 400
    def test_cancel_delivered_order_returns_400(self):
        
        delivered_order_id = 2997
        delivered_user_id = 681    
        
        res = requests.post(
            f"{BASE_URL}/orders/{delivered_order_id}/cancel", 
            headers=h(delivered_user_id)
        )
        assert res.status_code == 400, "Cannot cancel a delivered order"

# ══════════════════════════════════════════════════════════════════════════════
# 12. REVIEWS
# ══════════════════════════════════════════════════════════════════════════════

class TestReviews:
    """
    TC-REV-01..09
    Rating: 1–5 inclusive. Comment: 1–200 chars.
    Average must be a real decimal, not integer-truncated. 0 if no reviews.
    """
    UID = 55  # Olivia Sharma

    # TC-REV-01: GET reviews returns list
    def test_get_reviews(self):
        res = requests.get(f"{BASE_URL}/products/1/reviews", headers=h(self.UID))
        assert res.status_code == 200

    # TC-REV-02: POST valid review → 200/201
    def test_add_review_valid(self):
        res = requests.post(f"{BASE_URL}/products/1/reviews",
                            json={"rating": 4, "comment": "Good product, will buy again."},
                            headers=h(self.UID))
        assert res.status_code in [200, 201]

    # TC-REV-03: Rating 0 → 400
    def test_rating_zero_returns_400(self):
        res = requests.post(f"{BASE_URL}/products/1/reviews",
                            json={"rating": 0, "comment": "Bad"},
                            headers=h(self.UID))
        assert res.status_code == 400

    # TC-REV-04: Rating 6 → 400
    def test_rating_six_returns_400(self):
        res = requests.post(f"{BASE_URL}/products/1/reviews",
                            json={"rating": 6, "comment": "Too good"},
                            headers=h(self.UID))
        assert res.status_code == 400

    # TC-REV-05: Rating 1 (boundary min) → 200/201
    def test_rating_boundary_min_1(self):
        res = requests.post(f"{BASE_URL}/products/2/reviews",
                            json={"rating": 1, "comment": "Not great."},
                            headers=h(self.UID))
        assert res.status_code in [200, 201]

    # TC-REV-06: Rating 5 (boundary max) → 200/201
    def test_rating_boundary_max_5(self):
        res = requests.post(f"{BASE_URL}/products/3/reviews",
                            json={"rating": 5, "comment": "Excellent!"},
                            headers=h(self.UID))
        assert res.status_code in [200, 201]

    # TC-REV-07: Empty comment → 400
    def test_empty_comment_returns_400(self):
        res = requests.post(f"{BASE_URL}/products/1/reviews",
                            json={"rating": 3, "comment": ""},
                            headers=h(self.UID))
        assert res.status_code == 400

    # TC-REV-08: Comment 201 chars → 400
    def test_comment_too_long_returns_400(self):
        res = requests.post(f"{BASE_URL}/products/1/reviews",
                            json={"rating": 3, "comment": "A" * 201},
                            headers=h(self.UID))
        assert res.status_code == 400

    # TC-REV-09: Comment 200 chars (boundary max) → 200/201
    def test_comment_boundary_200_chars(self):
        res = requests.post(f"{BASE_URL}/products/4/reviews",
                            json={"rating": 3, "comment": "A" * 200},
                            headers=h(self.UID))
        assert res.status_code in [200, 201]

    # TC-REV-10: Average rating is a proper decimal (not truncated integer)
    def test_average_rating_is_decimal(self):
        # Add two reviews: ratings 3 and 4 → average must be 3.5, not 3
        uid_a = 200  # Xavier Singh
        uid_b = 201  # Karan Thomas
        requests.post(f"{BASE_URL}/products/10/reviews",
                      json={"rating": 3, "comment": "Okay product"},
                      headers=h(uid_a))
        requests.post(f"{BASE_URL}/products/10/reviews",
                      json={"rating": 4, "comment": "Pretty good"},
                      headers=h(uid_b))
        res = requests.get(f"{BASE_URL}/products/10/reviews", headers=h(self.UID))
        data = res.json()
        avg = data.get("average_rating")
        if avg is not None and data.get("reviews") and len(data["reviews"]) >= 2:
            # average must not be integer-truncated
            assert isinstance(avg, float) or (avg != int(avg)), \
                f"Average rating must be decimal, got {avg}"


# ══════════════════════════════════════════════════════════════════════════════
# 13. SUPPORT TICKETS
# ══════════════════════════════════════════════════════════════════════════════

class TestSupportTickets:
    """
    TC-TKT-01..11
    subject: 5–100 chars. message: 1–500 chars.
    New tickets start as OPEN.
    Transitions: OPEN→IN_PROGRESS→CLOSED only. No skips, no backwards.
    """
    UID = 70  # Jack Sharma

    def _create_ticket(self, subject="Support needed here", message="Details of my issue go here."):
        return requests.post(f"{BASE_URL}/support/ticket",
                             json={"subject": subject, "message": message},
                             headers=h(self.UID))

    def _ticket_id(self, res):
        data = res.json()
        ticket = data.get("ticket") or data
        return ticket.get("ticket_id")

    # TC-TKT-01: POST valid ticket → 200/201
    def test_create_ticket_valid(self):
        res = self._create_ticket()
        assert res.status_code in [200, 201]

    # TC-TKT-02: New ticket status = OPEN
    def test_new_ticket_is_open(self):
        res = self._create_ticket("My order did not arrive today", "Please help me track it.")
        assert res.status_code in [200, 201]
        ticket = (res.json().get("ticket") or res.json())
        assert ticket.get("status") == "OPEN"

    # TC-TKT-03: Subject too short (4 chars) → 400
    def test_subject_too_short_returns_400(self):
        res = self._create_ticket(subject="Hi!!")
        assert res.status_code == 400

    # TC-TKT-04: Subject too long (101 chars) → 400
    def test_subject_too_long_returns_400(self):
        res = self._create_ticket(subject="A" * 101)
        assert res.status_code == 400

    # TC-TKT-05: Subject boundary min 5 chars → 200/201
    def test_subject_boundary_min_5_chars(self):
        res = self._create_ticket(subject="Help!")
        assert res.status_code in [200, 201]

    # TC-TKT-06: Message empty → 400
    def test_empty_message_returns_400(self):
        res = self._create_ticket(message="")
        assert res.status_code == 400

    # TC-TKT-07: Message 501 chars → 400
    def test_message_too_long_returns_400(self):
        res = self._create_ticket(message="A" * 501)
        assert res.status_code == 400

    # TC-TKT-08: GET all tickets → 200
    def test_get_all_tickets(self):
        res = requests.get(f"{BASE_URL}/support/tickets", headers=h(self.UID))
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    # TC-TKT-09: OPEN → IN_PROGRESS → 200
    def test_transition_open_to_in_progress(self):
        tid = self._ticket_id(self._create_ticket("Status test one here", "Moving to in progress."))
        if tid:
            res = requests.put(f"{BASE_URL}/support/tickets/{tid}",
                               json={"status": "IN_PROGRESS"},
                               headers=h(self.UID))
            assert res.status_code == 200

    # TC-TKT-10: OPEN → CLOSED (skip) → 400
    def test_transition_open_to_closed_is_invalid(self):
        tid = self._ticket_id(self._create_ticket("Skip transition test!", "Should fail closed."))
        if tid:
            res = requests.put(f"{BASE_URL}/support/tickets/{tid}",
                               json={"status": "CLOSED"},
                               headers=h(self.UID))
            assert res.status_code == 400, "Skipping IN_PROGRESS must be rejected"

    # TC-TKT-11: IN_PROGRESS → CLOSED → 200, then CLOSED → OPEN → 400
    def test_full_lifecycle_and_backward_rejected(self):
        tid = self._ticket_id(self._create_ticket("Full lifecycle ticket", "Testing all transitions now."))
        if tid:
            # OPEN → IN_PROGRESS
            requests.put(f"{BASE_URL}/support/tickets/{tid}",
                         json={"status": "IN_PROGRESS"}, headers=h(self.UID))
            # IN_PROGRESS → CLOSED
            r1 = requests.put(f"{BASE_URL}/support/tickets/{tid}",
                              json={"status": "CLOSED"}, headers=h(self.UID))
            assert r1.status_code == 200
            # CLOSED → OPEN (backward) → must fail
            r2 = requests.put(f"{BASE_URL}/support/tickets/{tid}",
                              json={"status": "OPEN"}, headers=h(self.UID))
            assert r2.status_code == 400, "Backward transition must be rejected"