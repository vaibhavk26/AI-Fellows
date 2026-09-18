import json
from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest
from openai import RateLimitError

from app.agents import generation
from app.agents.generation import parse_generation_response
from app.api.schemas.question import QuestionGenerationRequest
from app.graph.generation import QuestionGenerationWorkflow, WorkflowError


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


def _rate_limit_error() -> RateLimitError:
    request = httpx.Request("POST", "https://example.test/v1/chat/completions")
    response = httpx.Response(429, request=request)
    return RateLimitError("Rate limit reached, try again in 2.5s", response=response, body=None)


class RateLimitModel:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def invoke(self, prompt):
        self.calls += 1
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return type("Response", (), {"content": json.dumps({"questions": item})})()


def test_parse_generation_response_accepts_json_fences():
    response = type("Response", (), {"content": "```json\n{\"questions\": []}\n```"})()

    assert parse_generation_response(response) == []


def test_parse_generation_response_repairs_stray_quoted_brace_between_array_items():
    # Reproduces an observed gpt-oss quirk, confirmed against live output: the real opening
    # brace of the next item gets wrapped in stray quotes, e.g. `}},"{","question_text":...`.
    malformed = (
        '{"questions":[{"question_text":"A","question_type":"numerical","options":null,'
        '"correct_answer":"1 T","expected_answer":"1 T","explanation":"e","learning_objective":"l",'
        '"difficulty":"easy","formula":"I","quantities":{"I":"1 A"}},"{",'
        '"question_text":"B","question_type":"numerical","options":null,'
        '"correct_answer":"2 T","expected_answer":"2 T","explanation":"e","learning_objective":"l",'
        '"difficulty":"easy","formula":"I","quantities":{"I":"2 A"}}]}'
    )
    response = type("Response", (), {"content": malformed})()

    result = parse_generation_response(response)

    assert [item["question_text"] for item in result] == ["A", "B"]


def test_parse_generation_response_recovers_objects_via_brace_scan_fallback():
    # A corruption shape the targeted quote repair does not cover: a bare missing comma
    # between two otherwise well-formed objects. The brace-depth scanner fallback should
    # still recover both items independently.
    malformed = (
        '{"questions":[{"question_text":"A","question_type":"numerical","options":null,'
        '"correct_answer":"1 T","expected_answer":"1 T","explanation":"e","learning_objective":"l",'
        '"difficulty":"easy","formula":"I","quantities":{"I":"1 A"}}'
        '{"question_text":"B","question_type":"numerical","options":null,'
        '"correct_answer":"2 T","expected_answer":"2 T","explanation":"e","learning_objective":"l",'
        '"difficulty":"easy","formula":"I","quantities":{"I":"2 A"}}]}'
    )
    response = type("Response", (), {"content": malformed})()

    result = parse_generation_response(response)

    assert [item["question_text"] for item in result] == ["A", "B"]


def test_parse_generation_response_normalizes_nested_value_unit_quantities():
    response = type("Response", (), {"content": json.dumps({"questions": [{
        "question_text": "Calculate the field.", "question_type": "numerical", "options": None,
        "correct_answer": "1 T", "expected_answer": "1 T", "explanation": "e", "learning_objective": "l",
        "difficulty": "easy", "formula": "I", "quantities": {"I": {"value": 5.0, "unit": "A"}},
    }]})})()

    result = parse_generation_response(response)

    assert result[0]["quantities"] == {"I": "5.0 A"}


def test_generation_prompt_can_exclude_questions_already_in_exam_batch():
    request = QuestionGenerationRequest(
        subject_id=uuid4(), chapter_id=uuid4(), difficulty="easy", question_type="mcq", marks=1,
        number_of_questions=1,
    )

    prompt = generation.build_generation_prompt(request, "Electricity and current", ["What is current?"])

    assert "Do not repeat any of these existing questions" in prompt
    assert "What is current?" in prompt


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


def test_workflow_validates_multiple_distinct_mcqs_in_one_batch():
    request = QuestionGenerationRequest(
        subject_id=uuid4(), chapter_id=uuid4(), difficulty="easy", question_type="mcq", marks=1,
        number_of_questions=3,
    )
    questions = [
        {
            "question_text": f"What is current concept {index}?",
            "options": [
                {"key": "A", "text": "Charge flow"}, {"key": "B", "text": "Mass"},
                {"key": "C", "text": "Heat"}, {"key": "D", "text": "Light"},
            ],
            "correct_answer": "A", "expected_answer": "A", "explanation": "Current is charge flow.",
            "learning_objective": "Define current.", "difficulty": "easy", "question_type": "mcq",
        }
        for index in range(3)
    ]
    workflow = QuestionGenerationWorkflow.__new__(QuestionGenerationWorkflow)
    workflow.request = request

    result = workflow.validate_questions({"request": request, "context": [], "generated": questions})

    assert [item["status"] for item in result["validations"]] == ["validated", "validated", "validated"]


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


def test_workflow_retries_numerical_response_with_unsupported_formula_or_answer_format():
    request = QuestionGenerationRequest(
        subject_id=uuid4(), chapter_id=uuid4(), difficulty="easy", question_type="numerical", marks=1,
        number_of_questions=1,
    )
    workflow = QuestionGenerationWorkflow.__new__(QuestionGenerationWorkflow)
    workflow.request = request
    workflow.model = RetryModel([
        [{
            "question_text": "Find the angle.", "options": None, "correct_answer": "19.5°",
            "expected_answer": "19.5°", "difficulty": "easy", "question_type": "numerical",
            "formula": "arcsin(value)", "quantities": {"value": "0.3333"},
        }],
        [{
            "question_text": "Calculate charge.", "options": None, "correct_answer": "30 C",
            "expected_answer": "30 C", "difficulty": "easy", "question_type": "numerical",
            "formula": "I * t", "quantities": {"I": "2 A", "t": "15 s"},
        }],
    ])

    result = workflow.generate_questions({"request": request, "context": []})

    assert workflow.model.calls == 2
    assert result["generated"][0]["correct_answer"] == "30 c"


def test_numerical_prompt_excludes_unsupported_calculations_and_symbols():
    request = QuestionGenerationRequest(
        subject_id=uuid4(), chapter_id=uuid4(), difficulty="easy", question_type="numerical", marks=1,
        number_of_questions=1,
    )

    prompt = generation.build_generation_prompt(request, "Electricity and current")

    assert "Do not use trigonometric" in prompt
    assert "never symbols such as `×`, `^`, or `°`" in prompt


def test_numerical_prompt_includes_self_consistent_worked_example():
    request = QuestionGenerationRequest(
        subject_id=uuid4(), chapter_id=uuid4(), difficulty="easy", question_type="numerical", marks=1,
        number_of_questions=1,
    )
    mcq_request = QuestionGenerationRequest(
        subject_id=uuid4(), chapter_id=uuid4(), difficulty="easy", question_type="mcq", marks=1,
        number_of_questions=1,
    )

    numerical_prompt = generation.build_generation_prompt(request, "Electricity and current")
    retry_prompt = generation.build_numerical_retry_prompt(request, "Electricity and current", [])
    mcq_prompt = generation.build_generation_prompt(mcq_request, "Electricity and current")

    assert "Worked example" in numerical_prompt
    assert "Worked example" in retry_prompt
    assert "Worked example" not in mcq_prompt


def test_workflow_retries_questions_not_grounded_in_curriculum_context():
    request = QuestionGenerationRequest(
        subject_id=uuid4(), chapter_id=uuid4(), difficulty="easy", question_type="mcq", marks=1,
        number_of_questions=1,
    )
    workflow = QuestionGenerationWorkflow.__new__(QuestionGenerationWorkflow)
    workflow.request = request
    workflow.model = RetryModel([
        [{
            "question_text": "What is photosynthesis?", "options": [
                {"key": "A", "text": "A plant process"}, {"key": "B", "text": "A force"},
                {"key": "C", "text": "A circuit"}, {"key": "D", "text": "A sound"},
            ], "correct_answer": "A", "expected_answer": "A", "explanation": "Plants make food.",
            "learning_objective": "Define photosynthesis.", "difficulty": "easy", "question_type": "mcq",
        }],
        [{
            "question_text": "What does electric current measure?", "options": [
                {"key": "A", "text": "The flow of electric charge"}, {"key": "B", "text": "The mass of a wire"},
                {"key": "C", "text": "The colour of a circuit"}, {"key": "D", "text": "The temperature of light"},
            ], "correct_answer": "A", "expected_answer": "A", "explanation": "Electric current is the flow of charge.",
            "learning_objective": "Define electric current and charge.", "difficulty": "easy", "question_type": "mcq",
        }],
    ])
    context = [SimpleNamespace(text="Electric current is the flow of electric charge through a circuit.")]

    result = workflow.generate_questions({"request": request, "context": context})

    assert workflow.model.calls == 2
    assert result["generated"][0]["question_text"] == "What does electric current measure?"
    assert "at least two meaningful terms" in generation.build_grounding_retry_prompt(request, "electric current", [])


def test_generate_questions_retries_once_on_rate_limit_then_succeeds(monkeypatch):
    request = QuestionGenerationRequest(
        subject_id=uuid4(), chapter_id=uuid4(), difficulty="easy", question_type="mcq", marks=1,
        number_of_questions=1,
    )
    workflow = QuestionGenerationWorkflow.__new__(QuestionGenerationWorkflow)
    workflow.request = request
    workflow.model = RateLimitModel([
        _rate_limit_error(),
        [{
            "question_text": "What is current?", "options": [
                {"key": "A", "text": "Charge flow"}, {"key": "B", "text": "Mass"},
                {"key": "C", "text": "Heat"}, {"key": "D", "text": "Light"},
            ], "correct_answer": "A", "expected_answer": "A", "explanation": "Current is charge flow.",
            "learning_objective": "Define current.", "difficulty": "easy", "question_type": "mcq",
        }],
    ])
    monkeypatch.setattr("app.graph.generation.time.sleep", lambda seconds: None)

    result = workflow.generate_questions({"request": request, "context": []})

    assert workflow.model.calls == 2
    assert result["generated"][0]["question_text"] == "What is current?"


def test_generate_questions_raises_rate_limited_error_after_persistent_rate_limit(monkeypatch):
    request = QuestionGenerationRequest(
        subject_id=uuid4(), chapter_id=uuid4(), difficulty="easy", question_type="mcq", marks=1,
        number_of_questions=1,
    )
    workflow = QuestionGenerationWorkflow.__new__(QuestionGenerationWorkflow)
    workflow.request = request
    workflow.model = RateLimitModel([_rate_limit_error(), _rate_limit_error(), _rate_limit_error()])
    monkeypatch.setattr("app.graph.generation.time.sleep", lambda seconds: None)

    with pytest.raises(WorkflowError) as excinfo:
        workflow.generate_questions({"request": request, "context": []})

    assert excinfo.value.code == "AI_PROVIDER_RATE_LIMITED"
    assert workflow.model.calls == 3


def test_estimate_max_tokens_scales_with_question_type_and_caps_at_setting(monkeypatch):
    monkeypatch.setattr("app.graph.generation.get_settings", lambda: SimpleNamespace(llm_max_tokens=8192))
    mcq_request = QuestionGenerationRequest(
        subject_id=uuid4(), chapter_id=uuid4(), difficulty="easy", question_type="mcq", marks=1,
        number_of_questions=5,
    )
    numerical_request = QuestionGenerationRequest(
        subject_id=uuid4(), chapter_id=uuid4(), difficulty="easy", question_type="numerical", marks=1,
        number_of_questions=10,
    )

    mcq_tokens = QuestionGenerationWorkflow._estimate_max_tokens(mcq_request)
    numerical_tokens = QuestionGenerationWorkflow._estimate_max_tokens(numerical_request)

    assert mcq_tokens < numerical_tokens
    assert numerical_tokens <= 8192