"""
Test: Support Ticket Endpoints
Tests POST /api/v1/support/ticket, GET /api/v1/support/tickets,
PUT /api/v1/support/tickets/{ticket_id}.
Techniques: Equivalence Class Partitioning (ECP), Boundary Value Analysis (BVA)
"""

import pytest
from .conftest import get, post, put, user_headers

# Use dedicated users for support tests
SUPPORT_USER = 60
SUPPORT_USER_STATUS = 61


class TestCreateTicket:
    """Tests for POST /api/v1/support/ticket."""

    def test_create_valid_ticket(self):
        """[ECP - Valid Class: Valid subject and message]
        Subject 5-100 chars, message 1-500 chars should succeed.
        """
        resp = post("/support/ticket", headers=user_headers(SUPPORT_USER), json={
            "subject": "Cannot checkout my order",
            "message": "I am unable to proceed to checkout. Please help."
        })
        assert resp.status_code in [200, 201]
        data = resp.json()
        ticket = data.get("ticket", data)
        assert ticket.get("status") == "OPEN", "New ticket should start with status OPEN"

    def test_create_ticket_starts_as_open(self):
        """[ECP - Valid Class: New ticket status = OPEN]
        Every new ticket must start with status OPEN.
        """
        resp = post("/support/ticket", headers=user_headers(SUPPORT_USER), json={
            "subject": "Status check test",
            "message": "Testing that new tickets start as OPEN."
        })
        assert resp.status_code in [200, 201]
        data = resp.json()
        ticket = data.get("ticket", data)
        assert ticket.get("status") == "OPEN"

    def test_message_saved_exactly(self):
        """[ECP - Valid Class: Message preserved exactly]
        The full message must be saved exactly as written.
        """
        msg = "This is  a test    message with   extra   spaces! @#$% 123"
        resp = post("/support/ticket", headers=user_headers(SUPPORT_USER), json={
            "subject": "Message preservation test",
            "message": msg
        })
        assert resp.status_code in [200, 201]
        data = resp.json()
        ticket = data.get("ticket", data)
        assert ticket.get("message") == msg

    def test_subject_below_min_length_rejected(self):
        """[BVA - Boundary: Subject = 4 characters (below minimum)]
        Subject must be 5-100 chars. 4 chars should be rejected.
        """
        resp = post("/support/ticket", headers=user_headers(SUPPORT_USER), json={
            "subject": "Abcd",
            "message": "Valid message here."
        })
        assert resp.status_code == 400

    def test_subject_min_length_valid(self):
        """[BVA - Boundary: Subject = 5 characters (minimum valid)]
        Subject with exactly 5 characters should be accepted.
        """
        resp = post("/support/ticket", headers=user_headers(SUPPORT_USER), json={
            "subject": "Abcde",
            "message": "Valid message here."
        })
        assert resp.status_code in [200, 201]

    def test_subject_max_length_valid(self):
        """[BVA - Boundary: Subject = 100 characters (maximum valid)]
        Subject with exactly 100 characters should be accepted.
        """
        resp = post("/support/ticket", headers=user_headers(SUPPORT_USER), json={
            "subject": "A" * 100,
            "message": "Valid message."
        })
        assert resp.status_code in [200, 201]

    def test_subject_above_max_length_rejected(self):
        """[BVA - Boundary: Subject = 101 characters (above maximum)]
        Subject with 101 characters should be rejected.
        """
        resp = post("/support/ticket", headers=user_headers(SUPPORT_USER), json={
            "subject": "A" * 101,
            "message": "Valid message."
        })
        assert resp.status_code == 400

    def test_message_empty_rejected(self):
        """[BVA - Boundary: Message = 0 characters (empty)]
        Message must be 1-500 chars. Empty should be rejected.
        """
        resp = post("/support/ticket", headers=user_headers(SUPPORT_USER), json={
            "subject": "Empty message test",
            "message": ""
        })
        assert resp.status_code == 400

    def test_message_one_char_valid(self):
        """[BVA - Boundary: Message = 1 character (minimum valid)]
        Minimum valid message length.
        """
        resp = post("/support/ticket", headers=user_headers(SUPPORT_USER), json={
            "subject": "One char message",
            "message": "X"
        })
        assert resp.status_code in [200, 201]

    def test_message_500_chars_valid(self):
        """[BVA - Boundary: Message = 500 characters (maximum valid)]
        Maximum valid message length.
        """
        resp = post("/support/ticket", headers=user_headers(SUPPORT_USER), json={
            "subject": "Max message test",
            "message": "M" * 500
        })
        assert resp.status_code in [200, 201]

    def test_message_501_chars_rejected(self):
        """[BVA - Boundary: Message = 501 characters (above maximum)]
        Message exceeding 500 chars should be rejected.
        """
        resp = post("/support/ticket", headers=user_headers(SUPPORT_USER), json={
            "subject": "Over max message",
            "message": "M" * 501
        })
        assert resp.status_code == 400

    def test_create_ticket_missing_subject(self):
        """[ECP - Invalid Class: Missing subject]
        Missing subject should return 400.
        """
        resp = post("/support/ticket", headers=user_headers(SUPPORT_USER), json={
            "message": "Message present, subject missing"
        })
        assert resp.status_code == 400

    def test_create_ticket_missing_message(self):
        """[ECP - Invalid Class: Missing message]
        Missing message should return 400.
        """
        resp = post("/support/ticket", headers=user_headers(SUPPORT_USER), json={
            "subject": "Subject present"
        })
        assert resp.status_code == 400

    def test_create_ticket_missing_subject_and_message(self):
        """[ECP - Invalid Class: Missing subject and message]
        Empty payload should return 400.
        """
        resp = post("/support/ticket", headers=user_headers(SUPPORT_USER), json={})
        assert resp.status_code == 400


class TestGetTickets:
    """Tests for GET /api/v1/support/tickets."""

    def test_get_tickets_returns_list(self):
        """[ECP - Valid Class: Retrieve user's tickets]
        Should return 200 with a list of tickets.
        """
        resp = get("/support/tickets", headers=user_headers(SUPPORT_USER))
        assert resp.status_code == 200


class TestUpdateTicketStatus:
    """Tests for PUT /api/v1/support/tickets/{ticket_id}."""

    def _create_ticket(self, user_id):
        """Helper to create a ticket and return its ID."""
        resp = post("/support/ticket", headers=user_headers(user_id), json={
            "subject": "Status transition test",
            "message": "Testing status transitions."
        })
        data = resp.json()
        ticket = data.get("ticket", data)
        return ticket.get("ticket_id")

    def test_open_to_in_progress(self):
        """[ECP - Valid Class: OPEN → IN_PROGRESS (valid transition)]
        Status can move from OPEN to IN_PROGRESS.
        """
        ticket_id = self._create_ticket(SUPPORT_USER_STATUS)
        if ticket_id:
            resp = put(f"/support/tickets/{ticket_id}", headers=user_headers(SUPPORT_USER_STATUS), json={
                "status": "IN_PROGRESS"
            })
            assert resp.status_code == 200

    def test_in_progress_to_closed(self):
        """[ECP - Valid Class: IN_PROGRESS → CLOSED (valid transition)]
        Status can move from IN_PROGRESS to CLOSED.
        """
        ticket_id = self._create_ticket(SUPPORT_USER_STATUS)
        if ticket_id:
            # First transition to IN_PROGRESS
            put(f"/support/tickets/{ticket_id}", headers=user_headers(SUPPORT_USER_STATUS), json={
                "status": "IN_PROGRESS"
            })
            # Then to CLOSED
            resp = put(f"/support/tickets/{ticket_id}", headers=user_headers(SUPPORT_USER_STATUS), json={
                "status": "CLOSED"
            })
            assert resp.status_code == 200

    def test_update_status_with_extra_fields_rejected_open_to_in_progress(self):
        """[ECP - Invalid Class: Status update must not include other field changes]
        OPEN -> IN_PROGRESS request with extra fields should be rejected.
        """
        ticket_id = self._create_ticket(SUPPORT_USER_STATUS)
        if ticket_id:
            resp = put(
                f"/support/tickets/{ticket_id}",
                headers=user_headers(SUPPORT_USER_STATUS),
                json={
                    "status": "IN_PROGRESS",
                    "subject": "Illegal subject change",
                },
            )
            assert resp.status_code == 400

    def test_update_status_with_extra_fields_rejected_in_progress_to_closed(self):
        """[ECP - Invalid Class: Status-only update enforcement]
        IN_PROGRESS -> CLOSED request with extra fields should be rejected.
        """
        ticket_id = self._create_ticket(SUPPORT_USER_STATUS)
        if ticket_id:
            first = put(
                f"/support/tickets/{ticket_id}",
                headers=user_headers(SUPPORT_USER_STATUS),
                json={"status": "IN_PROGRESS"},
            )
            assert first.status_code == 200

            resp = put(
                f"/support/tickets/{ticket_id}",
                headers=user_headers(SUPPORT_USER_STATUS),
                json={
                    "status": "CLOSED",
                    "message": "Illegal message change",
                },
            )
            assert resp.status_code == 400

    def test_open_to_closed_rejected(self):
        """[ECP - Invalid Class: OPEN → CLOSED (invalid transition)]
        Status cannot skip from OPEN directly to CLOSED.
        """
        ticket_id = self._create_ticket(SUPPORT_USER_STATUS)
        if ticket_id:
            resp = put(f"/support/tickets/{ticket_id}", headers=user_headers(SUPPORT_USER_STATUS), json={
                "status": "CLOSED"
            })
            assert resp.status_code == 400

    def test_closed_to_open_rejected(self):
        """[ECP - Invalid Class: CLOSED → OPEN (reverse transition)]
        Status cannot go backwards.
        """
        ticket_id = self._create_ticket(SUPPORT_USER_STATUS)
        if ticket_id:
            put(f"/support/tickets/{ticket_id}", headers=user_headers(SUPPORT_USER_STATUS), json={
                "status": "IN_PROGRESS"
            })
            put(f"/support/tickets/{ticket_id}", headers=user_headers(SUPPORT_USER_STATUS), json={
                "status": "CLOSED"
            })
            resp = put(f"/support/tickets/{ticket_id}", headers=user_headers(SUPPORT_USER_STATUS), json={
                "status": "OPEN"
            })
            assert resp.status_code == 400

    def test_in_progress_to_open_rejected(self):
        """[ECP - Invalid Class: IN_PROGRESS → OPEN (reverse transition)]
        Cannot go backwards.
        """
        ticket_id = self._create_ticket(SUPPORT_USER_STATUS)
        if ticket_id:
            put(f"/support/tickets/{ticket_id}", headers=user_headers(SUPPORT_USER_STATUS), json={
                "status": "IN_PROGRESS"
            })
            resp = put(f"/support/tickets/{ticket_id}", headers=user_headers(SUPPORT_USER_STATUS), json={
                "status": "OPEN"
            })
            assert resp.status_code == 400

    def test_invalid_status_value(self):
        """[ECP - Invalid Class: Invalid status string]
        A status value not in {OPEN, IN_PROGRESS, CLOSED} should be rejected.
        """
        ticket_id = self._create_ticket(SUPPORT_USER_STATUS)
        if ticket_id:
            resp = put(f"/support/tickets/{ticket_id}", headers=user_headers(SUPPORT_USER_STATUS), json={
                "status": "RESOLVED"
            })
            assert resp.status_code == 400
