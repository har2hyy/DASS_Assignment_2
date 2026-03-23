"""
Test: Admin / Data Inspection Endpoints
Tests GET /api/v1/admin/* endpoints for retrieving full database contents.
Techniques: Equivalence Class Partitioning (ECP), Boundary Value Analysis (BVA)
"""

import pytest
from .conftest import get, base_headers, user_headers


class TestAdminUsers:
    """Tests for GET /api/v1/admin/users and GET /api/v1/admin/users/{user_id}."""

    def test_get_all_users_returns_list(self):
        """[ECP - Valid Class: Retrieve all users]
        Should return 200 with a JSON array of all users.
        """
        resp = get("/admin/users")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_user_has_expected_fields(self):
        """[ECP - Valid Class: Response structure verification]
        Each user object should contain expected fields.
        """
        resp = get("/admin/users")
        user = resp.json()[0]
        for field in ["user_id", "name", "email", "phone", "wallet_balance", "loyalty_points"]:
            assert field in user, f"Missing field: {field}"

    def test_get_specific_user_by_id(self):
        """[ECP - Valid Class: Retrieve single user by ID]
        Should return 200 with the specific user data.
        """
        resp = get("/admin/users/1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == 1

    def test_get_non_existent_user_returns_404(self):
        """[ECP - Invalid Class: Non-existent user ID]
        Should return 404 for a user ID that does not exist.
        """
        resp = get("/admin/users/99999")
        assert resp.status_code == 404

    def test_get_user_id_zero(self):
        """[BVA - Boundary: User ID = 0]
        Zero is not a valid user ID, should return 404.
        """
        resp = get("/admin/users/0")
        assert resp.status_code == 404

    def test_get_user_id_negative(self):
        """[BVA - Boundary: Negative user ID]
        Negative ID should return 404.
        """
        resp = get("/admin/users/-1")
        assert resp.status_code == 404

    def test_get_first_user(self):
        """[BVA - Boundary: First user ID = 1]
        The minimum valid user ID.
        """
        resp = get("/admin/users/1")
        assert resp.status_code == 200

    def test_get_last_user(self):
        """[BVA - Boundary: Last user ID = 800]
        The maximum valid user ID in the database.
        """
        resp = get("/admin/users/800")
        assert resp.status_code == 200

    def test_get_user_just_beyond_max(self):
        """[BVA - Boundary: User ID = 801]
        One beyond the maximum user ID, should return 404.
        """
        resp = get("/admin/users/801")
        assert resp.status_code == 404


class TestAdminProducts:
    """Tests for GET /api/v1/admin/products."""

    def test_get_all_products(self):
        """[ECP - Valid Class: Retrieve all products]
        Should return all products including inactive ones.
        """
        resp = get("/admin/products")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        # Should include inactive products
        inactive = [p for p in data if not p["is_active"]]
        assert len(inactive) > 0, "Admin endpoint should include inactive products"

    def test_product_has_expected_fields(self):
        """[ECP - Valid Class: Response structure]
        Each product should have expected fields.
        """
        resp = get("/admin/products")
        product = resp.json()[0]
        for field in ["product_id", "name", "category", "price", "stock_quantity", "is_active"]:
            assert field in product, f"Missing field: {field}"


class TestAdminCarts:
    """Tests for GET /api/v1/admin/carts."""

    def test_get_all_carts(self):
        """[ECP - Valid Class: Retrieve all carts]
        Should return 200 with a JSON list of carts.
        """
        resp = get("/admin/carts")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_cart_record_shape(self):
        """[ECP - Valid Class: Cart data semantics]
        Cart rows should expose cart/user identifiers and item collection.
        """
        resp = get("/admin/carts")
        assert resp.status_code == 200
        data = resp.json()
        if data:
            cart = data[0]
            assert "user_id" in cart
            assert "items" in cart
            assert isinstance(cart["items"], list)


class TestAdminOrders:
    """Tests for GET /api/v1/admin/orders."""

    def test_get_all_orders(self):
        """[ECP - Valid Class: Retrieve all orders]
        Should return 200 with a JSON list of orders.
        """
        resp = get("/admin/orders")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_order_record_shape(self):
        """[ECP - Valid Class: Order data semantics]
        Orders should contain order/user linkage and status-related fields.
        """
        resp = get("/admin/orders")
        assert resp.status_code == 200
        data = resp.json()
        if data:
            order = data[0]
            assert "order_id" in order
            assert "user_id" in order
            # APIs sometimes use total/order_total and status/order_status naming.
            assert any(key in order for key in ["total", "order_total", "total_amount"])
            assert any(key in order for key in ["status", "order_status"])


class TestAdminCoupons:
    """Tests for GET /api/v1/admin/coupons."""

    def test_get_all_coupons(self):
        """[ECP - Valid Class: Retrieve all coupons]
        Should return all coupons including expired ones.
        """
        resp = get("/admin/coupons")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_coupon_record_shape(self):
        """[ECP - Valid Class: Coupon data semantics]
        Coupon records should include code and discount rule metadata.
        """
        resp = get("/admin/coupons")
        assert resp.status_code == 200
        data = resp.json()
        if data:
            coupon = data[0]
            assert "coupon_code" in coupon
            assert any(key in coupon for key in ["discount", "discount_value", "discount_type"])


class TestAdminTickets:
    """Tests for GET /api/v1/admin/tickets."""

    def test_get_all_tickets(self):
        """[ECP - Valid Class: Retrieve all tickets]
        Should return 200.
        """
        resp = get("/admin/tickets")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_ticket_record_shape(self):
        """[ECP - Valid Class: Ticket data semantics]
        Ticket records should contain ticket id, subject, message, and status.
        """
        resp = get("/admin/tickets")
        assert resp.status_code == 200
        data = resp.json()
        if data:
            ticket = data[0]
            for field in ["ticket_id", "subject", "message", "status"]:
                assert field in ticket


class TestAdminAddresses:
    """Tests for GET /api/v1/admin/addresses."""

    def test_get_all_addresses(self):
        """[ECP - Valid Class: Retrieve all addresses]
        Should return 200.
        """
        resp = get("/admin/addresses")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_address_record_shape(self):
        """[ECP - Valid Class: Address data semantics]
        Address records should include user linkage and address components.
        """
        resp = get("/admin/addresses")
        assert resp.status_code == 200
        data = resp.json()
        if data:
            address = data[0]
            for field in ["address_id", "user_id", "label", "street", "city", "pincode", "is_default"]:
                assert field in address
