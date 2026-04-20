import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

backend_path = str(Path(__file__).parent.parent)
sys.path.insert(0, backend_path)

os.environ["JWT_SECRET"] = "test-secret-key"
os.environ["JWT_EXPIRE_HOURS"] = "24"

# Мокаем Neo4j ДО импорта app
_mock_neo4j_driver = MagicMock()
_mock_neo4j_session = MagicMock()
_mock_neo4j_session.__enter__.return_value = _mock_neo4j_session
_mock_neo4j_session.__exit__.return_value = False

_mock_result = MagicMock()
_mock_result.single.return_value = {"total": 10, "cnt": 10}
_mock_neo4j_session.run.return_value = _mock_result
_mock_neo4j_driver.session.return_value = _mock_neo4j_session

# Патчим get_connection до импорта app - но создаем фабрику для моков
with patch("neo4j.GraphDatabase.driver", return_value=_mock_neo4j_driver):
    from app.main import app

# Подменяем драйверы в модулях приложения
sys.modules["app.db"].neo4j_driver = _mock_neo4j_driver
sys.modules["app.main"].neo4j_driver = _mock_neo4j_driver


@pytest.fixture
def mock_postgres():
    """Создает свежий мок для PostgreSQL для каждого теста"""
    mock_cursor = MagicMock()
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.close = MagicMock()
    mock_conn.commit = MagicMock()
    mock_conn.rollback = MagicMock()
    
    # Патчим get_connection только для этого теста
    with patch("app.main.get_connection", return_value=mock_conn), \
         patch("app.auth.get_connection", return_value=mock_conn), \
         patch("app.db_postgres.get_connection", return_value=mock_conn):
        yield mock_conn, mock_cursor


@pytest.fixture
def mock_neo4j():
    """Возвращает мок для Neo4j сессии"""
    yield _mock_neo4j_session


@pytest.fixture
def test_user():
    """Тестовый пользователь"""
    return {"id": 1, "first_name": "Иван", "last_name": "Петров", "login": "ivan.petrov"}


@pytest.fixture
def auth_headers(test_user):
    """Заголовки с авторизацией"""
    from app.auth import create_access_token
    token = create_access_token(test_user["id"], test_user["login"])
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def override_auth(test_user):
    """Переопределяет get_current_user для тестов, где нужна аутентификация"""
    from app.auth import get_current_user
    original = app.dependency_overrides.get(get_current_user)
    app.dependency_overrides[get_current_user] = lambda: test_user
    yield
    if original:
        app.dependency_overrides[get_current_user] = original
    else:
        del app.dependency_overrides[get_current_user]