import os
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.pop("DEEPSEEK_API_KEY", None)
os.environ.pop("AMAP_API_KEY", None)

from graph.nodes import (  # noqa: E402
    node_candidates,
    node_cluster_and_pool,
    node_intent_parse,
    node_profile_load,
    node_reachable,
    node_route_gen,
    node_score,
    node_time_slots,
)


class CandidateRecallTest(unittest.TestCase):
    def test_frontend_natural_categories_build_clusters(self):
        state = {
            "user_id": "test",
            "intent": {
                "origin_lat": 31.2304,
                "origin_lng": 121.4737,
                "origin_name": "人民广场",
                "time_slot": "下午",
                "people_count": 2,
                "transport_mode": "transit",
                "moods": ["静下来", "城市漫游"],
                "sub_categories": ["咖啡馆", "展览"],
                "free_text": "",
                "budget_per_person": 200,
                "locked_poi_ids": [],
                "health_constraints": [],
                "city_code": "021",
            },
            "weather": {"condition": "晴"},
            "follow_up_rounds": 0,
            "candidate_pool": [],
        }
        for node in (
            node_intent_parse,
            node_profile_load,
            node_reachable,
            node_time_slots,
            node_candidates,
            node_score,
            node_cluster_and_pool,
        ):
            state.update(node(state))

        self.assertGreater(len(state["candidate_pool"]), 0)
        self.assertGreater(len(state["clusters"]), 0)
        self.assertTrue(any(cluster["members"] for cluster in state["clusters"]))

    def test_single_category_coffee_request_still_generates_routes(self):
        state = {
            "user_id": "test",
            "intent": {
                "origin_lat": 31.2304,
                "origin_lng": 121.4737,
                "origin_name": "人民广场",
                "time_slot": "下午",
                "people_count": 2,
                "transport_mode": "transit",
                "moods": ["静下来"],
                "sub_categories": ["窗边咖啡"],
                "free_text": "推荐一个咖啡店",
                "budget_per_person": 200,
                "locked_poi_ids": [],
                "health_constraints": [],
                "city_code": "021",
            },
            "weather": {"condition": "晴"},
            "follow_up_rounds": 0,
            "candidate_pool": [],
            "candidate_routes": [],
        }
        for node in (
            node_intent_parse,
            node_profile_load,
            node_reachable,
            node_time_slots,
            node_candidates,
            node_score,
            node_cluster_and_pool,
            node_route_gen,
        ):
            state.update(node(state))

        self.assertGreater(len(state["candidate_routes"]), 0)
        self.assertTrue(all(len(route["stops"]) >= 2 for route in state["candidate_routes"]))


if __name__ == "__main__":
    unittest.main()
