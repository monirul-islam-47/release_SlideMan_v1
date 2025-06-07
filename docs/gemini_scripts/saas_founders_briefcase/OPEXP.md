Of course. The plan unfolds.

We have now specified the business logic and the construction plan for the SaaS platform. We must now create the final two operational documents that ensure the application is not only built correctly but is also professional, secure, and delightful for the end user from their very first click.

The next document is the **Operations & Experience Handbook**. For the SaaS version, this is arguably even more critical than for the desktop app. It defines the user's entire journey outside of the core application, including how they sign up, log in, manage their account, and get help. It is the blueprint for a professional and trustworthy service.

Here is **Document 9 of 10**, the definitive O&E Handbook for the PrezI SaaS platform.

---
---

### **Document 9 of 10: Operations & Experience (O&E) Handbook - SaaS Edition**

# PrezI Cloud: Operations & Experience (O&E) Handbook

*   **Version:** 2.0 (SaaS)
*   **Date:** June 7, 2025
*   **Status:** Finalized

## 1. User Authentication & Account Management

This section defines the user's journey for accessing and managing their account.

### 1.1. Sign-Up & Onboarding
*   **Flow:**
    1.  User lands on the marketing homepage and clicks "Sign Up Free."
    2.  They are directed to a simple sign-up form requiring `email` and `password`.
    3.  Upon submission, a verification email with a magic link is sent to their address.
    4.  Clicking the link verifies their email and logs them into the PrezI application for the first time.
*   **Single Sign-On (SSO):** Buttons for "Sign Up with Google" and "Sign Up with Microsoft" will be prominently displayed. This is the recommended path for most users.
*   **First Run Experience:** Immediately after their first login, the user is seamlessly guided through the "Guided Tour" as specified in the desktop O&E Handbook, but adapted for the web interface.

### 1.2. Login
*   A clean, focused login page will provide fields for `email` and `password`, as well as the Google and Microsoft SSO buttons.
*   A "Forgot Password?" link will trigger a secure password reset flow via email.

### 1.3. User Profile & Settings
*   A user-accessible "Account Settings" page will allow them to:
    *   Change their name and password.
    *   View their current subscription tier.
    *   Delete their account.

## 2. Team & Subscription Management (Admin Role)

This is the central hub for our paying customers.

*   **Team Invitation:** Admins can invite new members by entering their email addresses. Invitees will receive an email with a link to join the team.
*   **Role Management:** Admins can assign roles (`Admin`, `Creator`, `Viewer`) to team members from a simple user list interface.
*   **Billing Portal (Stripe Integration):** A secure "Billing" tab in the Admin settings will embed the Stripe customer portal. This portal will allow admins to:
    *   View their current plan (`Pro`, `Teams`).
    *   See the number of active seats and the price per seat.
    *   Update the credit card on file.
    *   View and download all past invoices.
    *   Upgrade, downgrade, or cancel their subscription.

## 3. Security & Compliance

*   **Data Encryption:** All data will be encrypted both in transit (TLS 1.3 everywhere) and at rest (using AWS's built-in encryption for RDS and S3).
*   **Password Policy:** Passwords will be securely hashed using a modern, strong algorithm (e.g., Argon2). We will enforce minimum password complexity.
*   **Two-Factor Authentication (2FA):** While not in the MVP, the system will be designed to easily add 2FA (via authenticator app) in a future release for enhanced security.
*   **Privacy Policy:** A clear, human-readable Privacy Policy will be accessible from the website footer and within the application. It will explicitly state what data is collected and how it is used.

## 4. Logging & Monitoring

*   **Application Logging:** All microservices will stream their logs to **AWS CloudWatch Logs**. This provides a centralized place to search and analyze logs from across the entire application.
*   **Performance Monitoring:** We will use **AWS CloudWatch** to monitor key performance metrics of our infrastructure (CPU utilization of RDS, number of messages in SQS queue, Lambda function execution times).
*   **Alerting:** Automated alerts will be configured to notify the development team via email or Slack if any critical error rates spike or performance metrics exceed established thresholds.

## 5. User-Facing Error Message Dictionary (SaaS Edition)

This ensures PrezI's personality remains consistent, even when dealing with web-specific issues.

| Error Code / Situation | Technical Reason | PrezI's User-Facing Message |
| :--- | :--- | :--- |
| **`NETWORK_OFFLINE`** | The user's browser loses internet connectivity. | "It seems you've gone offline. I'll save your current work locally and will automatically sync everything as soon as you reconnect." |
| **`SESSION_EXPIRED`** | The user's JWT authentication token has expired. | "For your security, I've logged you out after a period of inactivity. Please log back in to continue where you left off." |
| **`UPLOAD_FAILED`** | A file upload to S3 fails due to a network issue. | "The upload for `[filename]` was interrupted. No worries, just check your connection and feel free to drag it back in to try again." |
| **`PERMISSION_DENIED`**| A non-admin user tries to access an admin-only feature.| "That's an admin-level power! If you need access, you can ask your team's administrator to upgrade your role." |
| **`PLAN_LIMIT_REACHED`**| A free-tier user tries to exceed a plan limit (e.g., import a 4th presentation).| "You're a power user! You've reached the slide limit for the Free plan. To unlock unlimited slides and advanced AI features, you can upgrade to our Professional plan." |

This O&E Handbook provides the final layer of professional polish, ensuring the PrezI SaaS platform is not just a powerful tool, but a secure, trustworthy, and delightful service to use.