"""
Shared fixtures and helpers for QuickCart BlackBox API tests.
"""

import pytest
import requests

BASE_URL = "http://localhost:8080/api/v1"
ROLL_NUMBER = "2023111016"

# Known valid user IDs from the database (800 users: 1-800)
VALID_USER_ID = 1
SECOND_USER_ID = 2

# Known product IDs
VALID_PRODUCT_ID = 1       # Apple - Red, price=120, stock=195, active
INACTIVE_PRODUCT_ID = 90   # Inactive Product 1


def base_headers():
    """Return headers with only X-Roll-Number."""
    return {"X-Roll-Number": ROLL_NUMBER}


def user_headers(user_id=VALID_USER_ID):
    """Return headers with X-Roll-Number and X-User-ID."""
    return {
        "X-Roll-Number": ROLL_NUMBER,
        "X-User-ID": str(user_id),
    }


def get(endpoint, headers=None, params=None):
    """Make a GET request."""
    return requests.get(f"{BASE_URL}{endpoint}", headers=headers or base_headers(), params=params)


def post(endpoint, headers=None, json=None):
    """Make a POST request."""
    return requests.post(f"{BASE_URL}{endpoint}", headers=headers or base_headers(), json=json)


def put(endpoint, headers=None, json=None):
    """Make a PUT request."""
    return requests.put(f"{BASE_URL}{endpoint}", headers=headers or base_headers(), json=json)


def delete(endpoint, headers=None):
    """Make a DELETE request."""
    return requests.delete(f"{BASE_URL}{endpoint}", headers=headers or base_headers())


@pytest.fixture
def clear_cart():
    """Clear the cart for the default user before and after a test."""
    delete("/cart/clear", headers=user_headers())
    yield
    delete("/cart/clear", headers=user_headers())


@pytest.fixture
def add_product_to_cart():
    """Add a known product to the cart and clear after."""
    delete("/cart/clear", headers=user_headers())
    post("/cart/add", headers=user_headers(), json={"product_id": VALID_PRODUCT_ID, "quantity": 1})
    yield
    delete("/cart/clear", headers=user_headers())


@pytest.fixture
def clear_cart_user2():
    """Clear the cart for user 2 before and after a test."""
    delete("/cart/clear", headers=user_headers(SECOND_USER_ID))
    yield
    delete("/cart/clear", headers=user_headers(SECOND_USER_ID))
