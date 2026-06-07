import os
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.pop("DEEPSEEK_API_KEY", None)
os.environ.pop("AMAP_API_KEY", None)

from agents.chat import chat_reply, classify_chat_intent  # noqa: E402


def _sample_route():
    return [
        {
            "poi_id": "p001",
            "poi_name": "外滩观景步道",
            "lat": 31.2400,
            "lng": 121.4900,
            "category_sub": "网红地标",
            "stay_minutes": 60,
            "transit_to_next_minutes": 12,
            "transit_to_next_mode": "walk",
            "locked": False,
        },
        {
            "poi_id": "p003",
            "poi_name": "静雅书局",
            "lat": 31.2282,
            "lng": 121.4489,
            "category_sub": "图书馆",
            "stay_minutes": 60,
            "transit_to_next_minutes": 10,
            "transit_to_next_mode": "walk",
            "locked": False,
        },
        {
            "poi_id": "p004",
            "poi_name": "街角旧梦咖啡",
            "lat": 31.2290,
            "lng": 121.4500,
            "category_sub": "窗边咖啡",
            "stay_minutes": 50,
            "transit_to_next_minutes": 0,
            "transit_to_next_mode": "walk",
            "locked": False,
        },
    ]


class ChatAgentTest(unittest.TestCase):
    def test_classify_five_supported_intents(self):
        cases = {
            "推荐一个适合休息的咖啡店": "recommend_place",
            "把第2站换成室内的地方": "replace_stop",
            "加一个甜品店": "add_stop",
            "这条路线太赶了，帮我重新排一下顺序": "adjust_route",
            "今天下雨，帮我改成室内路线": "weather_adapt",
        }
        for message, expected in cases.items():
            self.assertEqual(classify_chat_intent(message), expected)

    def test_recommend_place_returns_candidates(self):
        result = chat_reply(
            user_id="tester",
            message="推荐一个适合休息的咖啡店",
            current_route=_sample_route(),
            weather={"condition": "晴"},
        )

        self.assertEqual(result["intent"], "recommend_place")
        self.assertGreater(len(result["recommendations"]), 0)
        self.assertIn("recommendations", result["actions"])

    def test_replace_stop_updates_route(self):
        route = _sample_route()
        result = chat_reply(
            user_id="tester",
            message="把第2站换成咖啡馆",
            current_route=route,
            weather={"condition": "晴"},
        )

        self.assertEqual(result["intent"], "replace_stop")
        self.assertEqual(len(result["updated_route"]), len(route))
        self.assertNotEqual(result["updated_route"][1]["poi_id"], route[1]["poi_id"])
        self.assertEqual(result["updated_route"][1]["category_sub"], "窗边咖啡")

    def test_add_stop_appends_new_point(self):
        route = _sample_route()
        result = chat_reply(
            user_id="tester",
            message="新增一个甜品店",
            current_route=route,
            weather={"condition": "晴"},
        )

        self.assertEqual(result["intent"], "add_stop")
        self.assertEqual(len(result["updated_route"]), len(route) + 1)
        self.assertNotIn(result["updated_route"][-1]["poi_id"], {stop["poi_id"] for stop in route})

    def test_adjust_route_reorders_stops(self):
        route = _sample_route()
        result = chat_reply(
            user_id="tester",
            message="这条路线太赶了，帮我放慢一点并重新排一下",
            current_route=route,
            weather={"condition": "晴"},
        )

        self.assertEqual(result["intent"], "adjust_route")
        before = [stop["poi_id"] for stop in route]
        after = [stop["poi_id"] for stop in result["updated_route"]]
        self.assertEqual(set(after), set(before))
        self.assertNotEqual(after, before)

    def test_weather_adapt_replaces_outdoor_stops(self):
        route = _sample_route()
        result = chat_reply(
            user_id="tester",
            message="今天下雨，帮我改成室内路线",
            current_route=route,
            weather={"condition": "暴雨"},
        )

        self.assertEqual(result["intent"], "weather_adapt")
        self.assertTrue(all(stop.get("indoor", True) for stop in result["updated_route"]))

if __name__ == "__main__":
    unittest.main()
