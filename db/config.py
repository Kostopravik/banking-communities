"""Общие настройки подключения к БД для скриптов заполнения."""
import os

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "banking")
POSTGRES_USER = os.getenv("POSTGRES_USER", "bank")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "bankpass")


NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "mystrongpass")

