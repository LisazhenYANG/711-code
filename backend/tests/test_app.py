import unittest
import os
from pathlib import Path
import tempfile

from fastapi.testclient import TestClient

_tmpdir = tempfile.TemporaryDirectory()
os.environ["MANYOU_DB_PATH"] = str(Path(_tmpdir.name) / "test.sqlite3")
from backend.main import app


client = TestClient(app)


class ManyouBackendTest(unittest.TestCase):
    def test_health_reports_backend_status(self):
        response = client.get("/api/health")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])
        self.assertEqual(response.json()["service"], "manyou-backend")

    def test_catalog_returns_frontend_seed_data(self):
        response = client.get("/api/catalog")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertGreaterEqual(len(payload["spots"]), 3)
        self.assertIn("静下来", payload["venue_categories"])
        self.assertEqual(len(payload["meal_slots"]), 3)

    def test_generate_routes_uses_requested_moods_and_discover_items(self):
        response = client.post(
            "/api/routes/generate",
            json={
                "location": {"city": "上海", "area": "静安区"},
                "time_slot": "下午",
                "people": "2人",
                "moods": ["静下来"],
                "discover_items": ["窗边咖啡", "图书馆"],
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload["routes"]), 3)
        self.assertTrue(payload["routes"][0]["name"])
        self.assertGreaterEqual(len(payload["routes"][0]["stops"]), 3)
        self.assertTrue(payload["routes"][0]["stops"][0]["time"])

    def test_checkout_creates_booking_results_and_packing_list(self):
        response = client.post(
            "/api/bookings/checkout",
            json={
                "trip_id": "trip-test",
                "items": [
                    {
                        "name": "UCCA · 当代艺术",
                        "category": "展览",
                        "booking_type": "门票",
                        "time": "14:30",
                        "selected_product": {"name": "常设展通票", "price": "¥60/人"},
                        "paid": True,
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["results"][0]["status"], "purchased")
        self.assertTrue(payload["results"][0]["code"].startswith("QR-"))
        self.assertIn("预约二维码/购票凭证", payload["packing_list"])

    def test_trip_archive_round_trip(self):
        create_response = client.post(
            "/api/trips",
            json={
                "title": "静安慢悠悠之旅",
                "city": "上海",
                "route": [{"name": "静雅书局", "category": "书店", "time": "14:00"}],
            },
        )
        self.assertEqual(create_response.status_code, 201)
        trip_id = create_response.json()["id"]

        get_response = client.get(f"/api/trips/{trip_id}")

        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.json()["title"], "静安慢悠悠之旅")

    def test_route_action_preserves_paid_bookings_and_heart_choice(self):
        checkout = client.post(
            "/api/bookings/checkout",
            json={
                "items": [
                    {
                        "name": "UCCA · 当代艺术",
                        "category": "展览",
                        "bookingType": "门票",
                        "time": "15:00",
                        "selectedProduct": {"name": "普通票", "price": "¥60"},
                    }
                ]
            },
        )
        self.assertEqual(checkout.status_code, 200)
        self.assertTrue(checkout.json()["results"][0]["qr"])

        heart = client.post(
            "/api/route/action",
            json={
                "action": "heart",
                "value": "change",
                "route": [],
                "lockedIndexes": [0],
                "hiddenIndexes": [],
            },
        )
        self.assertEqual(heart.status_code, 200)
        self.assertEqual(heart.json()["last_action"]["choice"], "change")
        self.assertTrue(heart.json()["bookings"][0]["qr"])

    def test_add_meal_uses_selected_slot_and_restaurant(self):
        response = client.post(
            "/api/route/action",
            json={
                "action": "add_meal",
                "value": "dinner|鸟啸炭火烧",
                "route": [],
                "lockedIndexes": [0],
                "hiddenIndexes": [],
            },
        )
        self.assertEqual(response.status_code, 200)
        route = response.json()["route"]
        self.assertEqual(route[-1]["name"], "鸟啸炭火烧")
        self.assertEqual(route[-1]["time"], "18:30")

    def test_add_place_uses_custom_place_name(self):
        response = client.post(
            "/api/route/action",
            json={
                "action": "add_place",
                "value": "武康路",
                "route": [],
                "lockedIndexes": [0],
                "hiddenIndexes": [],
            },
        )
        self.assertEqual(response.status_code, 200)
        route = response.json()["route"]
        self.assertEqual(route[-1]["name"], "武康路")
        self.assertEqual(route[-1]["category"], "自定义地点")


if __name__ == "__main__":
    unittest.main()
