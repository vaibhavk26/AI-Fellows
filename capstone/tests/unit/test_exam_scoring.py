from types import SimpleNamespace

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