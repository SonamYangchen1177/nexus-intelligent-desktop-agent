from pathlib import Path

import streamlit as st
import requests
import logging

from datetime import datetime
from html import escape
from textwrap import dedent

from config import WORKSPACE, OLLAMA_BASE_URL, OLLAMA_MODEL
from agent.planner import TaskPlanner
from agent.decision_maker import AgentController


# ==========================================================
# 1. PAGE CONFIGURATION
# ==========================================================

st.set_page_config(
    page_title="Nexus | Intelligent Desktop Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


def render_html(content):
    """Render trusted HTML/CSS."""
    st.html(dedent(content).strip())


# ==========================================================
# 2. SESSION STATE AND AGENT INITIALIZATION
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
    "feedback_submitted": False,
    "page": "Dashboard",
}

for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value

if st.session_state.controller is None:
    st.session_state.controller = AgentController()

if st.session_state.planner is None:
    st.session_state.planner = TaskPlanner()

controller = st.session_state.controller
planner = st.session_state.planner


# ==========================================================
# 3. PROFESSIONAL THEME AND HEADER STYLES
# ==========================================================

render_html("""
<style>
:root {
    --nx-primary: #2563eb;
    --nx-primary-dark: #1d4ed8;
    --nx-primary-soft: #eff6ff;
    --nx-bg: #f4f7fb;
    --nx-surface: #ffffff;
    --nx-text: #172b4d;
    --nx-secondary: #475569;
    --nx-muted: #64748b;
    --nx-border: #e2e8f0;
    --nx-success: #15803d;
    --nx-danger: #dc2626;
}

.stApp {
    background: var(--nx-bg);
    color: var(--nx-text);
}

.block-container {
    max-width: 1500px;
    padding-top: 1.1rem;
    padding-bottom: 2.5rem;
}

/* Make standard Streamlit text readable */
h1, h2, h3, h4, h5, h6 {
    color: var(--nx-text) !important;
    font-weight: 750 !important;
}
.stMarkdown p, .stMarkdown li, .stCaption,
[data-testid="stCaptionContainer"] {
    color: var(--nx-secondary) !important;
}
label, [data-testid="stWidgetLabel"] p {
    color: var(--nx-text) !important;
}

/* Streamlit's own top chrome */
header[data-testid="stHeader"] {
    background: var(--nx-bg);
}
[data-testid="stToolbar"] {
    background: transparent;
}

/* HEADER BRAND */
.nexus-brand {
    display: flex;
    align-items: center;
    gap: 12px;
    min-height: 58px;
}
.nexus-logo {
    width: 46px;
    height: 46px;
    flex: 0 0 46px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 13px;
    color: #ffffff !important;
    background: linear-gradient(135deg, #3478f6, #1746a2);
    font-size: 25px;
    font-weight: 900;
    box-shadow: 0 5px 14px rgba(37, 99, 235, .22);
}
.nexus-brand-name {
    color: #172b4d !important;
    font-size: 24px;
    line-height: 1.1;
    font-weight: 900;
    letter-spacing: 1.2px;
}
.nexus-brand-subtitle {
    color: #64748b !important;
    font-size: 10px;
    line-height: 1.5;
    font-weight: 750;
    letter-spacing: 1.45px;
    margin-top: 3px;
}

/* Header shell */
.nexus-header-shell {
    background: #ffffff;
    border: 1px solid #dfe7f1;
    border-radius: 16px;
    padding: 12px 18px;
    margin-bottom: 23px;
    box-shadow: 0 4px 16px rgba(15, 35, 65, .055);
}

/* Navigation buttons */
div.stButton > button {
    min-height: 42px;
    border-radius: 9px;
    border: 1px solid #d7e0ec;
    background: #ffffff;
    color: #334155 !important;
    font-weight: 700;
    transition: all .18s ease;
}
div.stButton > button:hover {
    border-color: #2563eb;
    background: #eff6ff;
    color: #1d4ed8 !important;
}
div.stButton > button[kind="primary"] {
    background: #2563eb !important;
    border-color: #2563eb !important;
    color: #ffffff !important;
}
div.stButton > button[kind="primary"]:hover {
    background: #1d4ed8 !important;
    border-color: #1d4ed8 !important;
    color: #ffffff !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid var(--nx-border);
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: var(--nx-text) !important;
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label {
    color: var(--nx-secondary) !important;
}

/* Hero */
.nexus-hero {
    background: linear-gradient(115deg, #eaf2ff 0%, #f2f7ff 58%, #ffffff 100%);
    border: 1px solid #d9e6fa;
    border-radius: 18px;
    padding: 30px;
    margin-bottom: 22px;
}
.nexus-hero-kicker {
    color: #2563eb !important;
    font-size: 11px;
    font-weight: 850;
    letter-spacing: 2px;
}
.nexus-hero-title {
    color: #172b4d !important;
    font-size: 39px;
    font-weight: 900;
    margin: 8px 0;
}
.nexus-hero-copy {
    color: #475569 !important;
    font-size: 15px;
    line-height: 1.65;
    margin: 0;
}

/* Overview cards */
.nexus-card {
    background: #ffffff;
    border: 1px solid var(--nx-border);
    border-radius: 15px;
    padding: 21px;
    min-height: 148px;
    margin-bottom: 12px;
    box-shadow: 0 4px 14px rgba(15, 35, 65, .04);
}
.nexus-card-label {
    color: #64748b !important;
    font-size: 10px;
    font-weight: 850;
    letter-spacing: 1.3px;
    margin-bottom: 12px;
}
.nexus-card-value {
    color: #2563eb !important;
    font-size: 26px;
    font-weight: 850;
    margin-bottom: 7px;
}
.nexus-card-copy {
    color: #64748b !important;
    font-size: 13px;
    line-height: 1.55;
}

/* Status and goal panels */
.nexus-status {
    background: #f8fafc;
    border: 1px solid var(--nx-border);
    border-radius: 10px;
    padding: 13px;
    margin: 9px 0;
}
.nexus-status-label {
    color: #64748b !important;
    font-size: 10px;
    font-weight: 850;
    letter-spacing: 1px;
    margin-bottom: 6px;
}
.nexus-goal {
    background: #eff6ff;
    border: 1px solid #dbeafe;
    border-left: 4px solid #2563eb;
    border-radius: 10px;
    padding: 17px;
    margin: 12px 0;
    overflow-wrap: anywhere;
}
.nexus-goal-label {
    color: #64748b !important;
    font-size: 10px;
    font-weight: 850;
    letter-spacing: 1px;
}
.nexus-goal-text {
    color: #172b4d !important;
    font-size: 15px;
    font-weight: 650;
    line-height: 1.6;
    margin-top: 6px;
}

/* Metrics */
[data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid var(--nx-border);
    border-radius: 13px;
    padding: 16px;
    box-shadow: 0 3px 12px rgba(15, 35, 65, .035);
}
[data-testid="stMetricLabel"],
[data-testid="stMetricLabel"] p {
    color: #64748b !important;
}
[data-testid="stMetricValue"] {
    color: #2563eb !important;
    font-weight: 850;
}

/* Inputs */
div[data-testid="stTextArea"] textarea,
div[data-testid="stTextInput"] input {
    background: #ffffff !important;
    color: #172b4d !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: 9px !important;
}
div[data-testid="stTextArea"] textarea::placeholder,
div[data-testid="stTextInput"] input::placeholder {
    color: #94a3b8 !important;
}
div[data-testid="stTextArea"] label,
div[data-testid="stTextInput"] label {
    color: #334155 !important;
    font-weight: 650;
}

/* Expanders, bordered containers, tables */
div[data-testid="stExpander"] {
    background: #ffffff;
    border: 1px solid var(--nx-border);
    border-radius: 11px;
}
div[data-testid="stExpander"] summary,
div[data-testid="stExpander"] summary p {
    color: #26384f !important;
    font-weight: 650;
}
div[data-testid="stVerticalBlockBorderWrapper"] {
    border-color: var(--nx-border) !important;
    border-radius: 11px;
}
[data-testid="stDataFrame"] {
    border: 1px solid var(--nx-border);
    border-radius: 10px;
    overflow: hidden;
}
div[data-testid="stAlert"] {
    border-radius: 10px;
}

/* Footer */
.nexus-footer {
    text-align: center;
    color: #64748b !important;
    font-size: 12px;
    padding: 22px 0 8px;
    border-top: 1px solid var(--nx-border);
    margin-top: 38px;
}
.nexus-footer p {
    color: #64748b !important;
    margin: 4px 0;
}

/* Small-screen header: allow buttons to wrap naturally */
@media (max-width: 760px) {
    .nexus-brand-name { font-size: 21px; }
    .nexus-header-shell { padding: 10px; }
}
</style>
""")


# ==========================================================
# 4. OLLAMA CONNECTION CHECK
# ==========================================================

def check_ollama_status():
    try:
        response = requests.get(
            f"{OLLAMA_BASE_URL}/api/tags",
            timeout=5,
        )

        if response.status_code != 200:
            return False, False

        models = response.json().get("models", [])
        model_names = [model.get("name", "") for model in models]

        model_available = any(
            name == OLLAMA_MODEL
            or name.startswith(OLLAMA_MODEL + ":")
            for name in model_names
        )

        return True, model_available

    except requests.RequestException as error:
        logger.warning("Ollama connection failed: %s", error)
        return False, False


ollama_connected, model_available = check_ollama_status()


# ==========================================================
# 5. PROPER APPLICATION HEADER / NAVIGATION
# ==========================================================
# The header is a single full-width white container.
# The logo is on the left; real Streamlit navigation buttons
# are on the right so navigation works reliably.

with st.container():
    render_html('<div class="nexus-header-shell">')

    header_logo_col, header_nav_col = st.columns(
        [1.25, 2.75],
        vertical_alignment="center",
        gap="small",
    )

    with header_logo_col:
        render_html("""
        <div class="nexus-brand">
            <div class="nexus-logo">N</div>
            <div>
                <div class="nexus-brand-name">NEXUS</div>
                <div class="nexus-brand-subtitle">
                    INTELLIGENT DESKTOP AGENT
                </div>
            </div>
        </div>
        """)

    with header_nav_col:
        nav_cols = st.columns(3, gap="small")
        navigation = ["Dashboard", "Chat", "Analytics"]

        for nav_col, nav_page in zip(nav_cols, navigation):
            with nav_col:
                is_active = st.session_state.page == nav_page
                if st.button(
                    nav_page,
                    key=f"nav_{nav_page.lower()}",
                    type="primary" if is_active else "secondary",
                    use_container_width=True,
                ):
                    if st.session_state.page != nav_page:
                        st.session_state.page = nav_page
                        st.rerun()

    render_html("</div>")


# ==========================================================
# 6. SIDEBAR — SYSTEM STATUS AND WORKSPACE
# ==========================================================

with st.sidebar:
    st.markdown("### ⚙️ System Monitor")
    st.caption("Nexus environment status")
    st.divider()

    server_color = "#15803d" if ollama_connected else "#dc2626"
    server_text = "Connected" if ollama_connected else "Disconnected"

    render_html(f"""
    <div class="nexus-status">
        <div class="nexus-status-label">OLLAMA SERVER</div>
        <div style="color:{server_color};font-weight:750">
            ● {server_text}
        </div>
    </div>
    """)

    model_color = "#15803d" if model_available else "#dc2626"
    model_text = "Model available" if model_available else "Model not found"

    render_html(f"""
    <div class="nexus-status">
        <div class="nexus-status-label">LANGUAGE MODEL</div>
        <div style="color:{model_color};font-weight:750">
            ● {model_text}
        </div>
    </div>
    """)

    st.caption(f"Configured model: {OLLAMA_MODEL}")
    st.divider()

    st.markdown("### 📁 Workspace")
    st.code(str(WORKSPACE), language="text")
    st.divider()

    st.markdown("### 📌 Current Task")
    st.write(st.session_state.task_status)
    st.divider()

    if st.button("↻ Refresh system status", use_container_width=True):
        st.rerun()

    if st.button("🗑 Clear current task", use_container_width=True):
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
# 7. SHARED PAGE TITLE
# ==========================================================

page = st.session_state.page

page_subtitles = {
    "Dashboard": "A clear overview of your intelligent desktop agent.",
    "Chat": "Describe a goal, review the plan, and approve execution.",
    "Analytics": "Review task outcomes and execution performance.",
}

st.markdown(f"# {page}")
st.caption(page_subtitles.get(page, ""))


# ==========================================================
# 8. DASHBOARD PAGE
# ==========================================================

if page == "Dashboard":
    render_html("""
    <div class="nexus-hero">
        <div class="nexus-hero-kicker">INTELLIGENT AGENT SYSTEM</div>
        <div class="nexus-hero-title">NEXUS</div>
        <p class="nexus-hero-copy">
            An intelligent, goal-driven desktop agent that plans,
            executes, verifies and learns from user feedback.
        </p>
    </div>
    """)

    total_steps = len(st.session_state.execution_history)

    successful_steps = sum(
        1 for item in st.session_state.execution_history
        if isinstance(item, dict) and item.get("status") == "success"
    )

    failed_steps = sum(
        1 for item in st.session_state.execution_history
        if isinstance(item, dict) and item.get("status") == "failed"
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Task Status", st.session_state.task_status)
    col2.metric("Execution Steps", total_steps)
    col3.metric("Successful Steps", successful_steps)
    col4.metric("Failed Steps", failed_steps)

    st.markdown("### 🤖 Agent Overview")

    c1, c2, c3 = st.columns(3)

    with c1:
        render_html("""
        <div class="nexus-card">
            <div class="nexus-card-label">LLM ENGINE</div>
            <div class="nexus-card-value">Qwen3</div>
            <div class="nexus-card-copy">
                Local language model for intelligent planning and reasoning.
            </div>
        </div>
        """)

    with c2:
        render_html("""
        <div class="nexus-card">
            <div class="nexus-card-label">AGENT ARCHITECTURE</div>
            <div class="nexus-card-value">Goal-Driven</div>
            <div class="nexus-card-copy">
                Planning, reasoning, execution and verification of user tasks.
            </div>
        </div>
        """)

    with c3:
        render_html("""
        <div class="nexus-card">
            <div class="nexus-card-label">EXECUTION ENVIRONMENT</div>
            <div class="nexus-card-value">Sandbox</div>
            <div class="nexus-card-copy">
                Controlled file operations inside the configured workspace.
            </div>
        </div>
        """)

    st.markdown("### 📌 Current Task")

    if st.session_state.goal:
        st.info(st.session_state.goal)
    else:
        st.write("No task has been submitted in this session yet.")

    if st.button("＋ Start a New Task", type="primary"):
        st.session_state.page = "Chat"
        st.rerun()


# ==========================================================
# 9. CHAT PAGE — INPUT AND PLAN GENERATION
# ==========================================================

elif page == "Chat":
    st.markdown("## 🎯 Give Nexus a Goal")
    st.write(
        "Describe what you want the agent to accomplish. "
        "Nexus will analyse your request and generate an execution "
        "plan before performing any operation."
    )

    goal = st.text_area(
        "Enter your task",
        height=120,
        placeholder=(
            "Example: Create a folder called ProjectData, then search "
            "for CSV files in the workspace and generate a report."
        ),
        key="goal_input",
    )
    st.session_state.goal = goal

    if st.button(
        "🧠 Generate Execution Plan",
        type="primary",
        use_container_width=True,
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
                f"The configured model '{OLLAMA_MODEL}' is not available. "
                "Please check your Ollama models."
            )

        else:
            try:
                with st.spinner(
                    "Nexus is analysing your goal and generating a plan..."
                ):
                    previous_experiences = controller.get_previous_experiences(
                        limit=5
                    )
                    previous_feedback = controller.get_user_feedback(
                        limit=5
                    )

                    plan = planner.create_plan(
                        goal,
                        previous_experiences=previous_experiences,
                        previous_feedback=previous_feedback,
                    )

                    if not plan or not getattr(plan, "steps", None):
                        raise ValueError(
                            "The planner generated an empty execution plan."
                        )

                    st.session_state.plan = plan
                    st.session_state.goal = goal
                    st.session_state.execution_history = []
                    st.session_state.task_completed = False
                    st.session_state.task_finished = False
                    st.session_state.task_status = "Awaiting Approval"
                    st.session_state.task_error = None
                    st.session_state.feedback_submitted = False

                st.success("Execution plan generated successfully!")

            except Exception as error:
                logger.exception("Plan generation failed")
                st.session_state.plan = None
                st.session_state.task_status = "Plan Generation Failed"
                st.error(f"Could not generate the plan: {error}")

    # Display proposed plan
    if st.session_state.plan is not None:
        st.divider()
        st.markdown("## 📋 Proposed Execution Plan")

        render_html(f"""
        <div class="nexus-goal">
            <div class="nexus-goal-label">USER GOAL</div>
            <div class="nexus-goal-text">
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
                    st.markdown(f"**Step {step_id}:** {description}")

                with col_b:
                    st.caption(f"Tool: `{tool}`")

                parameters = getattr(step, "parameters", {})
                if parameters:
                    with st.expander("View Parameters"):
                        st.json(parameters)

        st.info(
            "Review the proposed steps and parameters carefully. "
            "Nexus will execute the plan only after your approval."
        )

        st.markdown("### Execution Approval")
        approve_col, cancel_col = st.columns(2)

        with approve_col:
            execute_button = st.button(
                "▶ Approve and Execute",
                type="primary",
                use_container_width=True,
                disabled=st.session_state.task_finished,
            )

        with cancel_col:
            cancel_button = st.button(
                "✖ Cancel Plan",
                use_container_width=True,
                disabled=st.session_state.task_finished,
            )

        if cancel_button:
            st.session_state.plan = None
            st.session_state.execution_history = []
            st.session_state.task_completed = False
            st.session_state.task_finished = False
            st.session_state.task_status = "Cancelled"
            st.warning("Execution plan cancelled.")
            st.rerun()

        # Execute only after explicit approval
        if execute_button:
            st.markdown("---")
            st.markdown("## ⚙️ Execution Monitor")
            st.session_state.task_status = "Executing"

            try:
                with st.spinner(
                    "Nexus is executing and verifying the task..."
                ):
                    execution_result = controller.execute_plan(plan)

                    if isinstance(execution_result, dict):
                        execution_history = execution_result.get(
                            "execution_history", []
                        )
                        overall_status = execution_result.get(
                            "overall_status", "failed"
                        )

                    elif isinstance(execution_result, list):
                        execution_history = execution_result
                        overall_status = (
                            "success"
                            if execution_history
                            and all(
                                isinstance(item, dict)
                                and item.get("status") == "success"
                                for item in execution_history
                            )
                            else "failed"
                        )

                    else:
                        raise TypeError(
                            "Unexpected execution result returned "
                            "by AgentController."
                        )

                    st.session_state.execution_history = execution_history
                    st.session_state.task_completed = (
                        overall_status == "success"
                    )
                    st.session_state.task_finished = True
                    st.session_state.task_status = (
                        "Completed"
                        if st.session_state.task_completed
                        else "Failed"
                    )

                if st.session_state.task_completed:
                    st.success(
                        "Nexus successfully completed and verified the task!"
                    )
                else:
                    st.error(
                        "Nexus finished execution, but one or more steps "
                        "failed or could not be verified."
                    )

            except Exception as error:
                logger.exception("Task execution failed")
                st.session_state.task_completed = False
                st.session_state.task_finished = True
                st.session_state.task_status = "Execution Error"
                st.session_state.task_error = str(error)
                st.session_state.execution_history = [
                    {"status": "failed", "error": str(error)}
                ]
                st.error(f"Execution failed: {error}")

    # Execution results
    if st.session_state.execution_history:
        st.divider()
        st.markdown("## 📊 Execution Results")

        if st.session_state.task_completed:
            st.success("Overall Status: SUCCESS")
        else:
            st.error("Overall Status: FAILED")

        for index, result in enumerate(
            st.session_state.execution_history
        ):
            if not isinstance(result, dict):
                continue

            step_status = result.get("status", "unknown")
            step_title = result.get(
                "description",
                f"Execution Step {index + 1}",
            )

            icon = (
                "✅" if step_status == "success"
                else "❌" if step_status == "failed"
                else "⚠️"
            )

            with st.expander(
                f"{icon} Step {index + 1}: {step_title}",
                expanded=True,
            ):
                st.markdown(
                    f"**Tool:** `{result.get('tool', 'Unknown')}`"
                )
                st.markdown(f"**Status:** {step_status.upper()}")

                if "attempts" in result:
                    st.write(f"**Attempts:** {result['attempts']}")

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
                                "No verification message.",
                            )
                        )
                        st.write(
                            "Verified:",
                            verification.get("verified", False),
                        )

                        with st.expander("View Verification Details"):
                            st.json(verification)
                    else:
                        st.write(verification)

                if "error" in result:
                    st.error(result["error"])

    # User feedback
    if st.session_state.task_finished:
        st.divider()
        st.markdown("## 💬 User Feedback")
        st.write(
            "Your feedback helps Nexus improve future task planning "
            "and execution."
        )

        if not st.session_state.feedback_submitted:
            feedback = st.text_area(
                "How did Nexus perform?",
                placeholder=(
                    "Example: The agent successfully created the folder "
                    "but should verify the report contents before finishing."
                ),
                height=100,
                key="feedback_input",
            )

            if st.button("Submit Feedback", use_container_width=True):
                if not feedback.strip():
                    st.warning("Please enter feedback before submitting.")
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
                        logger.exception("Feedback submission failed")
                        st.error(f"Could not save feedback: {error}")
        else:
            st.success("Thank you! Your feedback has been saved.")


# ==========================================================
# 10. ANALYTICS PAGE
# ==========================================================

elif page == "Analytics":
    history = [
        item for item in st.session_state.execution_history
        if isinstance(item, dict)
    ]

    total = len(history)
    successes = sum(
        1 for item in history if item.get("status") == "success"
    )
    failures = sum(
        1 for item in history if item.get("status") == "failed"
    )
    other = total - successes - failures
    success_rate = successes / total * 100 if total else 0

    st.markdown("## 📈 Performance Overview")

    a, b, c, d = st.columns(4)
    a.metric("Total Steps", total)
    b.metric("Successful", successes)
    c.metric("Failed", failures)
    d.metric("Success Rate", f"{success_rate:.1f}%")

    st.markdown("### Execution Status Distribution")

    if total:
        chart_data = {
            "Status": ["Successful", "Failed", "Other"],
            "Count": [successes, failures, other],
        }
        st.bar_chart(
            chart_data,
            x="Status",
            y="Count",
            use_container_width=True,
        )
    else:
        st.info(
            "No execution data is available yet. "
            "Complete a task in the Chat page to populate analytics."
        )

    st.markdown("### 📋 Step-Level History")

    if history:
        table_rows = []

        for index, item in enumerate(history, start=1):
            table_rows.append({
                "Step": index,
                "Description": item.get(
                    "description",
                    f"Execution Step {index}",
                ),
                "Tool": item.get("tool", "Unknown"),
                "Status": str(
                    item.get("status", "unknown")
                ).upper(),
                "Attempts": item.get("attempts", "—"),
            })

        st.dataframe(
            table_rows,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.write("There are no execution steps to display.")

    st.markdown("### Current Session")

    info_col1, info_col2, info_col3 = st.columns(3)

    info_col1.metric("Task Status", st.session_state.task_status)
    info_col2.metric(
        "Task Completed",
        "Yes" if st.session_state.task_completed else "No",
    )
    info_col3.metric(
        "Feedback Submitted",
        "Yes" if st.session_state.feedback_submitted else "No",
    )

    if st.session_state.task_error:
        st.error(f"Last task error: {st.session_state.task_error}")


# ==========================================================
# 11. FOOTER
# ==========================================================

render_html("""
<div class="nexus-footer">
    <p><strong>NEXUS</strong> | Intelligent Goal-Driven Desktop Agent</p>
    <p>DAT404 – Intelligent and Generative Agents</p>
    <p>Built with Python, Streamlit and Ollama</p>
</div>
""")

st.caption(
    "Session refreshed: "
    + datetime.now().strftime("%d %B %Y, %I:%M:%S %p")
)

