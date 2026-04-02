from fastapi import FastAPI
from app.db import neo4j_driver

app = FastAPI()

@app.get("/recommend/{user_id}")
def recommend(user_id: int):
    recommendations = []
    with neo4j_driver.session() as session:
        result = session.run(
            """
            MATCH (u:User {id:$uid})-[r:HAS_TRANSACTION]->(p:Place)
            WHERE r.count >= 3
            RETURN p.name AS place_name, p.category AS category
            """,
            uid=user_id
        )
        for record in result:
            recommendations.append({
                "place_name": record["place_name"],
                "category": record["category"]
            })
    return {"recommendations": recommendations}