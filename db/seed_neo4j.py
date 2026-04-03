"""
Заполнение Neo4j: User (id = client.id из PostgreSQL), Place, связь HAS_TRANSACTION
с полями tx_count (кол-во операций) и total_amount (сумма трат в рублях).
Запуск: python db/seed_neo4j.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import NEO4J_PASSWORD, NEO4J_URI, NEO4J_USER
from mcc_data import category_by_mcc

from neo4j import GraphDatabase


def _meta_for_mcc(mcc: int) -> tuple[str, str, int, int]:
    cat = category_by_mcc(mcc)
    if cat:
        return cat.key, cat.name_ru, cat.cashback_min, cat.cashback_max
    return "unknown", "Прочее", 1, 3


# Торговые точки: имя, MCC (из справочника ВТБ)
PLACES: list[dict] = [
    {"name": "Кофемания Тверская", "mcc": 5812},
    {"name": "Starbucks Невский", "mcc": 5812},
    {"name": "Пятёрочка у дома", "mcc": 5411},
    {"name": "ВкусВилл", "mcc": 5412},
    {"name": "Спортмастер", "mcc": 5651},
    {"name": "Мир фитнеса", "mcc": 8041},
    {"name": "36,6 Аптека", "mcc": 5122},
    {"name": "DNS Электроника", "mcc": 5732},
    {"name": "Лукойл АЗС", "mcc": 5541},
    {"name": "Яндекс Go", "mcc": 4121},
    {"name": "Пекарня Хлебница", "mcc": 5462},
    {"name": "Отель Marriott", "mcc": 7011},
]

# Пользователь ↔ место: число операций и сумма (раздельно, как просили)
TRANSACTIONS: list[dict] = [
    {"user_id": 1, "place_name": "Кофемания Тверская", "tx_count": 12, "total_amount": 18600.0},
    {"user_id": 1, "place_name": "Starbucks Невский", "tx_count": 5, "total_amount": 4200.0},
    {"user_id": 1, "place_name": "Пекарня Хлебница", "tx_count": 8, "total_amount": 6400.0},
    {"user_id": 2, "place_name": "Мир фитнеса", "tx_count": 10, "total_amount": 45000.0},
    {"user_id": 2, "place_name": "36,6 Аптека", "tx_count": 4, "total_amount": 3200.0},
    {"user_id": 3, "place_name": "Пятёрочка у дома", "tx_count": 20, "total_amount": 28000.0},
    {"user_id": 3, "place_name": "Пекарня Хлебница", "tx_count": 6, "total_amount": 2100.0},
    {"user_id": 4, "place_name": "DNS Электроника", "tx_count": 3, "total_amount": 89000.0},
    {"user_id": 4, "place_name": "Отель Marriott", "tx_count": 2, "total_amount": 24000.0},
    {"user_id": 5, "place_name": "Спортмастер", "tx_count": 4, "total_amount": 12000.0},
    {"user_id": 5, "place_name": "Кофемания Тверская", "tx_count": 7, "total_amount": 9800.0},
    {"user_id": 6, "place_name": "Лукойл АЗС", "tx_count": 15, "total_amount": 22500.0},
    {"user_id": 6, "place_name": "Яндекс Go", "tx_count": 9, "total_amount": 5400.0},
]


def seed() -> None:
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        with driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")

            users = [
                {"id": 1, "first_name": "Анна", "last_name": "Иванова"},
                {"id": 2, "first_name": "Борис", "last_name": "Петров"},
                {"id": 3, "first_name": "Елена", "last_name": "Смирнова"},
                {"id": 4, "first_name": "Дмитрий", "last_name": "Козлов"},
                {"id": 5, "first_name": "Мария", "last_name": "Новикова"},
                {"id": 6, "first_name": "Игорь", "last_name": "Волков"},
            ]
            for u in users:
                session.run(
                    """
                    MERGE (x:User {id: $id})
                    SET x.first_name = $fn, x.last_name = $ln
                    """,
                    id=u["id"],
                    fn=u["first_name"],
                    ln=u["last_name"],
                )

            for p in PLACES:
                mcc = p["mcc"]
                ck, cr, cmin, cmax = _meta_for_mcc(mcc)
                session.run(
                    """
                    MERGE (pl:Place {name: $name})
                    SET pl.mcc = $mcc,
                        pl.category_key = $ck,
                        pl.category = $cat_ru,
                        pl.cashback_min = $cmin,
                        pl.cashback_max = $cmax
                    """,
                    name=p["name"],
                    mcc=mcc,
                    ck=ck,
                    cat_ru=cr,
                    cmin=cmin,
                    cmax=cmax,
                )

            for t in TRANSACTIONS:
                session.run(
                    """
                    MATCH (u:User {id: $uid}), (pl:Place {name: $pname})
                    MERGE (u)-[r:HAS_TRANSACTION]->(pl)
                    SET r.tx_count = $tx_count,
                        r.total_amount = $total_amount,
                        r.currency = 'RUB'
                    """,
                    uid=t["user_id"],
                    pname=t["place_name"],
                    tx_count=t["tx_count"],
                    total_amount=t["total_amount"],
                )

        print("Neo4j: граф очищен, пользователи, места и связи HAS_TRANSACTION созданы.")
        print("  Связь: tx_count — число операций, total_amount — сумма трат (руб.).")
    finally:
        driver.close()


if __name__ == "__main__":
    seed()
