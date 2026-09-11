from decimal import Decimal
from types import SimpleNamespace

from app.services.analytics_service import AnalyticsService
from app.services.exam_service import ExamService


def test_mcq_scoring_requires_the_answer_key() -> None:
    question = SimpleNamespace(question_type="mcq", correct_answer="A")

    assert ExamService._is_correct(question, "A")
    assert not ExamService._is_correct(question, "B")
    assert not ExamService._is_correct(question, None)


def test_numerical_scoring_accepts_five_percent_boundary_only_with_matching_unit() -> None:
    question = SimpleNamespace(question_type="numerical", correct_answer="100 m")

    assert ExamService._is_correct(question, "105 m")
    assert not ExamService._is_correct(question, "105.01 m")
    assert not ExamService._is_correct(question, "104 cm")


def test_numerical_scoring_accepts_shared_parser_formats() -> None:
    assert ExamService._is_correct(SimpleNamespace(question_type="numerical", correct_answer="2.5e1 %"), "25 %")
    assert ExamService._is_correct(SimpleNamespace(question_type="numerical", correct_answer="1/2 m"), "0.5 m")
    assert ExamService._is_correct(SimpleNamespace(question_type="numerical", correct_answer="10 m/s^2"), "10 m/s^2")


def test_numerical_scoring_rejects_invalid_fraction_and_unit() -> None:
    question = SimpleNamespace(question_type="numerical", correct_answer="1/2 m")

    assert not ExamService._is_correct(question, "1/0 m")
    assert not ExamService._is_correct(question, "0.5 s")


def test_missing_numerical_answer_is_incorrect() -> None:
    assert not ExamService._is_correct(SimpleNamespace(question_type="numerical", correct_answer="0"), None)


def test_topic_performance_status_boundaries() -> None:
    assert AnalyticsService.status_for(Decimal("59.99")) == "needs_practice"
    assert AnalyticsService.status_for(Decimal("60.00")) == "good"
    assert AnalyticsService.status_for(Decimal("79.99")) == "good"
    assert AnalyticsService.status_for(Decimal("80.00")) == "strong"