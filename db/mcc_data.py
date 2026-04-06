"""
Категории MCC по программе ВТБ + человекочитаемые сообщества.
Диапазоны (авиа, отели, аренда) представлены репрезентативными кодами.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class MccCategory:
    """Одна категория кэшбэка: ключ, название, MCC, диапазон кэшбэка %."""
    key: str
    name_ru: str
    mcc_codes: List[int]
    cashback_min: int
    cashback_max: int


# Основные категории ВТБ (MCC из вашего списка; диапазоны — несколько кодов из диапазона)
MCC_CATEGORIES: List[MccCategory] = [
    MccCategory(
        "supermarkets",
        "Супермаркеты",
        [5412, 5462, 5411, 5422, 5441, 5451, 5499, 9751],
        1,
        3,
    ),
    MccCategory(
        "pharmacy",
        "Аптеки",
        [5122, 5912],
        1,
        3,
    ),
    MccCategory(
        "health",
        "Здоровье",
        [8050, 4119, 5975, 5976, 8011, 8021, 8031, 8041, 8042, 8043, 8044, 8049, 8062, 8071, 8099],
        1,
        3,
    ),
    MccCategory(
        "cafe_restaurants",
        "Кафе и рестораны",
        [5812, 5811, 5813, 5814],
        1,
        4,
    ),
    MccCategory(
        "fashion",
        "Одежда и обувь",
        [5137, 5611, 5621, 5651, 5691, 5699, 5931, 5681, 5948, 5139, 5661, 5631],
        1,
        3,
    ),
    MccCategory(
        "kids",
        "Детские товары",
        [5945, 5641],
        1,
        3,
    ),
    MccCategory(
        "transport",
        "Транспорт",
        [4111, 4131, 4789],
        1,
        2,
    ),
    MccCategory(
        "taxi",
        "Такси",
        [4121],
        1,
        2,
    ),
    MccCategory(
        "car_rental",
        "Аренда авто",
        [3351, 3400, 3420, 7513, 7519, 7512],
        1,
        2,
    ),
    MccCategory(
        "beauty",
        "Красота",
        [5698, 7230, 7297, 7298, 5977],
        1,
        3,
    ),
    MccCategory(
        "electronics",
        "Электроника",
        [5997, 5946, 5044, 5045, 5722, 5732],
        1,
        2,
    ),
    MccCategory(
        "flights",
        "Авиабилеты",
        [3010, 3200, 4511, 4582],
        1,
        2,
    ),
    MccCategory(
        "duty_free",
        "Duty Free",
        [5309],
        1,
        2,
    ),
    MccCategory(
        "hotels",
        "Отели",
        [3501, 3600, 7011, 7012, 7033, 7032],
        1,
        2,
    ),
    MccCategory(
        "rail",
        "Ж/д билеты",
        [4011, 4112],
        1,
        2,
    ),
    MccCategory(
        "travel_agencies",
        "Турагентства",
        [5962, 4723, 4722, 4411],
        1,
        2,
    ),
    MccCategory(
        "gas",
        "АЗС",
        [5541, 5172, 5542, 5983, 9752, 5552],
        1,
        3,
    ),
    MccCategory(
        "auto_service",
        "Автоуслуги",
        [5531, 5532, 5533, 7531, 7534, 7535, 7538, 7542, 7549, 7511],
        1,
        2,
    ),
]

# Дополнительные «интересные» сообщества (подбор по MCC из списка ВТБ)
INTEREST_COMMUNITIES = [
    {"key": "baking", "name": "Любители выпечки", "mcc_hint": 5462, "category_key": "supermarkets"},
    {"key": "coffee", "name": "Кофеманы", "mcc_hint": 5812, "category_key": "cafe_restaurants"},
    {"key": "fitness", "name": "Фитнес", "mcc_hint": 8041, "category_key": "health"},
]


def category_by_mcc(mcc: int) -> MccCategory | None:
    for c in MCC_CATEGORIES:
        if mcc in c.mcc_codes:
            return c
    return None


def all_mcc_codes() -> List[int]:
    seen = set()
    out: List[int] = []
    for c in MCC_CATEGORIES:
        for m in c.mcc_codes:
            if m not in seen:
                seen.add(m)
                out.append(m)
    return out
