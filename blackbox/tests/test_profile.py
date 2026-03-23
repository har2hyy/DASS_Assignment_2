"""
Test: Profile Endpoints
Tests GET /api/v1/profile and PUT /api/v1/profile.
Techniques: Equivalence Class Partitioning (ECP), Boundary Value Analysis (BVA)
"""

import pytest
from .conftest import get, put, user_headers, VALID_USER_ID, SECOND_USER_ID


class TestGetProfile:
    """Tests for GET /api/v1/profile."""

    def test_get_profile_valid_user(self):
        """[ECP - Valid Class: Existing user]
        Should return 200 with the user's profile data.
        """
        resp = get("/profile", headers=user_headers())
        assert resp.status_code == 200
        data = resp.json()
        assert "name" in data
        assert "email" in data
        assert "phone" in data

    def test_get_profile_different_user(self):
        """[ECP - Valid Class: Another existing user]
        Should return profile for user 2.
        """
        resp = get("/profile", headers=user_headers(SECOND_USER_ID))
        assert resp.status_code == 200
        data = resp.json()
        assert "name" in data


class TestUpdateProfile:
    """Tests for PUT /api/v1/profile."""

    def test_update_profile_valid_data(self):
        """[ECP - Valid Class: Valid name and phone]
        Updating with a valid name (2-50 chars) and phone (10 digits) should succeed.
        """
        resp = put("/profile", headers=user_headers(), json={
            "name": "Test User",
            "phone": "9876543210"
        })
        assert resp.status_code == 200

    def test_update_name_min_length_valid(self):
        """[BVA - Boundary: Name = 2 characters (minimum valid)]
        Name with exactly 2 characters should be accepted.
        """
        resp = put("/profile", headers=user_headers(), json={
            "name": "Ab",
            "phone": "9876543210"
        })
        assert resp.status_code == 200

    def test_update_name_below_min_length(self):
        """[BVA - Boundary: Name = 1 character (below minimum)]
        Name with 1 character should be rejected with 400.
        """
        resp = put("/profile", headers=user_headers(), json={
            "name": "A",
            "phone": "9876543210"
        })
        assert resp.status_code == 400

    def test_update_name_max_length_valid(self):
        """[BVA - Boundary: Name = 50 characters (maximum valid)]
        Name with exactly 50 characters should be accepted.
        """
        resp = put("/profile", headers=user_headers(), json={
            "name": "A" * 50,
            "phone": "9876543210"
        })
        assert resp.status_code == 200

    def test_update_name_above_max_length(self):
        """[BVA - Boundary: Name = 51 characters (above maximum)]
        Name with 51 characters should be rejected with 400.
        """
        resp = put("/profile", headers=user_headers(), json={
            "name": "A" * 51,
            "phone": "9876543210"
        })
        assert resp.status_code == 400

    def test_update_phone_valid_10_digits(self):
        """[BVA - Boundary: Phone = exactly 10 digits (valid)]
        Phone with exactly 10 digits should be accepted.
        """
        resp = put("/profile", headers=user_headers(), json={
            "name": "Test User",
            "phone": "1234567890"
        })
        assert resp.status_code == 200

    def test_update_phone_9_digits_invalid(self):
        """[BVA - Boundary: Phone = 9 digits (below minimum)]
        Phone with 9 digits should be rejected with 400.
        """
        resp = put("/profile", headers=user_headers(), json={
            "name": "Test User",
            "phone": "123456789"
        })
        assert resp.status_code == 400

    def test_update_phone_11_digits_invalid(self):
        """[BVA - Boundary: Phone = 11 digits (above maximum)]
        Phone with 11 digits should be rejected with 400.
        """
        resp = put("/profile", headers=user_headers(), json={
            "name": "Test User",
            "phone": "12345678901"
        })
        assert resp.status_code == 400

    def test_update_phone_with_letters_invalid(self):
        """[ECP - Invalid Class: Non-digit characters in phone]
        Phone with letters should be rejected with 400.
        """
        resp = put("/profile", headers=user_headers(), json={
            "name": "Test User",
            "phone": "abcdefghij"
        })
        assert resp.status_code == 400

    def test_update_empty_name_invalid(self):
        """[ECP - Invalid Class: Empty name]
        Empty name string should be rejected with 400.
        """
        resp = put("/profile", headers=user_headers(), json={
            "name": "",
            "phone": "9876543210"
        })
        assert resp.status_code == 400

    def test_update_missing_fields(self):
        """[ECP - Invalid Class: Missing required fields]
        Sending an empty body should be rejected.
        """
        resp = put("/profile", headers=user_headers(), json={})
        assert resp.status_code == 400

    def test_update_missing_phone_invalid(self):
        """[ECP - Invalid Class: Missing phone field]
        Omitting phone should be rejected.
        """
        resp = put("/profile", headers=user_headers(), json={
            "name": "Test User"
        })
        assert resp.status_code == 400

    def test_update_missing_name_invalid(self):
        """[ECP - Invalid Class: Missing name field]
        Omitting name should be rejected.
        """
        resp = put("/profile", headers=user_headers(), json={
            "phone": "9876543210"
        })
        assert resp.status_code == 400

    def test_update_missing_name_and_phone_invalid(self):
        """[ECP - Invalid Class: Missing both fields]
        Omitting both name and phone should be rejected.
        """
        resp = put("/profile", headers=user_headers(), json={})
        assert resp.status_code == 400
