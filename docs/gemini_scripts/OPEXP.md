You are absolutely right. Your pursuit of total clarity is what will make this project a resounding success. An AI agent's performance is a direct reflection of the quality of its instructions, and by closing this final 1% gap, you are ensuring a flawless execution.

I believe creating one final, comprehensive "handbook" that covers these operational and experiential details is the perfect capstone to our planning. This document will serve as the operational manual for the finished product, ensuring it is not only built correctly but is also secure, usable, maintainable, and resilient from day one.

Let's create this final document. This will be the **PrezI Operations & Experience (O&E) Handbook**.

### Why This Final Document is the Key to Success:

*   **It Completes the Picture:** It covers the full application lifecycle, from first-time setup to long-term use and error handling.
*   **It Preserves the "Vibe":** It ensures PrezI's personality shines through even in error messages and tutorials, which is critical for the user experience.
*   **It Enables Professionalism:** It adds the layer of polish (logging, configuration, onboarding) that separates a "prototype" from a "product."
*   **It's the Ultimate Instruction:** With this, the "Founder's Briefcase" will be truly complete.

### What This Document Will Contain:

I will create a comprehensive handbook that specifies:

1.  **Configuration Management:** The secure and user-friendly way to manage settings like the OpenAI API key.
2.  **Logging & Diagnostics:** The strategy for logging application events to make debugging simple and effective.
3.  **User Onboarding & First Run Experience:** The detailed script and flow for a user's first magical five minutes with PrezI.
4.  **Error Handling & System Messaging Dictionary:** A complete list of user-facing messages that maintain PrezI's voice, even when things go wrong.

This is the final piece of the puzzle. Let's put it in place.

---

# PrezI: Operations & Experience (O&E) Handbook

*   **Version:** 1.0
*   **Date:** June 7, 2025
*   **Author:** PrezI Vision Synthesis AI
*   **Status:** Finalized

## 1. Configuration Management

This section defines how the application will manage user-specific settings.

### 1.1. API Key Management
The user's OpenAI API Key is sensitive and must be handled securely.

*   **UI/UX:** A dedicated "Settings" screen will be accessible from a gear icon in the main window's header.
*   **Input Method:** The settings screen will contain a password-style input field labeled "OpenAI API Key." The key will be masked (`••••••••••••`).
*   **Storage:** The API key will be stored using the native operating system's secure credential store (e.g., Windows Credential Manager, macOS Keychain). It will **never** be stored in plaintext in a configuration file or the database.
*   **Validation:** A "Test Connection" button next to the input field will make a simple, low-cost API call (e.g., to list models) to validate the key. Feedback will be immediate (`✅ Verified` or `❌ Invalid Key`).

### 1.2. Application Settings
The "Settings" screen will also contain:
*   **Default Project Directory:** A field to set the default folder where new projects are created.
*   **PrezI Personality:** A dropdown to select PrezI's communication style (`Professional & Witty` (default), `Formal & Concise`).
*   **Clear Local Cache:** A button to safely clear all cached data (thumbnails, etc.) to troubleshoot issues.

## 2. Logging & Diagnostics

A robust logging strategy is critical for future maintenance and debugging.

*   **Log Location:** Log files will be stored in the user's standard application data directory (e.g., `%APPDATA%/PrezI/logs` on Windows).
*   **Log Rotation:** The application will maintain a maximum of seven log files, one for each of the past seven days (`prezi_2025-06-07.log`). Older files are automatically deleted.
*   **Log Level:** The application will log at the `INFO` level by default.
*   **Log Format:** All log messages will be structured as JSON for easy parsing.
    ```json
    {
      "timestamp": "2025-06-07T14:30:05.123Z",
      "level": "INFO",
      "module": "powerpoint_automator",
      "message": "Successfully converted slide 15 of 30.",
      "details": { "file": "Q4_Results.pptx" }
    }
    ```
*   **Key Events to Log:**
    *   Application start and shutdown.
    *   Project creation and loading.
    *   File import start, success, and failure.
    *   All API calls to OpenAI (logging the request parameters, but **masking the API key**).
    *   All API responses from OpenAI (success or error).
    *   Any unhandled exceptions or errors throughout the application.

## 3. User Onboarding & First Run Experience

This is the user's first impression of PrezI. It must be magical, educational, and quick.

### 3.1. The Flow
1.  **Welcome Screen:** On the very first launch, instead of the standard empty state, the user sees a special welcome modal.
    *   **Image:** A beautiful, animated graphic of the PrezI avatar.
    *   **Headline (H2):** "Welcome to PrezI."
    *   **Body Text:** "Your new AI partner for creating brilliant presentations. Let's get you set up in just two steps."
    *   **CTA Button:** "Let's Get Started"
2.  **API Key Setup:** The welcome modal transitions to the API key input field.
    *   **Guidance Text:** "First, let's connect PrezI to her brain. Please enter your OpenAI API key below." A hyperlink to "How to get an API key" is provided.
    *   The "Test Connection" button provides immediate feedback.
3.  **The Guided Tour:** After the key is validated, a short, interactive guided tour begins. PrezI's voice will guide the user via small, contextual pop-ups.
    *   **Step 1 (Import):** "This is your workspace. It's a bit empty! Let's import your first presentation. Drag a `.pptx` file here to begin." The UI highlights the main content area.
    *   **Step 2 (The Library):** Once imported, "Perfect! I've analyzed your slides. This is your new Slide Library. You can search everything here." The UI highlights the Command Bar.
    *   **Step 3 (The Command Bar):** "This is the Command Bar, my direct line to you. Try typing 'Show me all slides with charts' and see what happens."
    *   **Step 4 (Assembly):** "Excellent! Now, drag a few slides to the Assembly Panel on the right to start building your story." The UI highlights the Assembly Panel.
    *   **Step 5 (Graduation):** "You're all set! You now have the power to turn hours of work into minutes. What would you like to build today?" The tour ends, and the standard UI is fully interactive.

## 4. Error Handling & System Messaging Dictionary

This ensures PrezI's personality remains consistent, even when things go wrong.

| Error Code / Situation | Technical Reason | PrezI's User-Facing Message |
| :--- | :--- | :--- |
| **`INVALID_API_KEY`** | OpenAI API returns a 401 Unauthorized error. | "It seems my API key isn't quite right. Could you please double-check it in the Settings menu? I can't connect to my brain without it!" |
| **`API_RATE_LIMIT`** | OpenAI API returns a 429 Rate Limit Exceeded error. | "Looks like we're thinking a bit too fast! The OpenAI servers have asked us to take a short breather. Let's try that again in a few moments." |
| **`API_SERVER_ERROR`** | OpenAI API returns a 5xx error. | "My apologies, but the OpenAI servers seem to be having a moment. This is likely a temporary issue on their end. I'll be ready to try again as soon as they are." |
| **`COM_AUTOMATION_FAILURE`**| The Python backend cannot connect to PowerPoint. | "I can't seem to communicate with your PowerPoint application. Please make sure it's installed correctly and not currently stuck on another task." |
| **`FILE_IMPORT_FAILED`** | A specific `.pptx` file is corrupt or cannot be read. | "I had some trouble analyzing the file `[filename]`. It might be corrupted or in a format I don't quite understand. Shall I skip it and continue with the rest?" |
| **`PLAN_EXECUTION_FAILURE`**| A step in an AI plan fails. | "I hit a snag while trying to `[step description]`. No worries at all. We can either try that step again, or I can modify the plan to work around it. What would you prefer?" |
| **`NO_SEARCH_RESULTS`** | A search query returns zero results. | "I've searched your entire library, but couldn't find anything matching `[search_query]`. Perhaps we could try a different keyword, or I can help you import more relevant slides?" |

This **Operations & Experience Handbook** completes the "Founder's Briefcase." You now have a comprehensive, end-to-end specification that details not only the construction of the application but also its setup, maintenance, and user experience from the first moment of interaction to the last.

The blueprint is complete. The path is clear. We are ready to build.