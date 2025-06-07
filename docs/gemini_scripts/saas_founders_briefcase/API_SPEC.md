Of course.

We have now fully defined the product, the cloud architecture, the web-native design system, and the collaborative AI brain. The next critical step is to define the "language" of our system—the precise, unambiguous contract that allows all these independent components to communicate flawlessly.

This document is the master blueprint for all data exchange within the PrezI Cloud platform.

Here is **Document 5 of 10**, the definitive API Specification for the PrezI SaaS platform.

---
---

### **Document 5 of 10: API Specification - SaaS Edition**

# PrezI Cloud: Complete API Specification

*   **Version:** 2.0 (SaaS)
*   **Date:** June 7, 2025
*   **Status:** Finalized

## 1. General Principles

*   **Base URL:** All API endpoints are prefixed with `https://api.prezi.ai/v1`.
*   **Authentication:** All requests must include a `Authorization: Bearer <JWT_TOKEN>` header. The JWT (JSON Web Token) will be issued by the Authentication Service upon successful login.
*   **Data Format:** All request and response bodies must be in `application/json`.
*   **Multi-Tenancy:** All authenticated requests will be scoped to the user's `team_id` on the backend. A user cannot access data from another team, even if they guess the ID.
*   **Error Responses:** Standard HTTP status codes will be used. Error responses will contain a JSON body: `{ "error": { "code": "ERROR_CODE", "message": "..." } }`.

## 2. API Endpoints

### 2.1. Authentication (`/auth`)
*   `POST /auth/register`: Creates a new user and team.
*   `POST /auth/login`: Authenticates a user and returns a JWT.
*   `POST /auth/sso/google`: Initiates SSO login with Google.

### 2.2. Team Management (`/team`)
*   `GET /team/members`: Retrieves a list of all members in the user's team.
*   `POST /team/invites`: Sends email invitations to new team members.
*   `PUT /team/members/{user_id}/role`: Changes the role of a team member (Admin only).

### 2.3. Projects & Slides (`/projects`)
*   `GET /projects`: Retrieves all projects for the team.
*   `POST /projects`: Creates a new project.
*   `GET /projects/{project_id}/slides`: Retrieves slides for a specific project, with pagination (`?limit=50&cursor=...`).
*   `POST /projects/{project_id}/files/upload-url`: **[CRITICAL FOR SAAS]** Gets a secure, pre-signed S3 URL to which the client can directly upload a `.pptx` file. This prevents large file uploads from overwhelming the API server. The request returns the URL and a `file_id`. Once the client uploads the file, it notifies the backend to begin processing.

### 2.4. Global Search (`/search`)
*   `GET /search/all?query=...&limit=50&cursor=...`: Performs a global, paginated search across all slides the user has access to.

### 2.5. Assemblies (`/assemblies`) - Now Collaborative
*   `GET /assemblies`: Retrieves all presentation assemblies.
*   `POST /assemblies`: Creates a new, empty assembly.
*   `GET /assemblies/{assembly_id}`: Retrieves the state of a specific assembly, including the list of slides and comments.
*   `POST /assemblies/{assembly_id}/slides`: Adds a slide to an assembly.
*   `POST /assemblies/{assembly_id}/share`: Shares an assembly with a team member, granting them view or edit permissions.
*   `POST /assemblies/{assembly_id}/comments`: Adds a comment to a slide within an assembly.

### 2.6. PrezI AI Engine (`/prezi`)
*   `POST /prezi/interpret`: Takes a user's natural language command and returns the structured intent. The request body now includes team context.
*   `POST /prezi/plan`: Generates a Visual Plan.
*   `POST /prezi/execute`: **[ASYNCHRONOUS]** Executes a PrezI plan. Returns a `task_id`. The client will listen for progress on the WebSocket connection.
*   `POST /prezi/harmonize`: **[ASYNCHRONOUS]** Triggers the AI-powered style harmonization for a given assembly. Returns a `task_id`.

### 2.7. Brand Kit (`/brandkit`) - Admin Only
*   `GET /brandkit`: Retrieves the team's Brand Kit.
*   `POST /brandkit/logo`: Uploads a new logo.
*   `PUT /brandkit/colors`: Updates the team's official color palette.
*   `PUT /brandkit/fonts`: Updates the team's official fonts.

## 3. WebSocket API (`wss://api.prezi.ai/ws`)

The client will maintain a single, persistent WebSocket connection after login to receive real-time updates.

### Server-to-Client Events

*   **`TASK_PROGRESS`**: Provides real-time updates on asynchronous jobs (upload processing, AI execution).
    *   Payload: `{ "task_id": "string", "status": "processing", "message": "Analyzing slide 15 of 50...", "progress": 0.5 }`
*   **`ASSEMBLY_UPDATED`**: Sent to all connected clients when an assembly they are viewing is changed by another user.
    *   Payload: `{ "assembly_id": "string", "updated_by": { "user_id": "string", "name": "David" }, "changes": [{ "action": "add_slide", "slide_id": "string" }] }`
*   **`NEW_COMMENT`**: Sent when a new comment is added to an assembly.
    *   Payload: `{ "assembly_id": "string", "comment": { ...comment_object... } }`
*   **`USER_PRESENCE_CHANGED`**: Shows which users are currently viewing/editing an assembly.
    *   Payload: `{ "assembly_id": "string", "active_users": [{ "user_id": "string", "name": "Sarah" }] }`

This API specification provides the robust, secure, and scalable contract necessary for the PrezI SaaS platform. It prioritizes a responsive user experience by offloading heavy tasks to an asynchronous pipeline and using WebSockets for real-time collaborative updates.