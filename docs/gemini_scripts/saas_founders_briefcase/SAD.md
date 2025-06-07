Of course. We move to the next foundational document.

With the "What" and "Why" of the PrezI SaaS platform clearly defined in the PRD, we must now architect the "How." This requires a completely different approach from the desktop application. We are no longer building a self-contained program; we are designing a scalable, secure, and resilient cloud-native system capable of serving thousands of users.

This **System Architecture Document** is the master technical blueprint for that system.

Here is **Document 2 of 10**, the definitive architecture for the PrezI SaaS platform.

---
---

### **Document 2 of 10: System Architecture Document - SaaS Edition**

# PrezI Cloud: System Architecture Document (SAD)

*   **Version:** 2.0 (SaaS)
*   **Date:** June 7, 2025
*   **Status:** Finalized

## 1. Architectural Vision: Scalable, Secure, & Microservice-Oriented

The architecture for PrezI Cloud is designed to be a modern, scalable, and resilient cloud-native platform. It will be built on a **Microservice Architecture**, where different parts of the application are independent, communicating services. This approach ensures high availability, independent scalability of components, and easier maintenance.

The entire system will be built upon a major cloud provider (e.g., AWS, Google Cloud, or Azure) to leverage managed services and global infrastructure. For this document, we will use **AWS** as the example provider, though the principles are transferable.

## 2. High-Level Architecture Diagram

```
+------------------+      +-------------------------+      +---------------------------+
|   User's Browser |----->|  Cloudflare (CDN & WAF) |----->| AWS API Gateway (REST/WS) |
+------------------+      +-------------------------+      +---------------------------+
        ^                                                               |
        | (Loads React App)                                             | (Routes requests)
        |                                                               v
+--------------------------+          +-------------------------------------------------------------+
| AWS S3 Bucket (Frontend) |<---------+                      AWS VPC (Private Network)              +
| - Stores static React    |          |                                                             |
|   app files (HTML/CSS/JS)|          | +-----------------+  +------------------+  +----------------+ |
+--------------------------+          | |   Auth Service  |  |  Slides Service  |  |  PrezI AI Svc  | |
                                      | | (e.g., Lambda)  |  | (e.g., ECS Task) |  | (e.g., Lambda) | |
                                      | +-------+---------+  +--------+--------+  +--------+-------+ |
                                      |         |                   |                   |            |
                                      |         | (User Pool)       | (Read/Write)      | (API Call) |
                                      |         v                   v                   v            |
                                      | +-----------------+  +------------------+  +----------------+ |
                                      | | AWS Cognito     |  |   PostgreSQL DB  |  |   OpenAI API   | |
                                      | | (User Mgmt)     |  | (e.g., AWS RDS)  |  | (External)     | |
                                      | +-----------------+  +------------------+  +----------------+ |
                                      |                                                             |
                                      |            +------------------------------------+           |
                                      |            |    Asynchronous Processing Pipeline    |           |
                                      |            +------------------------------------+           |
                                      |                          | (Events)                         |
                                      |                          v                                  |
                                      |                  +----------------+                       |
                                      |                  |  AWS SQS Queue |                       |
                                      |                  +----------------+                       |
                                      |                          | (Triggers)                       |
                                      |                          v                                  |
                                      |              +--------------------------+                   |
                                      |              | Slide Processing Service |                   |
                                      |              |      (e.g., ECS Fargate) |                   |
                                      |              +--------------------------+                   |
                                      |                          |                                  |
                                      |        (Store/Read PPTX) v                                  |
                                      |                +------------------+                       |
                                      |                |   AWS S3 Bucket  |                       |
                                      |                | (File Storage)   |                       |
                                      |                +------------------+                       |
                                      +-------------------------------------------------------------+
```

## 3. Component Deep Dive

### 3.1. Frontend (The Web App)
*   **Technology:** **React (with Vite)** using TypeScript.
*   **Hosting:** The compiled, static frontend assets (`index.html`, CSS, JS) will be hosted on **AWS S3** and distributed globally via **AWS CloudFront (CDN)**.
*   **Purpose:** To provide the entire interactive user experience in the browser. It is a single-page application (SPA) that communicates with the backend via the API Gateway.

### 3.2. API Gateway & Edge
*   **Technology:** **AWS API Gateway** and **Cloudflare**.
*   **Purpose:**
    *   **Cloudflare:** Acts as the entry point for all user traffic, providing CDN caching, DDoS protection, and a Web Application Firewall (WAF) for security.
    *   **AWS API Gateway:** Manages all API traffic, routing requests to the appropriate backend microservice. It handles both RESTful API calls and WebSocket connections for real-time features.

### 3.3. Backend Microservices
These services will run within a secure AWS Virtual Private Cloud (VPC).

*   **Authentication Service:**
    *   **Technology:** AWS Lambda function (serverless).
    *   **Responsibilities:** Handles user sign-up, login, and token validation. It integrates directly with **AWS Cognito**.
    *   **AWS Cognito:** A fully managed service for user identity management, handling user pools, password policies, and integration with SSO providers (Google, Microsoft).

*   **Slides Service:**
    *   **Technology:** A containerized Python application (using FastAPI) running on **Amazon ECS (Elastic Container Service)**.
    *   **Responsibilities:** Manages all core business logic related to projects, slides, keywords, and assemblies. Handles all CRUD operations by communicating with the primary database.

*   **PrezI AI Service:**
    *   **Technology:** AWS Lambda function (Python).
    *   **Responsibilities:** A stateless service that contains all the AI logic and prompt engineering. It receives requests from the API Gateway, communicates with the external **OpenAI API**, and returns the structured results. It is separate from the Slides Service to scale independently.

### 3.4. Asynchronous Processing Pipeline
This is the core of the SaaS platform's power, allowing it to handle heavy tasks without blocking the user.

*   **File Upload:** When a user uploads a `.pptx` file, it is first sent directly to a secure, pre-signed URL on an **AWS S3 Bucket** designated for raw file storage.
*   **Event Trigger:** Upon successful upload, the S3 bucket triggers an event message.
*   **Message Queue:** This message (containing the file path and user ID) is placed into an **AWS SQS (Simple Queue Service)** queue. This decouples the upload from the processing and ensures no task is lost.
*   **Processing Service:**
    *   **Technology:** A powerful, containerized service running on **AWS Fargate** (a serverless container engine). Fargate can automatically scale up with many worker instances if many users upload files simultaneously.
    *   **Responsibilities:** This service pulls a message from the SQS queue, downloads the corresponding `.pptx` file from S3, performs all heavy processing (slide conversion, text extraction), calls the PrezI AI service for analysis, and then populates the primary database with the results.

### 3.5. Data Storage

*   **Primary Database:**
    *   **Technology:** **PostgreSQL** running on **AWS RDS (Relational Database Service)**.
    *   **Rationale:** We are moving from SQLite to PostgreSQL because RDS provides managed, scalable, and production-ready features like automated backups, read replicas, and high availability, which are essential for a SaaS product. The database schema will be designed for multi-tenancy.
*   **File Storage:**
    *   **Technology:** **AWS S3**.
    *   **Usage:** There will be separate S3 buckets for:
        *   Raw uploaded `.pptx` files.
        *   Generated slide thumbnail images.
        *   User avatars and other static assets.
        *   Final exported presentations.

## 4. Key Architectural Decisions

*   **Serverless First:** We will use serverless technologies (Lambda, Fargate) wherever possible. This reduces operational overhead and allows for automatic scaling based on demand, which is highly cost-effective for a startup.
*   **Containerization:** Core stateful services like the Slides Service will be containerized using Docker, allowing for consistent development and deployment environments.
*   **Multi-Tenancy:** The database schema will be designed with a `team_id` on every table to ensure that data from one company is strictly isolated from another.
*   **Infrastructure as Code (IaC):** The entire cloud infrastructure will be defined in code using a tool like **Terraform** or **AWS CDK**. This allows us to create, update, or replicate the entire environment with a single command, ensuring consistency and disaster recovery.

This SaaS architecture provides a robust, secure, and highly scalable foundation upon which to build the future of PrezI as a collaborative, cloud-native platform.