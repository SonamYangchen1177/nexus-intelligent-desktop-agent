
from uuid import uuid4

import agent.decision_maker as decision_maker

from config import WORKSPACE
from memory.episodic import EpisodicMemory
from agent.planner import PlanStep, ExecutionPlan
from agent.decision_maker import AgentController


def test_agent_memory_integration(tmp_path, monkeypatch):

    # Use a temporary database to protect the real memory database.
    database_path = tmp_path / "integration_memory.db"

    monkeypatch.setattr(
        decision_maker,
        "EpisodicMemory",
        lambda: EpisodicMemory(db_path=database_path)
    )

    controller = AgentController()

    folder_name = "memory_test_" + uuid4().hex[:10]
    folder_path = WORKSPACE / folder_name

    try:
        # Create a two-step execution plan.
        plan = ExecutionPlan(
            goal="Create a folder and verify its existence.",
            reasoning="Create a folder and then verify it.",
            steps=[
                PlanStep(
                    step_id=1,
                    description="Create a test folder",
                    tool="create_folder",
                    parameters={
                        "folder_path": folder_name
                    }
                ),
                PlanStep(
                    step_id=2,
                    description="Verify the folder",
                    tool="verify_files",
                    parameters={
                        "paths": [folder_name]
                    }
                )
            ]
        )

        # Execute the plan through the agent controller.
        result = controller.execute_plan(plan)

        # Check the overall execution result.
        assert isinstance(result, dict)
        assert result["overall_status"] == "success"
        assert result["completed_steps"] == 2
        assert result["failed_steps"] == 0

        # Check that both steps succeeded.
        history = result["execution_history"]

        assert len(history) == 2
        assert all(
            step["status"] == "success"
            for step in history
        )

        # Check that the folder was actually created.
        assert folder_path.is_dir()

        # Check short-term memory.
        memory_context = controller.get_memory_context()

        assert memory_context is not None
        assert "Create a folder" in str(memory_context)

        # Check episodic memory.
        experiences = controller.get_previous_experiences()

        assert len(experiences) > 0

        assert any(
            experience["goal"] == plan.goal
            for experience in experiences
        )

    finally:
        # Remove the test folder and close the controller.
        if folder_path.exists():
            import shutil
            shutil.rmtree(folder_path)

        controller.close()
