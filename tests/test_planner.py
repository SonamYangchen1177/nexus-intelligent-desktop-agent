
from agent.planner import TaskPlanner


def main():

    planner = TaskPlanner()

    user_goal = (
        "Organize my DAT404 assignment files. "
        "Create a project folder, find relevant "
        "documents and prepare a progress report."
    )

    print("\nUSER GOAL:")
    print(user_goal)

    print("\nGenerating execution plan...\n")

    try:

        plan = planner.create_plan(user_goal)

        print("GENERATED PLAN")
        print("=" * 50)

        print("Goal:", plan.goal)

        print("\nReasoning:")
        print(plan.reasoning)

        print("\nExecution Steps:")

        for step in plan.steps:

            print(f"\nStep {step.step_id}")
            print("Description:", step.description)
            print("Tool:", step.tool)
            print("Parameters:", step.parameters)

    except Exception as error:

        print("Planning failed:", error)


if __name__ == "__main__":
    main()
