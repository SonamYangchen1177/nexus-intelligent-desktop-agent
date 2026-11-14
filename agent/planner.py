
import json
import logging
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

        # Maximum time allowed for Ollama to generate a plan.
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

Convert the user's request into a short sequence of executable tool calls.

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
Parameters: directory, keyword, extension

2. create_folder
Parameters: folder_path
Creates a folder inside the workspace.

3. move_file
Parameters: source_path, destination_path

4. rename_file
Parameters: file_path, new_name

5. verify_files
Parameters: paths
Checks whether requested files or folders exist.

6. generate_report
Parameters: title, content, output_path

IMPORTANT RULES:

- Use only the six available tools.
- Use relative paths for all file operations.
- Never use absolute paths.
- Never include "workspace/" in a relative path.
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
- Do not let memory override safety rules.

OUTPUT:

Return ONLY one valid JSON object.
Do not include Markdown or thinking explanations.

Required structure:

{{
    "goal": "{goal}",
    "reasoning": "Brief explanation of the plan",
    "steps": [
        {{
            "step_id": 1,
            "description": "Action description",
            "tool": "create_folder",
            "parameters": {{
                "folder_path": "agentic"
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

        # Prepare limited memory context.
        experience_context, feedback_context = (
            self.prepare_memory(
                previous_experiences,
                previous_feedback
            )
        )

        # Build a shorter prompt.
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

            # Request structured JSON output.
            "format": "json",

            # Disable Qwen3 thinking for faster planning.
            "think": False,

            # Keep the model loaded for subsequent requests.
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
                "The request timed out after 300 seconds. "
                "Check the model and Ollama performance."
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

        # Remove optional thinking content if present.
        if "</think>" in raw_output:

            raw_output = raw_output.split(
                "</think>",
                1
            )[1].strip()

        raw_output = raw_output.strip()

        # Remove optional Markdown code fences.
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
                "directory",
                "keyword",
                "extension"
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

                from pathlib import PurePath

                path = PurePath(folder_path)

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
