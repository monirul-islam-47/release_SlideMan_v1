Of course. My apologies for making you piece it together. You are absolutely correct; this is a foundational document and must be presented as a single, complete, and authoritative source of truth. There will be no need for copy-pasting.

Here is the entire, final version of the **PrezI Development & Testing Plan**, amended with the critical continuity protocols. This is the master instruction manual for the AI coding agent.

---

# PrezI: Development & Testing Plan

*   **Version:** 1.1
*   **Date:** June 7, 2025
*   **Author:** PrezI Vision Synthesis AI
*   **Status:** Finalized & Ready for Implementation

## 1. Introduction & Guiding Philosophy

### 1.1. Purpose
This document is the master implementation plan for the PrezI application. It synthesizes the requirements from all preceding documents (**PRD, SAD, Design System, AIDD, Database Schema**) into a prioritized, step-by-step development roadmap. It is the primary instruction set for the AI coding agent.

### 1.2. Development Philosophy
The AI agent must adhere to the following principles:

1.  **Document-Driven Development:** The specifications within the "Founder's Briefcase" are the single source of truth. No feature or design element shall be implemented unless it is specified in these documents.
2.  **Incremental & Verifiable Progress:** The application will be built in logical, testable sprints. The agent will report on the completion of each major task and await confirmation before proceeding.
3.  **Component-Based Architecture:** Both frontend and backend components shall be modular and reusable to ensure maintainability and scalability.
4.  **Quality is Paramount:** Adherence to the **Definition of "Done"** is non-negotiable for every task.
5.  **Explicit State:** The state of the project must reside entirely within the committed code and these documents, not in any single agent's session memory. This is critical for seamless handover.

## 2. Agent Handover Protocol & Continuity Plan

To mitigate context loss between development sessions, the following protocol is **mandatory**. It ensures that any AI agent can fluidly take over the project at any point.

### 2.1. End-of-Session Procedure: "The Commit & Handover"

Before ending any work session, the current AI agent **must** perform the following four steps in order:

1.  **Commit Code:** All newly created or modified files must be committed to the version control system. The commit message **must** follow this format:
    *   `feat(scope): Description (Task X.Y)` for new features.
    *   `fix(scope): Description (Task X.Y)` for bug fixes.
    *   *Example:* `feat(api): Implement GET /slides endpoint (Task 3.1)`
2.  **Run All Tests:** The agent must execute the *entire* test suite (`unit`, `integration`, and `E2E` tests) and paste the summary output. This serves as proof that the new code is correct and has not introduced any regressions. Work is not considered complete if any test fails.
3.  **Update the Master Plan:** The agent must edit **this document** (`Development & Testing Plan`) and place a checkmark (`✅`) next to the specific Task ID(s) it has just completed and verified.
4.  **Generate Handover Note:** The agent must conclude its session with a structured handover note in the following format:
    ```
    ---
    **HANDOVER NOTE**
    **Session Summary:** A brief, one-sentence summary of the work accomplished.
    **Last Task Completed:** Task X.Y - [Task Description]
    **Verification:** All tests passed successfully. [Link to test results if applicable].
    **Next Task:** Task X.Z - [Task Description]
    **Notes & Challenges:** [Any challenges encountered or important context for the next agent].
    ---
    ```

### 2.2. Start-of-Session Procedure: "The Wake-Up & Onboard"

To begin a new work session, any new AI agent **must** perform the following five steps in order:

1.  **Verify Environment:** Ensure the local development environment is correctly set up by running the dependency installation command (e.g., `pip install -r requirements.txt`).
2.  **Review Key Documents:** Ingest the necessary context by reading the following documents *in this specific order*:
    1.  This **Development & Testing Plan** to understand the immediate state of progress.
    2.  The **Handover Note** from the previous agent's session.
    3.  The specific design/spec documents relevant to the *next assigned task*.
3.  **Run All Tests:** Before writing any new code, execute the *entire* test suite to verify that the project is in a clean, working state. This builds trust in the previous agent's work.
4.  **Acknowledge Current State:** The agent must begin its work with a statement confirming its understanding of the project's status.
    *   *Example:* "I have successfully onboarded. The last completed task was 3.1. All tests are passing. I will now begin work on Task 3.2: Implement the UI for the Main Content Area."
5.  **Proceed with the Next Task:** Begin development on the next unchecked task in the Sprint Breakdown.

This protocol ensures that the project's state is always explicit, verifiable, and ready for a seamless handover, making the development process robust and agent-agnostic.

## 3. Phased Rollout Strategy

The development is structured into three major phases, ensuring that a valuable, stable core is built first, with AI magic layered on top.

```mermaid
graph TD
    subgraph Phase 1: The Functional Core (MVP)
        A[Foundation & Setup] --> B[Database & Models] --> C[File Import & Processing] --> D[Core UI & Slide Library] --> E[Manual Tagging & Search] --> F[Manual Assembly & Export]
    end
    subgraph Phase 2: The Intelligent Assistant (Release 1.0)
        G[PrezI Core Integration] --> H[AI-Powered Semantic Search] --> I[Proactive Suggestions & AI Tagging]
    end
    subgraph Phase 3: The Automated Partner (Release 2.0)
        J[The Visual Plan Workflow] --> K[Automated Presentation Engine] --> L[Style Harmonization Magic] --> M[Final Polish & Onboarding]
    end

    F --> G
    I --> J
```

## 4. Detailed Sprint Breakdown

This is the tactical, sequential plan for development.

### **Sprint 0: Project Foundation & Environment Setup**
*Goal: Create a runnable, empty shell of the application.*
| Task ID | Task Description | Key Documents | Status |
| :--- | :--- | :--- | :--- |
| ☐ **0.1**| Initialize the project directory with the specified `frontend` and `backend` folder structure. | SAD | |
| ☐ **0.2**| Set up the **Electron** project, configuring `main.js` to create a main window. | SAD | |
| ☐ **0.3**| Configure the Electron main window to load the `frontend/index.html` file on startup. | SAD, Design System | |
| ☐ **0.4**| Implement the Python backend launcher. The Electron app must start the **FastAPI** local server on launch and terminate it on exit. | SAD | |
| ☐ **0.5**| Establish the basic **WebSocket** communication bridge. Confirm that a "connected" message can be sent from backend to frontend on startup. | SAD, API Spec | |

### **Phase 1: The Functional Core (MVP)**

#### **Sprint 1: Database & Core Models**
*Goal: Implement the application's memory.*
| Task ID | Task Description | Key Documents | Status |
| :--- | :--- | :--- | :--- |
| ☐ **1.1**| Create the SQLite database initialization script. | Database Schema | |
| ☐ **1.2**| Implement all `CREATE TABLE` and `CREATE INDEX` statements exactly as specified. | Database Schema | |
| ☐ **1.3**| In `database_manager.py`, create Python functions for all basic CRUD operations (Create, Read, Update, Delete) for each table. | Database Schema | |

#### **Sprint 2: File Import & Processing**
*Goal: Get user content into the system reliably.*
| Task ID | Task Description | Key Documents | Status |
| :--- | :--- | :--- | :--- |
| ☐ **2.1**| Implement the `POST /projects/{project_id}/import` endpoint. | API Spec, SAD | |
| ☐ **2.2**| In `powerpoint_automator.py`, implement the slide conversion logic using COM automation. | SAD, PRD | |
| ☐ **2.3**| Logic must extract slide thumbnails, title text, body text, and speaker notes, saving them to the database. | Database Schema | |
| ☐ **2.4**| Implement the real-time `TASK_PROGRESS` updates via WebSocket for the import process. | API Spec | |
| ☐ **2.5**| Implement the UI for the "Import Progress" overlay as per the Wireframes. | Wireframes, Design System | |

#### **Sprint 3: The Slide Library UI**
*Goal: Beautifully display the imported slides.*
| Task ID | Task Description | Key Documents | Status |
| :--- | :--- | :--- | :--- |
| ☐ **3.1**| Implement the `GET /slides` endpoint. | API Spec | |
| ☐ **3.2**| Implement the frontend UI for the Main Content Area (Slide Library), including the responsive grid of **Slide Cards**. | Wireframes, Design System | |
| ☐ **3.3**| The UI must dynamically fetch and render slides from the backend when a project is opened. | API Spec, Wireframes | |

#### **Sprint 4: Manual Tagging & Search**
*Goal: Allow users to organize and find their content.*
| Task ID | Task Description | Key Documents | Status |
| :--- | :--- | :--- | :--- |
| ☐ **4.1**| Implement the full API for keywords (`GET /keywords`, `POST /slides/{slide_id}/keywords`, etc.). | API Spec, Database Schema | |
| ☐ **4.2**| Implement the Keyword Panel UI, including clickable Keyword Pills that filter the library. | Wireframes, Design System | |
| ☐ **4.3**| Implement the Element Mode UI, allowing users to select element bounding boxes and assign keywords. | PRD, Wireframes | |
| ☐ **4.4**| Connect the Command Bar to the `GET /slides` endpoint to enable basic keyword search. | API Spec | |

#### **Sprint 5: Manual Assembly & Export**
*Goal: Allow users to create a presentation and get a tangible result.*
| Task ID | Task Description | Key Documents | Status |
| :--- | :--- | :--- | :--- |
| ☐ **5.1**| Implement the full API for the assembly (`GET /assembly`, `POST /assembly/slides`, etc.). | API Spec | |
| ☐ **5.2**| Implement the Assembly Panel UI, including drag-and-drop functionality from the library. | Wireframes, Design System | |
| ☐ **5.3**| Implement the `POST /export` endpoint and the backend logic in `powerpoint_automator.py` to create a `.pptx` file from assembled slide IDs. | API Spec, SAD | |
| ☐ **5.4**| Implement the "Export Options" and "Export Progress" UI. | Wireframes, Design System | |

*(Further Sprints for Phases 2 & 3 will be detailed in the same format)*

## 5. Definition of "Done" (DoD)

A task or feature is only considered "Done" when it meets **all** of the following criteria:
1.  **Code Complete:** All required code is written and adheres to standard best practices.
2.  **Functionality Met:** The feature works exactly as described in the **PRD**.
3.  **Design Adherence:** The UI is pixel-perfect according to the **UI/UX Design System** and **Wireframes**.
4.  **API Contract Fulfilled:** All interactions between frontend and backend match the **API Specification**.
5.  **Database Integrity:** All data is stored correctly according to the **Database Schema**.
6.  **AI Logic Implemented:** The AI behavior matches the rules and prompts in the **AIDD**.
7.  **Testing Passed:** All relevant unit and integration tests pass with 100% success.
8.  **No Regressions:** The new code does not break any existing, previously completed features.

## 6. Testing Strategy

Quality will be ensured through a multi-layered testing approach (the "Testing Pyramid").

1.  **Unit Tests (Foundation):**
    *   **Backend:** Every Python function in the `services` and `managers` will have corresponding tests using `pytest`. (e.g., `test_database_manager.py` will test all CRUD functions).
    *   **Frontend:** Key JavaScript functions (e.g., API callers, state managers) will be tested using a framework like `Jest`.
2.  **Integration Tests (Mid-level):**
    *   These will test the critical connection points.
    *   **API Tests:** A suite of tests will be written to call every single API endpoint and verify that it returns the correct data and status codes, as defined in the **API Specification**.
    *   **Database Tests:** Tests to ensure that complex database operations involving multiple tables work as expected.
3.  **End-to-End (E2E) Tests (Peak):**
    *   Using a tool that can control Electron apps (e.g., Playwright), we will create automated scripts that simulate full user workflows.
    *   **Example E2E Test Script: `test_create_presentation.js`**
        1.  Launch the PrezI application.
        2.  Programmatically click the "Import Files" button.
        3.  Simulate a file selection.
        4.  Wait until the `TASK_PROGRESS` WebSocket event reports completion.
        5.  Verify that slide thumbnails have appeared in the UI.
        6.  Programmatically drag three slides to the assembly panel.
        7.  Verify the assembly count updates to "3".
        8.  Click "Export" and verify the success notification appears.

## 7. First Steps for the AI Coding Agent

To begin, you will execute the following sequence:

1.  **Acknowledge & Confirm:** Confirm that you have read and understood all eight documents in the "Founder's Briefcase," paying special attention to the **Agent Handover Protocol** in this document.
2.  **Execute Sprint 0:** Complete all tasks from **Sprint 0** to create the project's foundational shell.
3.  **Follow Handover Protocol:** At the end of your work, meticulously follow the **End-of-Session Procedure** defined in Section 2.1.

This plan provides the precise, structured, and comprehensive instructions necessary to build the PrezI application exactly as envisioned, ensuring consistency and quality throughout the development lifecycle.