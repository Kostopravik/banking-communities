from app.db import neo4j_driver

users = [
    {"id": 1, "name": "Alice"},
    {"id": 2, "name": "Bob"},
    {"id": 3, "name": "Kostopravik"},
]

places = [
    {"name": "Cafe 1", "mcc": 5812, "category": "Cafe", "cashback": 3},
    {"name": "Supermarket 1", "mcc": 5411, "category": "Supermarket", "cashback": 1},
    {"name": "Pharmacy 1", "mcc": 5122, "category": "Pharmacy", "cashback": 2},
]

transactions = [
    {"user_id": 1, "place_name": "Cafe 1", "amount": 100, "count": 4},
    {"user_id": 1, "place_name": "Supermarket 1", "amount": 50, "count": 2},
    {"user_id": 2, "place_name": "Cafe 1", "amount": 80, "count": 3},
]

with neo4j_driver.session() as session:
    # Создаем пользователей
    for u in users:
        session.run(
            "MERGE (u:User {id: $id, name: $name})",
            id=u["id"], name=u["name"]
        )

    # Создаем места
    for p in places:
        session.run(
            "MERGE (p:Place {name: $name}) "
            "SET p.mcc = $mcc, p.category = $category, p.cashback = $cashback",
            name=p["name"], mcc=p["mcc"], category=p["category"], cashback=p["cashback"]
        )

    # Создаем связи транзакций
    for t in transactions:
        session.run(
            "MATCH (u:User {id: $uid}), (p:Place {name: $pname}) "
            "MERGE (u)-[r:HAS_TRANSACTION]->(p) "
            "SET r.amount = $amount, r.count = $count",
            uid=t["user_id"], pname=t["place_name"], amount=t["amount"], count=t["count"]
        )

print("Пользователи, места и транзакции созданы!")