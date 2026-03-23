"""
Test: Product Endpoints
Tests GET /api/v1/products and GET /api/v1/products/{product_id}.
Techniques: Equivalence Class Partitioning (ECP), Boundary Value Analysis (BVA)
"""

from .conftest import get, user_headers, base_headers


class TestGetProducts:
    """Tests for GET /api/v1/products."""

    def test_get_all_products_returns_list(self):
        """[ECP - Valid Class: Retrieve product list]
        Should return 200 with a list of active products.
        """
        resp = get("/products", headers=user_headers())
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_product_list_only_active_products(self):
        """[ECP - Valid Class: Only active products shown]
        The product list should not contain inactive products.
        """
        # Get user-facing products
        user_products = get("/products", headers=user_headers()).json()
        # Get admin products (includes inactive)
        admin_products = get("/admin/products", headers=base_headers()).json()

        inactive_ids = {p["product_id"] for p in admin_products if not p["is_active"]}
        user_product_ids = {p["product_id"] for p in user_products}

        overlap = inactive_ids & user_product_ids
        assert len(overlap) == 0, f"Inactive products found in user's list: {overlap}"

    def test_product_list_contains_all_active_products(self):
        """[ECP - Valid Class: All active products included]
        Every active product from the admin endpoint should appear in the user list.
        """
        user_products = get("/products", headers=user_headers()).json()
        admin_products = get("/admin/products", headers=base_headers()).json()

        active_ids = {p["product_id"] for p in admin_products if p["is_active"]}
        user_product_ids = {p["product_id"] for p in user_products}

        missing = active_ids - user_product_ids
        assert len(missing) == 0, f"Active products missing from user list: {missing}"

    def test_product_price_matches_database(self):
        """[ECP - Valid Class: Price accuracy]
        The price shown for every product must match the database price.
        """
        user_products = get("/products", headers=user_headers()).json()
        admin_products = get("/admin/products", headers=base_headers()).json()

        admin_prices = {p["product_id"]: p["price"] for p in admin_products}

        for product in user_products:
            pid = product["product_id"]
            assert product["price"] == admin_prices[pid], \
                f"Price mismatch for product {pid}: user={product['price']}, admin={admin_prices[pid]}"


class TestGetProductById:
    """Tests for GET /api/v1/products/{product_id}."""

    def test_get_existing_product(self):
        """[ECP - Valid Class: Existing product ID]
        Should return 200 with the product data.
        """
        resp = get("/products/1", headers=user_headers())
        assert resp.status_code == 200
        data = resp.json()
        assert data["product_id"] == 1

    def test_get_non_existent_product_returns_404(self):
        """[ECP - Invalid Class: Non-existent product ID]
        Should return 404 for a product that does not exist.
        """
        resp = get("/products/251", headers=user_headers())
        assert resp.status_code == 404

    def test_get_product_id_zero(self):
        """[BVA - Boundary: Product ID = 0]
        Zero is not a valid product ID, should return 404.
        """
        resp = get("/products/0", headers=user_headers())
        assert resp.status_code == 404

    def test_get_product_id_negative(self):
        """[BVA - Boundary: Negative product ID]
        Should return 404.
        """
        resp = get("/products/-1", headers=user_headers())
        assert resp.status_code == 404

    def test_get_first_product(self):
        """[BVA - Boundary: Product ID = 1 (first)]
        The minimum valid product ID.
        """
        resp = get("/products/1", headers=user_headers())
        assert resp.status_code == 200

    def test_get_last_product(self):
        """[BVA - Boundary: Product ID = 250 (last valid)]
        The highest valid product ID should succeed.
        """
        resp = get("/products/250", headers=user_headers())
        assert resp.status_code == 200

class TestProductFiltering:
    """Tests for product filtering, searching, and sorting."""

    def test_filter_by_category(self):
        """[ECP - Valid Class: Filter by existing category]
        Filtering by 'Fruits' should return only fruit products.
        """
        resp = get("/products", headers=user_headers(), params={"category": "Fruits"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) > 0
        for product in data:
            assert product["category"] == "Fruits"

    def test_filter_by_category_dynamic_existing(self):
        """[ECP - Valid Class: Filter by any existing category]
        Use a known category from product data and verify all rows match that category.
        """
        all_products = get("/products", headers=user_headers()).json()
        assert len(all_products) > 0
        category = all_products[0]["category"]

        resp = get("/products", headers=user_headers(), params={"category": category})
        assert resp.status_code == 200
        data = resp.json()
        for product in data:
            assert product["category"] == category

    def test_filter_by_non_existent_category(self):
        """[ECP - Invalid Class: Non-existent category]
        Filtering by a non-existent category should return an empty list.
        """
        resp = get("/products", headers=user_headers(), params={"category": "ZZZ_NotReal"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 0

    def test_search_by_name(self):
        """[ECP - Valid Class: Search by name]
        Searching for 'Apple' should return products with 'Apple' in the name.
        """
        resp = get("/products", headers=user_headers(), params={"name": "Apple"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) > 0
        for product in data:
            assert "apple" in product["name"].lower() or "Apple" in product["name"]

    def test_sort_by_price_ascending(self):
        """[ECP - Valid Class: Sort by price ascending]
        Products should be sorted by price in ascending order.
        """
        resp = get("/products", headers=user_headers(), params={"sort": "price_asc"})
        assert resp.status_code == 200
        data = resp.json()
        if len(data) > 1:
            prices = [p["price"] for p in data]
            assert prices == sorted(prices), "Products not sorted by price ascending"

    def test_sort_by_price_descending(self):
        """[ECP - Valid Class: Sort by price descending]
        Products should be sorted by price in descending order.
        """
        resp = get("/products", headers=user_headers(), params={"sort": "price_desc"})
        assert resp.status_code == 200
        data = resp.json()
        if len(data) > 1:
            prices = [p["price"] for p in data]
            assert prices == sorted(prices, reverse=True), "Products not sorted by price descending"
