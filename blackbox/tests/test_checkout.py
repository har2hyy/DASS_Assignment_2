"""
Test: Checkout Endpoint
Tests POST /api/v1/checkout.
Techniques: Equivalence Class Partitioning (ECP), Boundary Value Analysis (BVA)
"""

import pytest
from .conftest import get, post, delete, user_headers, base_headers

# Use dedicated users for checkout tests (different users to avoid order interference)
CHECKOUT_USER_COD = 10
CHECKOUT_USER_WALLET = 11
CHECKOUT_USER_CARD = 12
CHECKOUT_USER_EMPTY = 13
CHECKOUT_USER_COD_LIMIT = 14
CHECKOUT_USER_GST = 15


class TestCheckoutPaymentMethods:
    """Tests for valid and invalid payment methods."""

    def test_checkout_with_card(self):
        """[ECP - Valid Class: CARD payment method]
        Checkout with CARD should succeed and set payment status to PAID.
        """
        delete("/cart/clear", headers=user_headers(CHECKOUT_USER_CARD))
        post("/cart/add", headers=user_headers(CHECKOUT_USER_CARD), json={"product_id": 1, "quantity": 1})
        resp = post("/checkout", headers=user_headers(CHECKOUT_USER_CARD), json={
            "payment_method": "CARD"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("payment_status") == "PAID"

    def test_checkout_with_cod(self):
        """[ECP - Valid Class: COD payment method]
        Checkout with COD should succeed (when total <= 5000) and set payment status to PENDING.
        """
        delete("/cart/clear", headers=user_headers(CHECKOUT_USER_COD))
        post("/cart/add", headers=user_headers(CHECKOUT_USER_COD), json={"product_id": 3, "quantity": 1})  # 40
        resp = post("/checkout", headers=user_headers(CHECKOUT_USER_COD), json={
            "payment_method": "COD"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("payment_status") == "PENDING"

    def test_checkout_with_wallet(self):
        """[ECP - Valid Class: WALLET payment method]
        Checkout with WALLET should succeed and set payment status to PENDING.
        """
        delete("/cart/clear", headers=user_headers(CHECKOUT_USER_WALLET))
        post("/cart/add", headers=user_headers(CHECKOUT_USER_WALLET), json={"product_id": 3, "quantity": 1})  # 40
        resp = post("/checkout", headers=user_headers(CHECKOUT_USER_WALLET), json={
            "payment_method": "WALLET"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("payment_status") == "PENDING"

    def test_checkout_invalid_payment_method(self):
        """[ECP - Invalid Class: Invalid payment method]
        Any payment method other than COD, WALLET, CARD should be rejected.
        """
        delete("/cart/clear", headers=user_headers(CHECKOUT_USER_EMPTY))
        post("/cart/add", headers=user_headers(CHECKOUT_USER_EMPTY), json={"product_id": 1, "quantity": 1})
        resp = post("/checkout", headers=user_headers(CHECKOUT_USER_EMPTY), json={
            "payment_method": "BITCOIN"
        })
        assert resp.status_code == 400


class TestCheckoutEmptyCart:
    """Tests for checkout with empty cart."""

    def test_checkout_empty_cart_rejected(self):
        """[ECP - Invalid Class: Empty cart]
        Checkout with an empty cart should return 400.
        """
        delete("/cart/clear", headers=user_headers(CHECKOUT_USER_EMPTY))
        resp = post("/checkout", headers=user_headers(CHECKOUT_USER_EMPTY), json={
            "payment_method": "CARD"
        })
        assert resp.status_code == 400


class TestCheckoutCODLimit:
    """Tests for COD payment limit."""

    def test_cod_above_5000_rejected(self):
        """[BVA - Boundary: COD with total > 5000]
        COD is not allowed if order total > 5000. Should return 400.
        Total = qty × price × 1.05 (GST). We need total > 5000.
        45 × 120 = 5400 + 5% GST = 5670. Should be rejected.
        """
        delete("/cart/clear", headers=user_headers(CHECKOUT_USER_COD_LIMIT))
        post("/cart/add", headers=user_headers(CHECKOUT_USER_COD_LIMIT), json={"product_id": 1, "quantity": 45})
        resp = post("/checkout", headers=user_headers(CHECKOUT_USER_COD_LIMIT), json={
            "payment_method": "COD"
        })
        assert resp.status_code == 400

    def test_cod_at_5000_boundary(self):
        """[BVA - Boundary: COD with total ≈ 5000]
        COD is allowed if order total is exactly 5000 or less.
        We need items summing to ~4762 (so that with 5% GST = ~5000).
        This is a boundary test – we test near the limit.
        """
        # Product 4 (Orange) = 80 each. 59 × 80 = 4720. + 5% GST = 4956. Should be OK.
        delete("/cart/clear", headers=user_headers(CHECKOUT_USER_COD_LIMIT))
        post("/cart/add", headers=user_headers(CHECKOUT_USER_COD_LIMIT), json={"product_id": 4, "quantity": 59})
        resp = post("/checkout", headers=user_headers(CHECKOUT_USER_COD_LIMIT), json={
            "payment_method": "COD"
        })
        assert resp.status_code == 200


class TestCheckoutGST:
    """Tests for GST calculation."""

    def test_gst_5_percent_applied(self):
        """[ECP - Valid Class: GST = 5% of subtotal]
        GST should be 5% and added only once. Verify the order total reflects this.
        Product 1 qty=2 => subtotal = 240. GST = 12. Total = 252.
        """
        delete("/cart/clear", headers=user_headers(CHECKOUT_USER_GST))
        post("/cart/add", headers=user_headers(CHECKOUT_USER_GST), json={"product_id": 1, "quantity": 2})
        resp = post("/checkout", headers=user_headers(CHECKOUT_USER_GST), json={
            "payment_method": "CARD"
        })
        assert resp.status_code == 200
        data = resp.json()
        order_total = data.get("total", data.get("order_total", 0))
        # Expected: 240 * 1.05 = 252
        assert order_total == pytest.approx(252.0, abs=0.01), f"Expected total 252.0, got {order_total}"

    def test_gst_5_percent_applied_cod(self):
        """[ECP - Valid Class: GST total for COD]
        Subtotal 240 should result in order total 252 with COD as payment method.
        """
        delete("/cart/clear", headers=user_headers(CHECKOUT_USER_COD))
        post("/cart/add", headers=user_headers(CHECKOUT_USER_COD), json={"product_id": 1, "quantity": 2})

        resp = post("/checkout", headers=user_headers(CHECKOUT_USER_COD), json={"payment_method": "COD"})
        assert resp.status_code == 200
        data = resp.json()
        order_total = data.get("total", data.get("order_total", 0))
        assert order_total == pytest.approx(252.0, abs=0.01), f"Expected COD total 252.0, got {order_total}"

    def test_gst_5_percent_applied_wallet(self):
        """[ECP - Valid Class: GST total for WALLET]
        Subtotal 240 should result in order total 252 with WALLET as payment method.
        """
        delete("/cart/clear", headers=user_headers(CHECKOUT_USER_WALLET))
        post("/wallet/add", headers=user_headers(CHECKOUT_USER_WALLET), json={"amount": 500})
        post("/cart/add", headers=user_headers(CHECKOUT_USER_WALLET), json={"product_id": 1, "quantity": 2})

        resp = post("/checkout", headers=user_headers(CHECKOUT_USER_WALLET), json={"payment_method": "WALLET"})
        assert resp.status_code == 200
        data = resp.json()
        order_total = data.get("total", data.get("order_total", 0))
        assert order_total == pytest.approx(252.0, abs=0.01), f"Expected WALLET total 252.0, got {order_total}"
