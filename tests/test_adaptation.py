
from pathlib import Path

from agent.adaptation import AdaptiveBehaviour
from memory.episodic import EpisodicMemory
from config import WORKSPACE


def main():

    adaptive = AdaptiveBehaviour()
    memory = EpisodicMemory()

    try:

        print("\nTESTING ADAPTIVE BEHAVIOUR")
        print("=" * 45)

        # Test 1: Existing folder
        folder = WORKSPACE / "test_project"
        folder.mkdir(exist_ok=True)

        original_result = {
            "success": False,
            "message": "Folder already exists.",
            "path": str(folder)
        }

        adapted_result = adaptive.adapt_result(
            "create_folder",
            original_result
        )

        print("\nExisting folder adaptation:")
        print(adapted_result)

        # Test 2: Feedback processing
        feedback = adaptive.process_feedback(
            "Do not recreate folders that already exist."
        )

        memory.save_feedback(
            feedback["feedback"]
        )

        print("\nSaved feedback:")
        print(feedback)

        # Test 3: Retrieve feedback
        print("\nRetrieved feedback:")

        for item in memory.get_recent_feedback():
            print(item)

        # Test 4: Previous experience guidance
        experiences = memory.get_recent_experiences(
            limit=5
        )

        guidance = adaptive.generate_guidance(
            experiences
        )

        print("\nAdaptive guidance:")
        print(guidance)

        print("\nADAPTATION TEST COMPLETED")

    finally:
        memory.close()


if __name__ == "__main__":
    main()
