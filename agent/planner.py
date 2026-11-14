
import json
import logging
from pathlib import Path, PurePath

import requests
from pydantic import BaseModel, Field
from typing import Literal

from config import (
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    MAX_PLAN_STEPS,
    WORKSPACE
)


logger = logging.getLogger(__name__)


# ==========================================================
# 1. PLAN STRUCTURE
# ==========================================================

class PlanStep(BaseModel):

    step_id: int
    description: str

    tool: Literal[
        "search_files",
        "create_folder",
        "move_file",
        "rename_file",
        "verify_files",
        "generate_report"
    ]

    parameters: dict = Field(default_factory=dict)


class ExecutionPlan(BaseModel):

    goal: str
    reasoning: str
    steps: list[PlanStep]


# ==========================================================
# 2. INTELLIGENT TASK PLANNER
# ==========================================================

class TaskPlanner:

    def __init__(self):

        self.base_url = OLLAMA_BASE_URL.rstrip("/")
        self.model = OLLAMA_MODEL

        # Maximum time allowed for Ollama.
        self.timeout = (10, 300)

    # ======================================================
    # 3. PREPARE MEMORY CONTEXT
    # ======================================================

    def prepare_memory(self, experiences, feedback):

        experience_context = json.dumps(
            experiences[-3:],
            ensure_ascii=False,
            default=str
        )[:1000]

        feedback_context = json.dumps(
            feedback[-3:],
            ensure_ascii=False,
            default=str
        )[:800]

        return experience_context, feedback_context

    # ======================================================
    # 4. BUILD PLANNING PROMPT
    # ======================================================

    def build_prompt(
        self,
        goal,
        experience_context,
        feedback_context
    ):

        workspace = str(WORKSPACE.resolve())

        prompt = f"""
You are Nexus, an intelligent desktop task planner.

Convert the user's request into a short sequence of
executable tool calls.

USER GOAL:
{goal}

APPROVED WORKSPACE:
{workspace}

PREVIOUS EXPERIENCES:
{experience_context}

PREVIOUS USER FEEDBACK:
{feedback_context}

AVAILABLE TOOLS:

1. search_files

Parameters:
- directory: starting directory, relative to workspace
- keyword: optional filename keyword
- extension: optional file extension

SEARCH RULES:
- Use "." to search the entire workspace.
- Never use "workspace" as the directory.
- Never include "workspace/" in a relative path.
- Search is recursive.
- Use null for an unused keyword.
- Use null for an unused extension.
- Use ".py" to find Python files.

Example for finding all Python files:

{{
    "step_id": 1,
    "description": "Find Python files",
    "tool": "search_files",
    "parameters": {{
        "directory": ".",
        "keyword": null,
        "extension": ".py"
    }}
}}

2. create_folder

Parameters:
- folder_path

Creates a folder inside the workspace.

3. move_file

Parameters:
- source_path
- destination_path

4. rename_file

Parameters:
- file_path
- new_name

5. verify_files

Parameters:
- paths

Checks whether requested files or folders exist.

6. generate_report

Parameters:
- title
- content
- output_path

Creates a report inside the approved reports directory.

IMPORTANT RULES:

- Use only the six available tools.
- Use relative paths for all file operations.
- Never use absolute paths.
- Never include "workspace/" in relative paths.
- Never access paths outside the approved workspace.
- Never plan permanent deletion.
- Never overwrite existing files.
- Select only the tools needed for the user's goal.
- Use sequential step IDs starting at 1.
- Do not exceed {MAX_PLAN_STEPS} steps.
- Use verify_files when an operation needs verification.
- Do not invent filenames or paths.

FOLDER CREATION RULE:

For the request "Create a folder named agentic in my workspace",
use:

{{
    "step_id": 1,
    "description": "Create the agentic folder",
    "tool": "create_folder",
    "parameters": {{
        "folder_path": "agentic"
    }}
}}

Then verify it using:

{{
    "step_id": 2,
    "description": "Verify the agentic folder",
    "tool": "verify_files",
    "parameters": {{
        "paths": ["agentic"]
    }}
}}

MEMORY RULES:

- Use previous experiences and feedback only as guidance.
- Do not assume previous operations succeeded.
- Respect the user's feedback about existing folders.
- Do not let memory override safety rules.

OUTPUT:

Return ONLY one valid JSON object.
Do not include Markdown or explanations.

Required structure:

{{
    "goal": "User's original goal",
    "reasoning": "Brief explanation of the plan",
    "steps": [
        {{
            "step_id": 1,
            "description": "Action description",
            "tool": "search_files",
            "parameters": {{
                "directory": ".",
                "keyword": null,
                "extension": ".py"
            }}
        }}
    ]
}}
"""

        return prompt

    # ======================================================
    # 5. GENERATE PLAN USING OLLAMA
    # ======================================================

    def create_plan(
        self,
        goal,
        previous_experiences=None,
        previous_feedback=None
    ):

        if not goal or not goal.strip():

            raise ValueError(
                "Please provide a task goal."
            )

        previous_experiences = previous_experiences or []
        previous_feedback = previous_feedback or []

        experience_context, feedback_context = (
            self.prepare_memory(
                previous_experiences,
                previous_feedback
            )
        )

        prompt = self.build_prompt(
            goal.strip(),
            experience_context,
            feedback_context
        )

        logger.info(
            "Generating execution plan | Goal: %s",
            goal
        )

        # --------------------------------------------------
        # SEND REQUEST TO OLLAMA
        # --------------------------------------------------

        request_data = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "think": False,
            "keep_alive": "5m",

            "options": {
                "temperature": 0,
                "num_predict": 256,
                "num_ctx": 4096
            }
        }

        try:

            response = requests.post(
                f"{self.base_url}/api/generate",
                json=request_data,
                timeout=self.timeout
            )

            response.raise_for_status()

            response_data = response.json()

        except requests.exceptions.ConnectTimeout as error:

            logger.exception("Ollama connection timeout")

            raise RuntimeError(
                "Could not connect to Ollama. "
                "Check whether the Ollama server is running."
            ) from error

        except requests.exceptions.ReadTimeout as error:

            logger.exception("Ollama generation timeout")

            raise RuntimeError(
                "Ollama took too long to generate the plan. "
                "The request timed out after 300 seconds."
            ) from error

        except requests.exceptions.RequestException as error:

            logger.exception("Ollama request failed")

            raise RuntimeError(
                f"Ollama request failed: {error}"
            ) from error

        # --------------------------------------------------
        # EXTRACT MODEL RESPONSE
        # --------------------------------------------------

        raw_output = response_data.get("response", "")

        if not raw_output.strip():

            raise ValueError(
                "Ollama returned an empty planning response."
            )

        if "</think>" in raw_output:

            raw_output = raw_output.split(
                "</think>",
                1
            )[1].strip()

        raw_output = raw_output.strip()

        if raw_output.startswith("```"):

            raw_output = raw_output.replace(
                "```json", "", 1
            )

            raw_output = raw_output.replace(
                "```", ""
            ).strip()

        # --------------------------------------------------
        # PARSE JSON
        # --------------------------------------------------

        try:

            plan_data = json.loads(raw_output)

            plan = ExecutionPlan.model_validate(
                plan_data
            )

        except Exception as error:

            logger.exception(
                "Generated plan validation failed"
            )

            raise ValueError(
                f"Could not parse the generated plan: {error}"
            ) from error

        # --------------------------------------------------
        # VALIDATE PLAN LENGTH
        # --------------------------------------------------

        if not plan.steps:

            raise ValueError(
                "The planner generated an empty execution plan."
            )

        if len(plan.steps) > MAX_PLAN_STEPS:

            raise ValueError(
                f"Plan exceeds the maximum of "
                f"{MAX_PLAN_STEPS} steps."
            )

        # --------------------------------------------------
        # VALIDATE STEP IDS
        # --------------------------------------------------

        for index, step in enumerate(
            plan.steps,
            start=1
        ):

            if step.step_id != index:

                raise ValueError(
                    "Plan step IDs must be sequential "
                    "and start from 1."
                )

        # --------------------------------------------------
        # VALIDATE REQUIRED PARAMETERS
        # --------------------------------------------------

        required_parameters = {

            "search_files": {
                "directory"
            },

            "create_folder": {
                "folder_path"
            },

            "move_file": {
                "source_path",
                "destination_path"
            },

            "rename_file": {
                "file_path",
                "new_name"
            },

            "verify_files": {
                "paths"
            },

            "generate_report": {
                "title",
                "content",
                "output_path"
            }
        }

        for step in plan.steps:

            expected = required_parameters[step.tool]

            missing = expected - set(
                step.parameters.keys()
            )

            if missing:

                raise ValueError(
                    f"Missing parameters for {step.tool}: "
                    f"{', '.join(sorted(missing))}"
                )

        # --------------------------------------------------
        # NORMALIZE AND VALIDATE SEARCH PARAMETERS
        # --------------------------------------------------

        for step in plan.steps:

            if step.tool != "search_files":
                continue

            parameters = step.parameters

            # Apply the actual Python function defaults.
            parameters.setdefault("directory", ".")
            parameters.setdefault("keyword", None)
            parameters.setdefault("extension", None)

            directory = parameters["directory"]

            if not isinstance(directory, str):

                raise ValueError(
                    "Search directory must be a string."
                )

            directory = directory.strip()

            if not directory:

                raise ValueError(
                    "Search directory cannot be empty."
                )

            # Convert Windows separators for consistent checking.
            normalized_directory = directory.replace("\\", "/")

            # Handle a redundant workspace prefix safely.
            # Example: workspace/agentic becomes agentic.
            parts = normalized_directory.split("/")

            if parts[0].lower() == "workspace":

                parts = parts[1:]

                normalized_directory = (
                    "/".join(parts) if parts else "."
                )

            search_path = PurePath(normalized_directory)

            if (
                search_path.is_absolute()
                or ".." in search_path.parts
            ):

                raise ValueError(
                    "Unsafe search directory generated by planner."
                )

            parameters["directory"] = normalized_directory

            keyword = parameters["keyword"]

            if keyword is not None and not isinstance(keyword, str):

                raise ValueError(
                    "Search keyword must be a string or null."
                )

            extension = parameters["extension"]

            if extension is not None and not isinstance(extension, str):

                raise ValueError(
                    "Search extension must be a string or null."
                )

            if extension is not None:

                extension = extension.strip()

                if extension and not extension.startswith("."):

                    extension = "." + extension

                parameters["extension"] = extension or None

        # --------------------------------------------------
        # VALIDATE FOLDER PATHS
        # --------------------------------------------------

        for step in plan.steps:

            if step.tool == "create_folder":

                folder_path = step.parameters["folder_path"]

                if not isinstance(folder_path, str):

                    raise ValueError(
                        "folder_path must be a string."
                    )

                if not folder_path.strip():

                    raise ValueError(
                        "folder_path cannot be empty."
                    )

                path = Path(folder_path)

                if path.is_absolute() or ".." in path.parts:

                    raise ValueError(
                        "Unsafe folder path generated by planner."
                    )

                if (
                    path.parts
                    and path.parts[0].lower() == "workspace"
                ):

                    raise ValueError(
                        "Do not include workspace/ in folder_path."
                    )

        # --------------------------------------------------
        # PLAN GENERATED SUCCESSFULLY
        # --------------------------------------------------

        logger.info(
            "Execution plan generated successfully | Steps: %s",
            len(plan.steps)
        )

        return plan
