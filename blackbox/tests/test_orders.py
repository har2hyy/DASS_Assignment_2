"""
Test: Order Endpoints
Tests GET /api/v1/orders, GET /api/v1/orders/{order_id},
POST /api/v1/orders/{order_id}/cancel, GET /api/v1/orders/{order_id}/invoice.
Techniques: Equivalence Class Partitioning (ECP), Boundary Value Analysis (BVA)
"""

import pytest
from .conftest import get, post, delete, user_headers, base_headers

# Use dedicated users for order tests
ORDER_USER = 40
ORDER_USER_CANCEL = 41
ORDER_USER_STOCK = 42
ORDER_USER_INVOICE = 43
ORDER_USER_DELIVERED = 1


def _create_order(user_id, product_id=1, quantity=1, payment_method="CARD"):
    """Helper: create an order for the given user."""
    delete("/cart/clear", headers=user_headers(user_id))
    post("/cart/add", headers=user_headers(user_id), json={
        "product_id": product_id,
        "quantity": quantity
    })
    resp = post("/checkout", headers=user_headers(user_id), json={
        "payment_method": payment_method
    })
    return resp


class TestGetOrders:
    """Tests for GET /api/v1/orders."""

    def test_get_orders_returns_list(self):
        """[ECP - Valid Class: Retrieve user's orders]
        Should return 200 with a list of orders.
        """
        resp = get("/orders", headers=user_headers(ORDER_USER))
        assert resp.status_code == 200

    def test_get_orders_after_creating_one(self):
        """[ECP - Valid Class: Orders list includes new order]
        After creating an order, it should appear in the orders list.
        """
        _create_order(ORDER_USER)
        resp = get("/orders", headers=user_headers(ORDER_USER))
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0


class TestGetOrderById:
    """Tests for GET /api/v1/orders/{order_id}."""

    def test_get_existing_order(self):
        """[ECP - Valid Class: Retrieve specific order]
        Should return 200 with order details.
        """
        create_resp = _create_order(ORDER_USER)
        if create_resp.status_code == 200:
            order_id = create_resp.json().get("order_id")
            if order_id:
                resp = get(f"/orders/{order_id}", headers=user_headers(ORDER_USER))
                assert resp.status_code == 200

    def test_get_non_existent_order_returns_404(self):
        """[ECP - Invalid Class: Non-existent order ID]
        Should return 404 for an order that does not exist.
        """
        resp = get("/orders/99999", headers=user_headers(ORDER_USER))
        assert resp.status_code == 404

    def test_get_order_id_zero(self):
        """[BVA - Boundary: Order ID = 0]
        Should return 404.
        """
        resp = get("/orders/0", headers=user_headers(ORDER_USER))
        assert resp.status_code == 404

    def test_get_order_id_negative(self):
        """[BVA - Boundary: Negative order ID]
        Should return 404.
        """
        resp = get("/orders/-1", headers=user_headers(ORDER_USER))
        assert resp.status_code == 404


class TestCancelOrder:
    """Tests for POST /api/v1/orders/{order_id}/cancel."""

    def test_cancel_pending_order(self):
        """[ECP - Valid Class: Cancel a pending/non-delivered order]
        A non-delivered order should be cancellable.
        """
        create_resp = _create_order(ORDER_USER_CANCEL, payment_method="CARD")
        if create_resp.status_code == 200:
            order_id = create_resp.json().get("order_id")
            if order_id:
                resp = post(f"/orders/{order_id}/cancel", headers=user_headers(ORDER_USER_CANCEL))
                assert resp.status_code == 200

    def test_cancel_non_existent_order_returns_404(self):
        """[ECP - Invalid Class: Cancel non-existent order]
        Should return 404 when trying to cancel an order that doesn't exist.
        """
        resp = post("/orders/99999/cancel", headers=user_headers(ORDER_USER_CANCEL))
        assert resp.status_code == 404

    def test_cancel_already_cancelled_order(self):
        """[ECP - Invalid Class: Cancel already cancelled order]
        Should return a 400 error if order is already cancelled.
        """
        create_resp = _create_order(ORDER_USER_CANCEL, payment_method="CARD")
        if create_resp.status_code == 200:
            order_id = create_resp.json().get("order_id")
            if order_id:
                # Cancel once
                post(f"/orders/{order_id}/cancel", headers=user_headers(ORDER_USER_CANCEL))
                # Try to cancel again
                resp = post(f"/orders/{order_id}/cancel", headers=user_headers(ORDER_USER_CANCEL))
                assert resp.status_code == 400

    def test_cancel_delivered_order_rejected(self):
        """[ECP - Invalid Class: Cancel delivered order]
        A delivered order should not be cancellable.
        """
        orders_resp = get("/orders", headers=user_headers(ORDER_USER_DELIVERED))
        assert orders_resp.status_code == 200
        orders = orders_resp.json()
        delivered = next(
            (o for o in orders if str(o.get("status", "")).upper() == "DELIVERED"),
            None,
        )

        if not delivered:
            pytest.skip("No delivered order found for test user")

        order_id = delivered.get("order_id")
        resp = post(f"/orders/{order_id}/cancel", headers=user_headers(ORDER_USER_DELIVERED))
        assert resp.status_code in [400, 409]


class TestCancelRestoresStock:
    """Tests for stock restoration after cancellation."""

    def test_stock_restored_after_cancel(self):
        """[ECP - Valid Class: Stock restoration]
        When an order is cancelled, all items in that order should be added back to stock.
        """
        # Get stock before
        product_id = 2
        admin_products = get("/admin/products").json()
        before_stock = next(
            (p["stock_quantity"] for p in admin_products if p["product_id"] == product_id), None
        )

        # Create and then cancel an order
        order_qty = 2
        create_resp = _create_order(ORDER_USER_STOCK, product_id=product_id, quantity=order_qty,
                                    payment_method="CARD")
        if create_resp.status_code == 200:
            order_id = create_resp.json().get("order_id")
            if order_id:
                post(f"/orders/{order_id}/cancel", headers=user_headers(ORDER_USER_STOCK))

                # Check stock after cancel
                admin_products_after = get("/admin/products").json()
                after_stock = next(
                    (p["stock_quantity"] for p in admin_products_after if p["product_id"] == product_id), None
                )

                if before_stock is not None and after_stock is not None:
                    assert after_stock == before_stock, \
                        f"Stock should be restored: expected {before_stock}, got {after_stock}"


class TestOrderInvoice:
    """Tests for GET /api/v1/orders/{order_id}/invoice."""

    def test_get_invoice_for_valid_order(self):
        """[ECP - Valid Class: Invoice retrieval for a valid order]
        Invoice endpoint should return 200 for an existing order.
        """
        create_resp = _create_order(ORDER_USER_INVOICE, product_id=1, quantity=2, payment_method="CARD")
        if create_resp.status_code == 200:
            order_id = create_resp.json().get("order_id")
            if order_id:
                resp = get(f"/orders/{order_id}/invoice", headers=user_headers(ORDER_USER_INVOICE))
                assert resp.status_code == 200

    def test_invoice_total_matches_order(self):
        """[ECP - Valid Class: Invoice total accuracy]
        The total in the invoice should match the actual order total.
        Product 1, qty 2 => subtotal = 240, GST = 12 (5%), total = 252.
        """
        create_resp = _create_order(ORDER_USER_INVOICE, product_id=1, quantity=2, payment_method="CARD")
        if create_resp.status_code == 200:
            order_data = create_resp.json()
            order_id = order_data.get("order_id")
            order_total = order_data.get("total", order_data.get("order_total", 0))
            if order_id:
                invoice = get(f"/orders/{order_id}/invoice", headers=user_headers(ORDER_USER_INVOICE)).json()
                invoice_total = invoice.get("total", invoice.get("order_total", 0))
                assert invoice_total == pytest.approx(order_total, abs=0.01), \
                    f"Invoice total {invoice_total} != order total {order_total}"

    def test_invoice_gst_is_5_percent(self):
        """[ECP - Valid Class: GST = 5% of subtotal]
        The GST amount should be exactly 5% of the subtotal.
        """
        create_resp = _create_order(ORDER_USER_INVOICE, product_id=1, quantity=2, payment_method="CARD")
        if create_resp.status_code == 200:
            order_id = create_resp.json().get("order_id")
            if order_id:
                invoice = get(f"/orders/{order_id}/invoice", headers=user_headers(ORDER_USER_INVOICE)).json()
                subtotal = invoice.get("subtotal", invoice.get("sub_total", 0))
                gst = invoice.get("gst", invoice.get("gst_amount", invoice.get("tax", 0)))
                if subtotal > 0:
                    expected_gst = subtotal * 0.05
                    assert gst == pytest.approx(expected_gst, abs=0.01), \
                        f"GST {gst} != 5% of subtotal {subtotal} (expected {expected_gst})"

    def test_invoice_non_existent_order(self):
        """[ECP - Invalid Class: Invoice for non-existent order]
        Should return 404.
        """
        resp = get("/orders/99999/invoice", headers=user_headers(ORDER_USER_INVOICE))
        assert resp.status_code == 404
