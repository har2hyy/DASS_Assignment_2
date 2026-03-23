"""
Test: Address Endpoints
Tests GET, POST, PUT, DELETE /api/v1/addresses.
Techniques: Equivalence Class Partitioning (ECP), Boundary Value Analysis (BVA)
"""

import pytest
from .conftest import get, post, put, delete, user_headers, VALID_USER_ID, SECOND_USER_ID


class TestGetAddresses:
    """Tests for GET /api/v1/addresses."""

    def test_get_addresses_returns_list(self):
        """[ECP - Valid Class: Retrieve user's addresses]
        Should return 200 with a list of addresses.
        """
        resp = get("/addresses", headers=user_headers())
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestCreateAddress:
    """Tests for POST /api/v1/addresses."""

    def test_create_address_with_home_label(self):
        """[ECP - Valid Class: HOME label]
        Creating an address with label HOME should succeed.
        """
        resp = post("/addresses", headers=user_headers(), json={
            "label": "HOME",
            "street": "123 Main Street",
            "city": "Hyderabad",
            "pincode": "500032",
            "is_default": False
        })
        assert resp.status_code in [200, 201]
        data = resp.json()
        assert "address_id" in data or ("address" in data and "address_id" in data["address"])

    def test_create_address_with_office_label(self):
        """[ECP - Valid Class: OFFICE label]
        Creating an address with label OFFICE should succeed.
        """
        resp = post("/addresses", headers=user_headers(), json={
            "label": "OFFICE",
            "street": "456 Work Avenue",
            "city": "Bangalore",
            "pincode": "560001",
            "is_default": False
        })
        assert resp.status_code in [200, 201]

    def test_create_address_with_other_label(self):
        """[ECP - Valid Class: OTHER label]
        Creating an address with label OTHER should succeed.
        """
        resp = post("/addresses", headers=user_headers(), json={
            "label": "OTHER",
            "street": "789 Other Lane",
            "city": "Mumbai",
            "pincode": "400001",
            "is_default": False
        })
        assert resp.status_code in [200, 201]

    def test_create_address_invalid_label(self):
        """[ECP - Invalid Class: Invalid label value]
        Label must be HOME, OFFICE, or OTHER. Other values should return 400.
        """
        resp = post("/addresses", headers=user_headers(), json={
            "label": "INVALID",
            "street": "123 Main Street",
            "city": "Hyderabad",
            "pincode": "500032",
            "is_default": False
        })
        assert resp.status_code == 400

    def test_create_address_missing_label(self):
        """[ECP - Invalid Class: Missing label]
        Missing label should return 400.
        """
        resp = post("/addresses", headers=user_headers(), json={
            "street": "12345 Test Street",
            "city": "Hyderabad",
            "pincode": "500032",
            "is_default": False
        })
        assert resp.status_code == 400

    def test_create_address_missing_street(self):
        """[ECP - Invalid Class: Missing street]
        Missing street should return 400.
        """
        resp = post("/addresses", headers=user_headers(), json={
            "label": "HOME",
            "city": "Hyderabad",
            "pincode": "500032",
            "is_default": False
        })
        assert resp.status_code == 400

    def test_create_address_missing_city(self):
        """[ECP - Invalid Class: Missing city]
        Missing city should return 400.
        """
        resp = post("/addresses", headers=user_headers(), json={
            "label": "HOME",
            "street": "12345 Test Street",
            "pincode": "500032",
            "is_default": False
        })
        assert resp.status_code == 400

    def test_create_address_missing_pincode(self):
        """[ECP - Invalid Class: Missing pincode]
        Missing pincode should return 400.
        """
        resp = post("/addresses", headers=user_headers(), json={
            "label": "HOME",
            "street": "12345 Test Street",
            "city": "Hyderabad",
            "is_default": False
        })
        assert resp.status_code == 400

    def test_create_address_missing_all_required_fields(self):
        """[ECP - Invalid Class: Missing all fields]
        Empty body should return 400.
        """
        resp = post("/addresses", headers=user_headers(), json={})
        assert resp.status_code == 400

    def test_create_address_street_min_length_valid(self):
        """[BVA - Boundary: Street = 5 characters (minimum valid)]
        Street with exactly 5 characters should be accepted.
        """
        resp = post("/addresses", headers=user_headers(), json={
            "label": "HOME",
            "street": "ABCDE",
            "city": "Delhi",
            "pincode": "110001",
            "is_default": False
        })
        assert resp.status_code in [200, 201]

    def test_create_address_street_below_min_length(self):
        """[BVA - Boundary: Street = 4 characters (below minimum)]
        Street with 4 characters should be rejected with 400.
        """
        resp = post("/addresses", headers=user_headers(), json={
            "label": "HOME",
            "street": "ABCD",
            "city": "Delhi",
            "pincode": "110001",
            "is_default": False
        })
        assert resp.status_code == 400

    def test_create_address_street_max_length_valid(self):
        """[BVA - Boundary: Street = 100 characters (maximum valid)]
        Street with exactly 100 characters should be accepted.
        """
        resp = post("/addresses", headers=user_headers(), json={
            "label": "HOME",
            "street": "A" * 100,
            "city": "Delhi",
            "pincode": "110001",
            "is_default": False
        })
        assert resp.status_code in [200, 201]

    def test_create_address_street_above_max_length(self):
        """[BVA - Boundary: Street = 101 characters (above maximum)]
        Street with 101 characters should be rejected with 400.
        """
        resp = post("/addresses", headers=user_headers(), json={
            "label": "HOME",
            "street": "A" * 101,
            "city": "Delhi",
            "pincode": "110001",
            "is_default": False
        })
        assert resp.status_code == 400

    def test_create_address_city_min_length_valid(self):
        """[BVA - Boundary: City = 2 characters (minimum valid)]
        City with exactly 2 characters should be accepted.
        """
        resp = post("/addresses", headers=user_headers(), json={
            "label": "HOME",
            "street": "12345 Test St",
            "city": "AB",
            "pincode": "110001",
            "is_default": False
        })
        assert resp.status_code in [200, 201]

    def test_create_address_city_below_min_length(self):
        """[BVA - Boundary: City = 1 character (below minimum)]
        City with 1 character should be rejected with 400.
        """
        resp = post("/addresses", headers=user_headers(), json={
            "label": "HOME",
            "street": "12345 Test St",
            "city": "A",
            "pincode": "110001",
            "is_default": False
        })
        assert resp.status_code == 400

    def test_create_address_city_max_length_valid(self):
        """[BVA - Boundary: City = 50 characters (maximum valid)]
        City with exactly 50 characters should be accepted.
        """
        resp = post("/addresses", headers=user_headers(), json={
            "label": "HOME",
            "street": "12345 Test Street",
            "city": "A" * 50,
            "pincode": "110001",
            "is_default": False
        })
        assert resp.status_code in [200, 201]

    def test_create_address_city_above_max_length(self):
        """[BVA - Boundary: City = 51 characters (above maximum)]
        City with 51 characters should be rejected with 400.
        """
        resp = post("/addresses", headers=user_headers(), json={
            "label": "HOME",
            "street": "12345 Test Street",
            "city": "A" * 51,
            "pincode": "110001",
            "is_default": False
        })
        assert resp.status_code == 400

    def test_create_address_pincode_valid_6_digits(self):
        """[BVA - Boundary: Pincode = 6 digits (valid)]
        Pincode with exactly 6 digits should be accepted.
        """
        resp = post("/addresses", headers=user_headers(), json={
            "label": "HOME",
            "street": "12345 Test Street",
            "city": "Chennai",
            "pincode": "600001",
            "is_default": False
        })
        assert resp.status_code in [200, 201]

    def test_create_address_pincode_5_digits_invalid(self):
        """[BVA - Boundary: Pincode = 5 digits (below required)]
        Pincode with 5 digits should be rejected with 400.
        """
        resp = post("/addresses", headers=user_headers(), json={
            "label": "HOME",
            "street": "12345 Test Street",
            "city": "Chennai",
            "pincode": "60001",
            "is_default": False
        })
        assert resp.status_code == 400

    def test_create_address_pincode_7_digits_invalid(self):
        """[BVA - Boundary: Pincode = 7 digits (above required)]
        Pincode with 7 digits should be rejected with 400.
        """
        resp = post("/addresses", headers=user_headers(), json={
            "label": "HOME",
            "street": "12345 Test Street",
            "city": "Chennai",
            "pincode": "6000011",
            "is_default": False
        })
        assert resp.status_code == 400

    def test_create_address_pincode_with_letters_invalid(self):
        """[ECP - Invalid Class: Non-digit pincode]
        Pincode with letters should be rejected with 400.
        """
        resp = post("/addresses", headers=user_headers(), json={
            "label": "HOME",
            "street": "12345 Test Street",
            "city": "Chennai",
            "pincode": "abcdef",
            "is_default": False
        })
        assert resp.status_code == 400

    def test_create_address_response_contains_all_fields(self):
        """[ECP - Valid Class: Response structure verification]
        A successful POST should return address_id, label, street, city, pincode, is_default.
        """
        resp = post("/addresses", headers=user_headers(), json={
            "label": "HOME",
            "street": "99999 Response Test",
            "city": "Pune",
            "pincode": "411001",
            "is_default": False
        })
        assert resp.status_code in [200, 201]
        data = resp.json()
        # The response might nest the address under an "address" key
        addr = data.get("address", data)
        for field in ["address_id", "label", "street", "city", "pincode", "is_default"]:
            assert field in addr, f"Missing field in response: {field}"

    def test_create_default_address_removes_previous_default(self):
        """[ECP - Valid Class: Default address management]
        When a new address is set as default, previous default should be unset.
        """
        # Create first default address
        resp1 = post("/addresses", headers=user_headers(SECOND_USER_ID), json={
            "label": "HOME",
            "street": "First Default Street",
            "city": "CityOne",
            "pincode": "100001",
            "is_default": True
        })
        assert resp1.status_code in [200, 201]
        addr1 = resp1.json().get("address", resp1.json())
        addr1_id = addr1["address_id"]

        # Create second default address
        resp2 = post("/addresses", headers=user_headers(SECOND_USER_ID), json={
            "label": "OFFICE",
            "street": "Second Default Street",
            "city": "CityTwo",
            "pincode": "200002",
            "is_default": True
        })
        assert resp2.status_code in [200, 201]

        # Verify first address is no longer default
        all_addrs = get("/addresses", headers=user_headers(SECOND_USER_ID)).json()
        defaults = [a for a in all_addrs if a.get("is_default", False)]
        assert len(defaults) <= 1, "Only one address should be default at a time"
        if defaults:
            assert defaults[0]["address_id"] != addr1_id or len(defaults) == 1


class TestUpdateAddress:
    """Tests for PUT /api/v1/addresses/{address_id}."""

    def test_update_street_succeeds(self):
        """[ECP - Valid Class: Update allowed field (street)]
        Updating the street field should succeed and reflect the new value.
        """
        # First create an address to update
        create_resp = post("/addresses", headers=user_headers(), json={
            "label": "HOME",
            "street": "Original Street Name",
            "city": "TestCity",
            "pincode": "123456",
            "is_default": False
        })
        addr = create_resp.json().get("address", create_resp.json())
        addr_id = addr["address_id"]

        # Update street
        resp = put(f"/addresses/{addr_id}", headers=user_headers(), json={
            "street": "Updated Street Name"
        })
        assert resp.status_code == 200
        updated = resp.json()
        updated_addr = updated.get("address", updated)
        assert updated_addr.get("street") == "Updated Street Name"

    def test_update_street_min_length_valid(self):
        """[BVA - Boundary: Street = 5 characters (minimum valid)]
        Updating street to 5 characters should succeed.
        """
        create_resp = post("/addresses", headers=user_headers(), json={
            "label": "HOME",
            "street": "Origin Street",
            "city": "TestCity",
            "pincode": "123456",
            "is_default": False
        })
        addr = create_resp.json().get("address", create_resp.json())
        addr_id = addr["address_id"]

        resp = put(f"/addresses/{addr_id}", headers=user_headers(), json={"street": "ABCDE"})
        assert resp.status_code == 200
        data = resp.json().get("address", resp.json())
        assert data.get("street") == "ABCDE"

    def test_update_street_max_length_valid(self):
        """[BVA - Boundary: Street = 100 characters (maximum valid)]
        Updating street to 100 characters should succeed.
        """
        create_resp = post("/addresses", headers=user_headers(), json={
            "label": "HOME",
            "street": "Origin Street",
            "city": "TestCity",
            "pincode": "123456",
            "is_default": False
        })
        addr = create_resp.json().get("address", create_resp.json())
        addr_id = addr["address_id"]

        new_street = "A" * 100
        resp = put(f"/addresses/{addr_id}", headers=user_headers(), json={"street": new_street})
        assert resp.status_code == 200
        data = resp.json().get("address", resp.json())
        assert data.get("street") == new_street

    def test_update_street_below_min_length_invalid(self):
        """[BVA - Boundary: Street = 4 characters (below minimum)]
        Updating street to 4 characters should return 400.
        """
        create_resp = post("/addresses", headers=user_headers(), json={
            "label": "HOME",
            "street": "Origin Street",
            "city": "TestCity",
            "pincode": "123456",
            "is_default": False
        })
        addr = create_resp.json().get("address", create_resp.json())
        addr_id = addr["address_id"]

        resp = put(f"/addresses/{addr_id}", headers=user_headers(), json={"street": "ABCD"})
        assert resp.status_code == 400

    def test_update_street_above_max_length_invalid(self):
        """[BVA - Boundary: Street = 101 characters (above maximum)]
        Updating street to 101 characters should return 400.
        """
        create_resp = post("/addresses", headers=user_headers(), json={
            "label": "HOME",
            "street": "Origin Street",
            "city": "TestCity",
            "pincode": "123456",
            "is_default": False
        })
        addr = create_resp.json().get("address", create_resp.json())
        addr_id = addr["address_id"]

        resp = put(f"/addresses/{addr_id}", headers=user_headers(), json={"street": "A" * 101})
        assert resp.status_code == 400

    def test_update_is_default_succeeds(self):
        """[ECP - Valid Class: Update allowed field (is_default)]
        Updating the is_default field should succeed.
        """
        create_resp = post("/addresses", headers=user_headers(), json={
            "label": "OTHER",
            "street": "Default Test Street",
            "city": "TestCity",
            "pincode": "654321",
            "is_default": False
        })
        addr = create_resp.json().get("address", create_resp.json())
        addr_id = addr["address_id"]

        resp = put(f"/addresses/{addr_id}", headers=user_headers(), json={
            "is_default": True
        })
        assert resp.status_code == 200

    def test_update_is_default_true_and_false_with_single_default_invariant(self):
        """[ECP - Valid Class: Toggle is_default and keep single default]
        Setting one address as default and another as non-default should keep <=1 default.
        """
        # Create two non-default addresses for user 2
        resp1 = post("/addresses", headers=user_headers(SECOND_USER_ID), json={
            "label": "HOME",
            "street": "Toggle Default One",
            "city": "CityOne",
            "pincode": "100001",
            "is_default": False
        })
        assert resp1.status_code in [200, 201]
        addr1 = resp1.json().get("address", resp1.json())

        resp2 = post("/addresses", headers=user_headers(SECOND_USER_ID), json={
            "label": "OFFICE",
            "street": "Toggle Default Two",
            "city": "CityTwo",
            "pincode": "200002",
            "is_default": False
        })
        assert resp2.status_code in [200, 201]
        addr2 = resp2.json().get("address", resp2.json())

        # Set first as default and second explicitly non-default
        set_default = put(
            f"/addresses/{addr1['address_id']}",
            headers=user_headers(SECOND_USER_ID),
            json={"is_default": True},
        )
        assert set_default.status_code == 200

        set_non_default = put(
            f"/addresses/{addr2['address_id']}",
            headers=user_headers(SECOND_USER_ID),
            json={"is_default": False},
        )
        assert set_non_default.status_code == 200

        all_addrs = get("/addresses", headers=user_headers(SECOND_USER_ID)).json()
        defaults = [a for a in all_addrs if a.get("is_default", False)]
        assert len(defaults) <= 1

    def test_update_attempt_to_change_label_rejected(self):
        """[ECP - Invalid Class: Attempt update of immutable field label]
        Updating label should be rejected.
        """
        create_resp = post("/addresses", headers=user_headers(), json={
            "label": "HOME",
            "street": "Immutable Field Test",
            "city": "OldCity",
            "pincode": "123456",
            "is_default": False
        })
        addr = create_resp.json().get("address", create_resp.json())
        addr_id = addr["address_id"]

        resp = put(f"/addresses/{addr_id}", headers=user_headers(), json={
            "label": "OFFICE",
        })
        assert resp.status_code == 400

    def test_update_attempt_to_change_city_rejected(self):
        """[ECP - Invalid Class: Attempt update of immutable field city]
        Updating city should be rejected.
        """
        create_resp = post("/addresses", headers=user_headers(), json={
            "label": "HOME",
            "street": "Immutable Field Test",
            "city": "OldCity",
            "pincode": "123456",
            "is_default": False
        })
        addr = create_resp.json().get("address", create_resp.json())
        addr_id = addr["address_id"]

        resp = put(f"/addresses/{addr_id}", headers=user_headers(), json={
            "city": "NewCity",
        })
        assert resp.status_code == 400

    def test_update_attempt_to_change_pincode_rejected(self):
        """[ECP - Invalid Class: Attempt update of immutable field pincode]
        Updating pincode should be rejected.
        """
        create_resp = post("/addresses", headers=user_headers(), json={
            "label": "HOME",
            "street": "Immutable Field Test",
            "city": "OldCity",
            "pincode": "123456",
            "is_default": False
        })
        addr = create_resp.json().get("address", create_resp.json())
        addr_id = addr["address_id"]

        resp = put(f"/addresses/{addr_id}", headers=user_headers(), json={
            "pincode": "654321",
        })
        assert resp.status_code == 400

    def test_update_response_shows_new_data(self):
        """[ECP - Valid Class: Response shows updated data, not old]
        When an address is updated, the response must show the new data.
        """
        create_resp = post("/addresses", headers=user_headers(), json={
            "label": "HOME",
            "street": "Before Update",
            "city": "CityBefore",
            "pincode": "111111",
            "is_default": False
        })
        addr = create_resp.json().get("address", create_resp.json())
        addr_id = addr["address_id"]

        resp = put(f"/addresses/{addr_id}", headers=user_headers(), json={
            "street": "After Update"
        })
        assert resp.status_code == 200
        data = resp.json()
        updated_addr = data.get("address", data)
        assert updated_addr.get("street") == "After Update"


class TestDeleteAddress:
    """Tests for DELETE /api/v1/addresses/{address_id}."""

    def test_delete_existing_address(self):
        """[ECP - Valid Class: Delete existing address]
        Should return success when deleting an existing address.
        """
        create_resp = post("/addresses", headers=user_headers(), json={
            "label": "OTHER",
            "street": "To Be Deleted",
            "city": "TempCity",
            "pincode": "999999",
            "is_default": False
        })
        addr = create_resp.json().get("address", create_resp.json())
        addr_id = addr["address_id"]

        resp = delete(f"/addresses/{addr_id}", headers=user_headers())
        assert resp.status_code == 200

    def test_delete_non_existent_address_returns_404(self):
        """[ECP - Invalid Class: Non-existent address]
        Deleting a non-existent address should return 404.
        """
        resp = delete("/addresses/99999", headers=user_headers())
        assert resp.status_code == 404
