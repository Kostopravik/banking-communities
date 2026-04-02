# Запуск проекта с Neo4j

1. Поднять контейнеры:
   docker-compose up -d

2. Инициализировать базу Neo4j:
   source backend/venv_linux/bin/activate
   python db/init_neo4j_users.py

3. Проверить FastAPI:
   http://127.0.0.1:8001/docs