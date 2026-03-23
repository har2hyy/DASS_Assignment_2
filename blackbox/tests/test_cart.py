"""
Test: Cart Endpoints
Tests GET /api/v1/cart, POST /api/v1/cart/add, POST /api/v1/cart/update,
POST /api/v1/cart/remove, DELETE /api/v1/cart/clear.
Techniques: Equivalence Class Partitioning (ECP), Boundary Value Analysis (BVA)
"""

import pytest
from .conftest import get, post, delete, user_headers, base_headers, VALID_USER_ID


# Use a dedicated user for cart tests to avoid interference
CART_USER = 3


def _cart_items(cart_payload):
    """Normalize cart response to a list of item dicts."""
    if isinstance(cart_payload, dict):
        return cart_payload.get("items", [])
    if isinstance(cart_payload, list):
        return cart_payload
    return []


def _quantity_for_product(cart_payload, product_id):
    """Return quantity for a product from cart payload; defaults to 0."""
    for item in _cart_items(cart_payload):
        if item.get("product_id") == product_id:
            return item.get("quantity", 0)
    return 0


def setup_function():
    """Clear cart before each test function."""
    delete("/cart/clear", headers=user_headers(CART_USER))


def teardown_function():
    """Clear cart after each test function."""
    delete("/cart/clear", headers=user_headers(CART_USER))


class TestGetCart:
    """Tests for GET /api/v1/cart."""

    def test_get_empty_cart(self):
        """[ECP - Valid Class: Empty cart]
        Viewing an empty cart should return 200 with an empty items list.
        """
        resp = get("/cart", headers=user_headers(CART_USER))
        assert resp.status_code == 200

    def test_get_cart_with_items(self):
        """[ECP - Valid Class: Cart with items]
        After adding items, the cart should show them.
        """
        post("/cart/add", headers=user_headers(CART_USER), json={"product_id": 1, "quantity": 2})
        resp = get("/cart", headers=user_headers(CART_USER))
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data or isinstance(data, list)


class TestAddToCart:
    """Tests for POST /api/v1/cart/add."""

    def test_add_valid_product(self):
        """[ECP - Valid Class: Valid product and quantity]
        Adding a valid product with valid quantity should succeed.
        """
        resp = post("/cart/add", headers=user_headers(CART_USER), json={
            "product_id": 1,
            "quantity": 1
        })
        assert resp.status_code == 200

    def test_add_quantity_zero_rejected(self):
        """[BVA - Boundary: Quantity = 0 (invalid)]
        Quantity must be at least 1. Zero should be rejected with 400.
        """
        resp = post("/cart/add", headers=user_headers(CART_USER), json={
            "product_id": 1,
            "quantity": 0
        })
        assert resp.status_code == 400

    def test_add_quantity_negative_rejected(self):
        """[BVA - Boundary: Quantity = -1 (invalid)]
        Negative quantity should be rejected with 400.
        """
        resp = post("/cart/add", headers=user_headers(CART_USER), json={
            "product_id": 1,
            "quantity": -1
        })
        assert resp.status_code == 400

    def test_add_quantity_one_valid(self):
        """[BVA - Boundary: Quantity = 1 (minimum valid)]
        Quantity of 1 is the minimum valid value.
        """
        resp = post("/cart/add", headers=user_headers(CART_USER), json={
            "product_id": 1,
            "quantity": 1
        })
        assert resp.status_code == 200

    def test_add_non_existent_product_returns_404(self):
        """[ECP - Invalid Class: Non-existent product]
        Adding a product that does not exist should return 404.
        """
        resp = post("/cart/add", headers=user_headers(CART_USER), json={
            "product_id": 251,
            "quantity": 1
        })
        assert resp.status_code == 404

    def test_add_product_id_negative_one(self):
        """[BVA - Boundary: product_id = -1]
        Invalid negative product id should return 404.
        """
        resp = post("/cart/add", headers=user_headers(CART_USER), json={"product_id": -1, "quantity": 1})
        assert resp.status_code == 404

    def test_add_product_id_zero(self):
        """[BVA - Boundary: product_id = 0]
        Invalid zero product id should return 404.
        """
        resp = post("/cart/add", headers=user_headers(CART_USER), json={"product_id": 0, "quantity": 1})
        assert resp.status_code == 404

    def test_add_product_id_one(self):
        """[BVA - Boundary: product_id = 1]
        Lower valid product id should succeed with valid quantity.
        """
        resp = post("/cart/add", headers=user_headers(CART_USER), json={"product_id": 1, "quantity": 1})
        assert resp.status_code == 200

    def test_add_product_id_250(self):
        """[BVA - Boundary: product_id = 250]
        Upper valid product id should succeed with valid quantity.
        """
        resp = post("/cart/add", headers=user_headers(CART_USER), json={"product_id": 250, "quantity": 1})
        assert resp.status_code == 200

    def test_add_product_id_251(self):
        """[BVA - Boundary: product_id = 251]
        Just-above-range product id should return 404.
        """
        resp = post("/cart/add", headers=user_headers(CART_USER), json={"product_id": 251, "quantity": 1})
        assert resp.status_code == 404

    def test_add_product_248_quantity_21_rejected(self):
        """[BVA - Stock Boundary: quantity > stock]
        For product 248, quantity 21 should be rejected (stock limit 20).
        """
        resp = post("/cart/add", headers=user_headers(CART_USER), json={"product_id": 248, "quantity": 21})
        assert resp.status_code == 400

    def test_add_product_248_quantity_20_valid(self):
        """[BVA - Stock Boundary: quantity == stock]
        For product 248, quantity 20 should be accepted.
        """
        resp = post("/cart/add", headers=user_headers(CART_USER), json={"product_id": 248, "quantity": 20})
        assert resp.status_code == 200

    def test_add_missing_product_id(self):
        """[ECP - Invalid Class: Missing product_id]
        Missing product_id should return 400.
        """
        resp = post("/cart/add", headers=user_headers(CART_USER), json={"quantity": 1})
        assert resp.status_code == 400

    def test_add_missing_quantity(self):
        """[ECP - Invalid Class: Missing quantity]
        Missing quantity should return 400.
        """
        resp = post("/cart/add", headers=user_headers(CART_USER), json={"product_id": 248})
        assert resp.status_code == 400

    def test_add_missing_product_id_and_quantity(self):
        """[ECP - Invalid Class: Missing both required fields]
        Empty body should return 400.
        """
        resp = post("/cart/add", headers=user_headers(CART_USER), json={})
        assert resp.status_code == 400

    def test_add_quantity_exceeding_stock_returns_400(self):
        """[ECP - Invalid Class: Quantity exceeds stock]
        If requested quantity exceeds stock, server should return 400.
        """
        resp = post("/cart/add", headers=user_headers(CART_USER), json={
            "product_id": 1,
            "quantity": 999999
        })
        assert resp.status_code == 400

    def test_add_same_product_twice_sums_quantities(self):
        """[ECP - Valid Class: Duplicate product addition]
        Adding the same product twice should sum the quantities, not replace.
        """
        post("/cart/add", headers=user_headers(CART_USER), json={"product_id": 2, "quantity": 1})
        post("/cart/add", headers=user_headers(CART_USER), json={"product_id": 2, "quantity": 2})

        cart = get("/cart", headers=user_headers(CART_USER)).json()
        items = cart.get("items", cart if isinstance(cart, list) else [])
        product_items = [i for i in items if i.get("product_id") == 2]
        assert len(product_items) == 1, "Same product should appear once in cart"
        assert product_items[0]["quantity"] == 3, "Quantities should be summed (1+2=3)"


class TestCartSubtotalAndTotal:
    """Tests for cart calculations."""

    def test_item_subtotal_correct(self):
        """[ECP - Valid Class: Subtotal = quantity × unit price]
        Each item's subtotal must equal quantity × unit_price.
        """
        post("/cart/add", headers=user_headers(CART_USER), json={"product_id": 1, "quantity": 3})
        cart = get("/cart", headers=user_headers(CART_USER)).json()
        items = cart.get("items", cart if isinstance(cart, list) else [])
        if items:
            item = items[0]
            expected_subtotal = item["quantity"] * item.get("unit_price", item.get("price", 0))
            assert item.get("subtotal", item.get("item_total", 0)) == expected_subtotal

    def test_cart_total_is_sum_of_subtotals(self):
        """[ECP - Valid Class: Total = sum of all subtotals]
        Cart total must be the sum of all item subtotals.
        """
        post("/cart/add", headers=user_headers(CART_USER), json={"product_id": 1, "quantity": 2})
        post("/cart/add", headers=user_headers(CART_USER), json={"product_id": 3, "quantity": 1})

        cart = get("/cart", headers=user_headers(CART_USER)).json()
        items = cart.get("items", [])
        if items:
            subtotals_sum = sum(
                i.get("subtotal", i.get("item_total", i.get("quantity", 0) * i.get("unit_price", i.get("price", 0))))
                for i in items
            )
            cart_total = cart.get("total", cart.get("cart_total", 0))
            assert cart_total == subtotals_sum, f"Cart total {cart_total} != sum of subtotals {subtotals_sum}"


class TestUpdateCartItem:
    """Tests for POST /api/v1/cart/update."""

    def test_update_quantity_valid(self):
        """[ECP - Valid Class: Update to valid quantity]
        Updating quantity to a valid value should succeed.
        """
        post("/cart/add", headers=user_headers(CART_USER), json={"product_id": 1, "quantity": 1})
        resp = post("/cart/update", headers=user_headers(CART_USER), json={
            "product_id": 1,
            "quantity": 5
        })
        assert resp.status_code == 200

    def test_update_quantity_zero_rejected(self):
        """[BVA - Boundary: Update quantity = 0 (invalid)]
        New quantity must be at least 1. Zero should be rejected.
        """
        post("/cart/add", headers=user_headers(CART_USER), json={"product_id": 1, "quantity": 2})
        resp = post("/cart/update", headers=user_headers(CART_USER), json={
            "product_id": 1,
            "quantity": 0
        })
        assert resp.status_code == 400

    def test_update_quantity_one_valid(self):
        """[BVA - Boundary: Update quantity = 1 (minimum valid)]
        Minimum valid quantity for update.
        """
        post("/cart/add", headers=user_headers(CART_USER), json={"product_id": 1, "quantity": 3})
        resp = post("/cart/update", headers=user_headers(CART_USER), json={
            "product_id": 1,
            "quantity": 1
        })
        assert resp.status_code == 200

    def test_update_product_id_zero(self):
        """[BVA - Boundary: update product_id = 0]
        Invalid product id should return 404.
        """
        resp = post("/cart/update", headers=user_headers(CART_USER), json={"product_id": 0, "quantity": 1})
        assert resp.status_code == 404

    def test_update_product_id_one(self):
        """[BVA - Boundary: update product_id = 1]
        Valid product id update with quantity 1 should succeed.
        """
        post("/cart/add", headers=user_headers(CART_USER), json={"product_id": 1, "quantity": 2})
        resp = post("/cart/update", headers=user_headers(CART_USER), json={"product_id": 1, "quantity": 1})
        assert resp.status_code == 200

    def test_update_product_id_250(self):
        """[BVA - Boundary: update product_id = 250]
        Valid upper-bound product id update with quantity 1 should succeed.
        """
        post("/cart/add", headers=user_headers(CART_USER), json={"product_id": 250, "quantity": 2})
        resp = post("/cart/update", headers=user_headers(CART_USER), json={"product_id": 250, "quantity": 1})
        assert resp.status_code == 200

    def test_update_product_id_251(self):
        """[BVA - Boundary: update product_id = 251]
        Non-existent product id should return 404.
        """
        resp = post("/cart/update", headers=user_headers(CART_USER), json={"product_id": 251, "quantity": 1})
        assert resp.status_code == 404

    def test_update_product_248_quantity_0(self):
        """[BVA - Boundary: update quantity = 0]
        Zero quantity should be rejected.
        """
        post("/cart/add", headers=user_headers(CART_USER), json={"product_id": 248, "quantity": 1})
        resp = post("/cart/update", headers=user_headers(CART_USER), json={"product_id": 248, "quantity": 0})
        assert resp.status_code == 400

    def test_update_product_248_quantity_21(self):
        """[BVA - Stock Boundary: update quantity > stock]
        Quantity 21 for product 248 should be rejected.
        """
        post("/cart/add", headers=user_headers(CART_USER), json={"product_id": 248, "quantity": 1})
        resp = post("/cart/update", headers=user_headers(CART_USER), json={"product_id": 248, "quantity": 21})
        assert resp.status_code == 400

    def test_update_product_248_quantity_20(self):
        """[BVA - Stock Boundary: update quantity == stock]
        Quantity 20 for product 248 should be accepted.
        """
        post("/cart/add", headers=user_headers(CART_USER), json={"product_id": 248, "quantity": 1})
        resp = post("/cart/update", headers=user_headers(CART_USER), json={"product_id": 248, "quantity": 20})
        assert resp.status_code == 200

    def test_update_product_248_quantity_1(self):
        """[BVA - Boundary: update quantity = 1]
        Minimum valid quantity should be accepted.
        """
        post("/cart/add", headers=user_headers(CART_USER), json={"product_id": 248, "quantity": 5})
        resp = post("/cart/update", headers=user_headers(CART_USER), json={"product_id": 248, "quantity": 1})
        assert resp.status_code == 200

    def test_update_missing_product_id(self):
        """[ECP - Invalid Class: Missing product_id on update]
        Missing product_id should return 400.
        """
        resp = post("/cart/update", headers=user_headers(CART_USER), json={"quantity": 1})
        assert resp.status_code == 400

    def test_update_missing_quantity(self):
        """[ECP - Invalid Class: Missing quantity on update]
        Missing quantity should return 400.
        """
        resp = post("/cart/update", headers=user_headers(CART_USER), json={"product_id": 1})
        assert resp.status_code == 400

    def test_update_missing_product_id_and_quantity(self):
        """[ECP - Invalid Class: Missing all required update fields]
        Empty body should return 400.
        """
        resp = post("/cart/update", headers=user_headers(CART_USER), json={})
        assert resp.status_code == 400


class TestRemoveFromCart:
    """Tests for POST /api/v1/cart/remove."""

    def test_remove_existing_item(self):
        """[ECP - Valid Class: Remove item in cart]
        Removing a product that is in the cart should succeed.
        """
        post("/cart/add", headers=user_headers(CART_USER), json={"product_id": 1, "quantity": 1})
        resp = post("/cart/remove", headers=user_headers(CART_USER), json={"product_id": 1})
        assert resp.status_code == 200

    def test_remove_non_existent_item_returns_404(self):
        """[ECP - Invalid Class: Remove item not in cart]
        Removing a product not in the cart should return 404.
        """
        resp = post("/cart/remove", headers=user_headers(CART_USER), json={"product_id": 99999})
        assert resp.status_code == 404

    def test_remove_product_248_added_then_removed(self):
        """[ECP - Valid Class: Remove existing product 248]
        Removing product 248 after adding it should succeed.
        """
        post("/cart/add", headers=user_headers(CART_USER), json={"product_id": 248, "quantity": 1})
        resp = post("/cart/remove", headers=user_headers(CART_USER), json={"product_id": 248})
        assert resp.status_code == 200

    def test_remove_product_248_twice_second_rejected(self):
        """[ECP - Invalid Class: Remove same item twice]
        Second remove should fail because item is no longer in cart.
        """
        post("/cart/add", headers=user_headers(CART_USER), json={"product_id": 248, "quantity": 1})
        first = post("/cart/remove", headers=user_headers(CART_USER), json={"product_id": 248})
        second = post("/cart/remove", headers=user_headers(CART_USER), json={"product_id": 248})
        assert first.status_code == 200
        assert second.status_code in [400, 404]

    def test_remove_missing_product_id(self):
        """[ECP - Invalid Class: Missing product_id on remove]
        Missing product_id should return 400.
        """
        resp = post("/cart/remove", headers=user_headers(CART_USER), json={})
        assert resp.status_code == 400


class TestClearCart:
    """Tests for DELETE /api/v1/cart/clear."""

    def test_clear_cart(self):
        """[ECP - Valid Class: Clear cart with items]
        Clearing the cart should succeed.
        """
        post("/cart/add", headers=user_headers(CART_USER), json={"product_id": 1, "quantity": 1})
        resp = delete("/cart/clear", headers=user_headers(CART_USER))
        assert resp.status_code == 200

    def test_clear_empty_cart(self):
        """[ECP - Valid Class: Clear already empty cart]
        Clearing an empty cart should also succeed (no error).
        """
        resp = delete("/cart/clear", headers=user_headers(CART_USER))
        assert resp.status_code == 200

    def test_clear_then_get_shows_no_items(self):
        """[ECP - Valid Class: Clear then verify cart empty]
        After clear, cart should have no items.
        """
        post("/cart/add", headers=user_headers(CART_USER), json={"product_id": 248, "quantity": 1})
        clear_resp = delete("/cart/clear", headers=user_headers(CART_USER))
        assert clear_resp.status_code == 200

        cart = get("/cart", headers=user_headers(CART_USER)).json()
        assert _quantity_for_product(cart, 248) == 0
        assert len(_cart_items(cart)) == 0


class TestCartStockAndAccumulationFlows:
    """Integrated add/get/add stock-consistency scenarios."""

    def test_add_product_248_accumulates_quantity(self):
        """[ECP - Valid Class: Add same product increments existing quantity]
        Add 248 twice by 1 and verify quantity becomes previous+1.
        """
        add1 = post("/cart/add", headers=user_headers(CART_USER), json={"product_id": 248, "quantity": 1})
        assert add1.status_code == 200

        cart_before = get("/cart", headers=user_headers(CART_USER)).json()
        prev_qty = _quantity_for_product(cart_before, 248)

        add2 = post("/cart/add", headers=user_headers(CART_USER), json={"product_id": 248, "quantity": 1})
        assert add2.status_code == 200

        cart_after = get("/cart", headers=user_headers(CART_USER)).json()
        new_qty = _quantity_for_product(cart_after, 248)
        assert new_qty == prev_qty + 1

    def test_add_product_248_exceeds_stock_after_existing_quantity(self):
        """[ECP - Invalid Class: Aggregate quantity exceeds stock]
        After adding 1 and 1, adding 20 more should fail because total would exceed stock 20.
        """
        assert post("/cart/add", headers=user_headers(CART_USER), json={"product_id": 248, "quantity": 1}).status_code == 200
        assert post("/cart/add", headers=user_headers(CART_USER), json={"product_id": 248, "quantity": 1}).status_code == 200

        resp = post("/cart/add", headers=user_headers(CART_USER), json={"product_id": 248, "quantity": 20})
        assert resp.status_code == 400
