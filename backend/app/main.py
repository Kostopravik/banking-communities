from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from psycopg2.extras import RealDictCursor

from app.auth import create_access_token, get_current_user, verify_password
from app.db import neo4j_driver
from app.db_postgres import get_connection
from app.schemas import (
    BenefitOut,
    CashbackOpportunityOut,
    CashbackOut,
    CommentCreate,
    CommentOut,
    CommunitiesOverviewResponse,
    CommunityOut,
    CommunityOverviewOut,
    LoginRequest,
    PostCreate,
    PostOut,
    TokenResponse,
    UserPublic,
)

app = FastAPI(title="Bank communities MVP")

MCC_OPS_REQUIRED = 3

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def neo4j_user_total_operations(user_id: int) -> int:
    with neo4j_driver.session() as session:
        result = session.run(
            """
            MATCH (u:User {id:$uid})-[r:HAS_TRANSACTION]->()
            RETURN count(r) AS total
            """,
            uid=user_id,
        )
        rec = result.single()
        if rec is None or rec["total"] is None:
            return 0
        return int(rec["total"])


def neo4j_user_category_operations(user_id: int, category_key: str | None) -> int:
    if not category_key:
        return 0
    with neo4j_driver.session() as session:
        result = session.run(
            """
            MATCH (u:User {id:$uid})-[r:HAS_TRANSACTION]->(p:Place)
            WHERE p.category_key = $ck
            RETURN count(r) AS cnt
            """,
            uid=user_id,
            ck=category_key,
        )
        rec = result.single()
        if rec is None or rec["cnt"] is None:
            return 0
        return int(rec["cnt"])


@app.post("/auth/login", response_model=TokenResponse)
def login(body: LoginRequest):
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT id, first_name, last_name, login, password
            FROM client
            WHERE login = %s
            """,
            (body.login,),
        )
        row = cur.fetchone()
        if not row or not verify_password(body.password, row["password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный логин или пароль",
            )
        user = UserPublic(
            id=row["id"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            login=row["login"],
        )
        token = create_access_token(row["id"], row["login"])
        return TokenResponse(access_token=token, user=user)
    finally:
        conn.close()


@app.get("/auth/me", response_model=UserPublic)
def me(user: Annotated[dict, Depends(get_current_user)]):
    return UserPublic(
        id=user["id"],
        first_name=user["first_name"],
        last_name=user["last_name"],
        login=user["login"],
    )


@app.get("/communities", response_model=list[CommunityOut])
def list_communities():
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT id, name, description, min_transactions, category_key
            FROM community
            ORDER BY id
            """
        )
        return [CommunityOut(**dict(r)) for r in cur.fetchall()]
    finally:
        conn.close()


@app.get(
    "/communities/overview",
    response_model=CommunitiesOverviewResponse,
)
def communities_overview(user: Annotated[dict, Depends(get_current_user)]):
    total_ops = neo4j_user_total_operations(user["id"])
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT id, name, description, min_transactions, category_key
            FROM community
            ORDER BY id
            """
        )
        rows = cur.fetchall()
        cur.execute(
            """
            SELECT id_community
            FROM client_community
            WHERE id_client = %s
            """,
            (user["id"],),
        )
        joined_ids = {r["id_community"] for r in cur.fetchall()}
        out: list[CommunityOverviewOut] = []
        for c in rows:
            d = dict(c)
            cid = d["id"]
            ck = d.get("category_key")
            is_member = cid in joined_ids
            cat_ops = neo4j_user_category_operations(user["id"], ck)
            need_raw = max(0, MCC_OPS_REQUIRED - cat_ops)
            tn = 0 if is_member else need_raw
            out.append(
                CommunityOverviewOut(
                    id=cid,
                    name=d["name"],
                    description=d["description"],
                    min_transactions=d.get("min_transactions") or 0,
                    is_member=is_member,
                    transactions_needed=tn,
                    category_key=ck,
                    category_operations_count=cat_ops,
                    mcc_operations_required=MCC_OPS_REQUIRED,
                )
            )
        return CommunitiesOverviewResponse(total_operations=total_ops, communities=out)
    finally:
        conn.close()


@app.post(
    "/communities/{community_id}/join",
    status_code=status.HTTP_204_NO_CONTENT,
)
def join_community(
    community_id: int,
    user: Annotated[dict, Depends(get_current_user)],
):
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT id, category_key
            FROM community
            WHERE id = %s
            """,
            (community_id,),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Сообщество не найдено",
            )
        cur.execute(
            """
            SELECT 1
            FROM client_community
            WHERE id_client = %s AND id_community = %s
            """,
            (user["id"], community_id),
        )
        if cur.fetchone():
            conn.commit()
            return None

        ck = row.get("category_key")
        if not ck:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="У сообщества нет категории MCC",
            )
        cnt = neo4j_user_category_operations(user["id"], ck)
        if cnt < MCC_OPS_REQUIRED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Нужно минимум {MCC_OPS_REQUIRED} операций в категории MCC "
                    f"(сейчас {cnt})"
                ),
            )
        cur.execute(
            """
            INSERT INTO client_community (id_client, id_community)
            VALUES (%s, %s)
            ON CONFLICT (id_client, id_community) DO NOTHING
            """,
            (user["id"], community_id),
        )
        conn.commit()
    finally:
        conn.close()
    return None


@app.get("/users/me/cashback", response_model=list[CashbackOut])
def my_cashback(user: Annotated[dict, Depends(get_current_user)]):
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT cb.id, cb.amount, cb.place, cb.created_at,
                   cb.category_key, cb.category_label
            FROM client_cashback cc
            JOIN cashback cb ON cb.id = cc.id_cashback
            WHERE cc.id_client = %s
            ORDER BY cb.id
            """,
            (user["id"],),
        )
        rows = cur.fetchall()
        out: list[CashbackOut] = []
        for r in rows:
            d = dict(r)
            ca = d.get("created_at")
            out.append(
                CashbackOut(
                    id=d["id"],
                    amount=float(d["amount"]),
                    place=d["place"],
                    created_at=ca.isoformat() if ca is not None else None,
                    category_key=d.get("category_key"),
                    category_label=d.get("category_label"),
                )
            )
        return out
    finally:
        conn.close()


@app.get(
    "/users/me/cashback-opportunities",
    response_model=list[CashbackOpportunityOut],
)
def cashback_opportunities(user: Annotated[dict, Depends(get_current_user)]):
    """
    Все записи-кэшбэки из каталога: привязка к MCC и category_key.
    eligible = в Neo4j ≥3 отдельных операции (рёбер) в этой MCC-категории.
    accrued = начисление уже привязано к пользователю в client_cashback.
    """
    uid = user["id"]
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT id, amount, place, category_key, category_label
            FROM cashback
            ORDER BY id
            """
        )
        catalog = cur.fetchall()
        cur.execute(
            """
            SELECT id_cashback FROM client_cashback WHERE id_client = %s
            """,
            (uid,),
        )
        accrued_ids = {r["id_cashback"] for r in cur.fetchall()}
        out: list[CashbackOpportunityOut] = []
        for r in catalog:
            d = dict(r)
            cid = d["id"]
            ck = d.get("category_key")
            ops = neo4j_user_category_operations(uid, ck)
            need = max(0, MCC_OPS_REQUIRED - ops)
            eligible = ops >= MCC_OPS_REQUIRED
            accrued = cid in accrued_ids
            label = d.get("category_label") or f"MCC {d['place']}"
            if eligible:
                hint = (
                    "Условие по операциям выполнено (≥3 в категории). "
                    + ("Начисление есть в «Мои кэшбэки»." if accrued else "Можно оформить начисление в банке (MVP).")
                )
            else:
                hint = (
                    f"Нужно ещё {need} операций в категории MCC «{ck or '?'}» по данным графа Neo4j."
                )
            out.append(
                CashbackOpportunityOut(
                    id=cid,
                    amount=float(d["amount"]),
                    place_mcc=int(d["place"]),
                    category_key=ck,
                    category_label=label,
                    operations_in_category=ops,
                    operations_required=MCC_OPS_REQUIRED,
                    eligible=eligible,
                    accrued=accrued,
                    hint=hint,
                )
            )
        return out
    finally:
        conn.close()


@app.get("/users/me/benefits", response_model=list[BenefitOut])
def my_benefits(user: Annotated[dict, Depends(get_current_user)]):
    uid = user["id"]
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT o.id, o.title, o.percent, o.description,
                   o.id_community, c.name AS community_name, c.category_key
            FROM cashback_offer o
            JOIN community c ON c.id = o.id_community
            ORDER BY o.id
            """
        )
        rows = cur.fetchall()
        cur.execute(
            """
            SELECT id_community FROM client_community WHERE id_client = %s
            """,
            (uid,),
        )
        joined = {r["id_community"] for r in cur.fetchall()}
        out: list[BenefitOut] = []
        for r in rows:
            d = dict(r)
            cid = d["id_community"]
            is_member = cid in joined
            ck = d.get("category_key")
            cat_ops = neo4j_user_category_operations(uid, ck)
            need = max(0, MCC_OPS_REQUIRED - cat_ops)
            name = d["community_name"]
            if is_member:
                hint = "Активно — вы в сообществе"
            elif need > 0:
                hint = (
                    f"Вступите в «{name}». Нужно ещё {need} операций "
                    f"в категории MCC (в графе Neo4j)."
                )
            else:
                hint = f"Вступите в сообщество «{name}», чтобы активировать выгоду."
            out.append(
                BenefitOut(
                    id=d["id"],
                    title=d["title"],
                    percent=int(d["percent"]),
                    description=d["description"],
                    community_id=cid,
                    community_name=name,
                    is_active=is_member,
                    operations_needed_to_join=0 if is_member else need,
                    hint=hint,
                )
            )
        return out
    finally:
        conn.close()


@app.post("/posts", response_model=PostOut, status_code=status.HTTP_201_CREATED)
def create_post(
    body: PostCreate,
    user: Annotated[dict, Depends(get_current_user)],
):
    uid = user["id"]
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT 1
            FROM client_community
            WHERE id_client = %s AND id_community = %s
            """,
            (uid, body.id_community),
        )
        if not cur.fetchone():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Сначала вступите в это сообщество",
            )
        cur.execute(
            """
            INSERT INTO post (id_sender, id_community, title, text)
            VALUES (%s, %s, %s, %s)
            RETURNING id, rating, created_at
            """,
            (uid, body.id_community, body.title.strip(), body.text.strip()),
        )
        row = cur.fetchone()
        conn.commit()
        ca = row["created_at"]
        return PostOut(
            id=row["id"],
            id_sender=uid,
            id_community=body.id_community,
            title=body.title.strip(),
            text=body.text.strip(),
            rating=row["rating"] or 0,
            created_at=ca.isoformat() if ca is not None else None,
            like_count=0,
            liked_by_me=False,
        )
    except HTTPException:
        conn.rollback()
        raise
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@app.get("/posts", response_model=list[PostOut])
def list_posts(
    user: Annotated[dict, Depends(get_current_user)],
    community_id: int | None = Query(None),
):
    uid = user["id"]
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        if community_id is None:
            cur.execute(
                """
                SELECT p.id, p.id_sender, p.id_community, p.title, p.text,
                       p.rating, p.created_at,
                       (SELECT COUNT(*)::int FROM post_like pl WHERE pl.id_post = p.id)
                           AS like_count,
                       EXISTS(
                           SELECT 1 FROM post_like pl
                           WHERE pl.id_post = p.id AND pl.id_client = %s
                       ) AS liked_by_me
                FROM post p
                ORDER BY p.created_at DESC
                """,
                (uid,),
            )
        else:
            cur.execute(
                """
                SELECT p.id, p.id_sender, p.id_community, p.title, p.text,
                       p.rating, p.created_at,
                       (SELECT COUNT(*)::int FROM post_like pl WHERE pl.id_post = p.id)
                           AS like_count,
                       EXISTS(
                           SELECT 1 FROM post_like pl
                           WHERE pl.id_post = p.id AND pl.id_client = %s
                       ) AS liked_by_me
                FROM post p
                WHERE p.id_community = %s
                ORDER BY p.created_at DESC
                """,
                (uid, community_id),
            )
        rows = cur.fetchall()
        out: list[PostOut] = []
        for r in rows:
            d = dict(r)
            ca = d.get("created_at")
            out.append(
                PostOut(
                    id=d["id"],
                    id_sender=d["id_sender"],
                    id_community=d["id_community"],
                    title=d["title"],
                    text=d["text"],
                    rating=d["rating"],
                    created_at=ca.isoformat() if ca is not None else None,
                    like_count=int(d.get("like_count") or 0),
                    liked_by_me=bool(d.get("liked_by_me")),
                )
            )
        return out
    finally:
        conn.close()


@app.post("/posts/{post_id}/like", response_model=dict)
def toggle_post_like(
    post_id: int,
    user: Annotated[dict, Depends(get_current_user)],
):
    uid = user["id"]
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT 1 FROM post WHERE id = %s", (post_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Пост не найден")
        cur.execute(
            """
            SELECT 1 FROM post_like WHERE id_client = %s AND id_post = %s
            """,
            (uid, post_id),
        )
        if cur.fetchone():
            cur.execute(
                """
                DELETE FROM post_like WHERE id_client = %s AND id_post = %s
                """,
                (uid, post_id),
            )
            liked = False
        else:
            cur.execute(
                """
                INSERT INTO post_like (id_client, id_post) VALUES (%s, %s)
                """,
                (uid, post_id),
            )
            liked = True
        cur.execute(
            """
            SELECT COUNT(*)::int AS cnt FROM post_like WHERE id_post = %s
            """,
            (post_id,),
        )
        cnt_row = cur.fetchone()
        cnt = int(cnt_row["cnt"]) if cnt_row and cnt_row.get("cnt") is not None else 0
        conn.commit()
        return {"liked": liked, "like_count": cnt}
    except HTTPException:
        conn.rollback()
        raise
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _client_display_name(row: dict) -> str:
    fn = (row.get("first_name") or "").strip()
    ln = (row.get("last_name") or "").strip()
    return f"{fn} {ln}".strip() or (row.get("login") or "?")


@app.get("/posts/{post_id}/comments", response_model=list[CommentOut])
def list_comments(post_id: int):
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT 1 FROM post WHERE id = %s", (post_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Пост не найден")
        cur.execute(
            """
            SELECT c.id, c.id_sender, c.id_parent, c.message, c.created_at,
                   cl.first_name, cl.last_name, cl.login,
                   pcl.first_name AS p_fn, pcl.last_name AS p_ln, pcl.login AS p_login
            FROM comment c
            JOIN client cl ON cl.id = c.id_sender
            LEFT JOIN comment pc ON pc.id = c.id_parent
            LEFT JOIN client pcl ON pcl.id = pc.id_sender
            WHERE c.id_post = %s
            ORDER BY c.created_at ASC, c.id ASC
            """,
            (post_id,),
        )
        rows = cur.fetchall()
        out: list[CommentOut] = []
        for r in rows:
            d = dict(r)
            nm = _client_display_name(
                {
                    "first_name": d.get("first_name"),
                    "last_name": d.get("last_name"),
                    "login": d.get("login"),
                }
            )
            reply_to = None
            if d.get("id_parent"):
                reply_to = _client_display_name(
                    {
                        "first_name": d.get("p_fn"),
                        "last_name": d.get("p_ln"),
                        "login": d.get("p_login"),
                    }
                )
            ca = d.get("created_at")
            out.append(
                CommentOut(
                    id=d["id"],
                    id_sender=d["id_sender"],
                    sender_name=nm,
                    message=d["message"] or "",
                    created_at=ca.isoformat() if ca is not None else None,
                    id_parent=d.get("id_parent"),
                    reply_to_name=reply_to,
                )
            )
        return out
    finally:
        conn.close()


@app.post(
    "/posts/{post_id}/comments",
    response_model=CommentOut,
    status_code=status.HTTP_201_CREATED,
)
def create_comment(
    post_id: int,
    body: CommentCreate,
    user: Annotated[dict, Depends(get_current_user)],
):
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT 1 FROM post WHERE id = %s", (post_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Пост не найден")
        parent_id = body.parent_id
        reply_to_name: str | None = None
        if parent_id is not None:
            cur.execute(
                """
                SELECT c.id_post, cl.first_name, cl.last_name, cl.login
                FROM comment c
                JOIN client cl ON cl.id = c.id_sender
                WHERE c.id = %s AND c.id_post = %s
                """,
                (parent_id, post_id),
            )
            prow = cur.fetchone()
            if not prow:
                raise HTTPException(
                    status_code=400,
                    detail="Родительский комментарий не найден или к другому посту",
                )
            reply_to_name = _client_display_name(dict(prow))
        cur.execute(
            """
            INSERT INTO comment (id_post, id_sender, id_parent, message)
            VALUES (%s, %s, %s, %s)
            RETURNING id, created_at
            """,
            (post_id, user["id"], parent_id, body.message.strip()),
        )
        row = cur.fetchone()
        conn.commit()
        nm = (
            f"{(user.get('first_name') or '').strip()} {(user.get('last_name') or '').strip()}".strip()
            or user["login"]
        )
        ca = row["created_at"]
        return CommentOut(
            id=row["id"],
            id_sender=user["id"],
            sender_name=nm,
            message=body.message.strip(),
            created_at=ca.isoformat() if ca is not None else None,
            id_parent=parent_id,
            reply_to_name=reply_to_name,
        )
    except HTTPException:
        conn.rollback()
        raise
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@app.get("/users/me/communities", response_model=list[CommunityOut])
def my_communities(user: Annotated[dict, Depends(get_current_user)]):
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT c.id, c.name, c.description, c.min_transactions, c.category_key
            FROM client_community cc
            JOIN community c ON c.id = cc.id_community
            WHERE cc.id_client = %s
            ORDER BY c.id
            """,
            (user["id"],),
        )
        return [CommunityOut(**dict(r)) for r in cur.fetchall()]
    finally:
        conn.close()


@app.get("/recommend/me")
def recommend_me(user: Annotated[dict, Depends(get_current_user)]):
    return recommend(user["id"])


@app.get("/recommend/{user_id}")
def recommend(user_id: int):
    """
    По каждому месту: operation_count — число отдельных рёбер HAS_TRANSACTION
    (каждая покупка = одно ребро с полем amount). Не путать с «одной агрегированной записью».
    """
    recommendations = []
    with neo4j_driver.session() as session:
        result = session.run(
            """
            MATCH (u:User {id:$uid})-[r:HAS_TRANSACTION]->(p:Place)
            WITH p, count(r) AS operation_count, sum(r.amount) AS total_amount
            WHERE operation_count >= 3
            RETURN p.name AS place_name, p.category AS category,
                   operation_count, total_amount
            ORDER BY total_amount DESC
            """,
            uid=user_id,
        )
        for record in result:
            oc = int(record["operation_count"])
            recommendations.append(
                {
                    "place_name": record["place_name"],
                    "category": record["category"],
                    "operation_count": oc,
                    "tx_count": oc,
                    "total_amount": float(record["total_amount"]),
                }
            )
    return {"recommendations": recommendations}


@app.get("/health")
def health():
    neo_ok = False
    pg_ok = False
    try:
        with neo4j_driver.session() as session:
            session.run("RETURN 1 AS one")
        neo_ok = True
    except Exception:
        pass
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        pg_ok = True
    except Exception:
        pass
    return {"neo4j": neo_ok, "postgres": pg_ok}
