Thank you for your trust. It's a privilege to continue building this vision with you. The diligence and thoroughness you appreciate are a direct result of the clarity and passion you've provided.

We have established a robust foundation. Now, we must architect the application's "nervous system"—the precise, unbreakable communication protocol that allows PrezI's beautiful "body" (the UI) to talk to her powerful "brain" (the Python Engine).

This next document is the **Complete API Specification**. It is the technical contract that governs all data flow within the application. By defining this now, we eliminate the biggest source of bugs in software development: miscommunication between the frontend and backend. Every command, every piece of data, and every possible error will be explicitly defined.

Let us proceed.

---

# PrezI: Complete API Specification

*   **Version:** 1.2
*   **Date:** June 15, 2025
*   **Author:** PrezI Vision Synthesis AI
*   **Status:** Amended & Finalized

## 1. Introduction

This document provides the complete specification for the local RESTful API and WebSocket communication bridge that connects the PrezI Frontend (UI) to the PrezI Backend (Python Engine). This is the definitive contract for all internal data exchange.

## 2. General Principles

*   **Base URL:** All API endpoints are prefixed with `http://127.0.0.1:8765/api/v1`. The server will only be accessible from the local machine.
*   **Data Format:** All request and response bodies must be in `application/json` format.
*   **Authentication:** None required, as the server is not exposed externally.
*   **Standard Success Response:** All successful `POST`, `PUT`, `DELETE` requests will return a `200 OK` with a confirmation message. `GET` requests will return `200 OK` with the requested data.
*   **Standard Error Response:** All client-side (`4xx`) or server-side (`5xx`) errors will return a JSON object with the following structure:
    ```json
    {
      "error": {
        "code": "ERROR_CODE_STRING",
        "message": "A human-readable explanation of the error."
      }
    }
    ```

## 3. API Endpoints

### 3.1. Projects
*   `POST /projects`
    *   **Description:** Creates a new project.
    *   **Request Body:** `{ "name": "string" }`
    *   **Success Response:** `{ "project_id": "integer", "name": "string" }`
*   `GET /projects`
    *   **Description:** Retrieves a list of all projects.
    *   **Success Response:** `[{ "project_id": "integer", "name": "string", "slide_count": "integer" }]`
*   `POST /projects/{project_id}/import`
    *   **Description:** Imports PowerPoint files into a specific project. This is a long-running, asynchronous task.
    *   **Request Body:** `{ "file_paths": ["string"] }`
    *   **Success Response (202 Accepted):** `{ "task_id": "string", "message": "Import process started." }` (Progress will be sent via WebSocket).

### 3.2. Slides & Keywords
*   `GET /slides`
    *   **Description:** Retrieves slides, with optional filtering.
    *   **Query Parameters:** `?project_id=integer&keyword_ids=[integer]&search_query=string`
    *   **Success Response:** `[{ "slide_id": "integer", "thumbnail_path": "string", "title": "string" }]`
*   `GET /slides/{slide_id}`
    *   **Description:** Retrieves detailed information for a single slide.
    *   **Success Response:** `{ "slide_id": "integer", "full_image_path": "string", "title": "string", "body_text": "string", "speaker_notes": "string", "keywords": [{"keyword_id": "integer", "text": "string"}] }`
*   `POST /slides/{slide_id}/keywords`
    *   **Description:** Adds a keyword to a specific slide.
    *   **Request Body:** `{ "keyword_text": "string" }`
    *   **Success Response:** `{ "message": "Keyword added successfully." }`
*   `GET /keywords`
    *   **Description:** Retrieves all keywords for a given project.
    *   **Query Parameters:** `?project_id=integer`
    *   **Success Response:** `[{ "keyword_id": "integer", "text": "string", "color_hex": "string" }]`
*   `PUT /keywords/{keyword_id}`
    *   **Description:** Updates a keyword (e.g., renames it or changes its color).
    *   **Request Body:** `{ "text": "string", "color_hex": "string" }`
    *   **Success Response:** `{ "message": "Keyword updated." }`

### 3.3. Assembly
*   `GET /assembly`
    *   **Description:** Gets the current state of the assembly panel.
    *   **Success Response:** `{ "slides": [{"slide_id": "integer", "thumbnail_path": "string", "title": "string"}], "estimated_duration_minutes": "integer" }`
*   `POST /assembly/slides`
    *   **Description:** Adds a slide to the assembly.
    *   **Request Body:** `{ "slide_id": "integer", "position": "integer" }` (position is optional)
    *   **Success Response:** The updated assembly object (as in `GET /assembly`).
*   `PUT /assembly/slides`
    *   **Description:** Reorders the slides in the assembly.
    *   **Request Body:** `{ "slide_order": ["integer"] }` (An array of slide_ids in the new order).
    *   **Success Response:** The updated assembly object.
*   `DELETE /assembly`
    *   **Description:** Clears the entire assembly.
    *   **Success Response:** `{ "message": "Assembly cleared." }`

### 3.4. PrezI AI Engine
*   `POST /prezi/interpret`
    *   **Description:** Takes a user's natural language command and returns the structured intent.
    *   **Request Body:** `{ "command": "string", "context": { "current_project_id": "integer" } }`
    *   **Success Response:** The structured JSON object as defined in the `AIDD` (e.g., `{ "primary_action": "CREATE", ... }`).
*   `POST /prezi/plan`
    *   **Description:** Generates a Visual Plan based on a structured intent.
    *   **Request Body:** The JSON output from `/prezi/interpret`.
    *   **Success Response:** The JSON plan object as defined in the `AIDD` (e.g., `{ "plan": [{...}] }`).
*   `POST /prezi/execute`
    *   **Description:** Executes a PrezI plan. This is a long-running, asynchronous task.
    *   **Request Body:** `{ "plan": [...] }` (The plan object from `/prezi/plan`).
    *   **Success Response (202 Accepted):** `{ "task_id": "string", "message": "PrezI is on it! Execution has started." }` (Progress will be sent via WebSocket).

### 3.5. Export
*   `POST /export`
    *   **Description:** Exports the current assembly. This is a long-running, asynchronous task.
    *   **Request Body:** `{ "filename": "string", "location_path": "string", "format": "pptx" | "pdf" }`
    *   **Success Response (202 Accepted):** `{ "task_id": "string", "message": "Export process started." }` (Progress will be sent via WebSocket).

---

## 4. WebSocket Communication

A WebSocket connection will be established on app startup for real-time, asynchronous communication from the backend to the frontend.

*   **URL:** `ws://127.0.0.1:8765/ws`

### 4.1. Server-to-Client Events
The backend will push messages with the following structure:
```json
{
  "event_type": "string",
  "payload": { ... }
}
```

*   **Event: `TASK_PROGRESS`**
    *   **Description:** Sent during long-running tasks like import, export, or AI execution.
    *   **Payload:**
        ```json
        {
          "task_id": "string",
          "status": "processing" | "completed" | "failed",
          "current_step": "integer",
          "total_steps": "integer",
          "message": "Human-readable progress message (e.g., 'Analyzing slide 15 of 50...')"
        }
        ```
*   **Event: `PREZI_SUGGESTION`**
    *   **Description:** Sent when PrezI has a proactive suggestion for the user.
    *   **Payload:**
        ```json
        {
          "suggestion_id": "string",
          "message": "The suggestion text from PrezI (e.g., 'A summary slide here might improve the flow.').",
          "actions": [
            { "label": "Create It", "api_call": "/prezi/execute", "body": "{...}" },
            { "label": "Dismiss", "api_call": null }
          ]
        }
        ```
*   **Event: `LIBRARY_UPDATED`**
    *   **Description:** Sent whenever the slide library changes (e.g., after an import). The UI should listen for this and refresh its view.
    *   **Payload:** `{ "project_id": "integer" }`

---

## 5. Onboarding API

The following endpoints specifically support the first-time user experience and interactive onboarding flow based on a defined state machine.

### 5.1. Onboarding State Management

*   `GET /onboarding/state`
    *   **Description:** Retrieves the current onboarding state for the user.
    *   **Success Response:** 
        ```json
        { 
          "onboarding_completed": boolean, 
          "current_state": "WELCOME|API_SETUP|FEATURE_TOUR|IMPORT_FIRST|COMMAND_BAR|ASSEMBLY_PANEL|GRADUATION",
          "progression": integer, 
          "max_progression": integer,
          "branch_path": "FEATURE_FIRST|IMPORT_FIRST|null"
        }
        ```

*   `PUT /onboarding/state`
    *   **Description:** Transitions to a new onboarding state.
    *   **Request Body:** 
        ```json
        { 
          "new_state": "WELCOME|API_SETUP|FEATURE_TOUR|IMPORT_FIRST|COMMAND_BAR|ASSEMBLY_PANEL|GRADUATION",
          "branch_path": "FEATURE_FIRST|IMPORT_FIRST" (optional)
        }
        ```
    *   **Success Response:** 
        ```json
        {
          "message": "Onboarding state transitioned successfully.",
          "current_state": "string",
          "progression": integer
        }
        ```

*   `POST /onboarding/complete`
    *   **Description:** Marks the onboarding process as completed and transitions to GRADUATION state.
    *   **Success Response:** `{ "message": "Onboarding completed.", "analytics_summary": { "time_to_completion": "string", "path_taken": "string" } }`

### 5.2. Onboarding Content

*   `GET /onboarding/content`
    *   **Description:** Retrieves the content for a specific onboarding state.
    *   **Query Parameters:** `?state=string&branch_path=string`
    *   **Success Response:**
        ```json
        {
          "state": "string",
          "title": "string",
          "content": "string",
          "ui_highlights": ["ids of UI elements to highlight"],
          "primary_action": {
            "label": "string",
            "action_type": "next_state|complete|demo_action",
            "target_state": "string" (required if action_type is next_state),
            "api_call": "/endpoint/to/call" (optional)
          },
          "secondary_actions": [
            {
              "label": "string",
              "action_type": "branch_select|skip|dismiss",
              "target_state": "string" (optional),
              "branch_path": "string" (required if action_type is branch_select)
            }
          ]
        }
        ```

*   `GET /onboarding/branches`
    *   **Description:** Retrieves available onboarding branch paths from the current state.
    *   **Query Parameters:** `?current_state=string`
    *   **Success Response:** 
        ```json
        {
          "available_branches": [
            {
              "branch_id": "FEATURE_FIRST|IMPORT_FIRST",
              "title": "string",
              "description": "string",
              "target_state": "string"
            }
          ]
        }
        ```

### 5.3. API Key Management

*   `POST /auth/validate-api-key`
    *   **Description:** Validates an OpenAI API key before secure storage.
    *   **Request Body:** `{ "api_key": "string" }`
    *   **Success Response:** `{ "valid": boolean, "model_access": ["gpt-4o", "gpt-4o-mini", etc], "message": "string" }`

*   `POST /auth/store-api-key`
    *   **Description:** Securely stores a validated API key in the OS credential store.
    *   **Request Body:** `{ "api_key": "string" }`
    *   **Success Response:** `{ "success": boolean, "message": "API key securely stored." }`
    *   **Error Responses:** 
        - `{ "error": { "code": "INVALID_API_KEY", "message": "The provided API key is invalid." } }`
        - `{ "error": { "code": "STORAGE_ERROR", "message": "Could not access OS credential store." } }`

*   `GET /auth/api-key-status`
    *   **Description:** Checks if a valid API key is stored and accessible.
    *   **Success Response:** `{ "key_configured": boolean, "model_access": ["string"], "token_usage": { "used": integer, "available": integer } }`

### 5.4. Onboarding Assistant

*   `POST /onboarding/assistant`
    *   **Description:** Triggers the onboarding assistant to generate contextual help.
    *   **Request Body:**
        ```json
        {
          "current_state": "string",
          "feature_context": "string",
          "user_actions": [{"action": "string", "timestamp": "ISO8601-timestamp"}],
          "user_difficulty_signals": ["string"] (optional)
        }
        ```
    *   **Success Response:** 
        ```json
        { 
          "assistant_message": "string", 
          "next_action_hint": "string",
          "ui_element_focus": "string" (optional)
        }
        ```

### 5.5. Onboarding Analytics

*   `POST /onboarding/analytics`
    *   **Description:** Records analytics about user progression through onboarding.
    *   **Request Body:**
        ```json
        {
          "event_type": "state_enter|state_exit|action_taken|difficulty_signal",
          "state": "string",
          "action": "string" (required if event_type is action_taken),
          "time_spent_ms": integer (required if event_type is state_exit),
          "difficulty_type": "string" (required if event_type is difficulty_signal)
        }
        ```
    *   **Success Response:** `{ "recorded": true }`

*   `GET /onboarding/analytics/summary`
    *   **Description:** Retrieves a summary of onboarding analytics for the current user.
    *   **Success Response:**
        ```json
        {
          "onboarding_started": "ISO8601-timestamp",
          "onboarding_completed": "ISO8601-timestamp" | null,
          "total_time_spent_ms": integer,
          "path_taken": "FEATURE_FIRST|IMPORT_FIRST",
          "states_visited": ["string"],
          "difficulty_signals": integer
        }
        ```

This API Specification provides the exact technical contract needed to build PrezI. It ensures that the frontend and backend can be developed independently while guaranteeing seamless integration, ultimately delivering the fluid and intelligent experience defined in our vision.