# bank_communities_app

Мобильное приложение (Flutter) + backend (FastAPI) + PostgreSQL + Neo4j.

### Запуск через Docker

#### Что нужно установить

- Docker Desktop (с Docker Compose)
- Flutter SDK 3.x (только для запуска мобильного клиента)

Важно: **PostgreSQL и Neo4j отдельно ставить не нужно** при запуске через Docker.  
Они поднимутся как контейнеры из `docker-compose.yml`.

#### 1) Клонировать репозиторий

`git clone <URL_ВАШЕГО_РЕПО>`

`cd banking-communities-main/banking-communities-main`

#### 2) Поднять backend + базы

`docker compose up -d --build`

#### 3) Заполнить БД тестовыми данными

`docker compose exec backend python /db/seed_all.py`

#### 4) Проверить, что API работает

- Swagger: [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs)
- Health: [http://127.0.0.1:8001/health](http://127.0.0.1:8001/health)

#### 5) Запустить Flutter-клиент

`cd mobile`

`flutter pub get`

`flutter run`

### Тестовые пользователи

- `anna`
- `boris`
- `elena`
- `dmitry`
- `maria`
- `igor`

Пароль для всех: `pass123`

---
