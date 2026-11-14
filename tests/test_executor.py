
from agent.planner import TaskPlanner
from agent.decision_maker import AgentController


def main():

    user_goal = (
        "Create a folder called DAT404_Project, "
        "find assignment files in the workspace, "
        "and generate a report about the files found."
    )

    print("\nUSER GOAL:")
    print(user_goal)

    # Generate plan
    planner = TaskPlanner()

    print("\nGenerating plan...")

    plan = planner.create_plan(user_goal)

    print("\nPLAN GENERATED")
    print("=" * 50)

    for step in plan.steps:
        print(step.step_id, step.tool, step.parameters)

    # Execute plan
    controller = AgentController()

    print("\nSTARTING EXECUTION")
    print("=" * 50)

    history = controller.execute_plan(plan)

    print("\nEXECUTION SUMMARY")
    print("=" * 50)

    for record in history:
        print(
            f"Step {record['step_id']}: "
            f"{record['status']}"
        )


if __name__ == "__main__":
    main()
