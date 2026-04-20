# tests/test_listening_module.py

import pytest
from unittest.mock import MagicMock, patch
from app.models.assessments_status import CEFRLevel
from app.services.listening_question_service import (
    evaluate_answers_batch,
    generate_passage,
    generate_questions_from_passage,
    generate_listening_module,
)
from app.services.cefr_grading_service import CEFRGradingService, GradingResult


# ── Fixtures ──────────────────────────────────────────────────────────────────

MOCK_PASSAGE = "The Amazon rainforest is home to millions of species. It covers much of Brazil."

MOCK_QUESTIONS = [
    {
        "id": 1,
        "cefr_level": "A2",
        "question": "Where is the Amazon rainforest located?",
        "options": {"A": "Africa", "B": "Brazil", "C": "India", "D": "China"},
        "correct_option": "B",
    },
    {
        "id": 2,
        "cefr_level": "B1",
        "question": "What is the Amazon rainforest known for?",
        "options": {"A": "Deserts", "B": "Snow", "C": "Millions of species", "D": "Oceans"},
        "correct_option": "C",
    },
    {
        "id": 3,
        "cefr_level": "B2",
        "question": "Which continent contains the Amazon rainforest?",
        "options": {"A": "Asia", "B": "Europe", "C": "South America", "D": "Australia"},
        "correct_option": "C",
    },
]

MOCK_GRADING = GradingResult(
    cefr_level="B1",
    ability_score=0.75,
    accuracy_by_level={"A1": 0.0, "A2": 1.0, "B1": 0.5, "B2": 0.0, "C1": 0.0, "C2": 0.0},
)


# ── generate_passage ──────────────────────────────────────────────────────────

class TestGeneratePassage:

    @patch("app.services.listening_question_service.get_chat_llm")
    def test_returns_passage_on_success(self, mock_llm):
        mock_response = MagicMock()
        mock_response.content = f"  {MOCK_PASSAGE}  "
        mock_llm.return_value.invoke.return_value = mock_response

        result = generate_passage("medium")

        assert result == MOCK_PASSAGE
        mock_llm.return_value.invoke.assert_called_once()

    @patch("app.services.listening_question_service.get_chat_llm")
    def test_returns_fallback_on_exception(self, mock_llm):
        mock_llm.return_value.invoke.side_effect = Exception("LLM down")

        result = generate_passage("medium")

        assert result == "The sun rises in the east and sets in the west."

    @patch("app.services.listening_question_service.get_chat_llm")
    def test_difficulty_injected_into_prompt(self, mock_llm):
        mock_response = MagicMock()
        mock_response.content = MOCK_PASSAGE
        mock_llm.return_value.invoke.return_value = mock_response

        generate_passage("hard")

        call_args = mock_llm.return_value.invoke.call_args
        prompt_content = call_args[0][0][0].content
        assert "hard" in prompt_content


# ── generate_questions_from_passage ──────────────────────────────────────────

class TestGenerateQuestions:

    @patch("app.services.listening_question_service.get_chat_llm")
    def test_returns_valid_mcq_list(self, mock_llm):
        import json
        mock_response = MagicMock()
        mock_response.content = json.dumps(MOCK_QUESTIONS)
        mock_llm.return_value.invoke.return_value = mock_response

        result = generate_questions_from_passage(MOCK_PASSAGE, num_questions=3)

        assert len(result) == 3
        for q in result:
            assert "options" in q
            assert "correct_option" in q
            assert "cefr_level" in q
            assert set(q["options"].keys()) == {"A", "B", "C", "D"}

    @patch("app.services.listening_question_service.get_chat_llm")
    def test_returns_fallback_on_llm_failure(self, mock_llm):
        mock_llm.return_value.invoke.side_effect = Exception("timeout")

        result = generate_questions_from_passage(MOCK_PASSAGE, num_questions=3)

        assert len(result) == 3
        assert all("options" in q for q in result)
        assert all("correct_option" in q for q in result)

    @patch("app.services.listening_question_service.get_chat_llm")
    def test_raises_on_missing_mcq_fields(self, mock_llm):
        import json
        # Questions missing options/correct_option → should trigger retry → fallback
        bad_questions = [{"id": 1, "question": "What?"}]
        mock_response = MagicMock()
        mock_response.content = json.dumps(bad_questions)
        mock_llm.return_value.invoke.return_value = mock_response

        result = generate_questions_from_passage(MOCK_PASSAGE, num_questions=1)

        # Should fall back gracefully
        assert len(result) == 1
        assert "options" in result[0]

    @patch("app.services.listening_question_service.get_chat_llm")
    def test_num_questions_respected_in_fallback(self, mock_llm):
        mock_llm.return_value.invoke.side_effect = Exception("fail")

        result = generate_questions_from_passage(MOCK_PASSAGE, num_questions=5)

        assert len(result) == 5


# ── evaluate_answers_batch ────────────────────────────────────────────────────

class TestEvaluateAnswersBatch:

    def _make_answers(self, selections: list[tuple]) -> list[dict]:
        """selections = [(question_id, selected, correct, cefr_level)]"""
        return [
            {
                "question_id":     qid,
                "question":        f"Question {qid}",
                "selected_option": selected,
                "correct_option":  correct,
                "cefr_level":      CEFRLevel(level),
            }
            for qid, selected, correct, level in selections
        ]

    @patch("app.services.listening_question_service.CEFRGradingService")
    def test_all_correct(self, mock_grading_cls):
        mock_grading_cls.return_value.grade.return_value = MOCK_GRADING
        answers = self._make_answers([
            (1, "B", "B", "A2"),
            (2, "C", "C", "B1"),
            (3, "C", "C", "B2"),
        ])

        result = evaluate_answers_batch(MOCK_PASSAGE, answers)

        assert all(r["correct"] for r in result["results"])
        assert "Correct" in result["results"][0]["feedback"]

    @patch("app.services.listening_question_service.CEFRGradingService")
    def test_all_wrong(self, mock_grading_cls):
        mock_grading_cls.return_value.grade.return_value = MOCK_GRADING
        answers = self._make_answers([
            (1, "A", "B", "A2"),
            (2, "A", "C", "B1"),
            (3, "A", "C", "B2"),
        ])

        result = evaluate_answers_batch(MOCK_PASSAGE, answers)

        assert not any(r["correct"] for r in result["results"])
        assert "Incorrect" in result["results"][0]["feedback"]

    @patch("app.services.listening_question_service.CEFRGradingService")
    def test_feedback_mentions_correct_answer(self, mock_grading_cls):
        mock_grading_cls.return_value.grade.return_value = MOCK_GRADING
        answers = self._make_answers([(1, "A", "B", "A2")])

        result = evaluate_answers_batch(MOCK_PASSAGE, answers)

        assert "B" in result["results"][0]["feedback"]

    @patch("app.services.listening_question_service.CEFRGradingService")
    def test_grading_result_shape(self, mock_grading_cls):
        mock_grading_cls.return_value.grade.return_value = MOCK_GRADING
        answers = self._make_answers([(1, "B", "B", "A2")])

        result = evaluate_answers_batch(MOCK_PASSAGE, answers)

        assert "grading" in result
        assert "cefr_level" in result["grading"]
        assert "ability_score" in result["grading"]
        assert "accuracy_by_level" in result["grading"]

    @patch("app.services.listening_question_service.CEFRGradingService")
    def test_attempts_passed_to_grading_service(self, mock_grading_cls):
        mock_grading_cls.return_value.grade.return_value = MOCK_GRADING
        answers = self._make_answers([
            (1, "B", "B", "A2"),
            (2, "A", "C", "B1"),
        ])

        evaluate_answers_batch(MOCK_PASSAGE, answers)

        call_args = mock_grading_cls.return_value.grade.call_args[0][0]
        assert len(call_args) == 2
        assert call_args[0]["is_correct"] is True
        assert call_args[1]["is_correct"] is False


# ── generate_listening_module ─────────────────────────────────────────────────

class TestGenerateListeningModule:

    @patch("app.services.listening_question_service.text_to_speech")
    @patch("app.services.listening_question_service.generate_questions_from_passage")
    @patch("app.services.listening_question_service.generate_passage")
    def test_returns_complete_module(self, mock_passage, mock_questions, mock_tts):
        mock_passage.return_value = MOCK_PASSAGE
        mock_questions.return_value = MOCK_QUESTIONS
        mock_tts.return_value = "/static/audio/test.mp3"

        result = generate_listening_module(difficulty="medium", num_questions=3)

        assert "session_id" in result
        assert result["passage"] == MOCK_PASSAGE
        assert result["audio_url"] == "/static/audio/test.mp3"
        assert len(result["listening_questions"]) == 3

    @patch("app.services.listening_question_service.text_to_speech")
    @patch("app.services.listening_question_service.generate_questions_from_passage")
    @patch("app.services.listening_question_service.generate_passage")
    def test_fallback_audio_url_on_tts_failure(self, mock_passage, mock_questions, mock_tts):
        mock_passage.return_value = MOCK_PASSAGE
        mock_questions.return_value = MOCK_QUESTIONS
        mock_tts.return_value = None  # TTS failed

        result = generate_listening_module()

        assert result["audio_url"] == "/static/audio/fallback_passage.mp3"

    @patch("app.services.listening_question_service.text_to_speech")
    @patch("app.services.listening_question_service.generate_questions_from_passage")
    @patch("app.services.listening_question_service.generate_passage")
    def test_session_id_is_valid_uuid(self, mock_passage, mock_questions, mock_tts):
        import uuid
        mock_passage.return_value = MOCK_PASSAGE
        mock_questions.return_value = MOCK_QUESTIONS
        mock_tts.return_value = "/audio/test.mp3"

        result = generate_listening_module()

        uuid.UUID(result["session_id"])  # raises if invalid

    @patch("app.services.listening_question_service.text_to_speech")
    @patch("app.services.listening_question_service.generate_questions_from_passage")
    @patch("app.services.listening_question_service.generate_passage")
    def test_fallback_module_on_exception(self, mock_passage, mock_questions, mock_tts):
        mock_passage.side_effect = Exception("total failure")

        result = generate_listening_module()

        assert "session_id" in result
        assert result["audio_url"] == "/static/audio/fallback_passage.mp3"
        assert len(result["listening_questions"]) == 1