Excellent. I am ready. You've set the perfect stage: the goal is to create the **System Architecture Document (SAD)**, the master technical blueprint for the PrezI Hybrid App.

My entire focus will be on architecting a system that delivers the **power and local file access of a desktop application** while ensuring the user experience is **indistinguishable from the fluid, beautiful web mockups** you love. Every decision in this document is made to serve that primary goal.

Here is the document.

---

# PrezI: System Architecture Document (SAD)

*   **Version:** 1.0
*   **Date:** June 7, 2025
*   **Author:** PrezI Vision Synthesis AI
*   **Status:** Finalized

## 1. Overview & Architectural Vision

### 1.1. Purpose
This document specifies the complete technical architecture for the PrezI application. It serves as the master blueprint for development, defining the system's components, their interactions, and the underlying technologies.

### 1.2. Architectural Vision
The core vision for PrezI is to deliver a **"Best of Both Worlds" Hybrid Application**. This architecture is explicitly chosen to achieve two non-negotiable goals derived from the Product Requirements Document (PRD):

1.  **Native Power:** The application must have unrestricted, high-performance access to the user's local file system and be able to directly integrate with locally installed software (Microsoft PowerPoint) via COM automation.
2.  **Web-First Experience:** The User Interface (UI) must have the exact look, feel, and fluid interactivity of the high-fidelity web mockups. The user experience is paramount.

To achieve this, PrezI will be a native desktop application that renders its entire interface using web technologies.

---

## 2. High-Level Architecture Diagram

The PrezI application is composed of three primary layers communicating over a local bridge.

```
+---------------------------------------------------------------------------------+
|                                 USER'S COMPUTER                                 |
|                                                                                 |
| +-----------------------------+      +-------------------------+      +-------+ |
| |    Electron Desktop Shell   |      |   PowerPoint / Office   |      | OpenAI| |
| |      (The App Wrapper)      |      |   (via COM Automation)  |      |  API  | |
| +-----------------------------+      +-------------------------+      +-------+ |
| |                             |                 ^   ^                     ^     |
| |  +-----------------------+  |                 |   |                     |     |
| |  |     Frontend UI       |  |                 |   | (HTTPS API Call)    |     |
| |  | (The "Cockpit")       |  |                 |   |                     |     |
| |  | - HTML, CSS, JS       |  | (Direct Control) |   |                     |     |
| |  +-----------------------+  |                 |   |                     |     |
| |            ^                |                 |   |                     |     |
| |            | (Localhost HTTP) |                 |   +---------------------+     |
| |            v                |                 v                         |     |
| |  +-----------------------+  |  +-------------------------------------+  |     |
| |  | Communication Bridge  |  |  |        Python Backend               |  |     |
| |  | (FastAPI Local Server)|  |  |        (The "Engine")               |  |     |
| |  +-----------------------+  |  +-------------------------------------+  |     |
| |            ^                |                 ^          ^            |     |
| |            |                |                 |          |            |     |
| |            +----------------------------------+          |            |     |
| |                                                          |            |     |
| +----------------------------------------------------------+------------+-----+
| |                                                          v            |
| |                                                +------------------+   |
| |                                                |  SQLite Database |   |
| |                                                | (Local .db File) |   |
| |                                                +------------------+   |
| |                                                                       |
+-------------------------------------------------------------------------+
```

---

## 3. Component Deep Dive

### 3.1. Electron Desktop Shell (The Wrapper)
*   **Technology:** [Electron](https://www.electronjs.org/)
*   **Purpose:** To provide a native, cross-platform (Windows, macOS) application window and act as the "shell" for the web-based UI.
*   **Key Responsibilities:**
    *   Create the main browser window.
    *   Load the `index.html` of the Frontend UI.
    *   Manage the lifecycle of the Python Backend process (start it on app launch, terminate it on app close).
    *   Handle native OS interactions like window controls, menus, and notifications.

### 3.2. Frontend UI (The "Cockpit")
*   **Technology:** HTML5, CSS3, JavaScript (Vanilla JS or a lightweight framework like Lit).
*   **Purpose:** To render the *entire* user interface. This is not a "skin" on a native app; it *is* the app's interface.
*   **Key Responsibilities:**
    *   Implement the complete visual design defined in the **UI/UX Design System**.
    *   Handle all user interactions (clicks, drags, typing).
    *   Manage UI state (e.g., which slide is selected, current search query).
    *   Send user commands to the Python Backend via the Communication Bridge.
    *   Receive data and status updates from the backend and render them dynamically.

### 3.3. Communication Bridge
*   **Technology:** [FastAPI](https://fastapi.tiangolo.com/) (Python web framework).
*   **Purpose:** To enable secure, high-speed communication between the JavaScript Frontend and the Python Backend.
*   **Key Responsibilities:**
    *   On app launch, the Python Backend will start a FastAPI server that listens *only* on a local port (e.g., `127.0.0.1:8765`). This is inaccessible from outside the user's machine.
    *   Define a clear RESTful API for all interactions (e.g., `POST /search`, `POST /create-plan`).
    *   Use JSON as the data exchange format.
    *   Utilize WebSockets for pushing real-time progress updates from the backend to the frontend without the frontend needing to poll.

### 3.4. Python Backend (The "Engine")
*   **Technology:** Python 3.10+
*   **Purpose:** To be the application's brain and workhorse, handling all core logic and heavy lifting.
*   **Modular Architecture:**
    *   `api_server.py`: The FastAPI entry point. Defines all API endpoints and routes requests to the appropriate service.
    *   `database_manager.py`: Handles all interactions with the SQLite database. Contains all SQL queries and data models.
    *   `powerpoint_automator.py`: Isolates all COM automation logic for interacting with Microsoft PowerPoint. Responsible for slide conversion and export.
    *   `prezi_agent.py`: The core AI module. Responsible for communicating with the OpenAI API, prompt engineering, and implementing PrezI's decision-making logic.
    *   `file_system_manager.py`: Manages all project files and directories.

### 3.5. Database
*   **Technology:** [SQLite](https://www.sqlite.org/index.html)
*   **Purpose:** To store all application metadata in a single, portable file on the user's local disk.
*   **Schema Highlights:**
    *   `Projects`: Stores project names and metadata.
    *   `Files`: Stores paths to imported `.pptx` files.
    *   `Slides`: Stores extracted text, speaker notes, and a path to the generated thumbnail image for each slide.
    *   `Elements`: Stores bounding box coordinates and extracted text for individual slide elements.
    *   `Keywords`: Stores all keywords.
    *   `Keyword_Links`: A mapping table to link keywords to slides and elements (many-to-many relationship).

---

## 4. Data Flow Diagrams

### 4.1. User Workflow: Natural Language Search
*A simple read operation.*

1.  **UI:** User types "revenue charts from Q4" into the command bar.
2.  **UI (JS):** Captures the input and sends a `POST` request to `http://127.0.0.1:8765/search` with the JSON body: `{ "query": "revenue charts from Q4" }`.
3.  **Bridge (FastAPI):** Receives the request and routes it to the search handler function.
4.  **Engine (Python):** The handler function passes the query to `prezi_agent.py`.
5.  **Engine (PrezI Agent):** Sends a structured prompt to the OpenAI API to interpret the intent. OpenAI returns structured data like `{ "keywords": ["revenue", "chart", "Q4"], "element_type": "chart" }`.
6.  **Engine (Python):** The PrezI Agent uses this structured data to query the SQLite database via `database_manager.py`.
7.  **Engine (Database):** Returns a list of slide IDs and their thumbnail paths that match the query.
8.  **Engine -> Bridge -> UI:** The list of slides is returned as a JSON array to the Frontend.
9.  **UI (JS):** Receives the JSON and dynamically re-renders the slide library grid to display only the matching slides, with a smooth animation.

### 4.2. User Workflow: "Create My Presentation"
*A complex, long-running operation with asynchronous updates.*

1.  **UI:** User types "Create a 5-minute investor pitch" and hits Enter.
2.  **UI -> Bridge -> Engine:** A `POST` request is sent to `/create-plan` with the user's intent.
3.  **Engine (PrezI Agent):** Analyzes the intent, queries the database for relevant slides, and formulates a step-by-step plan.
4.  **Engine -> Bridge -> UI:** The plan is returned as a JSON object. The UI displays the "Visual Plan" and waits for user confirmation.
5.  **UI:** User clicks "Execute Plan."
6.  **UI -> Bridge -> Engine:** A `POST` request is sent to `/execute-plan` with the plan's ID. This request returns an immediate `202 Accepted` response.
7.  **Engine (Python):** The backend starts the long-running task in a separate thread to avoid blocking the API server.
8.  **Engine -> Bridge -> UI (WebSocket):** As the backend completes each step (e.g., "Finding slides...", "Formatting title..."), it sends a progress update message over the WebSocket connection.
9.  **UI (JS):** The WebSocket listener receives these messages and updates the progress overlay in real-time.
10. **Engine -> Bridge -> UI (WebSocket):** Upon completion, a final "success" message is sent. The UI displays the "Done!" state and refreshes the assembly panel with the newly created presentation.

---

## 5. Technology Stack Summary

| Layer | Technology | Rationale |
| :--- | :--- | :--- |
| **Desktop Wrapper** | Electron | Mature, cross-platform, excellent community support. |
| **UI Frontend** | HTML5, CSS3, JavaScript | The only way to guarantee the exact look and feel of the mockups. |
| **Communication** | FastAPI (Python) | Lightweight, high-performance, async-native, provides auto-documentation. |
| **Backend Engine** | Python 3.10+ | Robust, excellent libraries for AI (OpenAI) and data (SQLite). Matches existing PoC. |
| **Database** | SQLite | Serverless, zero-configuration, single-file, perfect for a local-first desktop app. |
| **AI Services** | OpenAI API (GPT-4o, o3) | State-of-the-art models for the required natural language and reasoning tasks. |
| **Office Integration**| `pywin32` (COM) | The standard for direct, low-level control of Microsoft Office on Windows. |

---

## 6. Architectural Rationale & Trade-offs

*   **Hybrid vs. Native (Qt):** While a pure Qt app could be performant, achieving the fluid, modern, web-like aesthetic you desire is exponentially more difficult and time-consuming. The hybrid approach guarantees the UX.
*   **Hybrid vs. Pure Web App:** A pure web app is not viable due to the non-negotiable requirement for deep local file system access and direct COM automation with PowerPoint. Browser sandboxing makes this impossible.
*   **FastAPI vs. Flask:** FastAPI is chosen over Flask for its native `asyncio` support, which is critical for managing long-running background tasks (like presentation generation) without freezing the application.

This architecture is the optimal solution to satisfy all of PrezI's unique product requirements.