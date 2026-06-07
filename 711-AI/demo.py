"""
Demo - 端到端跑一次规划,展示新增的真实路网导航 + 餐厅推荐 + 取号字段。

用法:
  python demo.py                  完整跑(需要 DEEPSEEK_API_KEY)
  python demo.py --no-llm         不调 LLM
  python demo.py --user-id alice  指定用户
  python demo.py --feedback       附带反馈写回
  python demo.py --book           演示一次取号 + 一次预订
"""
from __future__ import annotations
import argparse
import json
import os
from datetime import datetime, timedelta

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-llm", action="store_true")
    parser.add_argument("--user-id", default="demo_user")
    parser.add_argument("--feedback", action="store_true")
    parser.add_argument("--book", action="store_true")
    args = parser.parse_args()

    if args.no_llm:
        os.environ.pop("DEEPSEEK_API_KEY", None)
        print("[demo] --no-llm 模式: LLM 已禁用,会走 fallback")

    from graph.builder import get_planning_graph, get_feedback_graph
    from providers import booking_mock as bm

    initial = {
        "user_id": args.user_id,
        "intent": {
            "origin_lat": 31.265,
            "origin_lng": 121.490,
            "origin_name": "上海·虹口区中心",
            "time_slot": "下午",
            "people_count": 2,
            "people_group": "情侣",
            "transport_mode": "walk",
            "moods": ["静下来", "休闲娱乐"],
            "sub_categories": ["窗边咖啡", "图书馆", "DIY工坊"],
            "free_text": "想找个安静的下午,少赶路,最好能出片",
            "budget_per_person": 200,
            "locked_poi_ids": [],
            "city_code": "021",
        },
        "weather": {"condition": "晴"},
        "follow_up_rounds": 0,
        "candidate_pool": [],
        "candidate_routes": [],
        "debate_transcript": [],
        "top_routes": [],
    }

    print(f"\n{'═' * 64}")
    print(f"[1] 跑规划主图")
    print(f"{'═' * 64}")
    graph = get_planning_graph()
    result = graph.invoke(initial)

    print(f"\n可达半径: {result.get('reachable_radius_km')} km   时间窗: {result.get('time_window')}")
    print(f"可排 POI 数: {result.get('max_pois_per_day')}   候选池: {len(result.get('candidate_pool', []))}")
    print(f"候选路线数: {result.get('candidate_routes_count', 0)}")
    print(f"LLM 降级: {result.get('llm_degraded', False)} | 导航降级: {result.get('navigation_degraded', False)}")
    dropped = result.get("intent", {}).get("_dropped_categories", [])
    if dropped:
        print(f"砍掉的超额类别: {dropped}")

    print(f"\n--- 主持人小结 ---")
    print(result.get("pre_brief", "(无)"))

    print(f"\n{'═' * 64}")
    print(f"[2] Top-3 路线")
    print(f"{'═' * 64}")
    for i, r in enumerate(result.get("top_routes", []), 1):
        print(f"\n┌─ Route {i}: {r.get('label', '(无标签)')} ─ {r.get('summary', '')}")
        print(f"│  quality={r.get('quality_score')} commute={r.get('total_commute_minutes')}min "
              f"nav_source={r.get('navigation_source')}")
        for stop_idx, stop in enumerate(r["stops"]):
            cross = " ⚠跨区" if stop.get("cross_zone") else ""
            lock = " 🔒" if stop.get("locked") else ""
            print(f"│  ▸ {stop['arrival_time']}-{stop['leave_time']} {stop['poi_name']}"
                  f" (停{stop['stay_minutes']}分){cross}{lock}")
            nav = stop.get("navigation_to_next")
            if nav:
                print(f"│       ↓ {stop['transit_to_next_minutes']}min "
                      f"{stop.get('transit_to_next_mode')}  距离 "
                      f"{nav.get('total_distance_m', 0)}m  "
                      f"{len(nav.get('steps') or [])} 步指示")
                for j, st in enumerate(nav.get("steps") or [], 1):
                    if j > 3:
                        print(f"│         ... 还有 {len(nav['steps']) - 3} 步")
                        break
                    instr = st["instruction"][:50]
                    print(f"│         {j}. {instr}  ({st['distance_m']}m, {st['duration_s']}s)")

        # 餐厅推荐
        recs = r.get("food_recommendations") or []
        for fb in recs:
            anchor = fb.get("anchor") or {}
            anchor_name = anchor.get("anchor_name", "?") if anchor else "(无锚点)"
            print(f"│")
            print(f"│  🍴 {fb['meal_block']} {fb['block_time']}  锚点: {anchor_name}")
            if fb.get("empty_reason"):
                breakdown = fb.get("filter_breakdown", {})
                print(f"│     (空: {fb['empty_reason']}, 硬过滤剔除: {breakdown})")
                continue
            for bk in fb["buckets"][:6]:
                marker = "❤" if bk["matched_loved"] else " "
                print(f"│     {marker} [{bk['cuisine']}] ({len(bk['restaurants'])}家)")
                for rest in bk["restaurants"]:
                    queue_info = ""
                    if rest.get("current_queue") is not None:
                        queue_info = f" 队{rest['current_queue']}桌(等{rest.get('queue_wait_minutes', 0)}分)"
                    print(f"│         · {rest['name']}  ¥{rest.get('avg_price')}  "
                          f"★{rest.get('rating')}  {int(rest.get('distance_m', 0))}m{queue_info}")
        print(f"└─")

    # ─────────────────────────────────────────────
    # 反馈写回 demo
    # ─────────────────────────────────────────────
    if args.feedback and result.get("top_routes"):
        print(f"\n{'═' * 64}")
        print(f"[3] 反馈写回(模拟用户选了第一条 + 5星)")
        print(f"{'═' * 64}")
        fb_initial = {
            "user_id": args.user_id,
            "intent": result.get("intent"),
            "top_routes": result["top_routes"],
            "debate_transcript": result.get("debate_transcript", []),
            "user_choice_route_id": result["top_routes"][0]["route_id"],
            "user_deleted_poi_ids": [],
            "user_rating": 5,
        }
        fb_graph = get_feedback_graph()
        fb_result = fb_graph.invoke(fb_initial)
        prof = fb_result.get("user_profile", {})
        print(f"  total_plans: {prof.get('total_plans')}")
        print(f"  agent_weights: {prof.get('agent_weights')}")
        print(f"  loved_categories: {dict(list(prof.get('loved_categories', {}).items())[:5])}")

    # ─────────────────────────────────────────────
    # 取号 + 预订 demo
    # ─────────────────────────────────────────────
    if args.book and result.get("top_routes"):
        print(f"\n{'═' * 64}")
        print(f"[4] 取号 / 预订演示")
        print(f"{'═' * 64}")
        # 找第一条路线的第一个推荐餐厅
        rt = result["top_routes"][0]
        first_rest = None
        for fb in rt.get("food_recommendations") or []:
            for bk in fb["buckets"]:
                if bk["restaurants"]:
                    first_rest = bk["restaurants"][0]
                    break
            if first_rest:
                break

        if not first_rest:
            print("  没有可推荐的餐厅,跳过 booking demo")
        else:
            print(f"\n  目标餐厅: {first_rest['name']} ({first_rest['id']})")
            print(f"  当前队列: {first_rest.get('current_queue', '?')} 桌, 等待 {first_rest.get('queue_wait_minutes', 0)} 分钟")

            # 取号
            print(f"\n  → 取号...")
            ticket = bm.take_queue_ticket(first_rest["id"], args.user_id, 2)
            print(f"     票号: {ticket['ticket_no']}")
            print(f"     当前排队位置: 第 {ticket['queue_position_at_issue']} 位")
            print(f"     预估等待: {ticket['estimated_wait_minutes']} 分钟")
            print(f"     预估叫号时间: {ticket['estimated_call_time']}")

            # 5 分钟后再查
            from datetime import datetime, timedelta
            later = datetime.now() + timedelta(minutes=5)
            t2 = bm.get_ticket(ticket["ticket_no"], now=later)
            print(f"\n  → 5 分钟后再查(模拟时间)")
            print(f"     当前位置: 第 {t2['queue_position_now']} 位 (移动 {ticket['queue_position_at_issue'] - t2['queue_position_now']} 桌)")
            print(f"     剩余等待: {t2['estimated_wait_remaining_minutes']} 分钟")
            print(f"     ready_to_call: {t2['ready_to_call']}")
            print(f"     [沉浸模式信号: ready_to_call='approaching' 时 App 可推送 '快到号了']")

            # 预订一个晚餐
            target_time = datetime.now() + timedelta(hours=6)
            print(f"\n  → 同时预订 6 小时后晚餐: {target_time.strftime('%H:%M')}")
            res = bm.reserve_table(first_rest["id"], args.user_id, 2, target_time, special_requests="想坐窗边")
            if "error" in res:
                print(f"     预订失败: {res}")
            else:
                print(f"     预订号: {res['reservation_id']}")
                print(f"     状态: {res['status']} ({res['confirm_hint']})")
                print(f"     [沉浸模式接入字段]:")
                print(f"        remind_at: {res['remind_at']}  (30分钟前提醒)")
                print(f"        arrive_window: {res['arrive_window_start']} ~ {res['arrive_window_end']}")

            # 列所有活跃订单
            all_bk = bm.list_user_bookings(args.user_id)
            print(f"\n  → 用户 {args.user_id} 当前活跃订单: {len(all_bk['tickets'])} 票 + {len(all_bk['reservations'])} 预订")


if __name__ == "__main__":
    main()
