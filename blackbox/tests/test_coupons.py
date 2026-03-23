"""
Test: Coupon Endpoints
Tests POST /api/v1/coupon/apply and POST /api/v1/coupon/remove.
Techniques: Equivalence Class Partitioning (ECP), Boundary Value Analysis (BVA)
"""

import pytest
from .conftest import get, post, delete, user_headers, base_headers

# Use a dedicated user for coupon tests
COUPON_USER = 5


def setup_function():
    """Clear cart and remove any applied coupon before each test."""
    delete("/cart/clear", headers=user_headers(COUPON_USER))
    post("/coupon/remove", headers=user_headers(COUPON_USER))


def teardown_function():
    """Clean up after each test."""
    post("/coupon/remove", headers=user_headers(COUPON_USER))
    delete("/cart/clear", headers=user_headers(COUPON_USER))


def _fill_cart(total_target):
    """Helper: add items to cart to reach approximately the given total.
    Product 1 (Apple-Red) costs 120 each.
    """
    qty = max(1, int(total_target / 120) + 1)
    post("/cart/add", headers=user_headers(COUPON_USER), json={"product_id": 1, "quantity": qty})


class TestApplyCoupon:
    """Tests for POST /api/v1/coupon/apply."""

    def test_apply_valid_fixed_coupon(self):
        """[ECP - Valid Class: Apply a valid FIXED coupon]
        SAVE50 is FIXED, discount_value=50, min_cart_value=500. Should succeed when cart >= 500.
        """
        # Need cart >= 500 => 5 x 120 = 600
        post("/cart/add", headers=user_headers(COUPON_USER), json={"product_id": 1, "quantity": 5})
        resp = post("/coupon/apply", headers=user_headers(COUPON_USER), json={
            "coupon_code": "SAVE50"
        })
        assert resp.status_code == 200

    def test_apply_valid_percent_coupon(self):
        """[ECP - Valid Class: Apply a valid PERCENT coupon]
        PERCENT10 is PERCENT, discount_value=10, min_cart_value=300, max_discount=100.
        """
        # Need cart >= 300 => 3 x 120 = 360
        post("/cart/add", headers=user_headers(COUPON_USER), json={"product_id": 1, "quantity": 3})
        resp = post("/coupon/apply", headers=user_headers(COUPON_USER), json={
            "coupon_code": "PERCENT10"
        })
        assert resp.status_code == 200

    def test_apply_expired_coupon_rejected(self):
        """[ECP - Invalid Class: Expired coupon]
        EXPIRED100 has expiry_date 2026-02-28, which is in the past. Should be rejected.
        """
        _fill_cart(1200)
        resp = post("/coupon/apply", headers=user_headers(COUPON_USER), json={
            "coupon_code": "EXPIRED100"
        })
        assert resp.status_code == 400

    def test_apply_coupon_cart_below_minimum(self):
        """[ECP - Invalid Class: Cart total below minimum]
        SAVE100 requires min_cart_value=1000. Cart < 1000 should fail.
        """
        post("/cart/add", headers=user_headers(COUPON_USER), json={"product_id": 3, "quantity": 1})  # 40
        resp = post("/coupon/apply", headers=user_headers(COUPON_USER), json={
            "coupon_code": "SAVE100"
        })
        assert resp.status_code == 400

    def test_apply_non_existent_coupon(self):
        """[ECP - Invalid Class: Non-existent coupon code]
        Should fail for a coupon that doesn't exist.
        """
        _fill_cart(500)
        resp = post("/coupon/apply", headers=user_headers(COUPON_USER), json={
            "coupon_code": "DOESNOTEXIST"
        })
        assert resp.status_code in [400, 404]

    def test_percent_coupon_discount_calculation(self):
        """[ECP - Valid Class: PERCENT discount calculated correctly]
        PERCENT10: 10% off, max_discount=100, min_cart=300.
        Cart = 3 × 120 = 360. Discount = 360 × 10% = 36 (within max of 100).
        """
        post("/cart/add", headers=user_headers(COUPON_USER), json={"product_id": 1, "quantity": 3})
        resp = post("/coupon/apply", headers=user_headers(COUPON_USER), json={
            "coupon_code": "PERCENT10"
        })
        assert resp.status_code == 200
        data = resp.json()
        # The discount should be 36.0 (10% of 360)
        discount = data.get("discount", data.get("discount_amount", 0))
        assert discount == pytest.approx(36.0, abs=0.01), f"Expected discount ~36.0, got {discount}"

    def test_percent_coupon_max_discount_cap(self):
        """[BVA - Boundary: Discount hits max_discount cap]
        PERCENT10: 10% off, max_discount=100.
        Cart = 15 × 120 = 1800. 10% = 180, but cap is 100.
        Discount should be capped at 100.
        """
        post("/cart/add", headers=user_headers(COUPON_USER), json={"product_id": 1, "quantity": 15})
        resp = post("/coupon/apply", headers=user_headers(COUPON_USER), json={
            "coupon_code": "PERCENT10"
        })
        assert resp.status_code == 200
        data = resp.json()
        discount = data.get("discount", data.get("discount_amount", 0))
        assert discount == pytest.approx(100.0, abs=0.01), f"Expected discount capped at 100, got {discount}"

    def test_percent30_coupon_discount_capped_at_300(self):
        """[BVA - Boundary: High percentage coupon capped by max_discount]
        PERCENT30 gives 30% off with max_discount=300. For subtotal 1200, raw discount=360, final should be 300.
        """
        post("/cart/add", headers=user_headers(COUPON_USER), json={"product_id": 1, "quantity": 10})  # 1200
        resp = post("/coupon/apply", headers=user_headers(COUPON_USER), json={"coupon_code": "PERCENT30"})
        assert resp.status_code == 200
        data = resp.json()
        discount = data.get("discount", data.get("discount_amount", 0))
        assert discount == pytest.approx(300.0, abs=0.01), f"Expected discount capped at 300, got {discount}"

    def test_cart_at_exactly_min_value(self):
        """[BVA - Boundary: Cart total exactly at minimum cart value]
        SUPER10: min_cart_value=250, 10%, max_discount=80.
        We need cart = exactly 250. Product 5 (Mango-Alphonso) = 250 each.
        """
        post("/cart/add", headers=user_headers(COUPON_USER), json={"product_id": 5, "quantity": 1})
        resp = post("/coupon/apply", headers=user_headers(COUPON_USER), json={
            "coupon_code": "SUPER10"
        })
        assert resp.status_code == 200


class TestRemoveCoupon:
    """Tests for POST /api/v1/coupon/remove."""

    def test_remove_applied_coupon(self):
        """[ECP - Valid Class: Remove a coupon that was applied]
        Should succeed and the discount should be removed.
        """
        post("/cart/add", headers=user_headers(COUPON_USER), json={"product_id": 1, "quantity": 5})
        post("/coupon/apply", headers=user_headers(COUPON_USER), json={"coupon_code": "SAVE50"})
        resp = post("/coupon/remove", headers=user_headers(COUPON_USER))
        assert resp.status_code == 200

    def test_remove_coupon_when_none_applied(self):
        """[ECP - Valid Class: Remove when no coupon applied]
        Should not error even if no coupon is applied.
        """
        resp = post("/coupon/remove", headers=user_headers(COUPON_USER))
        assert resp.status_code == 200

    def test_remove_coupon_removes_discount_effect(self):
        """[ECP - Valid Class: Coupon removal resets discount]
        After removing coupon, cart discount should be cleared and total should not include coupon reduction.
        """
        post("/cart/add", headers=user_headers(COUPON_USER), json={"product_id": 1, "quantity": 5})  # subtotal 600

        apply_resp = post("/coupon/apply", headers=user_headers(COUPON_USER), json={"coupon_code": "SAVE50"})
        assert apply_resp.status_code == 200

        cart_after_apply = get("/cart", headers=user_headers(COUPON_USER)).json()
        discount_after_apply = cart_after_apply.get("discount", cart_after_apply.get("discount_amount", cart_after_apply.get("coupon_discount", None)))
        total_after_apply = cart_after_apply.get("total", cart_after_apply.get("cart_total", None))

        remove_resp = post("/coupon/remove", headers=user_headers(COUPON_USER))
        assert remove_resp.status_code == 200

        cart_after_remove = get("/cart", headers=user_headers(COUPON_USER)).json()
        discount_after_remove = cart_after_remove.get("discount", cart_after_remove.get("discount_amount", cart_after_remove.get("coupon_discount", None)))
        total_after_remove = cart_after_remove.get("total", cart_after_remove.get("cart_total", None))

        if discount_after_apply is not None and discount_after_remove is not None:
            assert discount_after_remove in [0, 0.0]
            assert discount_after_apply >= discount_after_remove
        elif total_after_apply is not None and total_after_remove is not None:
            assert total_after_remove >= total_after_apply
