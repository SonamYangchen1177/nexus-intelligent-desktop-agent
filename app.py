
import streamlit as st
import streamlit.components.v1 as components
import requests
import logging

from datetime import datetime
from html import escape
from textwrap import dedent

from config import (
    WORKSPACE,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL
)

from agent.planner import TaskPlanner
from agent.decision_maker import AgentController


# ==========================================================
# 1. PAGE CONFIGURATION
# ==========================================================

st.set_page_config(
    page_title="Nexus | Intelligent Desktop Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


# ==========================================================
# 2. HTML RENDERING HELPER
# ==========================================================

def render_html(content):
    """
    Render trusted HTML and CSS directly using Streamlit's
    dedicated HTML rendering function.
    """

    html_content = dedent(content).strip()

    st.html(html_content)


# ==========================================================
# 3. SESSION STATE INITIALIZATION
# ==========================================================

DEFAULT_STATE = {
    "controller": None,
    "planner": None,
    "plan": None,
    "goal": "",
    "goal_input": "",
    "execution_history": [],
    "task_completed": False,
    "task_finished": False,
    "task_status": "Not Started",
    "task_error": None,
    "feedback_submitted": False
}

for key, value in DEFAULT_STATE.items():

    if key not in st.session_state:
        st.session_state[key] = value


# Initialize the agent controller once per Streamlit session.
if st.session_state.controller is None:

    st.session_state.controller = AgentController()


# Initialize the planner once per Streamlit session.
if st.session_state.planner is None:

    st.session_state.planner = TaskPlanner()


controller = st.session_state.controller
planner = st.session_state.planner


# ==========================================================
# 4. CUSTOM CSS
# ==========================================================

render_html("""
<style>

.stApp {
    background-color: #0b1120;
    color: #e5e7eb;
}

header[data-testid="stHeader"] {
    background: transparent;
}

.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
    max-width: 1400px;
}

h1, h2, h3 {
    color: #f8fafc;
}

p, label {
    color: #cbd5e1;
}

.custom-card {
    background: linear-gradient(145deg, #172338, #111827);
    border: 1px solid #29374d;
    border-radius: 14px;
    padding: 22px;
    min-height: 145px;
    margin-bottom: 12px;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
}

.card-title {
    color: #94a3b8;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 1.5px;
    margin-bottom: 12px;
}

.card-value {
    color: #38bdf8;
    font-size: 27px;
    font-weight: 700;
    margin-bottom: 8px;
}

.card-description {
    color: #94a3b8;
    font-size: 13px;
    line-height: 1.6;
}

.status-box {
    background: #172338;
    border: 1px solid #29374d;
    border-radius: 10px;
    padding: 14px;
    margin-bottom: 12px;
}

.status-label {
    color: #94a3b8;
    font-size: 12px;
    margin-bottom: 5px;
}

.status-value {
    color: #38bdf8;
    font-size: 15px;
    font-weight: 600;
}

.goal-card {
    background: #172338;
    border-left: 4px solid #38bdf8;
    padding: 18px;
    border-radius: 8px;
    margin: 12px 0;
    overflow-wrap: anywhere;
}

.footer {
    text-align: center;
    color: #64748b;
    font-size: 12px;
    padding: 25px 0 10px 0;
    border-top: 1px solid #29374d;
    margin-top: 40px;
}

.footer p {
    color: #64748b;
    margin-bottom: 5px;
}

div.stButton > button {
    border-radius: 8px;
    font-weight: 600;
    min-height: 42px;
}

div[data-testid="stTextArea"] textarea {
    background-color: #172338;
    color: #f8fafc;
    border: 1px solid #334155;
}

div[data-testid="stTextInput"] input {
    background-color: #172338;
    color: #f8fafc;
}

div[data-testid="stExpander"] {
    background-color: #111c2e;
    border: 1px solid #29374d;
    border-radius: 10px;
}

</style>
""")


# ==========================================================
# 5. OLLAMA CONNECTION CHECK
# ==========================================================

def check_ollama_status():

    try:

        response = requests.get(
            f"{OLLAMA_BASE_URL}/api/tags",
            timeout=5
        )

        if response.status_code != 200:
            return False, False

        models = response.json().get("models", [])

        model_names = [
            model.get("name", "")
            for model in models
        ]

        model_available = any(
            name == OLLAMA_MODEL
            or name.startswith(OLLAMA_MODEL + ":")
            for name in model_names
        )

        return True, model_available

    except requests.RequestException as error:

        logger.warning(
            "Ollama connection failed: %s",
            error
        )

        return False, False


ollama_connected, model_available = check_ollama_status()


# ==========================================================
# 6. HERO SECTION
# ==========================================================

components.html(
    """
    <div style="
        background: linear-gradient(120deg, #172554, #164e63);
        border: 1px solid #2563eb;
        border-radius: 18px;
        padding: 30px;
        font-family: Arial, sans-serif;
        color: white;
    ">

        <div style="
            font-size: 12px;
            letter-spacing: 3px;
            color: #7dd3fc;
            font-weight: bold;
            margin-bottom: 12px;
        ">
            INTELLIGENT AGENT SYSTEM
        </div>

        <h1 style="
            font-size: 38px;
            margin: 0 0 10px 0;
            color: white;
        ">
            NEXUS
        </h1>

        <p style="
            font-size: 16px;
            color: #dbeafe;
            margin: 0;
        ">
            An intelligent, goal-driven desktop agent
            that plans, executes, verifies and learns
            from user feedback.
        </p>

    </div>
    """,
    height=190,
    scrolling=False
)


# ==========================================================
# 7. SIDEBAR
# ==========================================================

with st.sidebar:

    st.title("🤖 Nexus")

    st.caption("Intelligent Desktop Agent")

    st.divider()

    st.subheader("System Status")

    if ollama_connected:

        render_html("""
        <div class="status-box">
            <div class="status-label">OLLAMA SERVER</div>
            <div class="status-value">● Connected</div>
        </div>
        """)

    else:

        render_html("""
        <div class="status-box">
            <div class="status-label">OLLAMA SERVER</div>
            <div style="color:#f87171;font-weight:600;">
                ● Disconnected
            </div>
        </div>
        """)

    if model_available:

        render_html("""
        <div class="status-box">
            <div class="status-label">LANGUAGE MODEL</div>
            <div class="status-value">● Model Available</div>
        </div>
        """)

    else:

        render_html("""
        <div class="status-box">
            <div class="status-label">LANGUAGE MODEL</div>
            <div style="color:#f87171;font-weight:600;">
                ● Model Not Found
            </div>
        </div>
        """)

    st.caption(f"Model: {OLLAMA_MODEL}")

    st.divider()

    st.subheader("Workspace")

    st.code(str(WORKSPACE), language="text")

    st.divider()

    st.subheader("Current Task")

    st.write(st.session_state.task_status)

    st.divider()

    if st.button(
        "🔄 Refresh System Status",
        use_container_width=True
    ):

        st.rerun()

    if st.button(
        "🧹 Clear Current Task",
        use_container_width=True
    ):

        st.session_state.plan = None
        st.session_state.goal = ""
        st.session_state.goal_input = ""

        st.session_state.execution_history = []

        st.session_state.task_completed = False
        st.session_state.task_finished = False

        st.session_state.task_status = "Not Started"
        st.session_state.task_error = None

        st.session_state.feedback_submitted = False

        if "feedback_input" in st.session_state:
            st.session_state.feedback_input = ""

        st.rerun()


# ==========================================================
# 8. DASHBOARD OVERVIEW
# ==========================================================

st.markdown("## Dashboard Overview")

col1, col2, col3 = st.columns(3)

with col1:

    render_html("""
    <div class="custom-card">

        <div class="card-title">LLM ENGINE</div>

        <div class="card-value">Qwen3</div>

        <div class="card-description">
            Local language model for intelligent planning
        </div>

    </div>
    """)

with col2:

    render_html("""
    <div class="custom-card">

        <div class="card-title">AGENT ARCHITECTURE</div>

        <div class="card-value">Goal-Driven</div>

        <div class="card-description">
            Planning, reasoning, execution and verification
        </div>

    </div>
    """)

with col3:

    render_html("""
    <div class="custom-card">

        <div class="card-title">EXECUTION ENVIRONMENT</div>

        <div class="card-value">Sandbox</div>

        <div class="card-description">
            Controlled file operations inside the workspace
        </div>

    </div>
    """)


# ==========================================================
# 9. TASK INPUT
# ==========================================================

st.markdown("---")

st.markdown("## 🎯 Give Nexus a Goal")

st.write(
    "Describe what you want the agent to accomplish. "
    "Nexus will analyse your request and generate an "
    "execution plan before performing any operation."
)

goal = st.text_area(
    "Enter your task",
    height=110,
    placeholder=(
        "Example: Create a folder called ProjectData, "
        "then search for CSV files in the workspace "
        "and generate a report."
    ),
    key="goal_input"
)

st.session_state.goal = goal


# ==========================================================
# 10. PLAN GENERATION
# ==========================================================

if st.button(
    "🧠 Generate Execution Plan",
    type="primary",
    use_container_width=True
):

    if not goal.strip():

        st.warning("Please enter a goal first.")

    elif not ollama_connected:

        st.error(
            "Ollama server is not running. "
            "Please start Ollama and try again."
        )

    elif not model_available:

        st.error(
            f"The configured model '{OLLAMA_MODEL}' "
            "is not available. Please check your Ollama models."
        )

    else:

        try:

            with st.spinner(
                "Nexus is analysing your goal and generating a plan..."
            ):

                # Retrieve previous experiences from episodic memory.
                previous_experiences = (
                    controller.get_previous_experiences(limit=5)
                )

                # Retrieve previous user feedback.
                previous_feedback = (
                    controller.get_user_feedback(limit=5)
                )

                # Generate a new execution plan.
                plan = planner.create_plan(
                    goal,
                    previous_experiences=previous_experiences,
                    previous_feedback=previous_feedback
                )

                if not plan or not getattr(plan, "steps", None):

                    raise ValueError(
                        "The planner generated an empty execution plan."
                    )

                # Store the generated plan.
                st.session_state.plan = plan
                st.session_state.goal = goal

                # Reset previous execution results.
                st.session_state.execution_history = []

                st.session_state.task_completed = False
                st.session_state.task_finished = False

                st.session_state.task_status = "Awaiting Approval"
                st.session_state.task_error = None

                st.session_state.feedback_submitted = False

            st.success(
                "Execution plan generated successfully!"
            )

        except Exception as error:

            logger.exception("Plan generation failed")

            st.session_state.plan = None
            st.session_state.task_status = "Plan Generation Failed"

            st.error(
                f"Could not generate the plan: {error}"
            )


# ==========================================================
# 11. DISPLAY GENERATED PLAN
# ==========================================================

if st.session_state.plan is not None:

    st.markdown("---")

    st.markdown("## 📋 Proposed Execution Plan")

    render_html(f"""
    <div class="goal-card">

        <div style="color:#94a3b8;font-size:12px;">
            USER GOAL
        </div>

        <div style="color:#f8fafc;font-size:16px;font-weight:600;">
            {escape(st.session_state.goal)}
        </div>

    </div>
    """)

    plan = st.session_state.plan

    steps = getattr(plan, "steps", [])

    st.markdown("### Planned Actions")

    for step in steps:

        step_id = getattr(step, "step_id", "?")
        description = getattr(step, "description", "")
        tool = getattr(step, "tool", "Unknown")

        with st.container(border=True):

            col_a, col_b = st.columns([3, 1])

            with col_a:

                st.markdown(
                    f"**Step {step_id}:** {description}"
                )

            with col_b:

                st.caption(f"Tool: `{tool}`")

            parameters = getattr(step, "parameters", {})

            if parameters:

                with st.expander("View parameters"):

                    st.json(parameters)

    st.info(
        "Review the proposed steps and parameters carefully. "
        "Nexus will execute the plan only after your approval."
    )


    # ======================================================
    # 12. PLAN APPROVAL
    # ======================================================

    st.markdown("### Execution Approval")

    approve_col, cancel_col = st.columns(2)

    with approve_col:

        execute_button = st.button(
            "▶ Approve and Execute",
            type="primary",
            use_container_width=True,
            disabled=st.session_state.task_finished
        )

    with cancel_col:

        cancel_button = st.button(
            "✖ Cancel Plan",
            use_container_width=True,
            disabled=st.session_state.task_finished
        )

    if cancel_button:

        st.session_state.plan = None
        st.session_state.execution_history = []

        st.session_state.task_completed = False
        st.session_state.task_finished = False

        st.session_state.task_status = "Cancelled"

        st.warning("Execution plan cancelled.")

        st.rerun()


    # ======================================================
    # 13. PLAN EXECUTION
    # ======================================================

    if execute_button:

        st.markdown("---")

        st.markdown("## ⚙️ Execution Monitor")

        st.session_state.task_status = "Executing"

        try:

            with st.spinner(
                "Nexus is executing and verifying the task..."
            ):

                # Execute the approved plan.
                execution_result = controller.execute_plan(plan)

                # Updated decision_maker.py returns a dictionary.
                if isinstance(execution_result, dict):

                    execution_history = execution_result.get(
                        "execution_history",
                        []
                    )

                    overall_status = execution_result.get(
                        "overall_status",
                        "failed"
                    )

                # Backward compatibility with the old list return.
                elif isinstance(execution_result, list):

                    execution_history = execution_result

                    overall_status = (
                        "success"
                        if execution_history
                        and all(
                            item.get("status") == "success"
                            for item in execution_history
                            if isinstance(item, dict)
                        )
                        else "failed"
                    )

                else:

                    raise TypeError(
                        "Unexpected execution result returned "
                        "by AgentController."
                    )

                # Store execution results.
                st.session_state.execution_history = (
                    execution_history
                )

                # Determine final task status.
                st.session_state.task_completed = (
                    overall_status == "success"
                )

                st.session_state.task_finished = True

                if st.session_state.task_completed:

                    st.session_state.task_status = "Completed"

                else:

                    st.session_state.task_status = "Failed"

            if st.session_state.task_completed:

                st.success(
                    "Nexus successfully completed and verified the task!"
                )

            else:

                st.error(
                    "Nexus finished execution, but one or more "
                    "steps failed or could not be verified."
                )

        except Exception as error:

            logger.exception("Task execution failed")

            st.session_state.task_completed = False
            st.session_state.task_finished = True

            st.session_state.task_status = "Execution Error"

            st.session_state.task_error = str(error)

            st.session_state.execution_history = [
                {
                    "status": "failed",
                    "error": str(error)
                }
            ]

            st.error(
                f"Execution failed: {error}"
            )


# ==========================================================
# 14. EXECUTION RESULTS
# ==========================================================

if st.session_state.execution_history:

    st.markdown("---")

    st.markdown("## 📊 Execution Results")

    # Display overall execution status.
    if st.session_state.task_completed:

        st.success("Overall Status: SUCCESS")

    else:

        st.error("Overall Status: FAILED")

    # Display individual execution steps.
    for index, result in enumerate(
        st.session_state.execution_history
    ):

        if not isinstance(result, dict):
            continue

        step_status = result.get("status", "unknown")

        step_title = result.get(
            "description",
            f"Execution Step {index + 1}"
        )

        if step_status == "success":

            icon = "✅"

        elif step_status == "failed":

            icon = "❌"

        else:

            icon = "⚠️"

        with st.expander(
            f"{icon} Step {index + 1}: {step_title}",
            expanded=True
        ):

            st.markdown(
                f"**Tool:** `{result.get('tool', 'Unknown')}`"
            )

            st.markdown(
                f"**Status:** {step_status.upper()}"
            )

            if "attempts" in result:

                st.write(
                    f"**Attempts:** {result['attempts']}"
                )

            if "result" in result:

                st.markdown("**Tool Result**")

                tool_result = result["result"]

                if isinstance(tool_result, (dict, list)):

                    st.json(tool_result)

                else:

                    st.write(tool_result)

            if "verification" in result:

                st.markdown("**Verification Result**")

                verification = result["verification"]

                if isinstance(verification, dict):

                    st.write(
                        verification.get(
                            "message",
                            "No verification message."
                        )
                    )

                    st.write(
                        "Verified:",
                        verification.get("verified", False)
                    )

                    with st.expander("View verification details"):

                        st.json(verification)

                else:

                    st.write(verification)

            if "error" in result:

                st.error(result["error"])


# ==========================================================
# 15. USER FEEDBACK
# ==========================================================

if st.session_state.task_finished:

    st.markdown("---")

    st.markdown("## 💬 User Feedback")

    st.write(
        "Your feedback helps Nexus improve future task "
        "planning and execution."
    )

    if not st.session_state.feedback_submitted:

        feedback = st.text_area(
            "How did Nexus perform?",
            placeholder=(
                "Example: The agent successfully created the folder "
                "but should verify the report contents before finishing."
            ),
            height=100,
            key="feedback_input"
        )

        if st.button(
            "Submit Feedback",
            use_container_width=True
        ):

            if not feedback.strip():

                st.warning(
                    "Please enter feedback before submitting."
                )

            else:

                try:

                    controller.record_feedback(feedback)

                    st.session_state.feedback_submitted = True

                    st.success(
                        "Feedback saved successfully. "
                        "Nexus can use it in future planning."
                    )

                    st.rerun()

                except Exception as error:

                    logger.exception(
                        "Feedback submission failed"
                    )

                    st.error(
                        f"Could not save feedback: {error}"
                    )

    else:

        st.success(
            "Thank you! Your feedback has been saved."
        )


# ==========================================================
# 16. SESSION INFORMATION
# ==========================================================

st.markdown("---")

st.markdown("## ℹ️ Session Information")

info_col1, info_col2, info_col3 = st.columns(3)

with info_col1:

    st.metric(
        "Execution Steps",
        len(st.session_state.execution_history)
    )

with info_col2:

    st.metric(
        "Task Status",
        st.session_state.task_status
    )

with info_col3:

    st.metric(
        "Completed Successfully",
        "Yes" if st.session_state.task_completed else "No"
    )

st.caption(
    "Session refreshed: "
    + datetime.now().strftime("%d %B %Y, %I:%M:%S %p")
)


# ==========================================================
# 17. FOOTER
# ==========================================================

render_html("""
<div class="footer">

    <p>
        NEXUS | Intelligent Goal-Driven Desktop Agent
    </p>

    <p>
        DAT404 – Intelligent and Generative Agents
    </p>

    <p>
        Built with Python, Streamlit and Ollama
    </p>

</div>
""")
