"""
Test: Review Endpoints
Tests GET /api/v1/products/{product_id}/reviews and
POST /api/v1/products/{product_id}/reviews.
Techniques: Equivalence Class Partitioning (ECP), Boundary Value Analysis (BVA)
"""

import pytest
from .conftest import get, post, user_headers

# Use dedicated users for review tests
REVIEW_USER = 50
REVIEW_PRODUCT = 4  # Orange - Nagpur


class TestGetReviews:
    """Tests for GET /api/v1/products/{product_id}/reviews."""

    def test_get_reviews_for_product(self):
        """[ECP - Valid Class: Retrieve reviews for a product]
        Should return 200 with review data.
        """
        resp = get(f"/products/{REVIEW_PRODUCT}/reviews", headers=user_headers(REVIEW_USER))
        assert resp.status_code == 200

    def test_get_reviews_non_existent_product(self):
        """[ECP - Invalid Class: Reviews for non-existent product]
        Should return 404.
        """
        resp = get("/products/99999/reviews", headers=user_headers(REVIEW_USER))
        assert resp.status_code == 404


class TestAddReview:
    """Tests for POST /api/v1/products/{product_id}/reviews."""

    def test_add_valid_review(self):
        """[ECP - Valid Class: Valid rating and comment]
        Rating between 1-5 and comment 1-200 chars should succeed.
        """
        resp = post(f"/products/{REVIEW_PRODUCT}/reviews", headers=user_headers(REVIEW_USER), json={
            "rating": 4,
            "comment": "Great product, fresh and tasty!"
        })
        assert resp.status_code in [200, 201]

    def test_rating_two_valid(self):
        """[BVA - Boundary: Rating = 2]
        Rating of 2 should be accepted.
        """
        resp = post(f"/products/{REVIEW_PRODUCT}/reviews", headers=user_headers(REVIEW_USER), json={
            "rating": 2,
            "comment": "Below average"
        })
        assert resp.status_code in [200, 201]

    def test_rating_three_valid(self):
        """[BVA - Boundary: Rating = 3]
        Rating of 3 should be accepted.
        """
        resp = post(f"/products/{REVIEW_PRODUCT}/reviews", headers=user_headers(REVIEW_USER), json={
            "rating": 3,
            "comment": "Average"
        })
        assert resp.status_code in [200, 201]

    def test_rating_four_valid(self):
        """[BVA - Boundary: Rating = 4]
        Rating of 4 should be accepted.
        """
        resp = post(f"/products/{REVIEW_PRODUCT}/reviews", headers=user_headers(REVIEW_USER), json={
            "rating": 4,
            "comment": "Good"
        })
        assert resp.status_code in [200, 201]

    def test_rating_zero_rejected(self):
        """[BVA - Boundary: Rating = 0 (below minimum)]
        Rating must be between 1 and 5. Zero should be rejected.
        """
        resp = post(f"/products/{REVIEW_PRODUCT}/reviews", headers=user_headers(REVIEW_USER), json={
            "rating": 0,
            "comment": "Test comment"
        })
        assert resp.status_code == 400

    def test_rating_one_valid(self):
        """[BVA - Boundary: Rating = 1 (minimum valid)]
        Rating of 1 should be accepted.
        """
        resp = post(f"/products/{REVIEW_PRODUCT}/reviews", headers=user_headers(REVIEW_USER), json={
            "rating": 1,
            "comment": "Not great"
        })
        assert resp.status_code in [200, 201]

    def test_rating_five_valid(self):
        """[BVA - Boundary: Rating = 5 (maximum valid)]
        Rating of 5 should be accepted.
        """
        resp = post(f"/products/{REVIEW_PRODUCT}/reviews", headers=user_headers(REVIEW_USER), json={
            "rating": 5,
            "comment": "Excellent product!"
        })
        assert resp.status_code in [200, 201]

    def test_rating_six_rejected(self):
        """[BVA - Boundary: Rating = 6 (above maximum)]
        Rating above 5 should be rejected.
        """
        resp = post(f"/products/{REVIEW_PRODUCT}/reviews", headers=user_headers(REVIEW_USER), json={
            "rating": 6,
            "comment": "Too high rating"
        })
        assert resp.status_code == 400

    def test_rating_negative_rejected(self):
        """[BVA - Boundary: Rating = -1 (negative)]
        Negative rating should be rejected.
        """
        resp = post(f"/products/{REVIEW_PRODUCT}/reviews", headers=user_headers(REVIEW_USER), json={
            "rating": -1,
            "comment": "Negative test"
        })
        assert resp.status_code == 400

    def test_comment_empty_rejected(self):
        """[BVA - Boundary: Comment = 0 characters (empty)]
        Comment must be between 1 and 200 characters. Empty should be rejected.
        """
        resp = post(f"/products/{REVIEW_PRODUCT}/reviews", headers=user_headers(REVIEW_USER), json={
            "rating": 3,
            "comment": ""
        })
        assert resp.status_code == 400

    def test_comment_one_char_valid(self):
        """[BVA - Boundary: Comment = 1 character (minimum valid)]
        Minimum valid comment length.
        """
        resp = post(f"/products/{REVIEW_PRODUCT}/reviews", headers=user_headers(REVIEW_USER), json={
            "rating": 3,
            "comment": "X"
        })
        assert resp.status_code in [200, 201]

    def test_comment_200_chars_valid(self):
        """[BVA - Boundary: Comment = 200 characters (maximum valid)]
        Maximum valid comment length.
        """
        resp = post(f"/products/{REVIEW_PRODUCT}/reviews", headers=user_headers(REVIEW_USER), json={
            "rating": 3,
            "comment": "A" * 200
        })
        assert resp.status_code in [200, 201]

    def test_comment_201_chars_rejected(self):
        """[BVA - Boundary: Comment = 201 characters (above maximum)]
        Comment exceeding 200 chars should be rejected.
        """
        resp = post(f"/products/{REVIEW_PRODUCT}/reviews", headers=user_headers(REVIEW_USER), json={
            "rating": 3,
            "comment": "A" * 201
        })
        assert resp.status_code == 400

    def test_missing_rating(self):
        """[ECP - Invalid Class: Missing rating]
        Missing rating should return 400.
        """
        resp = post(f"/products/{REVIEW_PRODUCT}/reviews", headers=user_headers(REVIEW_USER), json={
            "comment": "Missing rating field"
        })
        assert resp.status_code == 400

    def test_missing_comment(self):
        """[ECP - Invalid Class: Missing comment]
        Missing comment should return 400.
        """
        resp = post(f"/products/{REVIEW_PRODUCT}/reviews", headers=user_headers(REVIEW_USER), json={
            "rating": 4
        })
        assert resp.status_code == 400

    def test_missing_rating_and_comment(self):
        """[ECP - Invalid Class: Missing rating and comment]
        Empty body should return 400.
        """
        resp = post(f"/products/{REVIEW_PRODUCT}/reviews", headers=user_headers(REVIEW_USER), json={})
        assert resp.status_code == 400


class TestAverageRating:
    """Tests for average rating calculation."""

    def test_average_rating_is_decimal(self):
        """[ECP - Valid Class: Average rating is decimal, not rounded-down integer]
        The average should be a proper decimal.
        """
        # Add some reviews with different ratings
        post(f"/products/6/reviews", headers=user_headers(51), json={"rating": 4, "comment": "Good"})
        post(f"/products/6/reviews", headers=user_headers(52), json={"rating": 3, "comment": "OK"})

        resp = get(f"/products/6/reviews", headers=user_headers(REVIEW_USER))
        data = resp.json()
        avg = data.get("average_rating", data.get("avg_rating", None))
        if avg is not None and avg != 0:
            # Avg of 4 and 3 = 3.5 — should not be 3 (rounded down)
            assert isinstance(avg, float) or avg != int(avg), \
                f"Average rating {avg} appears to be rounded down to integer"

    def test_average_rating_matches_reviews_data(self):
        """[ECP - Valid Class: Average rating consistency]
        Reported average should match arithmetic mean of returned review ratings.
        """
        resp = get(f"/products/{REVIEW_PRODUCT}/reviews", headers=user_headers(REVIEW_USER))
        assert resp.status_code == 200
        data = resp.json()

        reviews = data.get("reviews", data if isinstance(data, list) else [])
        if not isinstance(reviews, list) or len(reviews) == 0:
            pytest.skip("No review list available to validate average")

        ratings = [r.get("rating") for r in reviews if isinstance(r, dict) and isinstance(r.get("rating"), (int, float))]
        if len(ratings) == 0:
            pytest.skip("No numeric rating values found in response")

        calculated_avg = sum(ratings) / len(ratings)
        reported_avg = data.get("average_rating", data.get("avg_rating", None))
        if reported_avg is None:
            pytest.skip("API response does not expose average rating field")

        assert reported_avg == pytest.approx(calculated_avg, abs=0.01)
