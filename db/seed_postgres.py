"""
Заполнение PostgreSQL: клиенты, сообщества (с category_key), посты, комментарии, лайки, офферы «Выгода».
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from random import choice, randint

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

        # ========== РАСШИРЕННЫЕ ПОСТЫ ДЛЯ ВСЕХ СООБЩЕСТВ ==========
        
        posts_data = [
            # Кофеманы
            (1, "Кофеманы", "Лучший эспрессо в городе", "Нашёл кофейню с зёрнами из Эфиопии. Кэшбэк 5%!", None),
            (1, "Кофеманы", "Кофе в зернах: где покупать?", "Заказываю на Wildberries с кэшбэком до 10%.", None),
            (3, "Кофеманы", "Альтернативные способы заваривания", "Воронка vs френч-пресс. Ваше мнение?", None),
            
            # Фитнес
            (2, "Фитнес", "Абонемент в зал", "Сравниваю цены на годовые карты. Где выгоднее?", None),
            (2, "Фитнес", "Домашние тренировки", "Купил гантели за 5000 ₽ - вернул 500 кэшбэком.", None),
            (5, "Фитнес", "Фитнес-браслеты", "Xiaomi или Huawei? Какой даёт больше бонусов?", None),
            
            # Здоровье
            (2, "Здоровье", "Чекап раз в год", "Собрал чек-лист анализов. Кэшбэк в лабораториях до 15%.", None),
            (4, "Здоровье", "Аптечные покупки", "Заметил, что в одной аптеке кэшбэк 10%, а в другой 3%.", None),
            (1, "Здоровье", "Витамины зимой", "Какие комплексы берете? С кэшбэком выгоднее.", None),
            
            # Любители выпечки
            (3, "Любители выпечки", "Домашний хлеб", "Рецепт закваски без заморочек. Муку беру с кэшбэком 7%.", None),
            (3, "Любители выпечки", "Печенье на кефире", "Дешево и вкусно. Ингредиенты с кэшбэком 5%.", None),
            (5, "Любители выпечки", "Куда тратите кэшбэк?", "Я на формы для выпечки и силиконовые коврики.", None),
            
            # Кафе и рестораны
            (1, "Кафе и рестораны", "Латте с овсяным", "Пробую все сети на Невском. В какой кэшбэк больше?", None),
            (5, "Кафе и рестораны", "Бизнес-ланчи", "Где вкусно и недорого? С кэшбэком ещё выгоднее.", None),
            (2, "Кафе и рестораны", "Доставка vs поход в кафе", "Кэшбэк в приложениях до 8%. А вы где берёте?", None),
            
            # Супермаркеты
            (3, "Супермаркеты", "Сезонные скидки", "ВкусВилл vs Пятёрочка - что выгоднее с кэшбэком?", None),
            (1, "Супермаркеты", "Программа лояльности Перекрёстка", "Коплю бонусы + кэшбэк до 7%. Окупается?", None),
            (4, "Супермаркеты", "Онлайн-заказы продуктов", "СберМаркет даёт кэшбэк 10% в первый заказ.", None),
            
            # Красота
            (5, "Красота", "Салон или дома?", "Делюсь находками по уходу. Кэшбэк на косметику до 15%.", None),
            (5, "Красота", "Корейская косметика", "Заказываю с кэшбэком 8%. Кто тоже фанат?", None),
            (2, "Красота", "Мужской уход", "Кремы и бритвы с кэшбэком - экономия до 500 ₽ в месяц.", None),
            
            # АЗС
            (6, "АЗС", "Карта заправок", "Где удобнее с кэшбэком? Лукойл даёт 5%, Газпром 3%.", None),
            (6, "АЗС", "Акции на топливо", "По вторникам скидка 2% + кэшбэк 5% по карте.", None),
            (2, "АЗС", "Электрозаправки", "Для владельцев электромобилей. Есть кэшбэк?", None),
            
            # Автоуслуги
            (6, "Автоуслуги", "Шиномонтаж с кэшбэком", "Отдам 2000 ₽, вернут 300. Выгодно?", None),
            (4, "Автоуслуги", "Автосервис", "Проверенный с кэшбэком 7%. Делюсь контактом.", None),
            (1, "Автоуслуги", "Мойка самообслуживания", "Экономлю до 500 ₽ в месяц с кэшбэком 10%.", None),
            
            # Электроника
            (4, "Электроника", "Скидки на наушники", "Кто ловил кэшбэк на 5732? Вернул 500 ₽.", None),
            (4, "Электроника", "Смартфоны с кэшбэком", "В М.Видео сейчас 15% на технику.", None),
            (6, "Электроника", "Ноутбук для работы", "Купил на Ozon с кэшбэком 10% - вернул 7000 ₽.", None),
            
            # Авиабилеты
            (4, "Авиабилеты", "Мили или кэшбэк", "Сравниваю программы лояльности. Кэшбэк выгоднее.", None),
            (2, "Авиабилеты", "Лайфхак: билеты с кэшбэком", "Покупаю через сервисы с возвратом 10%.", None),
            (3, "Авиабилеты", "Отели и авиабилеты", "Пакетный тур с кэшбэком 8% - делитесь опытом.", None),
        ]
        
        execute_values(
            cur,
            """
            INSERT INTO post (id_sender, id_community, title, text, image_url)
            VALUES %s
            """,
            [(sender, name_to_cid[comm], title, text, img) 
             for sender, comm, title, text, img in posts_data],
        )

        cur.execute("SELECT id, id_sender, id_community FROM post ORDER BY id")
        all_posts = cur.fetchall()
        post_ids = [p[0] for p in all_posts]
        
        # Создаем список пользователей для комментариев
        client_ids = [1, 2, 3, 4, 5, 6]
        
        # ========== МНОГО КОММЕНТАРИЕВ ДЛЯ КАЖДОГО ПОСТА ==========
        
        comments_pool = [
            "Отличный совет, спасибо!",
            "А где можно узнать подробнее?",
            "Тоже заметил такую выгоду.",
            "Кэшбэк реально работает?",
            "У меня не получилось, может я что-то не так делаю?",
            "Проверил - действительно выгодно!",
            "Лучший пост в сообществе!",
            "А есть альтернативы?",
            "Спасибо за наводку!",
            "Попробую в следующий раз.",
            "Давно ищу такую информацию.",
            "Поделитесь ссылкой?",
            "У меня кэшбэк пришел через 3 дня.",
            "Работает в любом городе?",
            "Только сегодня воспользовался - топ!",
        ]
        
        # Генерируем 2-5 комментариев на каждый пост
        for post_id, sender_id, comm_id in all_posts:
            num_comments = randint(2, 6)
            used_senders = set()
            used_senders.add(sender_id)  # автор поста может комментировать свой пост
            
            for _ in range(num_comments):
                # Выбираем случайного пользователя (не автора поста для разнообразия)
                available = [c for c in client_ids if c not in used_senders or len(used_senders) > 2]
                comment_sender = choice(available if available else client_ids)
                used_senders.add(comment_sender)
                
                comment_text = choice(comments_pool)
                # 20% комментариев делаем ответами на другие комментарии
                if randint(1, 100) <= 20:
                    # Находим существующий комментарий к этому посту
                    cur.execute(
                        "SELECT id FROM comment WHERE id_post = %s LIMIT 1",
                        (post_id,)
                    )
                    parent_comment = cur.fetchone()
                    if parent_comment:
                        cur.execute(
                            """
                            INSERT INTO comment (id_post, id_sender, id_parent, message)
                            VALUES (%s, %s, %s, %s)
                            """,
                            (post_id, comment_sender, parent_comment[0], f"Ответ: {comment_text}")
                        )
                        continue
                
                cur.execute(
                    """
                    INSERT INTO comment (id_post, id_sender, id_parent, message)
                    VALUES (%s, %s, NULL, %s)
                    """,
                    (post_id, comment_sender, comment_text),
                )

        # ========== ЛАЙКИ НА ПОСТЫ (случайные) ==========
        
        # Добавляем лайки от разных пользователей к разным постам
        for post_id in post_ids:
            # Каждый пост лайкают 2-5 пользователей
            num_likes = randint(2, 5)
            likers = choice([client_ids[:3], client_ids[3:], client_ids, client_ids[:4], client_ids[2:]])
            for liker in list(set(likers))[:num_likes]:
                cur.execute(
                    """
                    INSERT INTO post_like (id_client, id_post) 
                    VALUES (%s, %s)
                    ON CONFLICT (id_client, id_post) DO NOTHING
                    """,
                    (liker, post_id),
                )
        
        # Дополнительные лайки от авторов к своим постам (автолайк)
        for post_id, sender_id, _ in all_posts:
            cur.execute(
                """
                INSERT INTO post_like (id_client, id_post) 
                VALUES (%s, %s)
                ON CONFLICT (id_client, id_post) DO NOTHING
                """,
                (sender_id, post_id),
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

        # Подсчет статистики для вывода
        cur.execute("SELECT COUNT(*) FROM post")
        post_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM comment")
        comment_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM post_like")
        like_count = cur.fetchone()[0]

        conn.commit()
        print(f"PostgreSQL: данные загружены!")
        print(f"  - Постов: {post_count}")
        print(f"  - Комментариев: {comment_count}")
        print(f"  - Лайков: {like_count}")
        print(f"  - Сообществ: {len(communities)}")
        print("  Логины: anna, boris, elena, dmitry, maria, igor - пароль: pass123")
    except Exception as e:
        conn.rollback()
        print(f"Ошибка: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    seed()