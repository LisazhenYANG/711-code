from __future__ import annotations

from typing import Any


SPOTS: list[dict[str, Any]] = [
    {
        "name": "可纸工坊",
        "category": "手工坊",
        "time": "09:00",
        "dur": "约 1-2h",
        "meta": ["开放 10:00-18:00", "建议停留 1.5h"],
        "imgs": ["✂️", "🖼️", "🌿"],
        "prices": [["普通票", "¥88"], ["学生票", "¥44"], ["老人票", "¥44"], ["儿童票", "免费"]],
        "transitMode": None,
        "transitMin": None,
    },
    {
        "name": "UCCA · 当代艺术",
        "category": "展览",
        "time": "11:30",
        "dur": "约 1.5h",
        "meta": ["开放 10:00-19:00", "建议停留 1-2h"],
        "imgs": ["🎨", "🖼️", "✨"],
        "prices": [["普通票", "¥60"], ["学生票", "¥30"], ["老人票", "¥30"], ["军人票", "免费"]],
        "transitMode": "walk",
        "transitMin": 10,
    },
    {
        "name": "静雅书局",
        "category": "书店",
        "time": "14:00",
        "dur": "约 1h",
        "meta": ["开放 09:00-21:00", "免费入场"],
        "imgs": ["📚", "☕", "🌿"],
        "prices": [["入场", "免费"], ["咖啡区消费", "¥38起"]],
        "transitMode": "metro",
        "transitMin": 15,
    },
]

VENUE_CATEGORIES: dict[str, list[dict[str, str]]] = {
    "静下来": [
        {"name": "窗边咖啡", "desc": "安静座位和自然光", "count": "附近25家", "price": "¥35起", "duration": "约1h"},
        {"name": "图书馆", "desc": "低噪声、适合发呆阅读", "count": "附近5家", "price": "免费", "duration": "约1-2h"},
        {"name": "书店", "desc": "书咖和独立选书", "count": "附近9家", "price": "¥38起", "duration": "约1h"},
    ],
    "休闲娱乐": [
        {"name": "桌游", "desc": "轻松组局", "count": "附近12家", "price": "¥68起", "duration": "约2h"},
        {"name": "手工坊", "desc": "陶艺、纸艺、香薰", "count": "附近8家", "price": "¥88起", "duration": "约1.5h"},
        {"name": "展览", "desc": "当代艺术和小型策展", "count": "附近10家", "price": "¥60起", "duration": "约1.5h"},
    ],
    "热门打卡": [
        {"name": "网红地标", "desc": "好拍、动线短", "count": "附近18处", "price": "免费起", "duration": "约45min"},
        {"name": "设计师店", "desc": "买手店和生活方式集合", "count": "附近14家", "price": "¥80起", "duration": "约1h"},
    ],
}

MEAL_SLOTS = [
    {"key": "breakfast", "emoji": "🥐", "name": "早餐", "time": "08:30-09:30"},
    {"key": "lunch", "emoji": "🍜", "name": "中餐", "time": "12:00-13:00"},
    {"key": "dinner", "emoji": "🍽️", "name": "晚餐", "time": "18:00-19:30"},
]

MEALS = {
    "breakfast": [
        {"name": "老盛昌汤包", "cuisine": "本帮点心", "rating": "4.6", "price": "¥25/人", "wait": "5分钟"},
        {"name": "Manner Bakery", "cuisine": "烘焙咖啡", "rating": "4.8", "price": "¥30/人", "wait": "3分钟"},
    ],
    "lunch": [
        {"name": "沈大成", "cuisine": "本帮菜", "rating": "4.8", "price": "¥68/人", "wait": "15分钟"},
        {"name": "杏花楼", "cuisine": "粤菜", "rating": "4.7", "price": "¥75/人", "wait": "25分钟"},
        {"name": "弄堂小馆", "cuisine": "上海家常菜", "rating": "4.6", "price": "¥62/人", "wait": "10分钟"},
    ],
    "dinner": [
        {"name": "老克勒西餐", "cuisine": "海派西餐", "rating": "4.4", "price": "¥120/人", "wait": "20分钟"},
        {"name": "鸟啸炭火烧", "cuisine": "日式烧鸟", "rating": "4.9", "price": "¥150/人", "wait": "30分钟"},
        {"name": "桂满陇", "cuisine": "江浙菜", "rating": "4.6", "price": "¥110/人", "wait": "25分钟"},
    ],
}

RECOMMENDATIONS: list[dict[str, Any]] = [
    {
        "icon": "🎨",
        "title": "今日展览",
        "subtitle": "人少好拍 · 静安区",
        "rating": "★ 4.7",
        "price": "¥60起",
        "duration": "约 1.5h",
        "gallery": ["🎨", "🖼️", "✨"],
        "reason": "离当前路线顺路，工作日下午人流更友好，适合安排在咖啡和书店之间。",
    },
    {
        "icon": "☕",
        "title": "窗边咖啡",
        "subtitle": "适合慢慢坐 40 分钟",
        "rating": "★ 4.8",
        "price": "¥35起",
        "duration": "约 40min",
        "gallery": ["☕", "🪟", "🍰"],
        "reason": "窗边座位充足，适合看展后的缓冲休息，也方便继续步行到下一站。",
    },
    {
        "icon": "🌳",
        "title": "安静散步线",
        "subtitle": "少走路 · 少排队",
        "rating": "★ 4.6",
        "price": "免费",
        "duration": "约 45min",
        "gallery": ["🌳", "🚶", "☁️"],
        "reason": "路线短、岔路少，适合天气好的时候替换排队时间较长的室内点。",
    },
]

USER_PROFILES: dict[str, dict[str, Any]] = {
    "demo": {
        "name": "Lisa",
        "preferences": [
            {"label": "出行风格", "value": "慢慢逛型"},
            {"label": "饮食偏好", "value": "清淡 / 咖啡"},
            {"label": "交通偏好", "value": "地铁优先"},
        ],
        "modes": [
            {"title": "导览模式", "sub": "只看下一站和票根，界面干净不乱", "enabled": True},
            {"title": "心动模式", "sub": "实时感知天气、排队和定位变化", "enabled": True},
        ],
        "footprints": ["静安区", "艺术展", "咖啡", "手作"],
    }
}
