"""
Полное заполнение PostgreSQL и Neo4j согласованными id пользователей (1-6).

Из корня проекта (с установленными зависимостями из backend/requirements.txt):
  python db/seed_all.py

Переменные окружения: см. db/config.py (POSTGRES_*, NEO4J_*).
Внутри Docker-сети: POSTGRES_HOST=postgres, NEO4J_URI=bolt://neo4j:7687
На хосте: POSTGRES_HOST=localhost, NEO4J_URI=bolt://localhost:7687
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from seed_neo4j import seed as seed_neo
from seed_postgres import seed as seed_pg


def main() -> None:
    seed_pg()
    seed_neo()


if __name__ == "__main__":
    main()
    
