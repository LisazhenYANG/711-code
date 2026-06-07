import unittest
import os
from pathlib import Path
import tempfile

from fastapi.testclient import TestClient

_tmpdir = tempfile.TemporaryDirectory()
os.environ["MANYOU_DB_PATH"] = str(Path(_tmpdir.name) / "test.sqlite3")
from backend.main import app


client = TestClient(app)


class AiCompatApiTest(unittest.TestCase):
    def test_ai_inventory_endpoints_match_711_ai_shape(self):
        pois = client.get("/pois")
        restaurants = client.get("/restaurants")

        self.assertEqual(pois.status_code, 200)
        self.assertEqual(restaurants.status_code, 200)
        self.assertGreater(len(pois.json()), 0)
        self.assertGreater(len(restaurants.json()), 0)
        self.assertIn("id", restaurants.json()[0])

    def test_ai_plan_endpoint_returns_711_ai_summary_fields(self):
        before = client.get("/api/dashboard").json()["active_plan"]["route"]
        response = client.post(
            "/plan",
            json={
                "user_id": "alice",
                "intent": {
                    "origin_lat": 31.228,
                    "origin_lng": 121.449,
                    "time_slot": "下午",
                    "people_count": 2,
                    "transport_mode": "transit",
                    "moods": ["静下来"],
                    "sub_categories": ["窗边咖啡", "图书馆"],
                    "free_text": "想找个安静的下午",
                },
                "weather": {"condition": "晴"},
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("top_routes", payload)
        self.assertIn("debate_transcript", payload)
        self.assertIn("candidate_routes_count", payload)
        self.assertGreater(len(payload["top_routes"]), 0)
        after = client.get("/api/dashboard").json()["active_plan"]["route"]
        self.assertEqual(after, before)

    def test_ai_queue_ticket_lifecycle(self):
        restaurants = client.get("/restaurants").json()
        restaurant_id = restaurants[0]["id"]

        queue = client.get(f"/restaurants/{restaurant_id}/queue")
        self.assertEqual(queue.status_code, 200)
        self.assertIn("estimated_wait_minutes", queue.json())

        ticket = client.post(
            "/booking/queue",
            json={"restaurant_id": restaurant_id, "user_id": "alice", "people_count": 2},
        )
        self.assertEqual(ticket.status_code, 200)
        ticket_no = ticket.json()["ticket_no"]

        fetched = client.get(f"/booking/queue/{ticket_no}")
        self.assertEqual(fetched.status_code, 200)
        self.assertEqual(fetched.json()["ticket_no"], ticket_no)

        seated = client.post(f"/booking/queue/{ticket_no}/seat")
        self.assertEqual(seated.status_code, 200)
        self.assertEqual(seated.json()["status"], "seated")

    def test_ai_reservation_and_user_bookings(self):
        restaurants = client.get("/restaurants").json()
        restaurant_id = next(r["id"] for r in restaurants if r.get("supports_table_booking"))

        reservation = client.post(
            "/booking/reservation",
            json={
                "restaurant_id": restaurant_id,
                "user_id": "bob",
                "people_count": 2,
                "reserve_for_time": "2026-06-06T18:30:00",
                "special_requests": "靠窗",
            },
        )
        self.assertEqual(reservation.status_code, 200)
        reservation_id = reservation.json()["reservation_id"]

        fetched = client.get(f"/booking/reservation/{reservation_id}")
        self.assertEqual(fetched.status_code, 200)
        self.assertEqual(fetched.json()["reservation_id"], reservation_id)

        bookings = client.get("/bookings/user/bob")
        self.assertEqual(bookings.status_code, 200)
        self.assertIn("reservations", bookings.json())

    def test_ai_feedback_endpoint(self):
        response = client.post(
            "/feedback",
            json={"user_id": "alice", "user_rating": 5, "top_routes": [], "debate_transcript": []},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])
        self.assertIn("updated_profile", response.json())


if __name__ == "__main__":
    unittest.main()
