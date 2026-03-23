"""
Test: Global Header Validation
Tests the X-Roll-Number and X-User-ID header requirements that apply to all endpoints.
Techniques: Equivalence Class Partitioning (ECP), Boundary Value Analysis (BVA)
"""

import pytest
from .conftest import BASE_URL, ROLL_NUMBER, get, post, user_headers, base_headers
import requests


class TestXRollNumberHeader:
    """Tests for the mandatory X-Roll-Number header."""

    def test_missing_roll_number_returns_401(self):
        """[ECP - Invalid Class: Missing required header]
        Every request MUST include X-Roll-Number. Omitting it should return 401.
        """
        resp = requests.get(f"{BASE_URL}/admin/products", headers={})
        assert resp.status_code == 401

    def test_non_integer_roll_number_returns_400(self):
        """[ECP - Invalid Class: Wrong data type]
        X-Roll-Number must be a valid integer. Letters should return 400.
        """
        resp = requests.get(f"{BASE_URL}/admin/products", headers={"X-Roll-Number": "abc"})
        assert resp.status_code == 400

    def test_special_chars_roll_number_returns_400(self):
        """[ECP - Invalid Class: Special characters]
        X-Roll-Number with symbols should return 400.
        """
        resp = requests.get(f"{BASE_URL}/admin/products", headers={"X-Roll-Number": "!@#$"})
        assert resp.status_code == 400

    def test_valid_integer_roll_number_succeeds(self):
        """[ECP - Valid Class: Correct integer value]
        A valid integer X-Roll-Number should allow the request to proceed.
        """
        resp = requests.get(f"{BASE_URL}/admin/products", headers={"X-Roll-Number": "123456"})
        assert resp.status_code == 200

    def test_zero_roll_number(self):
        """[BVA - Boundary: Zero value]
        Zero is a valid integer, should be accepted.
        """
        resp = requests.get(f"{BASE_URL}/admin/products", headers={"X-Roll-Number": "0"})
        assert resp.status_code == 200

    def test_negative_roll_number(self):
        """[BVA - Boundary: Negative integer]
        Negative integer is out-of-range for roll number semantics and should be rejected.
        """
        resp = requests.get(f"{BASE_URL}/admin/products", headers={"X-Roll-Number": "-1"})
        assert resp.status_code == 400

    def test_large_roll_number(self):
        """[BVA - Boundary: Very large integer]
        Very large integer should still be a valid roll number.
        """
        resp = requests.get(f"{BASE_URL}/admin/products", headers={"X-Roll-Number": "999999999"})
        assert resp.status_code == 200

    def test_empty_roll_number_returns_error(self):
        """[ECP - Invalid Class: Empty string]
        Empty string is not a valid integer, should be rejected.
        """
        resp = requests.get(f"{BASE_URL}/admin/products", headers={"X-Roll-Number": ""})
        assert resp.status_code in [400, 401]

    def test_float_roll_number_returns_400(self):
        """[ECP - Invalid Class: Float value]
        A float is not a valid integer, should return 400.
        """
        resp = requests.get(f"{BASE_URL}/admin/products", headers={"X-Roll-Number": "12.34"})
        assert resp.status_code == 400


class TestXUserIDHeader:
    """Tests for the X-User-ID header on user-scoped endpoints."""

    def test_missing_user_id_returns_400(self):
        """[ECP - Invalid Class: Missing required header]
        User-scoped endpoints require X-User-ID. Omitting it should return 400.
        """
        resp = requests.get(f"{BASE_URL}/profile", headers=base_headers())
        assert resp.status_code == 400

    def test_non_integer_user_id_returns_400(self):
        """[ECP - Invalid Class: Wrong data type]
        X-User-ID must be a positive integer. Non-integer should return 400.
        """
        headers = base_headers()
        headers["X-User-ID"] = "abc"
        resp = requests.get(f"{BASE_URL}/profile", headers=headers)
        assert resp.status_code == 400

    def test_negative_user_id_returns_400(self):
        """[BVA - Boundary: Negative user ID]
        X-User-ID must be a positive integer. Negative should return 400.
        """
        headers = base_headers()
        headers["X-User-ID"] = "-1"
        resp = requests.get(f"{BASE_URL}/profile", headers=headers)
        assert resp.status_code == 400

    def test_zero_user_id_returns_400(self):
        """[BVA - Boundary: Zero user ID]
        X-User-ID must be a positive integer. Zero is not positive, should return 400.
        """
        headers = base_headers()
        headers["X-User-ID"] = "0"
        resp = requests.get(f"{BASE_URL}/profile", headers=headers)
        assert resp.status_code == 400

    def test_valid_user_id_succeeds(self):
        """[ECP - Valid Class: Existing positive integer]
        A valid positive user ID for an existing user should succeed.
        """
        resp = get("/profile", headers=user_headers(1))
        assert resp.status_code == 200

    def test_max_valid_user_id_succeeds(self):
        """[BVA - Boundary: Upper valid user ID]
        User ID 800 exists in dataset and should succeed.
        """
        resp = get("/profile", headers=user_headers(800))
        assert resp.status_code == 200

    def test_non_existent_user_id_returns_400(self):
        """[ECP - Invalid Class: Non-existent user]
        A positive integer that does not match any user should return 400.
        """
        resp = get("/profile", headers=user_headers(801))
        assert resp.status_code == 400

    def test_admin_endpoint_does_not_require_user_id(self):
        """[ECP - Valid Class: Admin endpoints]
        Admin endpoints should NOT require X-User-ID header.
        """
        resp = get("/admin/products", headers=base_headers())
        assert resp.status_code == 200
