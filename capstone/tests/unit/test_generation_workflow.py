import json
from uuid import uuid4

from app.agents.generation import parse_generation_response
from app.api.schemas.question import QuestionGenerationRequest
from app.graph.generation import QuestionGenerationWorkflow


class FakeModel:
    def __init__(self, questions):
        self.questions = questions

    def invoke(self, prompt):
        return type("Response", (), {"content": json.dumps({"questions": self.questions})})()


class RetryModel:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = 0

    def invoke(self, prompt):
        self.calls += 1
        return type("Response", (), {"content": json.dumps({"questions": next(self.responses)})})()


def test_parse_generation_response_accepts_json_fences():
    response = type("Response", (), {"content": "```json\n{\"questions\": []}\n```"})()

    assert parse_generation_response(response) == []


def test_workflow_validates_mcq_and_rejects_duplicate():
    request = QuestionGenerationRequest(
        subject_id=uuid4(), chapter_id=uuid4(), difficulty="easy", question_type="mcq", marks=1,
        number_of_questions=2,
    )
    questions = [{
        "question_text": "What is current?", "options": [
            {"key": "A", "text": "Charge flow"}, {"key": "B", "text": "Mass"},
            {"key": "C", "text": "Heat"}, {"key": "D", "text": "Light"},
        ], "correct_answer": "A", "expected_answer": "A", "explanation": "Current is charge flow.",
        "learning_objective": "Define current.", "difficulty": "easy", "question_type": "mcq",
    }] * 2
    workflow = QuestionGenerationWorkflow.__new__(QuestionGenerationWorkflow)
    workflow.request = request
    workflow.model = FakeModel(questions)

    state = {
        "request": request,
        "context": [],
    }
    result = workflow.validate_questions({**state, "generated": questions})

    assert result["validations"][0]["status"] == "validated"
    assert result["validations"][1]["status"] == "rejected"
    assert "duplicate question" in result["validations"][1]["failure_reasons"]


def test_workflow_rejects_mcq_with_numeric_expected_answer():
    request = QuestionGenerationRequest(
        subject_id=uuid4(), chapter_id=uuid4(), difficulty="easy", question_type="mcq", marks=1,
        number_of_questions=1,
    )
    workflow = QuestionGenerationWorkflow.__new__(QuestionGenerationWorkflow)
    workflow.request = request
    result = workflow.validate_questions({
        "request": request,
        "context": [],
        "generated": [{
            "question_text": "What is the mean?",
            "options": [
                {"key": "A", "text": "59.3"}, {"key": "B", "text": "60"},
                {"key": "C", "text": "61"}, {"key": "D", "text": "62"},
            ],
            "correct_answer": "A", "expected_answer": "59.3", "explanation": "Mean calculation.",
            "learning_objective": "Calculate a mean.", "difficulty": "easy", "question_type": "mcq",
        }],
    })

    assert result["validations"][0]["status"] == "rejected"
    assert "matching answer keys" in result["validations"][0]["failure_reasons"][0]


def test_workflow_accepts_numerical_answer_without_options():
    request = QuestionGenerationRequest(
        subject_id=uuid4(), chapter_id=uuid4(), difficulty="easy", question_type="numerical", marks=1,
        number_of_questions=1,
    )
    workflow = QuestionGenerationWorkflow.__new__(QuestionGenerationWorkflow)
    workflow.request = request
    result = workflow.validate_questions({
        "request": request,
        "context": [],
        "generated": [{
            "question_text": "Calculate the mean.", "options": None, "correct_answer": "59.3",
            "expected_answer": "59.3", "explanation": "Use the mean formula.",
            "learning_objective": "Calculate a mean.", "difficulty": "easy", "question_type": "numerical",
            "formula": "total / count", "quantities": {"total": "1186", "count": "20"},
        }],
    })

    assert result["validations"][0]["status"] == "validated"


def test_workflow_normalizes_groq_keyed_mcq_options():
    request = QuestionGenerationRequest(
        subject_id=uuid4(), chapter_id=uuid4(), difficulty="easy", question_type="mcq", marks=1,
        number_of_questions=1,
    )
    workflow = QuestionGenerationWorkflow.__new__(QuestionGenerationWorkflow)
    workflow.request = request
    options = {"A": "59.3 marks", "B": "60 marks", "C": "58 marks", "D": "57 marks"}
    result = workflow.validate_questions({
        "request": request,
        "context": [],
        "generated": [{
            "question_text": "What is the mean?", "options": options, "correct_answer": "A",
            "expected_answer": "A", "explanation": "Mean calculation.",
            "learning_objective": "Calculate a mean.", "difficulty": "easy", "question_type": "mcq",
        }],
    })

    assert result["validations"][0]["status"] == "validated"


def test_workflow_normalizes_groq_single_key_mcq_options():
    request = QuestionGenerationRequest(
        subject_id=uuid4(), chapter_id=uuid4(), difficulty="easy", question_type="mcq", marks=1,
        number_of_questions=1,
    )
    workflow = QuestionGenerationWorkflow.__new__(QuestionGenerationWorkflow)
    workflow.request = request
    result = workflow.validate_questions({
        "request": request,
        "context": [],
        "generated": [{
            "question_text": "What is the SI unit of current?",
            "options": [{"A": "coulomb"}, {"B": "ampere"}, {"C": "volt"}, {"D": "ohm"}],
            "correct_answer": "B", "expected_answer": "B", "explanation": "Ampere is the SI unit.",
            "learning_objective": "Identify the SI unit of current.", "difficulty": "easy", "question_type": "mcq",
        }],
    })

    assert result["validations"][0]["status"] == "validated"


def test_workflow_accepts_broad_numerical_formats():
    request = QuestionGenerationRequest(
        subject_id=uuid4(), chapter_id=uuid4(), difficulty="easy", question_type="numerical", marks=1,
        number_of_questions=1,
    )
    workflow = QuestionGenerationWorkflow.__new__(QuestionGenerationWorkflow)
    workflow.request = request
    result = workflow.validate_questions({
        "request": request, "context": [], "generated": [{
            "question_text": "Calculate the percentage.", "options": None,
            "correct_answer": "2.5e1 %", "expected_answer": "2.5e1 %",
            "explanation": "Convert the ratio to a percentage.", "learning_objective": "Calculate percentage.",
            "difficulty": "easy", "question_type": "numerical",
            "formula": "value", "quantities": {"value": "25"},
        }],
    })

    assert result["validations"][0]["status"] == "validated"


def test_workflow_normalizes_lowercase_and_unordered_mcq_keys():
    request = QuestionGenerationRequest(
        subject_id=uuid4(), chapter_id=uuid4(), difficulty="easy", question_type="mcq", marks=1,
        number_of_questions=1,
    )
    workflow = QuestionGenerationWorkflow.__new__(QuestionGenerationWorkflow)
    workflow.request = request
    result = workflow.validate_questions({
        "request": request, "context": [], "generated": [{
            "question_text": "Which unit measures current?", "options": [
                {"d": "Ohm"}, {"b": "Ampere"}, {"a": "Volt"}, {"c": "Coulomb"},
            ], "correct_answer": "b", "expected_answer": "b", "explanation": "Ampere measures current.",
            "learning_objective": "Identify a unit.", "difficulty": "easy", "question_type": "mcq",
        }],
    })

    assert result["validations"][0]["status"] == "validated"


def test_workflow_rejects_numerical_question_without_structured_calculation():
    request = QuestionGenerationRequest(
        subject_id=uuid4(), chapter_id=uuid4(), difficulty="easy", question_type="numerical", marks=1,
        number_of_questions=1,
    )
    workflow = QuestionGenerationWorkflow.__new__(QuestionGenerationWorkflow)
    workflow.request = request
    result = workflow.validate_questions({
        "request": request, "context": [], "generated": [{
            "question_text": "Calculate the charge.", "options": None,
            "correct_answer": "144 C", "expected_answer": "144 C",
            "explanation": "Use Q = I * t.", "learning_objective": "Calculate charge.",
            "difficulty": "easy", "question_type": "numerical",
        }],
    })

    assert result["validations"][0]["status"] == "rejected"
    assert "numerical answer requires a safe formula and quantities" in result["validations"][0]["failure_reasons"]


def test_workflow_rejects_numerical_answer_that_disagrees_with_formula():
    request = QuestionGenerationRequest(
        subject_id=uuid4(), chapter_id=uuid4(), difficulty="easy", question_type="numerical", marks=1,
        number_of_questions=1,
    )
    workflow = QuestionGenerationWorkflow.__new__(QuestionGenerationWorkflow)
    workflow.request = request
    result = workflow.validate_questions({
        "request": request, "context": [], "generated": [{
            "question_text": "Calculate the charge.", "options": None,
            "correct_answer": "150 C", "expected_answer": "150 C",
            "explanation": "Use Q = I * t.", "learning_objective": "Calculate charge.",
            "difficulty": "easy", "question_type": "numerical", "formula": "Q = I * t",
            "quantities": {"I": "0.6 A", "t": "4 min"},
        }],
    })

    assert result["validations"][0]["status"] == "rejected"
    assert "calculated result does not match expected answer" in result["validations"][0]["failure_reasons"]


def test_workflow_retries_numerical_response_missing_calculation_fields():
    request = QuestionGenerationRequest(
        subject_id=uuid4(), chapter_id=uuid4(), difficulty="easy", question_type="numerical", marks=1,
        number_of_questions=1,
    )
    workflow = QuestionGenerationWorkflow.__new__(QuestionGenerationWorkflow)
    workflow.request = request
    workflow.model = RetryModel([
        [{
            "question_text": "Calculate charge.", "options": None, "correct_answer": "30 C",
            "expected_answer": "30 C", "difficulty": "easy", "question_type": "numerical",
        }],
        [{
            "question_text": "Calculate charge.", "options": None, "correct_answer": "30 C",
            "expected_answer": "30 C", "difficulty": "easy", "question_type": "numerical",
            "formula": "Q = I * t", "quantities": {"I": "2 A", "t": "15 s"},
        }],
    ])

    result = workflow.generate_questions({
        "request": request,
        "context": [],
    })

    assert workflow.model.calls == 2
    assert result["generated"][0]["formula"] == "Q = I * t"
    assert result["generated"][0]["quantities"] == {"I": "2 A", "t": "15 s"}