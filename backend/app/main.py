from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from psycopg2.extras import RealDictCursor

from app.auth import create_access_token, get_current_user, verify_password
from app.db import neo4j_driver
from app.db_postgres import get_connection
from app.schemas import (
    CashbackOut,
    CommunitiesOverviewResponse,
    CommunityOut,
    CommunityOverviewOut,
    LoginRequest,
    PostOut,
    TokenResponse,
    UserPublic,
)

app = FastAPI(title="Bank communities MVP")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def neo4j_user_total_tx_count(user_id: int) -> int:
    with neo4j_driver.session() as session:
        result = session.run(
            """
            MATCH (u:User {id:$uid})-[r:HAS_TRANSACTION]->()
            RETURN coalesce(sum(r.tx_count), 0) AS total
            """,
            uid=user_id,
        )
        rec = result.single()
        if rec is None or rec["total"] is None:
            return 0
        return int(rec["total"])


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
            SELECT id, name, description, min_transactions
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
    total_tx = neo4j_user_total_tx_count(user["id"])
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT id, name, description, min_transactions
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
            is_member = cid in joined_ids
            need_raw = max(0, d["min_transactions"] - total_tx)
            tn = 0 if is_member else need_raw
            out.append(
                CommunityOverviewOut(
                    id=cid,
                    name=d["name"],
                    description=d["description"],
                    min_transactions=d["min_transactions"],
                    is_member=is_member,
                    transactions_needed=tn,
                )
            )
        return CommunitiesOverviewResponse(total_tx_count=total_tx, communities=out)
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
    total_tx = neo4j_user_total_tx_count(user["id"])
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT id, min_transactions
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
        if row["min_transactions"] > total_tx:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Недостаточно транзакций (проверка по Neo4j)",
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
            SELECT cb.id, cb.amount, cb.place, cb.created_at
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
                )
            )
        return out
    finally:
        conn.close()


@app.get("/posts", response_model=list[PostOut])
def list_posts(community_id: int | None = Query(None)):
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        if community_id is None:
            cur.execute(
                """
                SELECT p.id, p.id_sender, p.id_community, p.title, p.text, p.rating, p.created_at
                FROM post p
                ORDER BY p.created_at DESC
                """
            )
        else:
            cur.execute(
                """
                SELECT p.id, p.id_sender, p.id_community, p.title, p.text, p.rating, p.created_at
                FROM post p
                WHERE p.id_community = %s
                ORDER BY p.created_at DESC
                """,
                (community_id,),
            )
        rows = cur.fetchall()
        out = []
        for r in rows:
            d = dict(r)
            ca = d.get("created_at")
            created_str = ca.isoformat() if ca is not None else None
            out.append(
                PostOut(
                    id=d["id"],
                    id_sender=d["id_sender"],
                    id_community=d["id_community"],
                    title=d["title"],
                    text=d["text"],
                    rating=d["rating"],
                    created_at=created_str,
                )
            )
        return out
    finally:
        conn.close()


@app.get("/users/me/communities", response_model=list[CommunityOut])
def my_communities(user: Annotated[dict, Depends(get_current_user)]):
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT c.id, c.name, c.description
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


@app.get("/recommend/{user_id}")
def recommend(user_id: int):
    recommendations = []
    with neo4j_driver.session() as session:
        result = session.run(
            """
            MATCH (u:User {id:$uid})-[r:HAS_TRANSACTION]->(p:Place)
            WHERE r.tx_count >= 3
            RETURN p.name AS place_name, p.category AS category,
                   r.tx_count AS tx_count, r.total_amount AS total_amount
            ORDER BY r.total_amount DESC
            """,
            uid=user_id,
        )
        for record in result:
            recommendations.append(
                {
                    "place_name": record["place_name"],
                    "category": record["category"],
                    "tx_count": record["tx_count"],
                    "total_amount": record["total_amount"],
                }
            )
    return {"recommendations": recommendations}


@app.get("/recommend/me")
def recommend_me(user: Annotated[dict, Depends(get_current_user)]):
    return recommend(user["id"])


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
