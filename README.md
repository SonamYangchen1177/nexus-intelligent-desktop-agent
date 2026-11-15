# Nexus – Intelligent Goal-Driven Desktop Agent

Nexus is an LLM-powered desktop automation agent developed for the DAT404 Intelligent and Generative Agents assignment at Sherubtse College, Royal University of Bhutan.

It allows users to describe workspace-management tasks in natural language. The agent generates a structured plan, validates the plan, executes file-management tools, verifies results, and records task experiences and user feedback.

## 1. Features

- Natural-language goal input.
- LLM-powered task planning using Ollama.
- Structured execution plans with validation.
- Multi-step task execution.
- File searching.
- Folder creation.
- File moving and renaming.
- File and path verification.
- Report generation.
- Short-term memory.
- Persistent episodic memory using SQLite.
- User-feedback recording.
- Rule-based adaptive behaviour.
- Error classification and recovery.
- Workspace path restrictions.
- Execution status and verification reporting.

## 2. Architecture

Nexus uses a modular, single-agent architecture.

The main workflow is:

```text
User
  |
  v
Streamlit Interface
  |
  v
Task Planner <----> Ollama / Qwen
  |
  v
Plan Validation
  |
  v
Agent Controller
  |
  +---- Short-Term Memory
  |
  +---- Episodic Memory (SQLite)
  |
  v
Tool Executor
  |
  +---- Search Files
  +---- Create Folder
  +---- Move File
  +---- Rename File
  +---- Verify Files
  +---- Generate Report
  |
  v
Execution Verification
  |
  v
Recovery and Adaptive Behaviour
  |
  v
Execution Result and User Feedback
```

## 3. Technologies Used

| Technology | Purpose |
|---|---|
| Python | Core agent implementation |
| Streamlit | User interface |
| Ollama | Local LLM integration |
| Qwen3:4B | Current configured planning model |
| Pydantic | Structured plan validation |
| SQLite | Episodic memory |
| Requests | Ollama API communication |
| Pytest | Automated testing |
| Matplotlib | Evaluation visualisation |
| Git/GitHub | Version control |

## 4. Project Structure

```text
desktop-agent/
│
├── app.py
├── config.py
│
├── agent/
│   ├── planner.py
│   ├── executor.py
│   ├── verifier.py
│   ├── recovery.py
│   ├── adaptation.py
│   └── decision_maker.py
│
├── tools/
│   ├── file_search.py
│   ├── folder_manager.py
│   ├── file_manager.py
│   └── report_generator.py
│
├── memory/
│   ├── short_term.py
│   └── episodic.py
│
├── safety/
│   └── guardrails.py
│
├── evaluation/
│   ├── test_cases.json
│   ├── evaluate.py
│   ├── metrics.py
│   └── results.json
│
├── tests/
├── reports/
├── logs/
└── workspace/
```

## 5. Requirements

- Python 3.11 or a compatible Python version.
- Ollama installed and running.
- The configured Qwen model downloaded locally.
- Git (optional, for cloning the repository).

## 6. Installation

Clone the repository:

```bash
git clone https://github.com/SonamYangchen1177/nexus-intelligent-desktop-agent.git
cd nexus-intelligent-desktop-agent
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it in Git Bash on Windows:

```bash
source .venv/Scripts/activate
```

Alternatively, in Windows Command Prompt:

```cmd
.venv\Scripts\activate
```

Install the project dependencies using the repository's dependency file, if included:

```bash
pip install -r requirements.txt
```

Start Ollama and ensure the model configured in `config.py` is available.

For example:

```bash
ollama pull qwen3:4b
```

Check that Ollama is running and the model is available:

```bash
ollama list
```

## 7. Configuration

The Ollama settings are maintained in `config.py`.

Example configuration:

```python
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen3:4b"
```

The workspace directory is configured by the project. File operations should remain within that approved workspace.

If a different model is used, update the model setting and ensure that the model is available through Ollama.

## 8. Running Nexus

Activate the virtual environment and run:

```bash
streamlit run app.py
```

Streamlit will provide a local address in the terminal. Open that address in a web browser to use the application.

## 9. Example Tasks

**Example 1 – Search**

```text
Find all Python files inside the workspace.
```

**Example 2 – Create folders**

```text
Create a folder named nexus_test and create a documents subfolder inside it.
```

**Example 3 – Multi-step task**

```text
Create a folder named project_files, create a reports subfolder inside it, and search for all Python files in the workspace.
```

The exact plan and result depend on the model output and current workspace state.

## 10. Running Tests

Run the automated test suite:

```bash
python -m pytest -v
```

The latest recorded test result during development was:

- 82 passed.
- 2 skipped.
- 0 failed.

Two symbolic-link tests were skipped because the current Windows environment did not permit symbolic-link creation under its permissions.

## 11. Running the Evaluation

Run the evaluation script:

```bash
python evaluation/evaluate.py
```

The evaluation module records task execution results and calculates metrics. It also generates a visualisation in the reports directory.

Review the evaluation configuration and test cases before running it. Existing workspace contents may affect repeated runs unless the test environment is reset or isolated.

## 12. Safety

Nexus uses path validation to restrict file operations to the approved workspace.

Safety measures include:

- Resolving and validating file paths.
- Rejecting paths outside the approved workspace.
- Checking discovered file paths during searches.
- Disabling permanent deletion.
- Validating generated plans before execution.

The current implementation has limitations, including operating-system-dependent symbolic-link testing. It should not be treated as unrestricted operating-system control.

## 13. Evaluation Summary

The latest recorded two-case evaluation produced:

| Metric | Result |
|---|---:|
| Task success rate | 50% |
| Tool-selection accuracy | 50% |
| Verification accuracy | 100% |
| Recovery rate | 0% |
| Average execution time | 276.74 seconds |

The results are based on a small evaluation sample and should not be interpreted as a general performance guarantee.

## 14. Limitations

- Planner timeouts and inconsistent plan generation may occur.
- The quantitative evaluation currently uses a small number of test cases.
- Execution time requires improvement.
- Recovery performance needs additional controlled testing.
- Verification does not yet guarantee that the complete user goal was achieved.
- The system uses one central agent and does not implement multi-agent collaboration.
- RAG is not currently implemented.

## 15. Future Work

Potential improvements include:

- Expanding the evaluation dataset.
- Improving planning reliability and timeout handling.
- Adding isolated test workspaces.
- Improving goal-level verification.
- Measuring the effect of user feedback on future decisions.
- Improving execution tracing and performance reporting.
- Adding semantic file-content retrieval where appropriate.

## 16. Academic Context

This project was developed as an individual engineering project for:

**DAT404 – Intelligent and Generative Agents (A)**  
**Assignment D – Build, Evaluate and Defend a Custom AI Agent**  
**Sherubtse College, Royal University of Bhutan**

The project demonstrates planning, decision making, tool use, memory, feedback, adaptation, evaluation, and safety in an LLM-powered intelligent agent.

## 17. Author

**Sonam Yangchen**  
Data Science and Data Analytics  
Sherubtse College  
Royal University of Bhutan
