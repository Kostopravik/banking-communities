"""
Заполнение PostgreSQL: клиенты, сообщества, посты, комментарии, кэшбэк.
Запуск из корня репозитория: python db/seed_postgres.py
Требуется: применён db/schema.sql (или первый запуск создаст через seed_all).
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
from mcc_data import INTEREST_COMMUNITIES, MCC_CATEGORIES


def _hash_pw(plain: str) -> str:
    return hashlib.sha256(plain.encode()).hexdigest()


def apply_schema(conn) -> None:
    schema_path = Path(__file__).resolve().parent / "schema.sql"
    with open(schema_path, encoding="utf-8") as f:
        conn.cursor().execute(f.read())
    conn.commit()


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
            TRUNCATE TABLE client_cashback, cashback, comment, post,
                client_community, community, client
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

        communities: list[tuple[str, str]] = []
        for c in MCC_CATEGORIES:
            desc = f"Сообщество по категории «{c.name_ru}». Кэшбэк {c.cashback_min}–{c.cashback_max}%."
            communities.append((c.name_ru, desc))
        for ic in INTEREST_COMMUNITIES:
            desc = f"Интерес по транзакциям (MCC {ic['mcc_hint']})."
            communities.append((ic["name"], desc))

        execute_values(
            cur,
            """
            INSERT INTO community (name, description)
            VALUES %s
            """,
            communities,
        )

        cur.execute(
            "UPDATE community SET min_transactions = 2 WHERE name = 'Фитнес'"
        )
        cur.execute(
            "UPDATE community SET min_transactions = 3 WHERE name IN ('Duty Free', 'Авиабилеты')"
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
        ]
        execute_values(
            cur,
            """
            INSERT INTO post (id_sender, id_community, title, text, image_url)
            VALUES %s
            """,
            posts,
        )

        cur.execute("SELECT id FROM post ORDER BY id LIMIT 1")
        first_post = cur.fetchone()
        if first_post:
            pid = first_post[0]
            cur.execute(
                """
                INSERT INTO comment (id_post, id_sender, id_parent, message)
                VALUES (%s, %s, NULL, %s)
                RETURNING id
                """,
                (pid, 2, "Согласен, кэшбэк отличный."),
            )
            parent_cid = cur.fetchone()[0]
            cur.execute(
                """
                INSERT INTO comment (id_post, id_sender, id_parent, message)
                VALUES (%s, %s, %s, %s)
                """,
                (pid, 3, parent_cid, "Поделитесь адресом кофейни."),
            )

        cashback_rows = [
            (120.5, 5812),
            (340.0, 5411),
            (89.0, 8041),
            (200.0, 5997),
        ]
        cb_ids: list[int] = []
        for amount, place in cashback_rows:
            cur.execute(
                "INSERT INTO cashback (amount, place) VALUES (%s, %s) RETURNING id",
                (amount, place),
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
        print("PostgreSQL: схема применена, тестовые данные загружены.")
        print("  Логины: anna, boris, elena, dmitry, maria, igor — пароль: pass123")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    seed()
