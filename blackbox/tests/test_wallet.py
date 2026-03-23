"""
Test: Wallet Endpoints
Tests GET /api/v1/wallet, POST /api/v1/wallet/add, POST /api/v1/wallet/pay.
Techniques: Equivalence Class Partitioning (ECP), Boundary Value Analysis (BVA)
"""

import pytest
from .conftest import get, post, user_headers

# Use a dedicated user for wallet tests
WALLET_USER = 20


class TestGetWallet:
    """Tests for GET /api/v1/wallet."""

    def test_get_wallet_balance(self):
        """[ECP - Valid Class: Retrieve wallet balance]
        Should return 200 with the current balance.
        """
        resp = get("/wallet", headers=user_headers(WALLET_USER))
        assert resp.status_code == 200
        data = resp.json()
        assert "balance" in data or "wallet_balance" in data


class TestAddToWallet:
    """Tests for POST /api/v1/wallet/add."""

    def test_add_valid_amount(self):
        """[ECP - Valid Class: Add valid amount]
        Adding a valid amount (0 < amount <= 100000) should succeed.
        """
        resp = post("/wallet/add", headers=user_headers(WALLET_USER), json={
            "amount": 100
        })
        assert resp.status_code == 200

    def test_add_zero_amount_rejected(self):
        """[BVA - Boundary: Amount = 0 (invalid)]
        Amount must be more than 0. Zero should be rejected.
        """
        resp = post("/wallet/add", headers=user_headers(WALLET_USER), json={
            "amount": 0
        })
        assert resp.status_code == 400

    def test_add_negative_amount_rejected(self):
        """[BVA - Boundary: Amount = -1 (invalid)]
        Negative amount should be rejected.
        """
        resp = post("/wallet/add", headers=user_headers(WALLET_USER), json={
            "amount": -1
        })
        assert resp.status_code == 400

    def test_add_small_positive_amount(self):
        """[BVA - Boundary: Amount = 0.01 (minimum positive)]
        Very small positive amount should be valid.
        """
        resp = post("/wallet/add", headers=user_headers(WALLET_USER), json={
            "amount": 0.01
        })
        assert resp.status_code == 200

    def test_add_max_amount(self):
        """[BVA - Boundary: Amount = 100000 (maximum valid)]
        Amount at maximum allowed value should succeed.
        """
        resp = post("/wallet/add", headers=user_headers(WALLET_USER), json={
            "amount": 100000
        })
        assert resp.status_code == 200

    def test_add_above_max_amount_rejected(self):
        """[BVA - Boundary: Amount = 100001 (above maximum)]
        Amount exceeding max should be rejected.
        """
        resp = post("/wallet/add", headers=user_headers(WALLET_USER), json={
            "amount": 100001
        })
        assert resp.status_code == 400

    def test_add_one_amount(self):
        """[BVA - Boundary: Amount = 1 (valid low value)]
        Amount of 1 should be valid.
        """
        resp = post("/wallet/add", headers=user_headers(WALLET_USER), json={
            "amount": 1
        })
        assert resp.status_code == 200

    def test_wallet_balance_increases_after_add(self):
        """[ECP - Valid Class: Balance verification after add]
        After adding money, the balance should increase by the exact amount.
        """
        before = get("/wallet", headers=user_headers(WALLET_USER)).json()
        before_balance = before.get("balance", before.get("wallet_balance", 0))

        post("/wallet/add", headers=user_headers(WALLET_USER), json={"amount": 50})

        after = get("/wallet", headers=user_headers(WALLET_USER)).json()
        after_balance = after.get("balance", after.get("wallet_balance", 0))

        assert after_balance == pytest.approx(before_balance + 50, abs=0.01)


class TestWalletPay:
    """Tests for POST /api/v1/wallet/pay."""

    def test_pay_valid_amount(self):
        """[ECP - Valid Class: Pay with sufficient balance]
        Paying an amount within the wallet balance should succeed.
        """
        # First add money to ensure sufficient balance
        post("/wallet/add", headers=user_headers(WALLET_USER), json={"amount": 500})
        resp = post("/wallet/pay", headers=user_headers(WALLET_USER), json={
            "amount": 10
        })
        assert resp.status_code == 200

    def test_pay_zero_amount_rejected(self):
        """[BVA - Boundary: Pay amount = 0 (invalid)]
        Amount must be more than 0.
        """
        resp = post("/wallet/pay", headers=user_headers(WALLET_USER), json={
            "amount": 0
        })
        assert resp.status_code == 400

    def test_pay_negative_amount_rejected(self):
        """[BVA - Boundary: Pay amount = -1 (invalid)]
        Negative amount should be rejected.
        """
        resp = post("/wallet/pay", headers=user_headers(WALLET_USER), json={
            "amount": -1
        })
        assert resp.status_code == 400

    def test_pay_exceeds_balance_rejected(self):
        """[ECP - Invalid Class: Pay more than balance]
        When wallet balance is insufficient, should return 400.
        """
        resp = post("/wallet/pay", headers=user_headers(WALLET_USER), json={
            "amount": 9999999
        })
        assert resp.status_code == 400

    def test_exact_deduction_after_pay(self):
        """[ECP - Valid Class: Exact deduction verification]
        After paying, the exact amount requested must be deducted.
        """
        # Add known amount
        post("/wallet/add", headers=user_headers(WALLET_USER), json={"amount": 200})
        before = get("/wallet", headers=user_headers(WALLET_USER)).json()
        before_balance = before.get("balance", before.get("wallet_balance", 0))

        pay_amount = 75
        post("/wallet/pay", headers=user_headers(WALLET_USER), json={"amount": pay_amount})

        after = get("/wallet", headers=user_headers(WALLET_USER)).json()
        after_balance = after.get("balance", after.get("wallet_balance", 0))

        assert after_balance == pytest.approx(before_balance - pay_amount, abs=0.01), \
            f"Expected {before_balance - pay_amount}, got {after_balance}"
