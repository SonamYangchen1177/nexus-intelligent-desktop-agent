
import json
import pytest
import requests

from agent.planner import TaskPlanner
from config import MAX_PLAN_STEPS


# --------------------------------------------------
# MOCK OLLAMA RESPONSE
# --------------------------------------------------

class MockResponse:

    def __init__(self, data):
        self.data = data

    def raise_for_status(self):
        pass

    def json(self):
        return {
            "response": json.dumps(self.data)
        }


def mock_ollama(monkeypatch, plan_data):

    def fake_post(*args, **kwargs):
        return MockResponse(plan_data)

    monkeypatch.setattr(
        "agent.planner.requests.post",
        fake_post
    )


# --------------------------------------------------
# SAMPLE VALID PLAN
# --------------------------------------------------

def valid_plan():

    return {
        "goal": "Create and verify a project folder.",
        "reasoning": "Create the folder and verify its existence.",
        "steps": [
            {
                "step_id": 1,
                "description": "Create project folder",
                "tool": "create_folder",
                "parameters": {
                    "folder_path": "test_project"
                }
            },
            {
                "step_id": 2,
                "description": "Verify project folder",
                "tool": "verify_files",
                "parameters": {
                    "paths": ["test_project"]
                }
            }
        ]
    }


# --------------------------------------------------
# PLAN GENERATION TESTS
# --------------------------------------------------

def test_planner_generates_valid_plan(monkeypatch):

    plan_data = valid_plan()

    mock_ollama(monkeypatch, plan_data)

    planner = TaskPlanner()

    plan = planner.create_plan(
        "Create and verify a project folder."
    )

    assert plan.goal == plan_data["goal"]
    assert len(plan.steps) == 2
    assert plan.steps[0].tool == "create_folder"
    assert plan.steps[1].tool == "verify_files"


def test_planner_uses_sequential_step_ids(monkeypatch):

    plan_data = valid_plan()

    mock_ollama(monkeypatch, plan_data)

    planner = TaskPlanner()

    plan = planner.create_plan("Create a project folder.")

    step_ids = [
        step.step_id for step in plan.steps
    ]

    assert step_ids == [1, 2]


# --------------------------------------------------
# INVALID GOAL TESTS
# --------------------------------------------------

def test_empty_goal_raises_error():

    planner = TaskPlanner()

    with pytest.raises(
        ValueError,
        match="Please provide a task goal"
    ):

        planner.create_plan("")


def test_whitespace_goal_raises_error():

    planner = TaskPlanner()

    with pytest.raises(
        ValueError,
        match="Please provide a task goal"
    ):

        planner.create_plan("   ")


# --------------------------------------------------
# TOOL VALIDATION TESTS
# --------------------------------------------------

def test_invalid_tool_is_rejected(monkeypatch):

    plan_data = valid_plan()

    plan_data["steps"][0]["tool"] = "delete_file"

    mock_ollama(monkeypatch, plan_data)

    planner = TaskPlanner()

    with pytest.raises(Exception):

        planner.create_plan("Create a folder.")


def test_missing_required_parameters_are_rejected(monkeypatch):

    plan_data = valid_plan()

    plan_data["steps"][0]["parameters"] = {}

    mock_ollama(monkeypatch, plan_data)

    planner = TaskPlanner()

    with pytest.raises(
        ValueError,
        match="Missing parameters"
    ):

        planner.create_plan("Create a folder.")


# --------------------------------------------------
# PLAN STRUCTURE VALIDATION
# --------------------------------------------------

def test_empty_execution_plan_is_rejected(monkeypatch):

    plan_data = valid_plan()

    plan_data["steps"] = []

    mock_ollama(monkeypatch, plan_data)

    planner = TaskPlanner()

    with pytest.raises(
        ValueError,
        match="empty execution plan"
    ):

        planner.create_plan("Create a folder.")


def test_non_sequential_step_ids_are_rejected(monkeypatch):

    plan_data = valid_plan()

    plan_data["steps"][1]["step_id"] = 5

    mock_ollama(monkeypatch, plan_data)

    planner = TaskPlanner()

    with pytest.raises(
        ValueError,
        match="sequential"
    ):

        planner.create_plan("Create a folder.")


def test_plan_exceeding_maximum_steps_is_rejected(monkeypatch):

    plan_data = valid_plan()

    plan_data["steps"] = [
        {
            "step_id": index,
            "description": "Create folder",
            "tool": "create_folder",
            "parameters": {
                "folder_path": f"folder_{index}"
            }
        }
        for index in range(1, MAX_PLAN_STEPS + 2)
    ]

    mock_ollama(monkeypatch, plan_data)

    planner = TaskPlanner()

    with pytest.raises(
        ValueError,
        match="maximum"
    ):

        planner.create_plan("Create multiple folders.")


# --------------------------------------------------
# WORKSPACE SAFETY TESTS
# --------------------------------------------------

@pytest.mark.parametrize(
    "folder_path",
    [
        "../outside",
        "../../important",
        "workspace/test_folder"
    ]
)
def test_unsafe_folder_paths_are_rejected(
    monkeypatch,
    folder_path
):

    plan_data = valid_plan()

    plan_data["steps"] = [
        {
            "step_id": 1,
            "description": "Create folder",
            "tool": "create_folder",
            "parameters": {
                "folder_path": folder_path
            }
        }
    ]

    mock_ollama(monkeypatch, plan_data)

    planner = TaskPlanner()

    with pytest.raises(ValueError):

        planner.create_plan("Create a folder.")


def test_absolute_folder_path_is_rejected(monkeypatch):

    plan_data = valid_plan()

    plan_data["steps"] = [
        {
            "step_id": 1,
            "description": "Create folder",
            "tool": "create_folder",
            "parameters": {
                "folder_path": "C:/Users/test/outside"
            }
        }
    ]

    mock_ollama(monkeypatch, plan_data)

    planner = TaskPlanner()

    with pytest.raises(
        ValueError,
        match="Unsafe folder path"
    ):

        planner.create_plan("Create a folder.")


def test_empty_folder_path_is_rejected(monkeypatch):

    plan_data = valid_plan()

    plan_data["steps"][0]["parameters"]["folder_path"] = "   "

    mock_ollama(monkeypatch, plan_data)

    planner = TaskPlanner()

    with pytest.raises(
        ValueError,
        match="cannot be empty"
    ):

        planner.create_plan("Create a folder.")


# --------------------------------------------------
# INVALID JSON TEST
# --------------------------------------------------

def test_invalid_json_response_is_rejected(monkeypatch):

    class InvalidResponse:

        def raise_for_status(self):
            pass

        def json(self):
            return {
                "response": "This is not valid JSON"
            }

    def fake_post(*args, **kwargs):
        return InvalidResponse()

    monkeypatch.setattr(
        "agent.planner.requests.post",
        fake_post
    )

    planner = TaskPlanner()

    with pytest.raises(
        ValueError,
        match="Could not parse"
    ):

        planner.create_plan("Create a project folder.")


# --------------------------------------------------
# OLLAMA CONNECTION ERROR TEST
# --------------------------------------------------

def test_ollama_connection_error_is_handled(monkeypatch):

    def fake_post(*args, **kwargs):

        raise requests.exceptions.ConnectTimeout(
            "Connection timed out"
        )

    monkeypatch.setattr(
        "agent.planner.requests.post",
        fake_post
    )

    planner = TaskPlanner()

    with pytest.raises(
        RuntimeError,
        match="Could not connect to Ollama"
    ):

        planner.create_plan("Create a project folder.")


# --------------------------------------------------
# MEMORY CONTEXT TEST
# --------------------------------------------------

def test_planner_prepares_memory_context():

    planner = TaskPlanner()

    experiences = [
        {"goal": f"Previous task {i}"}
        for i in range(5)
    ]

    feedback = [
        {"feedback": f"Feedback {i}"}
        for i in range(5)
    ]

    experience_context, feedback_context = (
        planner.prepare_memory(
            experiences,
            feedback
        )
    )

    assert "Previous task 2" in experience_context
    assert "Previous task 4" in experience_context
    assert "Previous task 0" not in experience_context

    assert "Feedback 2" in feedback_context
    assert "Feedback 4" in feedback_context
    assert "Feedback 0" not in feedback_context
