"""
Заполнение PostgreSQL: клиенты, сообщества (с category_key), посты, комментарии, лайки, офферы «Выгода».
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import (
    POSTGRES_DB,
    POSTGRES_HOST,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
    POSTGRES_USER,
)
from mcc_data import INTEREST_COMMUNITIES, MCC_CATEGORIES, category_by_mcc


def _hash_pw(plain: str) -> str:
    return hashlib.sha256(plain.encode()).hexdigest()


def apply_schema(conn) -> None:
    schema_path = Path(__file__).resolve().parent / "schema.sql"
    with open(schema_path, encoding="utf-8") as f:
        conn.cursor().execute(f.read())
    conn.commit()


def _cashback_percent_for_key(category_key: str | None) -> int:
    if not category_key:
        return 3
    for c in MCC_CATEGORIES:
        if c.key == category_key:
            return c.cashback_max
    return 3


def _community_description(name: str, min_pct: int, max_pct: int) -> str:
    if name == "Здоровье":
        return f"Для тех, кто заботится о себе: аптеки, анализы и полезные сервисы. Кэшбэк до {max_pct}%."
    if name == "Фитнес":
        return f"Для тех, кто в движении: спортзалы, тренировки и активный образ жизни. Кэшбэк до {max_pct}%."
    if name == "Кафе и рестораны":
        return f"Для любителей вкусно поесть вне дома. Кэшбэк до {max_pct}%."
    if name == "Супермаркеты":
        return f"Для повседневных покупок и семейного бюджета. Кэшбэк до {max_pct}%."
    if name == "Красота":
        return f"Для ухода за собой и приятных бьюти-покупок. Кэшбэк до {max_pct}%."
    if name == "АЗС":
        return f"Для тех, кто часто за рулем. Кэшбэк до {max_pct}%."
    if min_pct == max_pct:
        return f"Выгоды и бонусы для участников сообщества «{name}». Кэшбэк до {max_pct}%."
    return f"Выгоды и бонусы для участников сообщества «{name}». Кэшбэк до {max_pct}%."


def seed() -> None:
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
    )
    conn.autocommit = False
    try:
        apply_schema(conn)
        cur = conn.cursor()

        cur.execute(
            """
            TRUNCATE TABLE post_like, client_cashback, cashback, comment, post,
                client_community, cashback_offer, community, client
            RESTART IDENTITY CASCADE
            """
        )

        pw = _hash_pw("pass123")
        clients = [
            (1, "Анна", "Иванова", "anna", pw),
            (2, "Борис", "Петров", "boris", pw),
            (3, "Елена", "Смирнова", "elena", pw),
            (4, "Дмитрий", "Козлов", "dmitry", pw),
            (5, "Мария", "Новикова", "maria", pw),
            (6, "Игорь", "Волков", "igor", pw),
        ]
        execute_values(
            cur,
            """
            INSERT INTO client (id, first_name, last_name, login, password)
            VALUES %s
            """,
            clients,
        )

        communities: list[tuple[str, str, str]] = []
        for c in MCC_CATEGORIES:
            desc = _community_description(c.name_ru, c.cashback_min, c.cashback_max)
            communities.append((c.name_ru, desc, c.key))
        for ic in INTEREST_COMMUNITIES:
            desc = f"Для тех, кому близка тема «{ic['name']}». Делитесь опытом и получайте выгоды."
            communities.append((ic["name"], desc, ic["category_key"]))

        execute_values(
            cur,
            """
            INSERT INTO community (name, description, category_key)
            VALUES %s
            """,
            communities,
        )

        cur.execute("SELECT id, name, category_key FROM community ORDER BY id")
        for rid, name, ck in cur.fetchall():
            pct = _cashback_percent_for_key(ck)
            cur.execute(
                """
                INSERT INTO cashback_offer (id_community, title, percent, description)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    rid,
                    f"Выгода: {name}",
                    pct,
                    f"Кэшбэк до {pct}% после вступления в сообщество «{name}».",
                ),
            )

        cur.execute("SELECT id, name FROM community ORDER BY id")
        comm_rows = cur.fetchall()
        name_to_cid = {name: cid for cid, name in comm_rows}

        memberships = [
            (1, "Кофеманы"),
            (1, "Кафе и рестораны"),
            (2, "Фитнес"),
            (2, "Здоровье"),
            (3, "Любители выпечки"),
            (3, "Супермаркеты"),
            (4, "Электроника"),
            (4, "Авиабилеты"),
            (5, "Красота"),
            (5, "Кафе и рестораны"),
            (6, "АЗС"),
            (6, "Автоуслуги"),
        ]
        mc_rows = [
            (cid, name_to_cid[name])
            for cid, name in memberships
            if name in name_to_cid
        ]
        if mc_rows:
            execute_values(
                cur,
                """
                INSERT INTO client_community (id_client, id_community)
                VALUES %s
                ON CONFLICT (id_client, id_community) DO NOTHING
                """,
                mc_rows,
            )

        posts = [
            (1, name_to_cid["Кофеманы"], "Лучший эспрессо в городе", "Нашёл кофейню с зёрнами из Эфиопии.", None),
            (2, name_to_cid["Фитнес"], "Абонемент в зал", "Сравниваю цены на годовые карты.", None),
            (3, name_to_cid["Любители выпечки"], "Домашний хлеб", "Рецепт закваски без заморочек.", None),
            (4, name_to_cid["Электроника"], "Скидки на наушники", "Кто ловил кэшбэк на 5732?", None),
            (1, name_to_cid["Кафе и рестораны"], "Латте с овсяным", "Пробую все сети на Невском.", None),
            (3, name_to_cid["Супермаркеты"], "Сезонные скидки", "ВкусВилл vs Пятёрочка — что выгоднее?", None),
            (5, name_to_cid["Красота"], "Салон или дома?", "Делюсь находками по уходу.", None),
            (6, name_to_cid["АЗС"], "Карта заправок", "Где удобнее с кэшбэком.", None),
            (2, name_to_cid["Здоровье"], "Чекап раз в год", "Собрал чек-лист анализов.", None),
            (4, name_to_cid["Авиабилеты"], "Мили или кэшбэк", "Сравниваю программы лояльности.", None),
        ]
        execute_values(
            cur,
            """
            INSERT INTO post (id_sender, id_community, title, text, image_url)
            VALUES %s
            """,
            posts,
        )

        cur.execute("SELECT id FROM post ORDER BY id")
        post_ids = [r[0] for r in cur.fetchall()]
        p0, p1 = post_ids[0], post_ids[1]

        cur.execute(
            """
            INSERT INTO comment (id_post, id_sender, id_parent, message)
            VALUES (%s, %s, NULL, %s)
            RETURNING id
            """,
            (p0, 2, "Согласен, кэшбэк отличный."),
        )
        c_parent = cur.fetchone()[0]
        cur.execute(
            """
            INSERT INTO comment (id_post, id_sender, id_parent, message)
            VALUES (%s, %s, %s, %s)
            """,
            (p0, 3, c_parent, "Поделитесь адресом кофейни."),
        )
        cur.execute(
            """
            INSERT INTO comment (id_post, id_sender, id_parent, message)
            VALUES (%s, %s, NULL, %s)
            """,
            (p0, 4, "Пробовал — топ."),
        )
        cur.execute(
            """
            INSERT INTO comment (id_post, id_sender, id_parent, message)
            VALUES (%s, %s, NULL, %s)
            """,
            (p1, 1, "У нас в зале акция на год."),
        )
        for pid, sender, msg in [
            (post_ids[2], 5, "Закваска на ржаной муке — огонь."),
            (post_ids[3], 6, "DNS часто даёт рассрочку."),
            (post_ids[4], 2, "Овсяное молоко бесплатно?"),
            (post_ids[5], 1, "Сравнил корзину на 5000 ₽."),
        ]:
            cur.execute(
                """
                INSERT INTO comment (id_post, id_sender, id_parent, message)
                VALUES (%s, %s, NULL, %s)
                """,
                (pid, sender, msg),
            )

        cur.execute(
            """
            INSERT INTO comment (id_post, id_sender, id_parent, message)
            VALUES (%s, %s, %s, %s)
            """,
            (p0, 5, c_parent, "Адрес в личку скину."),
        )

        for uid, pid in [(2, p0), (3, p0), (4, p0), (1, p1), (6, post_ids[2])]:
            cur.execute(
                """
                INSERT INTO post_like (id_client, id_post) VALUES (%s, %s)
                ON CONFLICT (id_client, id_post) DO NOTHING
                """,
                (uid, pid),
            )

        cashback_rows = [
            (120.5, 5812),
            (340.0, 5411),
            (89.0, 8041),
            (200.0, 5997),
            (150.0, 5541),
            (95.0, 4121),
            (180.0, 5732),
        ]
        cb_ids: list[int] = []
        for amount, place in cashback_rows:
            cat = category_by_mcc(place)
            ck = cat.key if cat else None
            label = cat.name_ru if cat else "Партнерские покупки"
            cur.execute(
                """
                INSERT INTO cashback (amount, place, category_key, category_label)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (amount, place, ck, label),
            )
            cb_ids.append(cur.fetchone()[0])

        links = [
            (1, cb_ids[0]),
            (2, cb_ids[1]),
            (3, cb_ids[2] if len(cb_ids) > 2 else cb_ids[0]),
        ]
        execute_values(
            cur,
            """
            INSERT INTO client_cashback (id_client, id_cashback)
            VALUES %s
            ON CONFLICT (id_client, id_cashback) DO NOTHING
            """,
            links,
        )

        conn.commit()
        print("PostgreSQL: данные загружены (посты, комментарии, лайки, офферы «Выгода»).")
        print("  Логины: anna, boris, elena, dmitry, maria, igor — пароль: pass123")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    seed()
