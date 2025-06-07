You have an exceptional understanding of the process. Your trust is the catalyst for this next phase. I am ready.

Let's build the visual and interactive roadmap for PrezI. This document will serve as the definitive storyboard for the user's entire journey, ensuring that the beautiful, fluid experience we've designed is translated perfectly into the final application. It will show every screen, every state, and every critical user path.

Here is the **Detailed UI Wireframes & User Flow Diagrams** document.

---

# PrezI: Detailed UI Wireframes & User Flow Diagrams

*   **Version:** 1.0
*   **Date:** June 15, 2025
*   **Author:** PrezI Vision Synthesis AI
*   **Status:** Finalized

## 1. Introduction

This document provides a comprehensive visual and navigational blueprint for the PrezI application. It translates the strategic goals from the **PRD** and the aesthetic rules from the **Design System** into tangible screen layouts and interaction flows. This guide is the primary reference for frontend development.

## 2. Core User Flow Diagrams

These diagrams illustrate the primary paths a user will take to accomplish their goals within PrezI.

### 2.1. Flow 1: First-Time User & Initial Project Setup

**Goal:** Guide a new user from a blank slate to having their first set of slides imported and ready.

```mermaid
graph TD
    A[Start Application] --> B(Display Main Workspace in 'Empty State');
    B --> C{User Clicks 'Create New Project'};
    C --> D[Show 'New Project' Modal];
    D --> E{User Enters Name & Clicks 'Create'};
    E --> F[Display Main Workspace - Library is Empty];
    F --> G(Show 'Import Your First Presentation' CTA);
    G --> H{User Drags/Drops or Clicks to Import .pptx files};
    H --> I[Show 'Import Progress' Overlay];
    I -- On Success --> J[Hide Overlay, Animate Slides into Library];
    J --> K[Display 'Workflow Help' Tip: "Tag your slides to find them!"];
    I -- On Error --> L[Show 'Import Error' Modal with details];
    L --> F;
```

### 2.2. Flow 2: Search, Assemble, and Export (The Core Loop)

**Goal:** The day-to-day workflow of finding slides and building a presentation manually.

```mermaid
graph TD
    A[Open Project with Populated Library] --> B{User types in Command Bar};
    B --> C[UI dynamically filters Slide Library Grid];
    C --> D{User drags a slide from Library};
    D --> E[Assembly Panel highlights with a 'Drop Zone'];
    E --> F{User drops slide into Assembly};
    F --> G[Slide animates into Assembly list];
    G --> H[Assembly count & duration estimate updates];
    H --> B; % User can continue searching
    H --> I{User clicks 'Export' in Assembly Panel};
    I --> J[Show 'Export Options' Modal];
    J --> K{User confirms export settings};
    K --> L[Show 'Export Progress' Overlay];
    L --> M[On Success, show 'Success!' notification];
    M --> N[Trigger system to open exported .pptx file];
```

### 2.3. Flow 3: PrezI-Powered Creation (The "Magic Moment")

**Goal:** The AI-driven workflow that delivers the "5 hours to 5 minutes" promise.

```mermaid
graph TD
    A[User types intent, e.g., "Create investor pitch"] --> B[UI sends command to PrezI Engine];
    B --> C[PrezI Engine returns Visual Plan];
    C --> D[Display 'PrezI's Plan' Modal];
    D --> E{User reviews plan and clicks 'Execute Plan'};
    E --> F[Show 'PrezI Execution' Progress Overlay];
    F --> G[Individual steps check off as they complete];
    G --> H[Assembly Panel populates in real-time as PrezI works];
    H --> I{Plan completes};
    I --> J[Display 'Success!' modal with a celebratory message from PrezI];
    J --> K[User now has a fully assembled deck, ready for review or export];
```

## 3. Detailed Screen Wireframes

These wireframes specify the layout and state for each key screen in the application. All components must adhere to the **UI/UX Design System**.

### 3.1. Screen: Main Workspace

This is the primary interface of the application.

#### 3.1.1. Empty State
*   **When:** On first launch or when a new, empty project is created.
*   **Layout:**
    *   **Left & Right Panels:** Visible but mostly empty.
    *   **Main Content Area:** Dominated by a large, friendly welcome message.
        *   **Icon:** A large, inviting `+` or folder icon.
        *   **Headline (H3):** "Let's Build Something Brilliant"
        *   **Body Text:** "Import your first PowerPoint files to begin building your slide universe."
        *   **Primary CTA Button:** "Import Presentations"
        *   **Secondary Text:** "Or drag and drop your files anywhere."

#### 3.1.2. Loading State
*   **When:** While slides are being imported and processed.
*   **Layout:**
    *   **Main Content Area:** The grid is populated with **"Skeleton Loader"** cards. These are gray, card-shaped placeholders with a subtle, shimmering animation to indicate loading.
    *   **Status Bar:** Displays clear progress, e.g., "⚡️ Processing: `Q4_Results.pptx` (Slide 32 of 78)..."

#### 3.1.3. Ideal State (Populated)
*   **When:** The default view when a project is open and contains slides.
*   **Layout:**
    *   **Header:**
        *   Left: App Logo/Name.
        *   Center: **Universal Command Bar** (see Component Library).
        *   Right: PrezI Status Indicator, User Profile/Settings icon.
    *   **Left Sidebar (`280px`):**
        *   Top: Project Info (Name, slide/file count).
        *   Middle: **Keyword Panel** (list of clickable Keyword Pills).
        *   Bottom: Quick Actions (`+ Import Files`, `🏷️ Tag All`).
    *   **Main Content Area (Slide Library):**
        *   Top: View controls (`Grid`/`List`), Sort options.
        *   Body: A responsive grid of **Slide Cards**. Each card shows a thumbnail.
    *   **Right Sidebar (`320px`, Collapsible):**
        *   Top: **Assembly Panel** with title, slide count, and duration.
        *   Body: Reorderable list of assembled slides or an empty state prompt ("Drag slides here to build your story").
        *   Bottom: **Export CTA Button**.

#### 3.1.4. Search Results State
*   **When:** After a user types in the Command Bar.
*   **Layout:**
    *   The Main Content Area animates to reflect the results.
    *   **Matching Slides:** Remain at full opacity.
    *   **Non-Matching Slides:** Fade to a lower opacity (e.g., `0.3`) but remain in place to maintain grid stability.
    *   A header appears above the grid: "Showing 42 results for 'revenue charts'."

### 3.2. Modal: PrezI's Visual Plan
*   **When:** Triggered by an AI creation command.
*   **Layout:** A modal overlay that dims the main workspace.
    *   **Header:** PrezI Avatar icon and Title (H4): "Here's My Plan".
    *   **Body:** A numbered, vertical list of steps.
        *   Each step has a `Title` (bold) and `Details` (secondary text).
        *   e.g., "**1. Find Opening Hook**" > "Searching for high-impact title and agenda slides."
    *   **Footer:**
        *   **Primary CTA Button (Success):** "✅ Execute Plan"
        *   **Secondary Button:** "🔧 Modify" (A future feature)
        *   **Tertiary Link Button:** "Cancel"

### 3.3. Modal: Export Options
*   **When:** User clicks "Export."
*   **Layout:** A simple, clean modal.
    *   **Title (H4):** "Export Presentation"
    *   **Form Fields:**
        *   **Filename:** Text Input, pre-filled with a suggested name (e.g., `Investor-Pitch-2025-06-07`).
        *   **Location:** File path input with a "Browse..." button.
        *   **Format:** Radio buttons or dropdown for `.pptx` (default) and `.pdf`.
    *   **Footer:**
        *   **Primary CTA Button:** "Export Now"
        *   **Secondary Button:** "Cancel"

### 3.4. Overlay: Progress Indicators
*   **When:** During any long-running backend task (Import, Export, AI Execution).
*   **Layout:**
    *   **For Import/Export:** A non-intrusive overlay in the bottom-right corner or a progress bar in the Status Bar. It must not block the user from continuing to work.
    *   **For AI Execution:** A more prominent modal overlay, as this is a primary action the user is waiting for. It displays the same step-list from the Visual Plan, with a checkmark appearing next to each step as it completes.

This document provides the explicit visual and navigational structure for PrezI. By combining these wireframes and flows with the rules in the **Design System**, a developer has a precise blueprint for building the application's user interface.