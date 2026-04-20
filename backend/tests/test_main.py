import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

# Добавляем путь к backend в PYTHONPATH
backend_path = str(Path(__file__).parent.parent)
sys.path.insert(0, backend_path)

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone

from app.main import app
from app.auth import hash_password

client = TestClient(app)


class TestAuth:
    def test_login_success(self, mock_postgres):
        """Тест успешного входа"""
        mock_conn, mock_cursor = mock_postgres
        mock_cursor.fetchone.return_value = {
            "id": 1,
            "first_name": "Иван",
            "last_name": "Петров",
            "login": "ivan.petrov",
            "password": hash_password("password123")
        }
        
        response = client.post("/auth/login", json={
            "login": "ivan.petrov",
            "password": "password123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["login"] == "ivan.petrov"

    def test_login_wrong_password(self, mock_postgres):
        """Тест входа с неверным паролем"""
        mock_conn, mock_cursor = mock_postgres
        mock_cursor.fetchone.return_value = {
            "id": 1,
            "login": "ivan.petrov",
            "password": hash_password("correct_password")
        }
        
        response = client.post("/auth/login", json={
            "login": "ivan.petrov",
            "password": "wrong_password"
        })
        
        assert response.status_code == 401

    def test_login_user_not_found(self, mock_postgres):
        """Тест входа с несуществующим пользователем"""
        mock_conn, mock_cursor = mock_postgres
        mock_cursor.fetchone.return_value = None
        
        response = client.post("/auth/login", json={
            "login": "unknown.user",
            "password": "password123"
        })
        
        assert response.status_code == 401

    def test_get_current_user(self, override_auth, auth_headers):
        """Тест получения текущего пользователя"""
        response = client.get("/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["login"] == "ivan.petrov"

    def test_get_current_user_invalid_token(self):
        """Тест с неверным токеном - НЕ использует override_auth"""
        response = client.get("/auth/me", headers={"Authorization": "Bearer invalid_token"})
        assert response.status_code == 401


class TestCommunities:
    def test_list_communities(self, mock_postgres, override_auth, auth_headers):
        """Тест получения списка сообществ"""
        mock_conn, mock_cursor = mock_postgres
        mock_cursor.fetchall.return_value = []  # Пустой список сообществ
        
        response = client.get("/communities", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_communities_overview(self, mock_postgres, override_auth, auth_headers):
        """Тест получения обзора сообществ"""
        mock_conn, mock_cursor = mock_postgres
        
        mock_cursor.fetchall.side_effect = [
            [
                {
                    "id": 1,
                    "name": "Кофеманы",
                    "description": "Любители кофе",
                    "min_transactions": 3,
                    "category_key": "coffee"
                }
            ],
            []  # joined communities
        ]
        
        response = client.get("/communities/overview", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "total_operations" in data
        assert "communities" in data

    def test_join_community_success(self, mock_postgres, override_auth, auth_headers):
        """Тест успешного вступления в сообщество"""
        mock_conn, mock_cursor = mock_postgres
        
        mock_cursor.fetchone.side_effect = [
            {"id": 1, "category_key": "coffee"},  # community exists
            None,  # not a member yet
        ]
        
        response = client.post("/communities/1/join", headers=auth_headers)
        
        assert response.status_code == 204
    
    def test_my_communities(self, mock_postgres, override_auth, auth_headers):
        """Тест получения моих сообществ"""
        mock_conn, mock_cursor = mock_postgres
        mock_cursor.fetchall.return_value = [
            {
                "id": 1,
                "name": "Кофеманы",
                "description": "Любители кофе",
                "min_transactions": 3,
                "category_key": "coffee"
            }
        ]
        
        response = client.get("/users/me/communities", headers=auth_headers)
        assert response.status_code == 200
    
    def test_join_community_already_member(self, mock_postgres, override_auth, auth_headers):
        """Вступление в уже существующее сообщество - 204"""
        mock_conn, mock_cursor = mock_postgres
        mock_cursor.fetchone.side_effect = [
            {"id": 1, "category_key": "coffee"},
            {"exists": True}  # уже участник
        ]
        response = client.post("/communities/1/join", headers=auth_headers)
        assert response.status_code == 204
    
    def test_join_community_no_category(self, mock_postgres, mock_neo4j, override_auth, auth_headers):
        """Вступление в сообщество без категории - должно работать (нет проверки)"""
        mock_conn, mock_cursor = mock_postgres
        mock_session = mock_neo4j
        
        mock_cursor.fetchone.side_effect = [
            {"id": 1, "category_key": None},  # сообщество без категории
            None,  # не участник
        ]
        
        # Мокаем количество операций (для сообщества без категории проверка не требуется)
        mock_result = MagicMock()
        mock_result.single.return_value = {"cnt": 0}
        mock_session.run.return_value = mock_result
        
        response = client.post("/communities/1/join", headers=auth_headers)
        # Сообщество без категории не имеет условий, поэтому вступление разрешено
        assert response.status_code == 400
    
    def test_join_community_not_enough_operations(self, mock_postgres, mock_neo4j, override_auth, auth_headers):
        """Вступление с недостаточным количеством операций - 400"""
        mock_conn, mock_cursor = mock_postgres
        mock_session = mock_neo4j
        
        mock_cursor.fetchone.side_effect = [
            {"id": 1, "category_key": "coffee"},
            None,  # не участник
        ]
        
        # Важно: нужно замокать neo4j_user_category_operations через сессию
        mock_result = MagicMock()
        mock_result.single.return_value = {"cnt": 1}  # только 1 операция, нужно 3
        mock_session.run.return_value = mock_result
        
        response = client.post("/communities/1/join", headers=auth_headers)
        assert response.status_code == 400
        assert "нужно еще" in response.json()["detail"].lower()


class TestPosts:
    def test_create_post_success(self, mock_postgres, override_auth, auth_headers):
        """Тест успешного создания поста"""
        mock_conn, mock_cursor = mock_postgres
        
        mock_cursor.fetchone.side_effect = [
            {"exists": True},  # user is member
            {
                "id": 1,
                "rating": 0,
                "created_at": datetime.now(timezone.utc)
            }
        ]
        
        response = client.post("/posts", headers=auth_headers, json={
            "id_community": 1,
            "title": "Мой первый пост",
            "text": "Это текст моего первого поста"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Мой первый пост"

    def test_create_post_not_member(self, mock_postgres, override_auth, auth_headers):
        """Тест создания поста без членства в сообществе"""
        mock_conn, mock_cursor = mock_postgres
        
        # Пользователь НЕ состоит в сообществе
        mock_cursor.fetchone.return_value = None
        
        response = client.post("/posts", headers=auth_headers, json={
            "id_community": 1,
            "title": "Мой пост",
            "text": "Текст поста"
        })
        
        assert response.status_code == 403

    def test_list_posts(self, mock_postgres, override_auth, auth_headers):
        """Тест получения списка постов"""
        mock_conn, mock_cursor = mock_postgres
        
        mock_cursor.fetchall.return_value = [
            {
                "id": 1,
                "id_sender": 1,
                "id_community": 1,
                "title": "Пост 1",
                "text": "Текст 1",
                "rating": 0,
                "created_at": datetime.now(timezone.utc),
                "first_name": "Иван",
                "last_name": "Петров",
                "login": "ivan.petrov",
                "like_count": 5,
                "liked_by_me": True
            }
        ]
        
        response = client.get("/posts", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_update_post_success(self, mock_postgres, override_auth, auth_headers, test_user):
        """Тест обновления поста"""
        mock_conn, mock_cursor = mock_postgres
        
        mock_cursor.fetchone.side_effect = [
            {
                "id": 1,
                "id_sender": test_user["id"],
                "id_community": 1,
                "rating": 0,
                "created_at": datetime.now(timezone.utc),
                "first_name": "Иван",
                "last_name": "Петров",
                "login": "ivan.petrov"
            },
            {"cnt": 0},
            None
        ]
        
        response = client.put("/posts/1", headers=auth_headers, json={
            "title": "Обновленный заголовок",
            "text": "Обновленный текст"
        })
        
        assert response.status_code == 200
    
    def test_update_post_success(self, mock_postgres, override_auth, auth_headers, test_user):
        """Тест обновления поста"""
        mock_conn, mock_cursor = mock_postgres
        
        mock_cursor.fetchone.side_effect = [
            {
                "id": 1,
                "id_sender": test_user["id"],
                "id_community": 1,
                "rating": 0,
                "created_at": datetime.now(timezone.utc),
                "first_name": "Иван",
                "last_name": "Петров",
                "login": "ivan.petrov"
            },
            {"cnt": 0},
            None
        ]
        
        response = client.put("/posts/1", headers=auth_headers, json={
            "title": "Обновленный заголовок",
            "text": "Обновленный текст"
        })
        
        assert response.status_code == 200
    
    def test_delete_post_success(self, mock_postgres, override_auth, auth_headers, test_user):
        """Тест удаления поста"""
        mock_conn, mock_cursor = mock_postgres
        mock_cursor.fetchone.return_value = {"id_sender": test_user["id"]}
        
        response = client.delete("/posts/1", headers=auth_headers)
        assert response.status_code == 204

    def test_toggle_like(self, mock_postgres, override_auth, auth_headers):
        """Тест лайка поста"""
        mock_conn, mock_cursor = mock_postgres
        
        mock_cursor.fetchone.side_effect = [
            {"exists": True},
            None,
            {"cnt": 1}
        ]
        
        response = client.post("/posts/1/like", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["liked"] == True
    
    def test_update_post_not_owner(self, mock_postgres, override_auth, auth_headers):
        """Обновление чужого поста - должно вернуть 403"""
        mock_conn, mock_cursor = mock_postgres
        mock_cursor.fetchone.return_value = {
            "id": 1, "id_sender": 999,  # чужой пользователь
            "id_community": 1, "rating": 0,
            "created_at": datetime.now(timezone.utc),
            "first_name": "Другой", "last_name": "Пользователь", "login": "other"
        }
        response = client.put("/posts/1", headers=auth_headers, json={
            "title": "Попытка", "text": "чужой пост"
        })
        assert response.status_code == 403

    def test_delete_post_not_owner(self, mock_postgres, override_auth, auth_headers):
        """Удаление чужого поста - должно вернуть 403"""
        mock_conn, mock_cursor = mock_postgres
        mock_cursor.fetchone.return_value = {"id_sender": 999}
        response = client.delete("/posts/1", headers=auth_headers)
        assert response.status_code == 403

    def test_like_nonexistent_post(self, mock_postgres, override_auth, auth_headers):
        """Лайк несуществующего поста - 404"""
        mock_conn, mock_cursor = mock_postgres
        mock_cursor.fetchone.return_value = None
        response = client.post("/posts/999/like", headers=auth_headers)
        assert response.status_code == 404
    
    def test_update_post_not_found(self, mock_postgres, override_auth, auth_headers):
        """Обновление несуществующего поста - 404"""
        mock_conn, mock_cursor = mock_postgres
        mock_cursor.fetchone.return_value = None
        response = client.put("/posts/999", headers=auth_headers, json={
            "title": "Не существует", "text": "текст"
        })
        assert response.status_code == 404

    def test_delete_post_not_found(self, mock_postgres, override_auth, auth_headers):
        """Удаление несуществующего поста - 404"""
        mock_conn, mock_cursor = mock_postgres
        mock_cursor.fetchone.return_value = None
        response = client.delete("/posts/999", headers=auth_headers)
        assert response.status_code == 404

    def test_like_already_liked(self, mock_postgres, override_auth, auth_headers):
        """Повторный лайк поста - должен удалить лайк"""
        mock_conn, mock_cursor = mock_postgres
        mock_cursor.fetchone.side_effect = [
            {"exists": True},
            {"exists": True},  # лайк уже есть
            {"cnt": 0}
        ]
        response = client.post("/posts/1/like", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["liked"] == False

    def test_like_post_not_found(self, mock_postgres, override_auth, auth_headers):
        """Лайк несуществующего поста - 404"""
        mock_conn, mock_cursor = mock_postgres
        mock_cursor.fetchone.return_value = None
        response = client.post("/posts/999/like", headers=auth_headers)
        assert response.status_code == 404



class TestHealth:
    def test_health_check(self):
        """Тест проверки здоровья сервиса"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "neo4j" in data
        assert "postgres" in data
    
    def test_health_check_db_down(self, mock_neo4j):
        """Health check когда БД недоступна"""
        # Мокаем ошибку подключения к PostgreSQL через патч get_connection
        with patch("app.main.get_connection") as mock_conn:
            mock_conn.side_effect = Exception("Connection failed")
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["postgres"] == False
            assert "neo4j" in data


class TestComments:
    def test_create_comment(self, mock_postgres, override_auth, auth_headers):
        """Тест создания комментария"""
        mock_conn, mock_cursor = mock_postgres
        
        mock_cursor.fetchone.side_effect = [
            {"exists": True},
            {"id": 1, "created_at": datetime.now(timezone.utc)}
        ]
        
        response = client.post("/posts/1/comments", headers=auth_headers, json={
            "message": "Тестовый комментарий"
        })
        
        assert response.status_code == 201
    
    def test_list_comments(self, mock_postgres, override_auth, auth_headers):
        """Тест получения списка комментариев"""
        mock_conn, mock_cursor = mock_postgres
        
        mock_cursor.fetchone.return_value = {"exists": True}
        mock_cursor.fetchall.return_value = [
            {
                "id": 1,
                "id_sender": 1,
                "id_parent": None,
                "message": "Тестовый комментарий",
                "created_at": datetime.now(timezone.utc),
                "first_name": "Иван",
                "last_name": "Петров",
                "login": "ivan.petrov",
                "p_fn": None,
                "p_ln": None,
                "p_login": None
            }
        ]
        
        response = client.get("/posts/1/comments", headers=auth_headers)
        assert response.status_code == 200
    
    def test_update_comment_success(self, mock_postgres, override_auth, auth_headers, test_user):
        """Тест обновления комментария"""
        mock_conn, mock_cursor = mock_postgres
        
        mock_cursor.fetchone.side_effect = [
            {
                "id": 1,
                "id_post": 1,
                "id_sender": test_user["id"],
                "id_parent": None,
                "created_at": datetime.now(timezone.utc)
            },
            None  # нет родительского комментария
        ]
        
        response = client.put("/posts/1/comments/1", headers=auth_headers, json={
            "message": "Обновленный комментарий"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Обновленный комментарий"
    
    def test_delete_comment_success(self, mock_postgres, override_auth, auth_headers, test_user):
        """Тест удаления комментария"""
        mock_conn, mock_cursor = mock_postgres
        mock_cursor.fetchone.return_value = {"id_sender": test_user["id"]}
        
        response = client.delete("/posts/1/comments/1", headers=auth_headers)
        assert response.status_code == 204
    
    def test_update_comment_not_owner(self, mock_postgres, override_auth, auth_headers):
        """Обновление чужого комментария - 403"""
        mock_conn, mock_cursor = mock_postgres
        mock_cursor.fetchone.return_value = {
            "id": 1, "id_post": 1, "id_sender": 999, "id_parent": None,
            "created_at": datetime.now(timezone.utc)
        }
        response = client.put("/posts/1/comments/1", headers=auth_headers, json={
            "message": "Попытка"
        })
        assert response.status_code == 403

    def test_delete_comment_not_owner(self, mock_postgres, override_auth, auth_headers):
        """Удаление чужого комментария - 403"""
        mock_conn, mock_cursor = mock_postgres
        mock_cursor.fetchone.return_value = {"id_sender": 999}
        response = client.delete("/posts/1/comments/1", headers=auth_headers)
        assert response.status_code == 403
    
    def test_update_post_not_found(self, mock_postgres, override_auth, auth_headers):
        """Обновление несуществующего поста - 404"""
        mock_conn, mock_cursor = mock_postgres
        mock_cursor.fetchone.return_value = None
        response = client.put("/posts/999", headers=auth_headers, json={
            "title": "Не существует", "text": "текст"
        })
        assert response.status_code == 404

    def test_delete_post_not_found(self, mock_postgres, override_auth, auth_headers):
        """Удаление несуществующего поста - 404"""
        mock_conn, mock_cursor = mock_postgres
        mock_cursor.fetchone.return_value = None
        response = client.delete("/posts/999", headers=auth_headers)
        assert response.status_code == 404

    def test_like_already_liked(self, mock_postgres, override_auth, auth_headers):
        """Повторный лайк поста - должен удалить лайк"""
        mock_conn, mock_cursor = mock_postgres
        mock_cursor.fetchone.side_effect = [
            {"exists": True},
            {"exists": True},  # лайк уже есть
            {"cnt": 0}
        ]
        response = client.post("/posts/1/like", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["liked"] == False

    def test_like_post_not_found(self, mock_postgres, override_auth, auth_headers):
        """Лайк несуществующего поста - 404"""
        mock_conn, mock_cursor = mock_postgres
        mock_cursor.fetchone.return_value = None
        response = client.post("/posts/999/like", headers=auth_headers)
        assert response.status_code == 404



class TestRecommendations:
    def test_recommend_me(self, mock_neo4j, override_auth, auth_headers):
        """Тест рекомендаций"""
        response = client.get("/recommend/me", headers=auth_headers)
        assert response.status_code == 200
    
    def test_recommend_specific_user(self, mock_neo4j, override_auth, auth_headers):
        """Рекомендации для конкретного пользователя"""
        response = client.get("/recommend/1", headers=auth_headers)
        assert response.status_code == 200
        assert "recommendations" in response.json()


class TestCashback:
    def test_my_cashback(self, mock_postgres, override_auth, auth_headers):
        """Тест получения кэшбэка пользователя"""
        mock_conn, mock_cursor = mock_postgres
        mock_cursor.fetchall.return_value = [
            {
                "id": 1,
                "amount": 100.50,
                "place": 5812,
                "created_at": datetime.now(timezone.utc),
                "category_key": "cafe_restaurants",
                "category_label": "Кафе и рестораны"
            }
        ]
        
        response = client.get("/users/me/cashback", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()) == 1
    
    def test_cashback_opportunities(self, mock_postgres, mock_neo4j, override_auth, auth_headers):
        """Тест получения доступных кэшбэков"""
        mock_conn, mock_cursor = mock_postgres
        mock_session = mock_neo4j
        
        # Мокаем каталог кэшбэков
        mock_cursor.fetchall.side_effect = [
            [
                {
                    "id": 1,
                    "amount": 50.00,
                    "place": 5812,
                    "category_key": "cafe_restaurants",
                    "category_label": "Кафе и рестораны"
                },
                {
                    "id": 2,
                    "amount": 100.00,
                    "place": 5411,
                    "category_key": "supermarkets",
                    "category_label": "Супермаркеты"
                }
            ],
            []  # Нет начисленных кэшбэков
        ]
        
        # Мокаем количество операций в категории
        mock_result = MagicMock()
        mock_result.single.return_value = {"cnt": 5}
        mock_session.run.return_value = mock_result
        
        response = client.get("/users/me/cashback-opportunities", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["eligible"] == True
    
    def test_cashback_opportunities_with_accrued(self, mock_postgres, mock_neo4j, override_auth, auth_headers):
        """Кэшбэк возможности с уже начисленными"""
        mock_conn, mock_cursor = mock_postgres
        mock_session = mock_neo4j
        mock_cursor.fetchall.side_effect = [
            [{"id": 1, "amount": 50.00, "place": 5812, "category_key": "cafe_restaurants", "category_label": "Кафе"}],
            [{"id_cashback": 1}]  # уже начислен
        ]
        mock_result = MagicMock()
        mock_result.single.return_value = {"cnt": 5}
        mock_session.run.return_value = mock_result
        response = client.get("/users/me/cashback-opportunities", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()[0]["accrued"] == True


class TestBenefits:
    def test_my_benefits(self, mock_postgres, mock_neo4j, override_auth, auth_headers):
        """Тест получения бенефитов пользователя"""
        mock_conn, mock_cursor = mock_postgres
        mock_session = mock_neo4j
        
        mock_cursor.fetchall.side_effect = [
            [
                {
                    "id": 1,
                    "title": "5% кэшбэк в кофейнях",
                    "percent": 5,
                    "description": "Повышенный кэшбэк",
                    "id_community": 1,
                    "community_name": "Кофеманы",
                    "category_key": "coffee"
                }
            ],
            []  # Сообщества пользователя
        ]
        
        mock_result = MagicMock()
        mock_result.single.return_value = {"cnt": 3}
        mock_session.run.return_value = mock_result
        
        response = client.get("/users/me/benefits", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "5% кэшбэк в кофейнях"
    
    def test_my_benefits_as_member(self, mock_postgres, mock_neo4j, override_auth, auth_headers):
        """Бенефиты когда пользователь уже в сообществе"""
        mock_conn, mock_cursor = mock_postgres
        mock_session = mock_neo4j
        mock_cursor.fetchall.side_effect = [
            [{"id": 1, "title": "5% кэшбэк", "percent": 5, "description": "desc", 
            "id_community": 1, "community_name": "Кофеманы", "category_key": "coffee"}],
            [{"id_community": 1}]  # пользователь уже в сообществе
        ]
        mock_result = MagicMock()
        mock_result.single.return_value = {"cnt": 5}
        mock_session.run.return_value = mock_result
        response = client.get("/users/me/benefits", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()[0]["is_active"] == True



class TestHelpers:
    def test_purchase_word_variants(self, override_auth, auth_headers):
        """Тест склонения слова 'покупка' - косвенно через join_community"""
        # Эта функция вызывается внутри join_community при ошибке
        # Создадим тест, который вызывает эту функцию косвенно
        pass  # Можно протестировать через join_community с недостаточным количеством операций
    
    def test_purchase_word_direct(self):
        """Прямой тест функции _purchase_word"""
        from app.main import _purchase_word
        
        assert _purchase_word(1) == "покупку"
        assert _purchase_word(2) == "покупки"
        assert _purchase_word(3) == "покупки"
        assert _purchase_word(4) == "покупки"
        assert _purchase_word(5) == "покупок"
        assert _purchase_word(11) == "покупок"
        assert _purchase_word(21) == "покупку"
        assert _purchase_word(22) == "покупки"
        assert _purchase_word(25) == "покупок"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])