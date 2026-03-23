"""
Test: Loyalty Points Endpoints
Tests GET /api/v1/loyalty and POST /api/v1/loyalty/redeem.
Techniques: Equivalence Class Partitioning (ECP), Boundary Value Analysis (BVA)
"""

import pytest
from .conftest import get, post, user_headers

# Use a dedicated user for loyalty tests
LOYALTY_USER = 30
LOYALTY_USER_394 = 394
LOYALTY_USER_395 = 395


class TestGetLoyalty:
    """Tests for GET /api/v1/loyalty."""

    def test_get_loyalty_points(self):
        """[ECP - Valid Class: Retrieve loyalty points]
        Should return 200 with the user's loyalty point balance.
        """
        resp = get("/loyalty", headers=user_headers(LOYALTY_USER))
        assert resp.status_code == 200
        data = resp.json()
        assert "points" in data or "loyalty_points" in data


class TestRedeemLoyalty:
    """Tests for POST /api/v1/loyalty/redeem."""

    def test_redeem_valid_amount(self):
        """[ECP - Valid Class: Redeem within available points]
        Redeeming when user has sufficient points should succeed.
        """
        # Check current points
        points_resp = get("/loyalty", headers=user_headers(LOYALTY_USER)).json()
        points = points_resp.get("points", points_resp.get("loyalty_points", 0))
        if points >= 1:
            resp = post("/loyalty/redeem", headers=user_headers(LOYALTY_USER), json={
                "points": 1
            })
            assert resp.status_code == 200

    def test_redeem_zero_rejected(self):
        """[BVA - Boundary: Redeem 0 points (invalid)]
        Amount to redeem must be at least 1.
        """
        resp = post("/loyalty/redeem", headers=user_headers(LOYALTY_USER), json={
            "points": 0
        })
        assert resp.status_code == 400

    def test_redeem_negative_rejected(self):
        """[BVA - Boundary: Redeem -1 points (invalid)]
        Negative redeem amount should be rejected.
        """
        resp = post("/loyalty/redeem", headers=user_headers(LOYALTY_USER), json={
            "points": -1
        })
        assert resp.status_code == 400

    def test_redeem_one_point_valid(self):
        """[BVA - Boundary: Redeem 1 point (minimum valid)]
        Minimum valid redemption is 1 point.
        """
        # First check if user has at least 1 point
        points_resp = get("/loyalty", headers=user_headers(LOYALTY_USER)).json()
        points = points_resp.get("points", points_resp.get("loyalty_points", 0))
        if points >= 1:
            resp = post("/loyalty/redeem", headers=user_headers(LOYALTY_USER), json={
                "points": 1
            })
            assert resp.status_code == 200

    def test_redeem_more_than_available_rejected(self):
        """[ECP - Invalid Class: Redeem more than available]
        Redeeming more points than the user has should fail.
        """
        resp = post("/loyalty/redeem", headers=user_headers(LOYALTY_USER), json={
            "points": 999999
        })
        assert resp.status_code == 400

    def test_redeem_exact_balance(self):
        """[BVA - Boundary: Redeem exactly all available points]
        Redeeming the exact number of available points should succeed.
        """
        points_resp = get("/loyalty", headers=user_headers(LOYALTY_USER)).json()
        points = points_resp.get("points", points_resp.get("loyalty_points", 0))
        if points > 0:
            resp = post("/loyalty/redeem", headers=user_headers(LOYALTY_USER), json={
                "points": points
            })
            assert resp.status_code == 200

    def test_redeem_one_above_balance_rejected(self):
        """[BVA - Boundary: Redeem one more than available]
        Trying to redeem balance+1 should fail.
        """
        points_resp = get("/loyalty", headers=user_headers(LOYALTY_USER)).json()
        points = points_resp.get("points", points_resp.get("loyalty_points", 0))
        resp = post("/loyalty/redeem", headers=user_headers(LOYALTY_USER), json={
            "points": points + 1
        })
        assert resp.status_code == 400

    def test_redeem_one_point_user_394(self):
        """[BVA - Boundary: Redeem 1 point for user 394]
        User 394 should be able to redeem 1 point.
        """
        resp = post("/loyalty/redeem", headers=user_headers(LOYALTY_USER_394), json={"points": 1})
        assert resp.status_code == 200

    def test_redeem_thirteen_points_user_395_rejected(self):
        """[ECP - Invalid Class: Redeem above available points]
        User 395 with 12 points should not be able to redeem 13 points.
        """
        resp = post("/loyalty/redeem", headers=user_headers(LOYALTY_USER_395), json={"points": 13})
        assert resp.status_code == 400
