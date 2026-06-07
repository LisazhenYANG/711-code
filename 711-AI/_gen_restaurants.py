"""一次性生成 mock_restaurants.json - 撒在虹口区。"""
import json
import hashlib
import random

CENTER_LAT, CENTER_LNG = 31.265, 121.490
SPREAD_LAT, SPREAD_LNG = 0.020, 0.022


def _hash_offset(s: str, scale: float) -> float:
    h = int(hashlib.md5(s.encode()).hexdigest()[:8], 16)
    return (h / 0xFFFFFFFF - 0.5) * scale


def _hash_int(s: str, lo: int, hi: int) -> int:
    h = int(hashlib.md5(s.encode()).hexdigest()[8:16], 16)
    return lo + h % (hi - lo + 1)


def _hash_float(s: str, lo: float, hi: float) -> float:
    h = int(hashlib.md5(s.encode()).hexdigest()[12:20], 16)
    return lo + (h / 0xFFFFFFFF) * (hi - lo)


# 菜系 → 各菜系下的店名模板 + 默认人均价格区间 + 是否含海鲜/清真/素食偏好
CUISINE_TEMPLATES = {
    "本帮菜": {
        "names": ["老吉士{0}", "本帮人家{0}", "上海弄堂菜{0}", "外婆家{0}", "红烧记{0}",
                  "海上人家{0}", "申城味道{0}", "老克勒{0}", "上海菜馆{0}", "石库门家宴{0}",
                  "老正兴{0}", "三鲜小馆{0}"],
        "sub_categories": ["家常", "小馆", "私房菜"],
        "price_range": (60, 180),
        "has_seafood": True,
        "halal": False,
        "vegetarian_friendly": False,
        "tags_pool": ["地道", "家常", "老字号", "下饭", "出片"],
    },
    "川菜": {
        "names": ["蜀九香{0}", "巴蜀小馆{0}", "川蜀人家{0}", "辣府{0}", "麻辣空间{0}",
                  "蓉记{0}", "锦城川菜{0}", "渝家小厨{0}", "川香坊{0}", "巴蜀豆花{0}"],
        "sub_categories": ["麻辣香锅", "川菜馆", "水煮", "钵钵鸡"],
        "price_range": (50, 150),
        "has_seafood": False,
        "halal": False,
        "vegetarian_friendly": False,
        "tags_pool": ["麻辣", "下饭", "聚会", "重口味"],
    },
    "粤菜": {
        "names": ["粤海轩{0}", "广式茶餐厅{0}", "白天鹅{0}", "港式茶餐厅{0}", "潮汕牛肉{0}",
                  "广式烧腊{0}", "翠园{0}", "粤味轩{0}", "南粤食府{0}", "湾仔茶记{0}"],
        "sub_categories": ["茶餐厅", "粤式酒楼", "潮汕菜", "烧腊"],
        "price_range": (70, 220),
        "has_seafood": True,
        "halal": False,
        "vegetarian_friendly": False,
        "tags_pool": ["清淡", "茶点", "出片", "商务"],
    },
    "湘菜": {
        "names": ["湘味人家{0}", "湖南人{0}", "辣椒炒肉{0}", "潇湘阁{0}", "湘江{0}",
                  "湘里湘亲{0}", "毛家饭店{0}", "三湘四水{0}"],
        "sub_categories": ["湘菜馆", "湘西菜"],
        "price_range": (50, 130),
        "has_seafood": False,
        "halal": False,
        "vegetarian_friendly": False,
        "tags_pool": ["麻辣", "下饭", "家常"],
    },
    "东北菜": {
        "names": ["东北人{0}", "关东人家{0}", "老东北{0}", "雪村{0}", "饺子馆{0}",
                  "东北大碗菜{0}", "黑土地{0}", "山海关{0}"],
        "sub_categories": ["东北菜", "饺子馆"],
        "price_range": (45, 100),
        "has_seafood": False,
        "halal": False,
        "vegetarian_friendly": False,
        "tags_pool": ["分量大", "家常", "便宜大碗"],
    },
    "日料": {
        "names": ["寿司贤{0}", "鲜鱼一{0}", "稻禾日料{0}", "鳗满{0}", "九本{0}",
                  "和心日料{0}", "鳥喜{0}", "鮨之心{0}", "蓝瓶日料{0}", "鲷之家{0}",
                  "千秋日料{0}", "禾绿回转{0}"],
        "sub_categories": ["寿司", "居酒屋", "拉面", "日式烧烤"],
        "price_range": (80, 400),
        "has_seafood": True,
        "halal": False,
        "vegetarian_friendly": False,
        "tags_pool": ["精致", "出片", "约会", "商务", "高级"],
    },
    "韩餐": {
        "names": ["首尔屋{0}", "韩舍{0}", "明洞{0}", "汉江{0}", "韩国料理{0}",
                  "炭火屋{0}", "金家{0}", "首尔之夜{0}"],
        "sub_categories": ["韩式烤肉", "石锅拌饭", "炸鸡"],
        "price_range": (70, 180),
        "has_seafood": False,
        "halal": False,
        "vegetarian_friendly": False,
        "tags_pool": ["烤肉", "聚会", "情侣"],
    },
    "西餐": {
        "names": ["BISTRO {0}", "Olive {0}", "Tartine {0}", "Sauce {0}",
                  "牛排工房{0}", "意面屋{0}", "Pizza {0}", "Brasserie {0}",
                  "Tavolo {0}", "Lumiere {0}"],
        "sub_categories": ["意餐", "法餐", "牛排", "披萨"],
        "price_range": (100, 380),
        "has_seafood": True,
        "halal": False,
        "vegetarian_friendly": True,
        "tags_pool": ["精致", "约会", "出片", "高级", "商务"],
    },
    "东南亚": {
        "names": ["泰象{0}", "椰岛{0}", "湄南{0}", "暹罗{0}", "曼谷小馆{0}",
                  "南洋食府{0}", "椰子鸡{0}", "香茅{0}"],
        "sub_categories": ["泰菜", "越南菜", "新马菜"],
        "price_range": (70, 180),
        "has_seafood": True,
        "halal": False,
        "vegetarian_friendly": True,
        "tags_pool": ["特色", "出片", "约会"],
    },
    "快餐": {
        "names": ["真功夫{0}", "永和大王{0}", "麦当劳{0}", "肯德基{0}", "汉堡王{0}",
                  "赛百味{0}", "吉野家{0}", "和合谷{0}", "杨国福{0}", "张亮{0}",
                  "沙县小吃{0}", "兰州拉面{0}"],
        "sub_categories": ["中式快餐", "汉堡", "麻辣烫"],
        "price_range": (20, 50),
        "has_seafood": False,
        "halal": False,
        "vegetarian_friendly": False,
        "tags_pool": ["快", "便宜", "外卖", "工作日"],
    },
    "面食": {
        "names": ["阿娘面{0}", "弄堂小面{0}", "兰州牛肉面{0}", "桂林米粉{0}", "重庆小面{0}",
                  "云吞大王{0}", "南翔小笼{0}", "苏州面馆{0}", "百年沪面{0}", "拉面说{0}"],
        "sub_categories": ["面馆", "粉馆", "小笼"],
        "price_range": (25, 60),
        "has_seafood": False,
        "halal": False,
        "vegetarian_friendly": False,
        "tags_pool": ["快", "本地", "实惠"],
    },
    "咖啡馆": {
        "names": ["Manner Coffee{0}", "Seesaw{0}", "M Stand{0}", "Peet's{0}",
                  "Tims{0}", "%Arabica{0}", "Blue Bottle{0}", "见山咖啡{0}",
                  "% 浓郁{0}", "白夜咖啡{0}", "Brew & Co{0}", "Local Beans{0}"],
        "sub_categories": ["精品咖啡", "网红咖啡", "连锁咖啡"],
        "price_range": (30, 75),
        "has_seafood": False,
        "halal": True,
        "vegetarian_friendly": True,
        "tags_pool": ["出片", "网红", "约会", "工作", "插座"],
    },
    "轻食": {
        "names": ["Wagas{0}", "Element Fresh{0}", "Green & Safe{0}", "莱杯沙拉{0}",
                  "GAGA鲜语{0}", "好色派沙拉{0}", "拾一沙拉{0}", "甜心摇滚{0}"],
        "sub_categories": ["沙拉", "三明治", "健康餐"],
        "price_range": (50, 100),
        "has_seafood": False,
        "halal": False,
        "vegetarian_friendly": True,
        "tags_pool": ["健康", "出片", "工作日", "白领"],
    },
    "清真": {
        "names": ["西部马华{0}", "白家牛肉拉面{0}", "兰州拉面{0}", "新疆餐厅{0}",
                  "回民街{0}", "西域风情{0}", "穆斯林餐厅{0}"],
        "sub_categories": ["清真菜", "西北菜", "新疆菜"],
        "price_range": (40, 120),
        "has_seafood": False,
        "halal": True,
        "vegetarian_friendly": False,
        "tags_pool": ["清真", "西北", "实惠"],
    },
    "素食": {
        "names": ["枣子树{0}", "素之家{0}", "绿无毒{0}", "净心斋{0}", "禅意斋{0}",
                  "本素{0}", "蔬食家{0}"],
        "sub_categories": ["素食馆"],
        "price_range": (60, 150),
        "has_seafood": False,
        "halal": True,
        "vegetarian_friendly": True,
        "tags_pool": ["素食", "健康", "禅意"],
    },
}

# 各菜系下生成餐厅数(目标总数 ~140)
COUNTS = {
    "本帮菜": 14, "川菜": 12, "粤菜": 10, "湘菜": 8, "东北菜": 8,
    "日料": 14, "韩餐": 8, "西餐": 10, "东南亚": 8,
    "快餐": 12, "面食": 12,
    "咖啡馆": 14, "轻食": 8,
    "清真": 6, "素食": 5,
}

# 不同菜系的店名后缀(凑数避免重名)
SUFFIXES = ["(虹口店)", "(欧阳店)", "(四川北路店)", "(今潮8弄店)", "(凉城店)",
            "(广中店)", "(临平店)", "(曲阳店)", "(瑞虹店)", "(虹湾店)",
            "(海伦店)", "(北外滩店)", "(乍浦路店)", "(东宝兴店)", "(运光店)",
            "(凉城路店)", "(永和路店)", "(花园路店)", "(红口店)"]


def generate():
    restaurants = []
    rid = 0
    for cuisine, tmpl in CUISINE_TEMPLATES.items():
        n = COUNTS[cuisine]
        names_pool = tmpl["names"]
        suffix_pool = SUFFIXES
        used_names = set()
        for _ in range(n):
            rid += 1
            attempts = 0
            while attempts < 20:
                idx = _hash_int(f"{cuisine}-{rid}-{attempts}", 0, len(names_pool) - 1)
                sfx_idx = _hash_int(f"{cuisine}-{rid}-sfx-{attempts}", 0, len(suffix_pool) - 1)
                name = names_pool[idx].format(suffix_pool[sfx_idx])
                if name not in used_names:
                    used_names.add(name)
                    break
                attempts += 1
            else:
                name = f"{names_pool[0].format('')}{rid}"

            sub_idx = _hash_int(f"sub-{rid}", 0, len(tmpl["sub_categories"]) - 1)
            sub = tmpl["sub_categories"][sub_idx]

            price = _hash_int(f"price-{rid}", *tmpl["price_range"])
            rating = round(_hash_float(f"rate-{rid}", 4.0, 4.9), 1)
            # 价格高的更可能预订
            supports_booking = price >= 80 or _hash_int(f"book-{rid}", 0, 99) < 40
            supports_queue = True
            max_party = _hash_int(f"party-{rid}", 4, 12)
            has_private = price >= 100 and _hash_int(f"priv-{rid}", 0, 99) < 60

            # tags 抽 2-3 个
            tags_pool = tmpl["tags_pool"]
            tag_n = _hash_int(f"tagn-{rid}", 2, min(3, len(tags_pool)))
            tags = []
            for i in range(tag_n):
                tg = tags_pool[_hash_int(f"tag-{rid}-{i}", 0, len(tags_pool) - 1)]
                if tg not in tags:
                    tags.append(tg)

            # 营业时间:大多 10-22,部分早开/晚开
            hour_pattern = _hash_int(f"hour-{rid}", 0, 4)
            if hour_pattern == 0:
                open_hours = [[10, 22]]
            elif hour_pattern == 1:
                open_hours = [[7, 22]]  # 早茶/快餐
            elif hour_pattern == 2:
                open_hours = [[11, 23]]  # 晚一点开
            elif hour_pattern == 3:
                open_hours = [[10, 14], [17, 22]]  # 中间休息
            else:
                open_hours = [[11, 24]]  # 夜宵

            # 队列模拟基础: 评分高 + 价格中等的店排队多
            avg_queue = 0
            if rating >= 4.5 and 60 <= price <= 200:
                avg_queue = _hash_int(f"queue-{rid}", 8, 25)
            elif rating >= 4.3:
                avg_queue = _hash_int(f"queue-{rid}", 3, 12)
            else:
                avg_queue = _hash_int(f"queue-{rid}", 0, 5)

            typical_wait = avg_queue * 2  # 每桌 2 分钟

            restaurants.append({
                "id": f"R{rid:03d}",
                "name": name,
                "cuisine": cuisine,
                "sub_category": sub,
                "lat": round(CENTER_LAT + _hash_offset(name, SPREAD_LAT), 6),
                "lng": round(CENTER_LNG + _hash_offset(name + "x", SPREAD_LNG), 6),
                "address": f"上海市虹口区{name[:-4] if name.endswith('店)') else name}",
                "rating": rating,
                "avg_price": price,
                "open_hours": open_hours,
                "supports_queue_ticket": supports_queue,
                "supports_table_booking": supports_booking,
                "max_party_size": max_party,
                "has_private_room": has_private,
                "is_halal": tmpl["halal"],
                "is_vegetarian_friendly": tmpl["vegetarian_friendly"],
                "has_seafood": tmpl["has_seafood"],
                "tags": tags,
                "intro": _gen_intro(cuisine, sub, name, tags),
                "base_queue_at_peak": avg_queue,
                "queue_speed_per_minute": 0.5,  # 0.5 桌/分钟 = 每 2 分钟叫一桌
                "typical_wait_minutes_at_peak": typical_wait,
            })
    return restaurants


def _gen_intro(cuisine, sub, name, tags):
    intros = {
        "本帮菜": f"经典本帮味道,{','.join(tags)},招牌红烧肉/八宝鸭/油爆虾。",
        "川菜": f"地道川味,辣度可调,{','.join(tags)}。",
        "粤菜": f"粤式{sub},清淡精致,{','.join(tags)}。",
        "湘菜": f"湖南家常菜,辣得过瘾,{','.join(tags)}。",
        "东北菜": f"东北家常,分量足实在,{','.join(tags)}。",
        "日料": f"{sub}专门店,选材考究,{','.join(tags)}。",
        "韩餐": f"韩式{sub},氛围地道,{','.join(tags)}。",
        "西餐": f"{sub},环境精致,{','.join(tags)}。",
        "东南亚": f"{sub}风味,酸辣开胃,{','.join(tags)}。",
        "快餐": f"{sub},出餐快效率高,{','.join(tags)}。",
        "面食": f"{sub},一碗就饱,{','.join(tags)}。",
        "咖啡馆": f"{sub},氛围适合{','.join(tags)}。",
        "轻食": f"{sub},健康选择,{','.join(tags)}。",
        "清真": f"{sub},清真认证,{','.join(tags)}。",
        "素食": f"全素菜单,{','.join(tags)}。",
    }
    return intros.get(cuisine, "本店欢迎光临。")


if __name__ == "__main__":
    data = generate()
    with open("data/mock_restaurants.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"生成 {len(data)} 家餐厅")
    from collections import Counter
    cuis = Counter(r["cuisine"] for r in data)
    print(f"菜系分布:", dict(cuis))
