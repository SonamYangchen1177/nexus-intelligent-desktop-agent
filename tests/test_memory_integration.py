
from datetime import datetime

from agent.planner import PlanStep, ExecutionPlan
from agent.decision_maker import AgentController


def main():

    controller = AgentController()

    try:

        # Generate a unique folder name for this test
        folder_name = (
            "memory_test_"
            + datetime.now().strftime("%Y%m%d_%H%M%S")
        )

        plan = ExecutionPlan(
            goal="Create a folder and verify its existence.",
            reasoning="Create a folder and check the result.",
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

        print("\nTESTING MEMORY INTEGRATION")
        print("=" * 45)

        history = controller.execute_plan(plan)

        print("\nSHORT-TERM MEMORY")
        print("=" * 45)

        print(controller.get_memory_context())

        print("\nEPISODIC MEMORY")
        print("=" * 45)

        experiences = (
            controller.get_previous_experiences()
        )

        for experience in experiences:
            print(experience)

        print("\nEXECUTION RESULTS")
        print("=" * 45)

        for record in history:
            print(
                f"Step {record['step_id']}: "
                f"{record['status']}"
            )

    finally:
        controller.close()


if __name__ == "__main__":
    main()
