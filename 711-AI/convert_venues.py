"""hongkou_venues.json → mock_pois.json 字段映射转换"""
import json, re, hashlib

# ── 虹口区中心 ──
CENTER_LAT, CENTER_LNG = 31.265, 121.490
SPREAD_LAT, SPREAD_LNG = 0.018, 0.020  # 虹口约 2km x 2.5km


def _hash_offset(s: str, scale: float) -> float:
    """用地址 hash 产生确定性偏移,同一地址永远得到相同坐标"""
    h = int(hashlib.md5(s.encode()).hexdigest()[:8], 16)
    return (h / 0xFFFFFFFF - 0.5) * scale


# ── 大类映射 ──
MAIN_MAP = {
    "休闲娱乐": "休闲娱乐", "热门打卡": "热门打卡", "购物": "购物",
    "身心焕新": "身心焕新", "运动": "运动", "静下来": "静下来",
}

# ── 小类映射:取 / 分隔的第一个词映射 ──
def _map_sub(raw: str) -> str:
    first = raw.split("/")[0].strip().rstrip("类")
    m = {
        "剧本杀": "剧本杀", "密室": "密室逃脱", "桌游": "棋牌室",
        "图书馆": "图书馆", "书店": "图书馆",
        "窗边咖啡": "窗边咖啡", "咖啡": "窗边咖啡",
        "古着vintage": "古着vintage", "古着": "古着vintage",
        "DIY": "DIY工坊", "SPA": "SPA护理",
        "按摩足疗": "按摩足疗", "按摩": "按摩足疗",
        "瑜伽": "瑜伽健身", "特色景区": "特色景区",
        "网红地标": "网红地标", "独立品牌": "独立品牌",
        "草坪时光": "草坪时光", "公园": "草坪时光",
        "时令景色": "时令景色", "萌宠体验": "萌宠体验",
        "创意市集": "创意市集", "KTV": "KTV",
        "综合商场": "综合商场", "文化场馆": "文化场馆",
        "洗浴汗蒸": "洗浴汗蒸", "室内运动": "室内运动",
    }
    return m.get(first, first)


# ── 时间解析: "10:00-22:00" → [[10,22]], "13:00-次日02:00" → [[13,26]] ──
def _parse_hours(raw: str) -> list[list[int]]:
    result = []
    for seg in re.split(r"[;；]", raw):
        seg = seg.strip()
        if not seg:
            continue
        # 格式: HH:MM-HH:MM 或 HH-HH 或 HH:MM-次日HH:MM
        m = re.match(r"(\d{1,2}):?(\d{2})?\s*[-–至到]\s*(次日)?(\d{1,2}):?(\d{2})?", seg)
        if m:
            sh = int(m.group(1))
            eh = int(m.group(4))
            if m.group(3):
                eh += 24
            result.append([sh, eh])
    return result if result else [[10, 22]]


# ── 价格解析: "60元/人" → 60 ──
def _parse_price(raw: str) -> tuple[int, bool]:
    raw = raw.strip()
    if "免费" in raw:
        return 0, True
    m = re.search(r"(\d+)", raw)
    return (int(m.group(1)), False) if m else (0, True)


# ── 时长解析: "2-3小时" → 150分钟 ──
def _parse_stay(raw: str) -> int:
    raw = raw.strip()
    m = re.match(r"(\d+)-(\d+)\s*小时", raw)
    if m:
        return (int(m.group(1)) + int(m.group(2))) * 30
    m = re.match(r"(\d+)\s*小时", raw)
    if m:
        return int(m.group(1)) * 60
    m = re.match(r"(\d+)-(\d+)\s*分钟", raw)
    if m:
        return (int(m.group(1)) + int(m.group(2))) // 2
    return 90


# ── 适配人群 ──
def _parse_group(raw: str) -> list[str]:
    m = {
        "成人": "独行", "老年人": "独行", "商务休闲": "独行",
        "青年": "独行", "学生": "独行", "情侣": "情侣",
        "亲子": "亲子", "家庭": "亲子",
        "朋友团": "小团", "朋友": "小团",
    }
    out = []
    for g in raw.replace("、", ",").split(","):
        g = g.strip()
        mapped = m.get(g, g)
        if mapped not in out:
            out.append(mapped)
    return out if out else ["独行"]


def convert():
    with open("data/hongkou_venues.json", encoding="utf-8") as f:
        raw = json.load(f)

    out = []
    for item in raw:
        addr = item.get("地理位置", "")
        price, is_free = _parse_price(item.get("均价", "0"))
        rank = float(item.get("榜单分", 4.0))

        out.append({
            "id":           item["id"],
            "name":         item.get("名字", ""),
            "category_main": MAIN_MAP.get(item.get("大类", ""), "休闲娱乐"),
            "category_sub":  _map_sub(item.get("小类", "")),
            "lat":           round(CENTER_LAT + _hash_offset(addr, SPREAD_LAT), 6),
            "lng":           round(CENTER_LNG + _hash_offset(addr + "x", SPREAD_LNG), 6),
            "open_hours":    _parse_hours(item.get("开放时间", "10:00-22:00")),
            "rank_score":    rank,
            "good_review_rate": round(min(0.99, 0.75 + rank * 0.05), 2),
            "indoor":        item.get("室内室外", "室内") == "室内",
            "stay_minutes":  _parse_stay(item.get("默认停留时长", "1-2小时")),
            "fit_group":     _parse_group(item.get("适配人群", "")),
            "avg_price":     price,
            "free":          is_free,
            "need_booking":  item.get("是否需预约", "否") in ("需预约", "建议预约"),
            "ticket_tiers":  [] if is_free else [{"type": "普通", "price": price}],
            "tags":          item.get("标签", []),
            "intro":         item.get("简介", ""),
        })

    with open("data/mock_pois.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"转换: {len(raw)} → {len(out)} 条")
    cats = set(c["category_main"] for c in out)
    subs = set(c["category_sub"] for c in out)
    print(f"大类({len(cats)}): {sorted(cats)}")
    print(f"小类({len(subs)}): {sorted(subs)}")


if __name__ == "__main__":
    convert()
