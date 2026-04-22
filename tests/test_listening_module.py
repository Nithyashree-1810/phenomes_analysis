import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from contextlib import asynccontextmanager

from app.main import app
from app.db.session import get_db

# ==========================================
# MOCK LIFESPAN — prevent Whisper from loading
# ==========================================

@asynccontextmanager
async def mock_lifespan(app):
    yield  # skip all startup/shutdown side effects

app.router.lifespan_context = mock_lifespan


# ==========================================
# MOCK DATA
# ==========================================

MOCK_MODULE_RESPONSE = {
    "session_id": "sess-123",
    "passage": "A sample listening passage.",
    "audio_url": "/audio/test.mp3",
    "listening_questions": [
        {
            "id": 1,
            "cefr_level": "B1",
            "question": "What is spoken?",
            "options": {"A": "Test", "B": "Unit", "C": "Check", "D": "None"},
            "correct_option": "A",
        }
    ],
}

MOCK_EVAL_RESULT = {
    "results": [
        {"question_id": 1, "correct": True, "feedback": "Correct!"}
    ],
    "grading": {
        "cefr_level": "B1",
        "ability_score": 0.88,
        "accuracy_by_level": {"B1": 1.0},
    },
}


# ==========================================
# HELPERS
# ==========================================

def make_mock_db():
    """Fresh MagicMock db for each test."""
    return MagicMock()


def db_override(mock_db):
    """FastAPI dependency override that yields mock_db."""
    def _override():
        yield mock_db
    return _override


# ==========================================
# GET /listening/module
# ==========================================

@patch("app.routes.listening_route.generate_listening_module")
def test_get_listening_module_success(mock_generate):
    mock_db = make_mock_db()
    app.dependency_overrides[get_db] = db_override(mock_db)
    mock_generate.return_value = MOCK_MODULE_RESPONSE

    try:
        with TestClient(app) as client:
            response = client.get("/listening/module")

        assert response.status_code == 200
        data = response.json()

        assert "correct_option" not in data["listening_questions"][0]
        assert data["session_id"] == "sess-123"
        assert isinstance(data["listening_questions"], list)
        assert mock_db.add.called
        assert mock_db.commit.called
    finally:
        app.dependency_overrides.clear()


def test_get_listening_module_invalid_difficulty():
    with TestClient(app) as client:
        response = client.get("/listening/module?difficulty=wrong")
    assert response.status_code == 422


def test_get_listening_module_invalid_num_questions():
    with TestClient(app) as client:
        response = client.get("/listening/module?num_questions=99")
    assert response.status_code == 422


# ==========================================
# POST /listening/evaluate
# ==========================================

@patch("app.routes.listening_route.evaluate_answers_batch")
def test_evaluate_success(mock_evaluate):
    mock_db = make_mock_db()
    mock_db.query.return_value.filter.return_value.first.return_value = MagicMock(
        session_id="sess-123",
        passage="A sample passage",
        questions=MOCK_MODULE_RESPONSE["listening_questions"],
        results=None,
        cefr_level=None,
        ability_score=None,
        accuracy_by_level=None,
    )
    mock_evaluate.return_value = MOCK_EVAL_RESULT
    app.dependency_overrides[get_db] = db_override(mock_db)

    payload = {
        "session_id": "sess-123",
        "answers": [{"question_id": 1, "selected_option": "A"}],
    }

    try:
        with TestClient(app) as client:
            response = client.post("/listening/evaluate", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["grading"]["cefr_level"] == "B1"
        assert data["results"][0]["correct"] is True
        assert mock_db.commit.called
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def client_with_mock_db():
    """Reusable fixture: yields (client, mock_db)."""
    mock_db = make_mock_db()
    app.dependency_overrides[get_db] = db_override(mock_db)
    with TestClient(app) as client:
        yield client, mock_db
    app.dependency_overrides.clear()


def test_evaluate_session_not_found(client_with_mock_db):
    client, mock_db = client_with_mock_db
    mock_db.query.return_value.filter.return_value.first.return_value = None

    payload = {
        "session_id": "invalid",
        "answers": [{"question_id": 1, "selected_option": "A"}],
    }
    response = client.post("/listening/evaluate", json=payload)

    assert response.status_code == 404
    assert response.json()["detail"] == "Listening session not found."


def test_evaluate_invalid_question_id(client_with_mock_db):
    client, mock_db = client_with_mock_db
    mock_db.query.return_value.filter.return_value.first.return_value = MagicMock(
        session_id="sess-123",
        passage="Test",
        questions=MOCK_MODULE_RESPONSE["listening_questions"],
    )

    payload = {
        "session_id": "sess-123",
        "answers": [{"question_id": 99, "selected_option": "A"}],
    }
    response = client.post("/listening/evaluate", json=payload)

    assert response.status_code == 422
    assert "not found in session" in response.json()["detail"]


def test_evaluate_invalid_option_format():
    with TestClient(app) as client:
        payload = {
            "session_id": "sess-123",
            "answers": [{"question_id": 1, "selected_option": "Z"}],
        }
        response = client.post("/listening/evaluate", json=payload)
    assert response.status_code == 422


# ==========================================
# FALLBACK / ERROR LOGIC
# ==========================================

@patch("app.routes.listening_route.generate_listening_module")
def test_module_generation_failure(mock_generate):
    mock_generate.side_effect = Exception("LLM crashed")
    mock_db = make_mock_db()
    app.dependency_overrides[get_db] = db_override(mock_db)

    try:
        with TestClient(app) as client:
            response = client.get("/listening/module")
        assert response.status_code == 200
    finally:
        app.dependency_overrides.clear()