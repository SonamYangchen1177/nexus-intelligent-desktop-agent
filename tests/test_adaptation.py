
from agent.adaptation import AdaptiveBehaviour


def test_existing_folder_is_adapted(tmp_path):

    adaptive = AdaptiveBehaviour()

    folder = tmp_path / "test_project"
    folder.mkdir()

    original_result = {
        "success": False,
        "message": "Folder already exists.",
        "path": str(folder)
    }

    result = adaptive.adapt_result(
        "create_folder",
        original_result
    )

    assert result["success"] is True
    assert result["adapted"] is True
    assert result["path"] == str(folder)
    assert "already existed" in result["message"]


def test_non_existing_folder_is_not_adapted(tmp_path):

    adaptive = AdaptiveBehaviour()

    folder = tmp_path / "missing_folder"

    original_result = {
        "success": False,
        "message": "Folder already exists.",
        "path": str(folder)
    }

    result = adaptive.adapt_result(
        "create_folder",
        original_result
    )

    assert result == original_result
    assert result["success"] is False


def test_unrelated_tool_result_remains_unchanged():

    adaptive = AdaptiveBehaviour()

    original_result = {
        "success": True,
        "message": "Search completed."
    }

    result = adaptive.adapt_result(
        "search_files",
        original_result
    )

    assert result == original_result


def test_feedback_processing():

    adaptive = AdaptiveBehaviour()

    result = adaptive.process_feedback(
        "  Do not recreate existing folders.  "
    )

    assert result["status"] == "recorded"

    assert result["feedback"] == (
        "Do not recreate existing folders."
    )


def test_empty_feedback_raises_error():

    adaptive = AdaptiveBehaviour()

    try:
        adaptive.process_feedback("   ")
        assert False, "Expected ValueError"

    except ValueError as error:
        assert "Feedback cannot be empty" in str(error)


def test_guidance_without_failures():

    adaptive = AdaptiveBehaviour()

    guidance = adaptive.generate_guidance([])

    assert "No previous failures" in guidance


def test_guidance_from_failed_experience():

    adaptive = AdaptiveBehaviour()

    experiences = [
        {
            "goal": "Create an existing folder",
            "status": "failed",
            "execution_history": [
                {
                    "status": "failed",
                    "result": {
                        "message": "Folder already exists."
                    }
                }
            ]
        }
    ]

    guidance = adaptive.generate_guidance(
        experiences
    )

    assert "Create an existing folder" in guidance
    assert "Folder already exists" in guidance
