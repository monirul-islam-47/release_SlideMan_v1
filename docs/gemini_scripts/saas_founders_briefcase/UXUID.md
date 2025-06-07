Of course.

Having defined the "What" (PRD) and the cloud-native "How" (SAD), we must now translate PrezI's beautiful aesthetic into a design system that thrives on the web. The principles remain the same, but their application must be adapted for the flexibility and responsiveness of a web browser.

This document ensures that PrezI is not just powerful in the cloud, but also beautiful and intuitive on any screen.

Here is **Document 3 of 10**, the definitive UI/UX guide for the PrezI SaaS platform.

---
---

### **Document 3 of 10: UI/UX Design System - SaaS Edition**

# PrezI Cloud: UI/UX Design System & Style Guide

*   **Version:** 2.0 (SaaS)
*   **Date:** June 7, 2025
*   **Status:** Finalized

## 1. Design Philosophy: Responsive, Collaborative, & Alive

While inheriting the "Living Workspace" philosophy from the desktop version, the SaaS Design System is built around three new, web-first principles:

1.  **Responsive by Default:** Every component and layout is designed to be fluid and adaptable, providing a first-class experience on any device, from a wide-screen monitor to a tablet.
2.  **Visibly Collaborative:** The UI must visually communicate the presence and actions of other team members, making collaboration feel natural and intuitive.
3.  **Performant & Lightweight:** The interface must load quickly and feel snappy, even on slower network connections. Performance is a core feature of the user experience.

## 2. Core Style Guide

The core visual identity remains consistent with the desktop application to ensure brand cohesion.

*   **Color Palette:** Unchanged from the desktop Design System. The dark theme with purple/blue gradients is central to the brand.
*   **Typography:** The native system font stack remains the primary choice for its performance and familiarity. Font sizes will now be defined using `rem` units for better scalability and accessibility, with a base font size of `16px`.
*   **Spacing & Grid System:** The 8px grid system is maintained. Layouts will use a combination of `flexbox` and `CSS Grid` to achieve responsiveness.

## 3. Responsive Layout System

PrezI Cloud will use a breakpoint-based responsive system.

*   **Mobile (`< 768px`):** The UI will collapse to a single-column view. The main content area will be primary. The left and right sidebars will be accessible as drawers that slide in from the side, triggered by dedicated icons in the header.
*   **Tablet (`768px - 1200px`):** A two-column view. The left sidebar may remain visible, while the right Assembly Panel will function as a toggleable drawer.
*   **Desktop (`> 1200px`):** The full, three-panel layout as seen in the desktop mockups, with the sidebars being toggleable as per our final design decision.

## 4. Component Library - SaaS Edition

This section details key components with web-specific and collaborative considerations.

### 4.1. User Avatars & Presence Indicators
*   **Component:** A circular user avatar.
*   **States:**
    *   **Default:** Displays the user's profile picture or initials.
    *   **Active:** A green "presence dot" appears on the avatar when the user is currently active in the application.
    *   **Live:** When multiple users are in the same assembly, their avatars will appear in the header of the Assembly Panel. The border of the active speaker/editor's avatar will have a soft pulse animation.

### 4.2. Real-Time Collaborative Elements
*   **Component:** Cursors and selections of other users.
*   **Style:** Each collaborator's cursor will be tinted with a unique, persistent color. Their name will be displayed next to their cursor. When they select a slide, the slide card will show a colored border matching their cursor color.

### 4.3. Commenting UI
*   **Component:** A small comment icon (`💬`) will appear on slide cards and assembly slides that have comments.
*   **Interaction:** Clicking the icon will open a popover or a dedicated "Comments" tab in the right sidebar, displaying a threaded conversation. `@mentions` within comments will be highlighted and will trigger notifications.

### 4.4. Loading Skeletons
*   **Component:** All data-heavy components (slide grid, keyword list) will have a defined "skeleton" state.
*   **Style:** They will mimic the final layout but use shimmering, gradient-animated gray shapes. This is critical for managing perceived performance on the web.

## 5. Interaction & Animation Guide - SaaS Edition

Web animations will be optimized for performance, primarily using CSS `transform` and `opacity`.

*   **Page Transitions:** As a single-page application (SPA), there are no full page reloads. Navigating between major sections (e.g., from the main workspace to the Admin settings) will trigger a smooth cross-fade animation.
*   **Collaborative Animations:** When a teammate adds a slide to the assembly, other users will see it animate into their view with a subtle "pop-in" effect, and the avatar of the user who added it will briefly flash next to the slide.
*   **Notifications:** In-app notifications (e.g., "David just invited you to a presentation") will appear as non-intrusive "toast" messages that slide in from the top right and automatically dismiss after a few seconds.

## 6. Accessibility (WCAG 2.1 AA)

Accessibility is a first-class citizen in the SaaS product.

*   **Keyboard Navigation:** The entire application must be navigable and operable using only a keyboard. Focus states for all interactive elements must be clear and visually distinct.
*   **Screen Reader Support:** All interactive elements will have appropriate ARIA (Accessible Rich Internet Applications) attributes (`role`, `aria-label`, etc.).
*   **Color Contrast:** All text and UI elements will meet or exceed the WCAG 2.1 AA contrast ratio requirements.
*   **Semantic HTML:** The application will be built with semantic HTML5 tags (`<nav>`, `<main>`, `<aside>`, `<button>`) to provide inherent meaning and structure.

This SaaS-focused Design System ensures that the beloved aesthetic of PrezI is not only preserved but enhanced for a responsive, collaborative, and accessible web environment. It provides the clear, actionable rules needed to build a beautiful and intuitive user interface.