
import pytest

from memory.short_term import ShortTermMemory
from memory.episodic import EpisodicMemory


def test_short_term_memory_stores_goal():
    memory = ShortTermMemory(max_messages=3)

    memory.set_goal("Organize DAT404 assignment files")

    assert memory.current_goal == "Organize DAT404 assignment files"


def test_short_term_memory_stores_messages():
    memory = ShortTermMemory(max_messages=3)

    memory.add_message("user", "Create a project folder.")
    memory.add_message("agent", "I will create the folder.")

    context = memory.get_context()

    assert "Create a project folder." in str(context)
    assert "I will create the folder." in str(context)


def test_short_term_memory_respects_message_limit():
    memory = ShortTermMemory(max_messages=3)

    memory.add_message("user", "Message 1")
    memory.add_message("agent", "Message 2")
    memory.add_message("tool", "Message 3")
    memory.add_message("agent", "Message 4")

    context = str(memory.get_context())

    assert "Message 4" in context
    assert "Message 1" not in context


def test_episodic_memory_saves_and_retrieves_experience(tmp_path):
    database_path = tmp_path / "test_memory.db"
    memory = EpisodicMemory(db_path=database_path)

    history = [
        {
            "step_id": 1,
            "tool": "create_folder",
            "status": "success"
        }
    ]

    try:
        memory.save_experience(
            goal="Create a DAT404 project folder",
            status="success",
            execution_history=history
        )

        experiences = memory.get_recent_experiences()

        assert len(experiences) == 1
        assert experiences[0]["goal"] == "Create a DAT404 project folder"
        assert experiences[0]["status"] == "success"

    finally:
        memory.close()


def test_episodic_memory_starts_empty(tmp_path):
    database_path = tmp_path / "empty_memory.db"
    memory = EpisodicMemory(db_path=database_path)

    try:
        experiences = memory.get_recent_experiences()

        assert experiences == []

    finally:
        memory.close()
