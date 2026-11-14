
from memory.short_term import ShortTermMemory
from memory.episodic import EpisodicMemory


def main():

    print("\nTESTING SHORT-TERM MEMORY")
    print("=" * 45)

    short_memory = ShortTermMemory(
        max_messages=3
    )

    short_memory.set_goal(
        "Organize DAT404 assignment files"
    )

    short_memory.add_message(
        "user",
        "Create a project folder."
    )

    short_memory.add_message(
        "agent",
        "I will create the folder."
    )

    short_memory.add_message(
        "tool",
        "Folder created successfully."
    )

    short_memory.add_message(
        "agent",
        "The folder is ready."
    )

    print(short_memory.get_context())

    print("\nTESTING EPISODIC MEMORY")
    print("=" * 45)

    episodic_memory = EpisodicMemory()

    history = [
        {
            "step_id": 1,
            "tool": "create_folder",
            "status": "success"
        }
    ]

    episodic_memory.save_experience(
        goal="Create a DAT404 project folder",
        status="success",
        execution_history=history
    )

    experiences = (
        episodic_memory.get_recent_experiences()
    )

    for experience in experiences:
        print(experience)

    episodic_memory.close()

    print("\nMEMORY TESTS COMPLETED")


if __name__ == "__main__":
    main()
