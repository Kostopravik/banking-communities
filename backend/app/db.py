import os

from neo4j import GraphDatabase

#neo4j_driver = GraphDatabase.driver(
#    "bolt://localhost:7687",  
#    auth=("neo4j", "mystrongpass")  # пароль из Docker
#)

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "mystrongpass")

neo4j_driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USER, NEO4J_PASSWORD),
)

